package com.ucsf.demo;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.os.PowerManager;
import android.util.Log;

import com.estimote.sdk.Beacon;
import com.google.android.gms.common.ConnectionResult;
import com.google.android.gms.common.api.GoogleApiClient;
import com.google.android.gms.common.api.ResultCallback;
import com.google.android.gms.common.api.Status;
import com.google.android.gms.wearable.DataApi;
import com.google.android.gms.wearable.DataMap;
import com.google.android.gms.wearable.PutDataMapRequest;
import com.google.android.gms.wearable.PutDataRequest;
import com.google.android.gms.wearable.Wearable;

import java.util.Calendar;
import java.util.GregorianCalendar;
import java.util.List;

/** Class responsible of ranging beacons every 30 seconds in background. */
public class RangingService extends BroadcastReceiver implements
        GoogleApiClient.ConnectionCallbacks,
        GoogleApiClient.OnConnectionFailedListener
{
    private static final String TAG                 = "RangingService";
    private static final String KEY_PATIENT         = "patient";
    private static final String KEY_ROOM            = "room";
    private static final String KEY_TIMESTAMP       = "timestamp";
    private static final int    MAX_QUEUE_SIZE      = 100;

    private GoogleApiClient mGoogleApiClient = null;

    /**
     * Callback responsible of closing the connection when all the entries have been
     * successfully sent to the phone.
     */
    private class Callback implements ResultCallback<DataApi.DataItemResult> {
        private int mPendingEntries;

        public Callback(int pendingEntries) {
            mPendingEntries = pendingEntries;
        }

        @Override
        public void onResult(DataApi.DataItemResult dataItemResult) {
            Status status = dataItemResult.getStatus();
            if (status.isSuccess()) {
                synchronized (RangingService.this) { // Prevents two parallel modifications
                    if (--mPendingEntries == 0) { // All the entries have been sent
                            mGoogleApiClient.disconnect();
                            mGoogleApiClient = null; // To avoid memory leaks
                    }
                }
            } else {
                // Something gone wrong
                Log.e(TAG, "ERROR: failed to putDataItem, status code: "
                        + status.getStatusCode());
                // TODO do we have to save the item?
            }
        }
    }

    @Override
    public void onReceive(Context context, Intent intent) {
        PowerManager pm = (PowerManager) context.getSystemService(Context.POWER_SERVICE);
        PowerManager.WakeLock wl = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "");
        wl.acquire();

        // Get the closest beacon
        BeaconMonitoring bm  = BeaconMonitoring.getInstance();
        Beacon closestBeacon = bm.getClosestBeacon(context);

        // Changes indicates new room location
        if(closestBeacon != bm.getPreviousClosestBeacon() && // in case of null pointer
                !closestBeacon.equals(bm.getPreviousClosestBeacon())) {
            bm.setPreviousClosestBeacon(closestBeacon);

            // Get the current room
            String room = bm.getRoom(closestBeacon);

            // Get the current timestamp
            Calendar currentTime = GregorianCalendar.getInstance();
            String timestamp = String.format("%d.%d.%d-%d.%d.%d",
                    currentTime.get(Calendar.YEAR),
                    currentTime.get(Calendar.MONTH) + 1,
                    currentTime.get(Calendar.DAY_OF_MONTH),
                    currentTime.get(Calendar.HOUR_OF_DAY),
                    currentTime.get(Calendar.MINUTE),
                    currentTime.get(Calendar.SECOND));

            // Display the changes
            Log.d(TAG, "New room is " + bm.getPatientID() + "'s " + room);
            Log.d(TAG, "Timestamp: " + timestamp);

            ((WearActivity) context).onBeaconRanging(bm.getPatientID(), room, timestamp);

            List<BeaconMonitoring.Entry> pendingEntries = bm.getPendingEntries();
            synchronized (pendingEntries) { // Prevent parallel changes on the entries
                // Add the new entry containing the current room and current timestamp
                pendingEntries.add(new BeaconMonitoring.Entry(room, timestamp));

                // If the number of entries is sufficient, send them to the phone
                if (pendingEntries.size() > MAX_QUEUE_SIZE) {
                    synchronized (this) { // Prevent parallel changes on the connection
                        // Create the google API if needed
                        if (mGoogleApiClient == null) {
                            mGoogleApiClient = new GoogleApiClient.Builder(context)
                                    .addApi(Wearable.API)
                                    .addConnectionCallbacks(this)
                                    .addOnConnectionFailedListener(this)
                                    .build();
                        }

                        // Start the connection if needed
                        if (!mGoogleApiClient.isConnected()) {
                            mGoogleApiClient.connect();
                        } else {
                            // The API is already connected, we can directly send the entries
                            sendEntries();
                        }
                    }
                }
            }
        }

        wl.release();
    }

    @Override
    public void onConnected(Bundle connectionHint) {
        Log.d(TAG, "onConnected(): Successfully connected to Google API client.");
        sendEntries(); // Send entries since we are connected now
    }

    @Override
    public void onConnectionSuspended(int cause) {
        Log.d(TAG, "onConnectionSuspended(): Connection to Google API client was suspended.");
        // Nothing to change, connection will be reestablished when needed
    }

    @Override
    public void onConnectionFailed(ConnectionResult result) {
        Log.e(TAG, "onConnectionFailed(): Failed to connect, with result: " + result);
        // Nothing to change, connection will be reestablished when needed
    }

    /**
     * Send data using Android Wear data layer API
     * http://developer.android.com/training/wearables/data-layer/data-items.html
     * use producer-consumer model where watch creates data and phone deletes data
     * each data entry has unique identifier based on timestamp
     * @note If the handset and wearable devices are disconnected, the data is
     * buffered and synced when the connection is re-established."
     * this is why the dataAPI is used over the messageAPI
     */
    private void sendEntries() {
        BeaconMonitoring bm = BeaconMonitoring.getInstance();
        List<BeaconMonitoring.Entry> pendingEntries = bm.getPendingEntries();

        synchronized (pendingEntries) { // Prevent parallel changes on the entries
            if (pendingEntries.size() > MAX_QUEUE_SIZE) { // Check that we still need to send entries
                Callback callback = new Callback(pendingEntries.size());

                // Create a request for each pending entry
                synchronized (this) { // Prevent parallel changes on the connection
                    for (BeaconMonitoring.Entry entry : pendingEntries) {
                        PutDataMapRequest dataMapRequest =
                                PutDataMapRequest.create("/entry:" + entry.getTimestamp());

                        DataMap dataEntry = dataMapRequest.getDataMap();
                        dataEntry.putString(KEY_PATIENT  , bm.getPatientID());
                        dataEntry.putString(KEY_ROOM     , entry.getRoom());
                        dataEntry.putString(KEY_TIMESTAMP, entry.getTimestamp());

                        PutDataRequest request = dataMapRequest.asPutDataRequest();
                        Log.d(TAG, "Generating DataItem: " + request);

                        Wearable.DataApi.putDataItem(mGoogleApiClient, request)
                                .setResultCallback(callback);
                    }
                }

                // Clear the pending entries list
                pendingEntries.clear();
            }
        }
    }

}

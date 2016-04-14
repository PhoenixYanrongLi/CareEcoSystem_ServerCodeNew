package com.ucsf.demo;

import android.net.Uri;
import android.util.Log;

import com.google.android.gms.common.ConnectionResult;
import com.google.android.gms.common.api.GoogleApiClient;
import com.google.android.gms.common.data.FreezableUtils;
import com.google.android.gms.wearable.DataEvent;
import com.google.android.gms.wearable.DataEventBuffer;
import com.google.android.gms.wearable.DataMap;
import com.google.android.gms.wearable.DataMapItem;
import com.google.android.gms.wearable.Wearable;
import com.google.android.gms.wearable.WearableListenerService;

import java.util.List;
import java.util.concurrent.TimeUnit;


/**
 *  This listener service receives data from the watch
 */
public class DataLayerListenerService extends WearableListenerService {

    private static final String TAG = "DataLayerListenerService";
    private String patient;
    private String room;
    private String timestamp;
    private static final String PATIENT_KEY = "patient";
    private static final String ROOM_KEY = "room";
    private static final String TIMESTAMP_KEY = "timestamp";
    private static final String START_ACTIVITY_PATH = "/start-activity";

    GoogleApiClient mGoogleApiClient;  // package private -- should be used for all calls
    private DBAdapter mDBHelper;

    @Override
    public void onCreate() {
        Log.w(TAG, "DO I EXIST??");
        super.onCreate();

        // open Google API connection
        mGoogleApiClient = new GoogleApiClient.Builder(this)
                .addApi(Wearable.API)
                .build();
        mGoogleApiClient.connect();

        // open SQLite database connection
        mDBHelper = new DBAdapter(this);
        try {
            mDBHelper.open();
        } catch(Exception e) {
            Log.e(TAG,"Failed to open SQLite database");
        }

        /* might use this to launch wearable app whenever a room change occurs
        // Trigger an AsyncTask that will query for a list of connected nodes and send a
        // "start-activity" message to each connected node.
        new StartWearableActivityTask().execute();
        Log.d(TAG, "Generating RPC");
        */
    }

    @Override
    public void onDataChanged(DataEventBuffer dataEvents) {
        Log.w(TAG, "onDataChanged: " + dataEvents);

        final List<DataEvent> events = FreezableUtils.freezeIterable(dataEvents);
        dataEvents.release();
        if(!mGoogleApiClient.isConnected()) {
            ConnectionResult connectionResult = mGoogleApiClient
                    .blockingConnect(30, TimeUnit.SECONDS);
            if (!connectionResult.isSuccess()) {
                Log.e(TAG, "DataLayerListenerService failed to connect to GoogleApiClient.");
                return;
            }
        }

        // Loop through the events, store in database, and remove across devices
        for (DataEvent event : events) {
            // pull out relevant information
            DataMapItem dataMapItem = DataMapItem.fromDataItem(event.getDataItem());
            DataMap dataMap = dataMapItem.getDataMap();
            patient = dataMap.getString(PATIENT_KEY);
            room = dataMap.getString(ROOM_KEY);
            timestamp = dataMap.getString(TIMESTAMP_KEY);
            Log.w(TAG, patient + room + timestamp);

            // ignore the strange appearance of null, null, null entries
            if(patient == null) {
                continue;
            }

            // store data into SQLite database
            Long row = mDBHelper.createEntry(
                    DBAdapter.ESTIMOTE_DATABASE_TABLE, patient, room, timestamp);
            Log.w(TAG, row.toString());

            // remove dataItem across all devices
            Uri uri = event.getDataItem().getUri();
            Wearable.DataApi.deleteDataItems(mGoogleApiClient,uri);

        }
    }

    @Override
    public void onDestroy() {
        mDBHelper.close();
    }

    /* might use this to launch wearable app whenever a room change occurs


    // start the wearable app on all watches in range
    private void sendStartActivityMessage(String node) {
        Wearable.MessageApi.sendMessage(
                mGoogleApiClient, node, START_ACTIVITY_PATH, new byte[0]).setResultCallback(
                new ResultCallback<MessageApi.SendMessageResult>() {
                    @Override
                    public void onResult(MessageApi.SendMessageResult sendMessageResult) {
                        if (!sendMessageResult.getStatus().isSuccess()) {
                            Log.e(TAG, "Failed to send message with status code: "
                                    + sendMessageResult.getStatus().getStatusCode());
                        }
                    }
                }
        );
    }

    // asynchronous thread to send message in background
    private class StartWearableActivityTask extends AsyncTask<Void, Void, Void> {

        @Override
        protected Void doInBackground(Void... args) {
            Collection<String> nodes = getNodes();
            Log.d(TAG,"Found " + nodes.size() + " nodes");
            for (String node : nodes) {
                sendStartActivityMessage(node);
            }
            return null;
        }
    }


    // find all watches in range
    private Collection<String> getNodes() {
        HashSet<String> results = new HashSet<String>();
        NodeApi.GetConnectedNodesResult nodes =
                Wearable.NodeApi.getConnectedNodes(mGoogleApiClient).await();

        for (Node node : nodes.getNodes()) {
            results.add(node.getId());
        }

        return results;
    }

    */
}
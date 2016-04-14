package com.ucsf.demo;

import android.content.Context;
import android.util.Log;

import com.estimote.sdk.Beacon;
import com.estimote.sdk.BeaconManager;
import com.estimote.sdk.Region;
import com.estimote.sdk.connection.BeaconConnection;

import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;

/** Class retrieving beacon's information and treating them. */
public class BeaconMonitoring implements BeaconManager.MonitoringListener {
    public static final long SCAN_PERIOD = 5000;
    public static final long WAIT_PERIOD = 15000;

    private static final String TAG = "BeaconMonitoring";
    private static final BeaconMonitoring mInstance = new BeaconMonitoring();

    public static class Entry {
        private final String mTimestamp;
        private final String mRoom;

        public Entry(String room, String timestamp) {
            mTimestamp = timestamp;
            mRoom      = room;
        }

        public String getTimestamp() { return mTimestamp; }
        public String getRoom() { return mRoom; }
    }

    private Beacon                        mPreviousClosestBeacon = null;
    private HashMap<Integer, String>      mRooms = new HashMap<>();
    private String                        mPatient;
    private List<Entry>                   mPendingEntries = new LinkedList<>();
    private HashMap<String, List<Beacon>> mInRangeBeacons = new HashMap<>();

    private BeaconMonitoring() {
        // Hard coded room initialization.
        mRooms.put(10001, "bedroom 1");
        mRooms.put(10002, "bathroom");
        mRooms.put(10003, "living room");
        mRooms.put(20001, "kitchen");
        mRooms.put(20002, "bedroom 2");
        mRooms.put(20003, "bedroom 3");

        // Hard coded patient
        mPatient = "George";
    }

    @Override
    public void onEnteredRegion(Region region, final List<Beacon> beacons) {
        // Add the beacons to the list of in range beacons
        String identifier = region.getIdentifier();
        if (!mInRangeBeacons.containsKey(identifier)) {
            mInRangeBeacons.put(identifier, beacons);
        } else {
            mInRangeBeacons.get(identifier).addAll(beacons);
        }
    }

    @Override
    public void onExitedRegion(Region region) {
        // Removes beacons in the given region
        mInRangeBeacons.remove(region.getIdentifier());
    }

    /** Get the closest beacon among currently in range beacons. */
    public Beacon getClosestBeacon(Context context) {
        Beacon closestBeacon = mPreviousClosestBeacon; // If there is no beacon in range, returns the previous one
        int maxPower = 0;

        synchronized (mInRangeBeacons) { // Avoid parallel modifications of the map
            for (HashMap.Entry<String, List<Beacon>> beacons : mInRangeBeacons.entrySet()) {
                for (Beacon beacon : beacons.getValue()) {
                    // Connect to the beacon
                    BeaconConnection connection = new BeaconConnection(context, beacon,
                            new BeaconConnection.ConnectionCallback() {
                                @Override
                                public void onAuthenticated(BeaconConnection.BeaconCharacteristics chars) {
                                    Log.d(TAG, "Authenticated to beacon: " + chars);
                                }

                                @Override
                                public void onAuthenticationError() {
                                    Log.d(TAG, "Authentication Error");
                                }

                                @Override
                                public void onDisconnected() {
                                    Log.d(TAG, "Disconnected");
                                }
                            });
                    connection.authenticate(); // Wait for the connection

                    // Get the beacon power and compare to the current closest beacon power
                    if (connection.isConnected()) {
                        int power = beacon.getMeasuredPower();
                        if (power > maxPower) {
                            closestBeacon = beacon;
                            maxPower = power;
                        }

                        connection.close();
                    }
                }
            }
        }

        return closestBeacon;
    }

    public Beacon getPreviousClosestBeacon() {
        return mPreviousClosestBeacon;
    }

    public void setPreviousClosestBeacon(Beacon beacon) {
        mPreviousClosestBeacon = beacon;
    }

    public String getPatientID() {
        return mPatient;
    }

    /** Get the room corresponding to the given beacon. */
    public String getRoom(Beacon beacon) {
        if (beacon == null)
            return "unknown room";
        String room = mRooms.get(beacon.getMajor() + beacon.getMinor());
        return room != null ? room : "unknown room";
    }

    public List<Entry> getPendingEntries() {
        return mPendingEntries;
    }

    public static BeaconMonitoring getInstance() {
        return mInstance;
    }

}

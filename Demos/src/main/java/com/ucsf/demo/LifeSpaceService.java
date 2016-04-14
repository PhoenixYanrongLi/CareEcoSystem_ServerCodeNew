package com.ucsf.demo;

import android.app.AlarmManager;
import android.content.Context;
import android.content.Intent;
import android.database.Cursor;
import android.location.Location;
import android.location.LocationManager;
import android.telephony.TelephonyManager;
import android.util.Log;

import java.util.Arrays;
import java.util.Comparator;
import java.util.LinkedList;
import java.util.List;

/** Service call each day to measure the life space of the patient and add this information to the database. */
public class LifeSpaceService extends DailyService.Service {
    private static final String TAG = "LifeSpaceService";

    @Override
    public void execute(Context context, Intent intent) {
        // Retrieve the patient's IMEI
        final TelephonyManager tm =
                (TelephonyManager) context.getSystemService(Context.TELEPHONY_SERVICE);
        String patientIMEI = tm.getDeviceId();

        // Get the timestamps corresponding to the current time and the same time one day ago
        String currentTimestamp  = TimestampMaker.getTimestamp();
        String previousTimestamp = TimestampMaker.getTimestamp((int) -AlarmManager.INTERVAL_DAY);

        // Get entries corresponding to the patient name and the last period of time
        DBAdapter db = new DBAdapter(context);
        db.open();
        Cursor cursor = db.fetchEntry(
                DBAdapter.GPS_LOCATION_DATABASE_TABLE,
                patientIMEI,
                previousTimestamp,
                currentTimestamp);

        List<Location> locationsList = new LinkedList<>();
        if (cursor.moveToFirst()) {
            do {
                String locString = cursor.getString(cursor.getColumnIndex(DBAdapter.KEY_LOCATION));
                try {
                    locationsList.add(GPSLocationService.stringToLocation(locString));
                } catch (Exception e) {
                    Log.e(TAG, "Invalid GPS coordinates: " + locString);
                }
            } while (cursor.moveToNext());
        }

        // Do nothing if no enough input points
        if (locationsList.size() < 2) {
            Log.e(TAG, "Not enough GPS location provided to compute median coordinates!");
            db.close();
            return;
        }

        // Take the median location
        Location[] locations = new Location[locationsList.size()];
        locationsList.toArray(locations);
        boolean isEven = locations.length % 2 == 0;
        int mid = locations.length / 2;
        Location median = new Location(LocationManager.GPS_PROVIDER);

        // Sort locations by latitude
        Arrays.sort(locations, new Comparator<Location>() {
            @Override
            public int compare(Location lhs, Location rhs) {
                return Double.compare(lhs.getLatitude(), rhs.getLatitude());
            }
        });
        if (isEven) median.setLatitude(0.5 * (locations[mid].getLatitude() + locations[mid-1].getLatitude()));
        else        median.setLatitude(locations[mid].getLatitude());

        // Sort locations by longitude
        Arrays.sort(locations, new Comparator<Location>() {
            @Override
            public int compare(Location lhs, Location rhs) {
                return Double.compare(lhs.getLongitude(), rhs.getLongitude());
            }
        });
        if (isEven) median.setLongitude(0.5 * (locations[mid].getLongitude() + locations[mid-1].getLongitude()));
        else        median.setLongitude(locations[mid].getLongitude());

        // Find the farthest point
        double maxDistance = 0.0;
        Location farthestLocation = null;
        for (Location location : locations) {
            double distance = median.distanceTo(location);
            if (distance > maxDistance) {
                maxDistance      = distance;
                farthestLocation = location;
            }
        }

        // Add the result to the database
        db.createEntry(DBAdapter.LIFE_SPACE_DATABASE_TABLE, new String[][] {
                { DBAdapter.KEY_PATIENT       , patientIMEI },
                { DBAdapter.KEY_TIMESTAMP     , currentTimestamp },
                { DBAdapter.KEY_HOME_COORD    , GPSLocationService.locationToString(median) },
                { DBAdapter.KEY_FARTHEST_COORD, GPSLocationService.locationToString(farthestLocation) },
                { DBAdapter.KEY_DIST_FROM_HOME, String.valueOf(maxDistance) }
        });
        db.close();

        Log.d(TAG, String.format("Life space: [from: %s; to: %s, distance: %f]",
                GPSLocationService.locationToString(median),
                GPSLocationService.locationToString(farthestLocation),
                maxDistance
        ));
    }
}

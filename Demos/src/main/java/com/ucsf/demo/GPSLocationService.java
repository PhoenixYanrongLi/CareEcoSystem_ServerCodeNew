package com.ucsf.demo;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.location.Location;
import android.location.LocationManager;
import android.telephony.TelephonyManager;
import android.util.Log;

import java.security.InvalidParameterException;

/** Save the GPS coordinates of the patient every 30 minutes. */
public class GPSLocationService extends DailyService.Service {
    public static final long INTERVAL = AlarmManager.INTERVAL_FIFTEEN_MINUTES;

    public static void startService(Context context, Class service) {
        LocationManager locationManager =
                (LocationManager) context.getSystemService(Context.LOCATION_SERVICE);
        Intent intent = new Intent(context, service);
        PendingIntent pendingIntent = PendingIntent.getBroadcast(context, 0, intent, 0);
        locationManager.requestLocationUpdates(
                LocationManager.GPS_PROVIDER,
                INTERVAL,
                10,
                pendingIntent);
    }

    public static void stopService(Context context, Class service) {
        LocationManager locationManager =
                (LocationManager) context.getSystemService(Context.LOCATION_SERVICE);
        Intent intent = new Intent(context, service);
        PendingIntent pendingIntent = PendingIntent.getBroadcast(context, 0, intent, 0);
        locationManager.removeUpdates(pendingIntent);
    }

    @Override
    public void execute(Context context, Intent intent) {
        // Retrieve the patient's IMEI
        final TelephonyManager tm =
                (TelephonyManager) context.getSystemService(Context.TELEPHONY_SERVICE);
        String patientIMEI = tm.getDeviceId();

        // Get the GPS location
        Location location = intent.getParcelableExtra(LocationManager.KEY_LOCATION_CHANGED);
        String locString = locationToString(location);

        // Create a new entry in the database
        DBAdapter db = new DBAdapter(context);
        db.open();
        db.createEntry(DBAdapter.GPS_LOCATION_DATABASE_TABLE, new String[][] {
                { DBAdapter.KEY_PATIENT, patientIMEI },
                { DBAdapter.KEY_TIMESTAMP, TimestampMaker.getTimestamp() },
                { DBAdapter.KEY_LOCATION, locString }
        });
        db.close();

        Log.d("GPSLocationService",
                String.format("New GPS entry: [patient: %s; location: %s]", patientIMEI, locString));
    }

    public static String locationToString(Location location) {
        return String.format("[%s; %s]",
                Location.convert(location.getLatitude(), Location.FORMAT_SECONDS),
                Location.convert(location.getLongitude(), Location.FORMAT_SECONDS));
    }

    public static Location stringToLocation(String locString) throws InvalidParameterException {
        String[] coordinates = locString.substring(1, locString.length()-1).split("; ");
        if (coordinates.length != 2)
            throw new InvalidParameterException();

        Location location = new Location(LocationManager.GPS_PROVIDER);
        location.setLatitude(Location.convert(coordinates[0]));
        location.setLongitude(Location.convert(coordinates[1]));

        return location;
    }

}

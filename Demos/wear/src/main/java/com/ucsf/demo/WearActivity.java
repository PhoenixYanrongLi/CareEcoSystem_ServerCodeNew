package com.ucsf.demo;

import android.app.Activity;
import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.os.RemoteException;
import android.support.wearable.view.WatchViewStub;
import android.util.Log;
import android.widget.TextView;

import com.estimote.sdk.BeaconManager;
import com.estimote.sdk.Region;

public class WearActivity extends Activity {

    private static final String TAG = "WEARABLE";
    private static final String START_ACTIVITY_PATH = "/start-activity";
    private static final String ESTIMOTE_PROXIMITY_UUID = "B9407F30-F5F8-466E-AFF9-25556B57FE6D";
    private static final Region ALL_ESTIMOTE_BEACONS = new Region("rid", ESTIMOTE_PROXIMITY_UUID, null, null);

    private TextView mTextView;
    private TextView mTextView2;

    private BeaconManager mBeaconManager;


    /** Update the GUI when the patient enters in a new room. */
    public void onBeaconRanging(String patient, String room, String timestamp) {
        mTextView.setText("New room is " + patient + "'s " + room);
        mTextView2.setText("Timestamp: " + timestamp);
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Initialize GUI
        setContentView(R.layout.activity_wear);
        // print screen - "Connected to wearable. Connecting to Estimote..."
        final WatchViewStub stub = (WatchViewStub) findViewById(R.id.watch_view_stub);
        stub.setOnLayoutInflatedListener(new WatchViewStub.OnLayoutInflatedListener() {
            @Override
            public void onLayoutInflated(WatchViewStub stub) {
                mTextView = (TextView) stub.findViewById(R.id.text);
                mTextView2 = (TextView) stub.findViewById(R.id.text2);
            }
        });
        Log.d(TAG, "successful connection to wearable");

        // Start beacon monitoring service (in background)
        mBeaconManager = new BeaconManager(this);
        mBeaconManager.setBackgroundScanPeriod(BeaconMonitoring.SCAN_PERIOD, BeaconMonitoring.WAIT_PERIOD);
        mBeaconManager.setMonitoringListener(BeaconMonitoring.getInstance());
        mBeaconManager.connect(new BeaconManager.ServiceReadyCallback() {
            @Override
            public void onServiceReady() {
                try {
                    mBeaconManager.startMonitoring(ALL_ESTIMOTE_BEACONS);
                } catch (RemoteException e) {
                    Log.e(TAG, "Cannot start monitoring: ", e);
                }
            }
        });

        // Start beacon ranging service (in background)
        AlarmManager am = (AlarmManager) getSystemService(Context.ALARM_SERVICE);
        Intent intent = new Intent(this, RangingService.class);
        PendingIntent pendingIntent = PendingIntent.getBroadcast(this, 0, intent, 0);
        am.setRepeating(
                AlarmManager.RTC_WAKEUP,
                System.currentTimeMillis(),
                BeaconMonitoring.WAIT_PERIOD,
                pendingIntent);
    }

    @Override
    protected void onStop() {
        // Stop the ranging service
        AlarmManager alarmManager = (AlarmManager) getSystemService(Context.ALARM_SERVICE);
        Intent intent = new Intent(this, RangingService.class);
        PendingIntent sender = PendingIntent.getBroadcast(this, 0, intent, 0);
        alarmManager.cancel(sender);

        // Stop the monitoring service
        mBeaconManager.disconnect();
        mBeaconManager = null; // to keep only one instance at any time

        super.onStop();
    }

}

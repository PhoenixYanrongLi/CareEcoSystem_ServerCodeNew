package com.ucsf.demo;

import android.content.Context;
import android.content.Intent;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.telephony.TelephonyManager;
import android.util.Log;

public class GaitService extends DailyService.Service {
    private static class StepCounter implements SensorEventListener {
        private static long MAX_DELTA_PERIOD = 10000; // 10 seconds

        private SensorManager mSensorManager;
        private Sensor        mStepCounterSensor;
        private int           mStepCount = 0;
        private int           mStepCountOffset;
        private long          mLastActivityTime;
        private float         mActivityPeriodLength;
        private boolean       mOnActivity;

        public StepCounter(Context context) {
            mSensorManager     = (SensorManager) context.getSystemService(Context.SENSOR_SERVICE);
            mStepCounterSensor = mSensorManager.getDefaultSensor(Sensor.TYPE_STEP_COUNTER);
        }

        public int   getStepCount() { return mStepCount - mStepCountOffset; }
        public float getGaitSpeed() {
            return mActivityPeriodLength == 0 ? 0.0f : getStepCount() / mActivityPeriodLength;
        }

        public void start() {
            reset();
            mSensorManager.registerListener(this, mStepCounterSensor, SensorManager.SENSOR_DELAY_FASTEST);
        }

        public void stop() {
            mSensorManager.unregisterListener(this, mStepCounterSensor);
        }

        public void reset() {
            mStepCountOffset      = mStepCount;
            mOnActivity           = false;
            mActivityPeriodLength = 0;
        }

        public void updateGaitSpeed() {
            if (mOnActivity) {
                long currentTime = System.currentTimeMillis();
                long delta = currentTime - mLastActivityTime;
                if (delta < MAX_DELTA_PERIOD) // Still in the same period
                    mActivityPeriodLength += ((float) delta) / 3600000;
                mLastActivityTime = currentTime;
            }
        }

        @Override
        public void onSensorChanged(SensorEvent event) {
            // Check if the event is valid
            if (event.sensor.getType() == Sensor.TYPE_STEP_COUNTER && event.values.length > 0) {
                // Update the step count
                mStepCount = (int) event.values[0];

                // Update the gait speed
                if (!mOnActivity) { // First step
                    mOnActivity       = true;
                    mLastActivityTime = System.currentTimeMillis();
                } else
                    updateGaitSpeed();
            }
        }

        @Override
        public void onAccuracyChanged(Sensor sensor, int accuracy) {}
    }

    private static StepCounter mStepCounter;

    public static void startService(Context context, Class service) throws Exception {
        mStepCounter = new StepCounter(context);
        mStepCounter.start();
        DailyService.Service.startService(context, service);
    }

    public static void stopService(Context context, Class service) {
        mStepCounter.stop();
        DailyService.Service.stopService(context, service);
    }

    @Override
    public void execute(Context context, Intent intent) {
        // Retrieve the patient's IMEI
        final TelephonyManager tm =
                (TelephonyManager) context.getSystemService(Context.TELEPHONY_SERVICE);
        String patientIMEI = tm.getDeviceId();

        // Get the timestamp corresponding to the current time
        String currentTimestamp = TimestampMaker.getTimestamp();

        // Make sure we capture the last period of activity
        mStepCounter.updateGaitSpeed();

        // Save the step count and the average gait speed in their respective tables
        DBAdapter db = new DBAdapter(context);
        db.open();

        db.createEntry(DBAdapter.STEP_COUNT_DATABASE_TABLE, new String[][] {
                { DBAdapter.KEY_PATIENT, patientIMEI },
                { DBAdapter.KEY_TIMESTAMP, currentTimestamp },
                { DBAdapter.KEY_STEP_COUNT, String.valueOf(mStepCounter.getStepCount()) }
        });

        db.createEntry(DBAdapter.GAIT_SPEED_DATABASE_TABLE, new String[][] {
                { DBAdapter.KEY_PATIENT, patientIMEI },
                { DBAdapter.KEY_TIMESTAMP, currentTimestamp },
                { DBAdapter.KEY_GAIT_SPEED, String.valueOf(mStepCounter.getGaitSpeed()) }
        });

        db.close();

        Log.d("GaitService",
                String.format("New entry: [patient: %s; step_count: %d; gait_speed: %f]",
                patientIMEI,
                mStepCounter.getStepCount(),
                mStepCounter.getGaitSpeed()
        ));

        // Reset counter
        mStepCounter.reset();
    }

}

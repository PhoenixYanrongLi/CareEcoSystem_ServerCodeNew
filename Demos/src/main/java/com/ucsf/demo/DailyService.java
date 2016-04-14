package com.ucsf.demo;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.PowerManager;
import android.util.Log;

import java.util.Calendar;
import java.util.GregorianCalendar;

/**
 *  Android service call each day to handle certain services,
 * as push the database to a Dropbox account, etc.
 * */
public class DailyService {
    private static final String TAG = "DailyService";

    /** Service interface */
    public static abstract class Service extends BroadcastReceiver {
        public static final long INTERVAL = AlarmManager.INTERVAL_DAY;

        @Override
        public void onReceive(Context context, Intent intent) {
            PowerManager pm = (PowerManager) context.getSystemService(Context.POWER_SERVICE);
            PowerManager.WakeLock wl = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "");
            wl.acquire();

            try {
                execute(context, intent);
            } catch (Exception e) {
                Log.e(TAG, "Failed to execute service '" + getClass().getName() +"': ", e);
            }

            wl.release();
        }

        /**
         * Start the service
         * @param context the context in which the service will run
         * @param service the class of the service to start
         */
        public static void startService(Context context, Class service) throws Exception {
            // Get a time corresponding to noon
            Calendar calendar = GregorianCalendar.getInstance();
            calendar.set(Calendar.HOUR_OF_DAY, 12);
            calendar.set(Calendar.MINUTE     ,  0);
            calendar.set(Calendar.SECOND     ,  0);

            // Register the service
            AlarmManager am = (AlarmManager) context.getSystemService(context.ALARM_SERVICE);
            Intent intent = new Intent(context, service);
            PendingIntent pendingIntent = PendingIntent.getBroadcast(context, 0, intent, 0);
            am.setRepeating(
                    AlarmManager.RTC_WAKEUP,
                    calendar.getTimeInMillis(),
                    service.getField("INTERVAL").getLong(null),
                    pendingIntent);
        }

        /**
         * Stop the given service
         * @param context the context in which the service run
         * @param service the class of the service to stop
         */
        public static void stopService(Context context, Class service) {
            AlarmManager alarmManager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
            Intent intent = new Intent(context, service);
            PendingIntent sender = PendingIntent.getBroadcast(context, 0, intent, 0);
            alarmManager.cancel(sender);
        }

        /**
         * Method called once a day
         * @param context the context in which the service is running
         */
        public abstract void execute(Context context, Intent intent);
    }

    /**
     * Starts the given services each day.
     * @param context the context in which the services will run
     * @param services the services to start
     */
    public static void startServices(Context context, Class[] services) {
        for (Class service : services) {
            try {
                // Initialize the service
                service.getMethod("startService", Context.class, Class.class)
                        .invoke(null, context, service);
                Log.d(TAG, String.format("Service '%s' launched.", service.getName()));
            } catch (Exception e) {
                Log.e(TAG, String.format("Service '%s' is not a valid service!",
                        service.getName(), Service.class.getName()), e);
            }
        }
    }

    /**
     * Stops the given registered services.
     * @param context the context in which the services are running
     * @param services the services to stop
     */
    public static void stopServices(Context context, Class[] services) {
        for (Class service : services) {
            try {
                // Initialize the service
                service.getMethod("stopService", Context.class, Class.class)
                        .invoke(null, context, service);
                Log.d(TAG, String.format("Service '%s' stopped.", service.getName()));
            } catch (Exception e) {
                Log.e(TAG, String.format("Service '%s' is not a valid service!",
                        service.getName(), Service.class.getName()), e);
            }
        }
    }

}

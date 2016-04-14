package com.ucsf.demo;

import android.content.Context;
import android.content.Intent;
import android.os.AsyncTask;
import android.util.Log;

/** Service that once per day push the application's database to a Dropbox account. */
public class DropboxService extends DailyService.Service {
    @Override
    public void execute(Context context, Intent intent) {
        // Network operations cannot be done in the main thread,
        // therefore we create an asynchronous task to execute them.
        new AsyncTask<Context, Void, Void>() {
            @Override
            protected Void doInBackground(Context ... params) {
                try {
                    Context context = params[0];
                    // Make sure we are connected
                    DropboxAdapter dbAdapter = new DropboxAdapter(context);
                    dbAdapter.connect();

                    // Create a subdirectory with an unique name corresponding to this device
                    String folder = "/" + dbAdapter.getUniqueId();
                    dbAdapter.makeDirectory(folder);

                    // Push the database
                    dbAdapter.pushFile(
                            DBAdapter.getPath(context),
                            folder + "/" + TimestampMaker.getTimestamp() + ".db",
                            true
                    );
                    Log.d("DropboxService", "Database pushed to Dropbox.");
                    return null;
                } catch (Exception e) {
                    Log.e("DropboxService", "An error occurred:", e);
                }
                return null;
            }
        }.execute(context);
    }

}
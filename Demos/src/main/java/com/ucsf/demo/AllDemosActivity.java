package com.ucsf.demo;

import android.app.Activity;
import android.content.Intent;
import android.os.AsyncTask;
import android.os.Bundle;
import android.util.Log;
import android.view.View;

import com.google.android.gms.common.api.GoogleApiClient;
import com.google.android.gms.common.api.ResultCallback;
import com.google.android.gms.wearable.MessageApi;
import com.google.android.gms.wearable.Node;
import com.google.android.gms.wearable.NodeApi;
import com.google.android.gms.wearable.Wearable;

import java.util.Collection;
import java.util.HashSet;


/**
 * Shows all available demos.
 */
public class AllDemosActivity extends Activity  {
    private static final String TAG = "AllDemosActivity";
    private static final String START_ACTIVITY_PATH = "/start-activity";

    private GoogleApiClient mGoogleApiClient;
    private DropboxAdapter  mDBAdapter;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        mGoogleApiClient = new GoogleApiClient.Builder(this)
                .addApi(Wearable.API)
                .build();
        mGoogleApiClient.connect();

        mDBAdapter = new DropboxAdapter(this);
        mDBAdapter.connect();

        Log.w(TAG, "LOG WORKING PROPERLY");
        setContentView(R.layout.all_demos);

        findViewById(R.id.data_management_button).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Intent intent = new Intent(AllDemosActivity.this, DataManagementActivity.class);
                startActivity(intent);
            }
        });
        findViewById(R.id.notify_demo_button).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Intent intent = new Intent(AllDemosActivity.this, ListBeaconsActivity.class);
                intent.putExtra(ListBeaconsActivity.EXTRAS_TARGET_ACTIVITY, NotifyDemoActivity.class.getName());
                startActivity(intent);
            }
        });
        findViewById(R.id.start_wearable_button).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                // Trigger an AsyncTask that will query for a list of connected nodes and send a
                // "start-activity" message to each connected node.
                new StartWearableActivityTask().execute();
                Log.d(TAG, "Generating RPC");
            }
        });
        findViewById(R.id.ground_trust_demo_button).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Intent intent = new Intent(AllDemosActivity.this, GroundTrustActivity.class);
                startActivity(intent);
            }
        });
        findViewById(R.id.reset_dropbox_connection_button).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                mDBAdapter.disconnect();
                mDBAdapter.resetAccess();
                mDBAdapter.connect();
            }
        });

        // Register the services
        DailyService.startServices(AllDemosActivity.this, new Class[] {
                GPSLocationService.class,
                LifeSpaceService.class,
                GaitService.class,
                DropboxService.class // Should be last as it pushes the whole database to dropbox
        });
    }

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
    public class StartWearableActivityTask extends AsyncTask<Void, Void, Void> {

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

    @Override
    public void onResume() {
        super.onResume();
        mDBAdapter.connect();
    }
}

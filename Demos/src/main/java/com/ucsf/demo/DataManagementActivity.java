package com.ucsf.demo;

import android.app.ListActivity;
import android.database.Cursor;
import android.os.Bundle;
import android.util.Log;
import android.view.Menu;
import android.view.MenuItem;
import android.widget.SimpleCursorAdapter;

import java.util.ArrayList;

/**
 *  This class will bind the database to a listview to display the data,
 *  copy this data to a dropbox folder every 24 hours,
 *  and clear data that is 1 week old
 */
public class DataManagementActivity extends ListActivity {

    private DataLayerListenerService listenerService;
    private static final String TAG = "DataManagementActivity";
    private DBAdapter mDBHelper;

    private static final int ESTIMOTE_ID = Menu.FIRST;
    private static final int GROUND_TRUST_ID = Menu.FIRST+1;
    private static final int GPS_LOCATION_ID = Menu.FIRST+2;
    private static final int LIFE_SPACE_ID = Menu.FIRST+3;


    // TODO: need to come back and generalize to work for all tables

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.data_display_list);
        mDBHelper = new DBAdapter(this);
        mDBHelper.open();
        fillData(mDBHelper.ESTIMOTE_DATABASE_TABLE);
        getActionBar().setDisplayHomeAsUpEnabled(true);

    }

    // TODO: generalize fillData(table) once DBAdapter is updated
    private void fillData(String table) {
        Log.d(TAG,"Successfully entered fillData()");

        Cursor entryCursor = mDBHelper.fetchAllEntries(table);
        //Log.w(TAG,entryCursor.getColumnName(0) + entryCursor.getColumnName(1) + entryCursor.getColumnName(2));
        startManagingCursor(entryCursor);

        // Create an array to specify the fields we want to display in the list
        String[] from;
        // and an array of the fields we want to bind those fields to
        int[] to;
        // fill in each array depending on the data type of the requested table
        if(table.equals(mDBHelper.GROUND_TRUST_DATABASE_TABLE)) {
            from = new String[]{DBAdapter.KEY_PATIENT, DBAdapter.KEY_ROOM, DBAdapter.KEY_TIMESTAMP};
            to = new int[]{R.id.text1, R.id.text2, R.id.text3};
        } else if(table.equals(mDBHelper.GPS_LOCATION_DATABASE_TABLE)) {
            from = new String[] {DBAdapter.KEY_PATIENT, DBAdapter.KEY_TIMESTAMP, DBAdapter.KEY_LOCATION};
            to = new int[]{R.id.text1, R.id.text2, R.id.text3};
        } else if(table.equals(mDBHelper.LIFE_SPACE_DATABASE_TABLE)) {
            from = new String[] { DBAdapter.KEY_PATIENT, DBAdapter.KEY_TIMESTAMP, DBAdapter.KEY_HOME_COORD, DBAdapter.KEY_FARTHEST_COORD, DBAdapter.KEY_DIST_FROM_HOME};
            to = new int[]{R.id.text1, R.id.text2, R.id.text3, R.id.text4, R.id.text5};
        } else {
            // use estimote table as default
            from = new String[]{DBAdapter.KEY_PATIENT, DBAdapter.KEY_ROOM, DBAdapter.KEY_TIMESTAMP};
            to = new int[]{R.id.text1, R.id.text2, R.id.text3};
        }

            // Now create a simple cursor adapter and set it to display
        SimpleCursorAdapter entries =
                new SimpleCursorAdapter(this, R.layout.data_display_row, entryCursor, from, to);
        setListAdapter(entries);
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        super.onCreateOptionsMenu(menu);
        menu.add(0, ESTIMOTE_ID, 0, "Estimote");
        menu.add(0, GROUND_TRUST_ID, 0, "Ground Truth");
        menu.add(0, GPS_LOCATION_ID, 0, "GPS");
        menu.add(0, LIFE_SPACE_ID, 0, "Life Space");
        return true;
    }

    @Override
    public boolean onMenuItemSelected(int featureId, MenuItem item) {
        switch(item.getItemId()) {
            case ESTIMOTE_ID:
                // display estimote table
                fillData(mDBHelper.ESTIMOTE_DATABASE_TABLE);
                return true;
            case GROUND_TRUST_ID:
                // display ground trust table
                fillData(mDBHelper.GROUND_TRUST_DATABASE_TABLE);
                return true;
            case GPS_LOCATION_ID:
                // display GPS table
                fillData(mDBHelper.GPS_LOCATION_DATABASE_TABLE);
            case LIFE_SPACE_ID:
                // display life space table
                fillData(mDBHelper.LIFE_SPACE_DATABASE_TABLE);
                return true;
            case android.R.id.home:
                finish();
                return true;

        }

        return super.onMenuItemSelected(featureId, item);
    }



}

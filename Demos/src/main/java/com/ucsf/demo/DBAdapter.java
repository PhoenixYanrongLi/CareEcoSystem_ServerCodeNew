package com.ucsf.demo;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.SQLException;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import android.os.Build;
import android.util.Log;

import java.io.File;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

/**
 * Simple database access helper class. Defines the basic CRUD operations
 * for the demo, and gives the ability to list all data as well as
 * retrieve or modify a specific piece of data.
 */
public class DBAdapter {
    public static final String DATABASE_NAME = "data.db";

    public static final String ESTIMOTE_DATABASE_TABLE     = "estimote";
    public static final String GROUND_TRUST_DATABASE_TABLE = "ground_trust";
    public static final String GPS_LOCATION_DATABASE_TABLE = "gps_location";
    public static final String LIFE_SPACE_DATABASE_TABLE   = "life_space";
    public static final String STEP_COUNT_DATABASE_TABLE   = "step_count";
    public static final String GAIT_SPEED_DATABASE_TABLE   = "gait_speed";

    public static final String KEY_PATIENT        = "patient";
    public static final String KEY_ROOM           = "room";
    public static final String KEY_TIMESTAMP      = "timestamp";
    public static final String KEY_LOCATION       = "location";
    public static final String KEY_HOME_COORD     = "home_coord";
    public static final String KEY_FARTHEST_COORD = "farthest_coord";
    public static final String KEY_DIST_FROM_HOME = "dist_from_home";
    public static final String KEY_STEP_COUNT     = "step_count";
    public static final String KEY_GAIT_SPEED     = "gait_speed";

    private static final int DATABASE_VERSION = 6;
    private static final String TAG = "DBAdapter";
    private static final String KEY_ROWID = "_id";
    private static final String[] DATABASE_TABLES = new String[] {
            ESTIMOTE_DATABASE_TABLE,
            GROUND_TRUST_DATABASE_TABLE,
            GPS_LOCATION_DATABASE_TABLE,
            LIFE_SPACE_DATABASE_TABLE,
            STEP_COUNT_DATABASE_TABLE,
            GAIT_SPEED_DATABASE_TABLE
    };
    private static final Map<String, String[][]> DATABASE_FIELDS;
    private static final Map<String, String[]>   DATABASE_ENTRIES;
    static {
        // Database fields initialization
        Map<String, String[][]> dbFields = new HashMap<>();
        dbFields.put(ESTIMOTE_DATABASE_TABLE, new String[][]
                { { KEY_PATIENT, "TEXT" }, { KEY_ROOM, "TEXT" }, { KEY_TIMESTAMP, "TEXT" } });
        dbFields.put(GROUND_TRUST_DATABASE_TABLE, new String[][]
                { { KEY_PATIENT, "TEXT" }, { KEY_ROOM, "TEXT" }, { KEY_TIMESTAMP, "TEXT" } });
        dbFields.put(GPS_LOCATION_DATABASE_TABLE, new String[][]
                { { KEY_PATIENT, "TEXT" }, { KEY_TIMESTAMP, "TEXT" }, { KEY_LOCATION, "TEXT" } });
        dbFields.put(LIFE_SPACE_DATABASE_TABLE, new String[][]
                { { KEY_PATIENT, "TEXT" }, { KEY_TIMESTAMP, "TEXT" }, { KEY_HOME_COORD, "TEXT" }, { KEY_FARTHEST_COORD, "TEXT" }, { KEY_DIST_FROM_HOME, "REAL" }});
        dbFields.put(STEP_COUNT_DATABASE_TABLE, new String[][]
                { { KEY_PATIENT, "TEXT" }, { KEY_TIMESTAMP, "TEXT" }, { KEY_STEP_COUNT, "INTEGER" } });
        dbFields.put(GAIT_SPEED_DATABASE_TABLE, new String[][]
                { { KEY_PATIENT, "TEXT" }, { KEY_TIMESTAMP, "TEXT" }, { KEY_GAIT_SPEED, "REAL" } });
        DATABASE_FIELDS = Collections.unmodifiableMap(dbFields);

        // Database entries initialization
        Map<String, String[]> dbEntries = new HashMap<>();
        for (String table : DATABASE_TABLES) {
            String[][] fields = DATABASE_FIELDS.get(table);
            String[] entries = new String[fields.length + 1];
            for (int i = 0; i < fields.length; ++i)
                entries[i] = fields[i][0];
            entries[fields.length] = KEY_ROWID;
            dbEntries.put(table, entries);
        }
        DATABASE_ENTRIES = Collections.unmodifiableMap(dbEntries);
    }

    private DatabaseHelper mDbHelper;
    private SQLiteDatabase mDb;
    private final Context  mCtx;



    private static class DatabaseHelper extends SQLiteOpenHelper {

        DatabaseHelper(Context context) {
            super(context, DATABASE_NAME, null, DATABASE_VERSION);
        }

        @Override
        public void onCreate(SQLiteDatabase db) {
            for (String table : DATABASE_TABLES) {
                String request = String.format("CREATE TABLE %s (%s INTEGER PRIMARY KEY ASC",
                        table, KEY_ROWID);
                final String[][] fields = DATABASE_FIELDS.get(table);
                for (final String[] field : fields)
                    request += String.format(", %s %s", field[0], field[1]);
                request += ");";

                db.execSQL(request);
            }
        }

        @Override
        public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
            Log.w(TAG, "Upgrading database from version " + oldVersion + " to "
                    + newVersion + ", which will destroy all old data");
            for (String table : DATABASE_TABLES)
                db.execSQL("DROP TABLE IF EXISTS " + table);
            onCreate(db);
        }
    }

    /**
     * Constructor - takes the context to allow the database to be
     * opened/created
     *
     * @param ctx the Context within which to work
     */
    public DBAdapter(Context ctx) {
        this.mCtx = ctx;
    }

    /**
     * Open the database. If it cannot be opened, try to create a new
     * instance of the database. If it cannot be created, throw an exception to
     * signal the failure
     *
     * @return this (self reference, allowing this to be chained in an
     *         initialization call)
     * @throws android.database.SQLException if the database could be neither opened or created
     */
    public DBAdapter open() throws SQLException {
        mDbHelper = new DatabaseHelper(mCtx);
        mDb = mDbHelper.getWritableDatabase();
        return this;
    }

    public void close() {
        mDbHelper.close();
    }

    /** Create a new entry in the given table.
     *
     * @param table the table to edit
     * @param fields data to add { { KEY, VALUE }... }
     * @return rowId or -1 if failed
     */
    public long createEntry(String table, String[][] fields) {
        ContentValues initialValues = new ContentValues();
        for (String[] field : fields)
            initialValues.put(field[0], field[1]);
        return mDb.insert(table, null, initialValues);
    }

    /**
     * Create a new entry using the patient, room, and timestamp provided. If
     * successfully created return the new rowId for that entry, otherwise return
     * a -1 to indicate failure.
     *
     * @param table the table to edit
     * @param patient the title of the entry
     * @param room the body of the entry
     * @param timestamp the body of the entry
     * @return rowId or -1 if failed
     */
    public long createEntry(String table, String patient, String room, String timestamp) {
        return createEntry(table, new String[][] {
                { KEY_PATIENT  , patient },
                { KEY_ROOM     , room },
                { KEY_TIMESTAMP, timestamp }
        });
    }

    /**
     * Delete the entry with the given rowId
     *
     * @param table the table to edit
     * @param rowId id of entry to delete
     * @return true if deleted, false otherwise
     */
    public boolean deleteEntry(String table, long rowId) {
        return mDb.delete(table, KEY_ROWID + "=" + rowId, null) > 0;
    }

    /**
     * Return a Cursor over the list of all entries in the database
     *
     * @param table the table to edit
     * @return Cursor over all entries
     */
    public Cursor fetchAllEntries(String table) {
        return mDb.query(table, DATABASE_ENTRIES.get(table), null, null, null, null, null);
    }

    /**
     * Return a Cursor positioned at the entry that matches the given rowId
     *
     * @param table the table to edit
     * @param rowId id of entry to retrieve
     * @return Cursor positioned to matching entry, if found
     * @throws SQLException if entry could not be found/retrieved
     */
    public Cursor fetchEntry(String table, long rowId) throws SQLException {
        Cursor mCursor =
                mDb.query(true, table,
                        DATABASE_ENTRIES.get(table),
                        KEY_ROWID + "=" + rowId,
                        null, null, null, null, null);
        if (mCursor != null) {
            mCursor.moveToFirst();
        }
        return mCursor;
    }

    /**
     * Return a Cursor positioned at the entry that matches the given patient and the given timestamp range.
     * @param table the table to edit
     * @param patient the patient of interest
     * @param start the first timestamp
     * @param end the last timestamp
     * @return  Cursor positioned to matching entry, if found
     * @throws SQLException if entry could not be found/retrieved
     */
    public Cursor fetchEntry(String table, String patient, String start, String end) {
        Cursor mCursor =
                mDb.query(true, table,
                        DATABASE_ENTRIES.get(table),
                        String.format("%s=\"%s\" AND %s BETWEEN \"%s\" AND \"%s\"",
                                KEY_PATIENT, patient,
                                KEY_TIMESTAMP, start, end),
                        null, null, null, null, null);
        if (mCursor != null) {
            mCursor.moveToFirst();
        }
        return mCursor;
    }

    /**
     * Update the entry using the details provided. The entry to be updated is
     * specified using the rowId, and it is altered to use the patient, room, and timestamp
     * values passed in
     *
     * @param table the table to edit
     * @param rowId id of entry to update
     * @param patient value to set entry patient to
     * @param room value to set entry room to
     * @param timestamp value to set entry timestamp to
     * @return true if the entry was successfully updated, false otherwise
     */
    public boolean updateEntry(String table, long rowId, String patient, String room, String timestamp) {
        ContentValues args = new ContentValues();
        args.put(KEY_PATIENT, patient);
        args.put(KEY_ROOM, room);
        args.put(KEY_TIMESTAMP, timestamp);

        return mDb.update(table, args, KEY_ROWID + "=" + rowId, null) > 0;
    }

    /** Returns the path to the database. */
    public static String getPath(Context context) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR1)
            return context.getFilesDir().getAbsolutePath().replace("files", "databases") + File.separator + DATABASE_NAME;
        return context.getFilesDir().getPath() + context.getPackageName() + "/databases/" + DATABASE_NAME;
    }
}
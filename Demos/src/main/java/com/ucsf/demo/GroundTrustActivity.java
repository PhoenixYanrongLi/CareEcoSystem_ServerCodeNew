package com.ucsf.demo;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.Dialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.SharedPreferences;
import android.database.SQLException;
import android.os.Bundle;
import android.preference.PreferenceManager;
import android.telephony.TelephonyManager;
import android.view.Menu;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;

/**
 * Activity allowing to register some timestamps associated with a room and an user name
 * in order to create ground trust data.
 */
public class GroundTrustActivity extends Activity implements View.OnClickListener {
    public static final String KEY_ROOM_NAME            = "ROOM_NAME_";

    private static final String TAG                     = "GroundTrustActivity";

    private Button[]           mButtons;
    private DBAdapter          mDBAdapter;

    /** Listener called when a button is click to write an entry into the database. */
    private View.OnClickListener pushListener = new View.OnClickListener() {
        @Override
        public void onClick(View v) {
            // Prepare the user notification
            AlertDialog.Builder dialogBuilder = new AlertDialog.Builder(GroundTrustActivity.this);
            dialogBuilder.setPositiveButton(R.string.action_edit_validate,
                    new Dialog.OnClickListener() {
                        @Override
                        public void onClick(DialogInterface dialog, int which) {}
                    }
            );
            dialogBuilder.setCancelable(true);

            // Retrieve the patient's IMEI
            final TelephonyManager tm =
                    (TelephonyManager) getSystemService(Context.TELEPHONY_SERVICE);
            String patientIMEI = tm.getDeviceId();

            // Push to the database
            try {
                mDBAdapter.open();
                mDBAdapter.createEntry(
                        DBAdapter.GROUND_TRUST_DATABASE_TABLE,
                        patientIMEI,
                        ((Button) v).getText().toString(),
                        TimestampMaker.getTimestamp());
                mDBAdapter.close();

                dialogBuilder.setMessage("Entry added to the database.");
            } catch (SQLException e) {
                dialogBuilder.setMessage("Failed to save entry: " + e);
            }

            // Notify the user
            dialogBuilder.show();
        }
    };

    /** Listener called when a button is clicked to edit its name. */
    private View.OnClickListener editListener = new View.OnClickListener() {
        @Override
        public void onClick(View v) {
            final Button button = (Button) v;
            final EditText new_name_field = new EditText(GroundTrustActivity.this);

            new_name_field.setText(button.getText());

            AlertDialog.Builder dialogBuilder = new AlertDialog.Builder(GroundTrustActivity.this);
            dialogBuilder.setTitle(R.string.edit_room_name_message);
            dialogBuilder.setView(new_name_field);

            dialogBuilder.setPositiveButton(R.string.action_edit_validate,
                    new Dialog.OnClickListener() {
                        @Override
                        public void onClick(DialogInterface dialog, int which) {
                            button.setText(new_name_field.getText());
                        }
                    }
            );

            dialogBuilder.setNegativeButton(R.string.action_edit_cancel,  new Dialog.OnClickListener() {
                @Override
                public void onClick(DialogInterface dialog, int which) {}
            });
            dialogBuilder.setCancelable(true);

            dialogBuilder.show();
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_ground_trust);

        mButtons = new Button[] {
                (Button) findViewById(R.id.room_button0),
                (Button) findViewById(R.id.room_button1),
                (Button) findViewById(R.id.room_button2),
                (Button) findViewById(R.id.room_button3),
                (Button) findViewById(R.id.room_button4),
                (Button) findViewById(R.id.room_button5),
        };

        ((Button) findViewById(R.id.editButton)).setOnClickListener(this);
        ((Button) findViewById(R.id.validateButton)).setOnClickListener(this);
        ((Button) findViewById(R.id.cancelButton)).setOnClickListener(this);

        setEditable(false);
        resetFields();

        // Create the database adapter
        mDBAdapter = new DBAdapter(this);
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        getMenuInflater().inflate(R.menu.scan_menu, menu);
        return true;
    }

    @Override
    public void onClick(View v) {
        int id = v.getId();

        switch (id) {
            case R.id.editButton:
                setEditable(true);
                break;
            case R.id.validateButton:
                setEditable(false);
                saveFields();
                break;
            case R.id.cancelButton:
                setEditable(false);
                resetFields();
                break;
            default:
                break;
        }
    }

    /** Reset the user's changes (rooms' name and patient's name). */
    private void resetFields() {
        SharedPreferences preferences = PreferenceManager.getDefaultSharedPreferences(this);

        for (int idx = 0; idx < 6; ++idx) {
            mButtons[idx].setText(preferences.getString(
                            KEY_ROOM_NAME + idx,
                            getResources().getString(R.string.room_default_name) + " " + idx)
            );
        }
    }

    /** Apply and save the user's changes (rooms' name and patient's name). */
    private void saveFields() {
        SharedPreferences preferences = PreferenceManager.getDefaultSharedPreferences(this);
        SharedPreferences.Editor editor = preferences.edit();

        for (int idx = 0; idx < 6; ++idx) {
            editor.putString(
                    KEY_ROOM_NAME + idx,
                    mButtons[idx].getText().toString()
            );
        }

        editor.commit();
    }

    /** Change the UI in order to edit rooms' and patient's name. */
    private void setEditable(boolean editable) {
        if (editable) {
            for (Button button : mButtons)
                button.setOnClickListener(editListener);

            ((Button) findViewById(R.id.editButton)).setVisibility(Button.INVISIBLE);
            ((Button) findViewById(R.id.validateButton)).setVisibility(Button.VISIBLE);
            ((Button) findViewById(R.id.cancelButton)).setVisibility(Button.VISIBLE);
        } else {
            for (Button button : mButtons)
                button.setOnClickListener(pushListener);

            ((Button) findViewById(R.id.editButton)).setVisibility(Button.VISIBLE);
            ((Button) findViewById(R.id.validateButton)).setVisibility(Button.INVISIBLE);
            ((Button) findViewById(R.id.cancelButton)).setVisibility(Button.INVISIBLE);
        }
    }
}

package com.ucsf.demo;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.AsyncTask;
import android.preference.PreferenceManager;
import android.telephony.TelephonyManager;
import android.util.Log;

import com.dropbox.client2.DropboxAPI;
import com.dropbox.client2.android.AndroidAuthSession;
import com.dropbox.client2.exception.DropboxException;
import com.dropbox.client2.session.AppKeyPair;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.util.UUID;

/** Simple wrapper around the Dropbox API. */
public class DropboxAdapter {
    final static private String DROPBOX_APP_KEY     = "3n2f8nwmd3fz2vk";
    final static private String DROPBOX_APP_SECRET  = "7ca1w9a1jtj40hu";
    final static private String AUTH_KEY_ID         = "DROPBOX_AUTH_KEY";

    private final Context mCtx;
    private DropboxAPI<AndroidAuthSession> mDBApi;

    public DropboxAdapter(Context context) {
        AppKeyPair appKeys = new AppKeyPair(DROPBOX_APP_KEY, DROPBOX_APP_SECRET);
        AndroidAuthSession session = new AndroidAuthSession(appKeys);
        mDBApi = new DropboxAPI<>(session);
        mCtx   = context;
    }

    /**
     * Starts a connection to the Dropbox account. The user has to authorize the app and sign in.
     * @return Returns if the connection is delayed or not.
     *         If it's the case, a web browser will be opened to authorize the access to Dropbox.
     *         Then the connection must be finalized when the activity resumes calling again connect().
     */
    public boolean connect() {
        // Check if we are not already connected
        if (!mDBApi.getSession().isLinked()) {
            // We may be in a partial authentication state
            if (mDBApi.getSession().authenticationSuccessful()) {
                try {
                    mDBApi.getSession().finishAuthentication();

                    // Save the access token for further authentication
                    SharedPreferences preferences = PreferenceManager.getDefaultSharedPreferences(mCtx);
                    SharedPreferences.Editor editor = preferences.edit();
                    editor.putString(AUTH_KEY_ID, mDBApi.getSession().getOAuth2AccessToken());
                    editor.commit();
                } catch (IllegalStateException e) {
                    Log.e("DbAuthLog", "Error authenticating: ", e);
                }
            } else {
                // Try to access previous authentication
                SharedPreferences preferences = PreferenceManager.getDefaultSharedPreferences(mCtx);
                String accessToken = preferences.getString(AUTH_KEY_ID, null);
                if (accessToken != null) {
                    mDBApi.getSession().setOAuth2AccessToken(accessToken);
                } else {
                    // Ask for a new authentication
                    mDBApi.getSession().startOAuth2Authentication(mCtx);
                    return true; // Delayed authentication
                }
            }
        }
        return false; // Direct authentication
    }

    public void disconnect() {
        mDBApi.getSession().unlink();
    }

    /** Removes the access token from the preferences. */
    public void resetAccess() {
        SharedPreferences preferences = PreferenceManager.getDefaultSharedPreferences(mCtx);
        SharedPreferences.Editor editor = preferences.edit();
        editor.remove(AUTH_KEY_ID);
        editor.commit();
    }

    /**
     * Push the given file in a Dropbox location. Cannot be called in the main thread.
     * @param srcFilename Name of the local file
     * @param dstFilename Filename of the destination file to write in the Dropbox.
     *                    Starts with a "/" (root directory)
     * @param deleteSource Indicates if the source file has to be deleted after the operation.
     *                     If the operation fails for any reason, the file is not deleted.
     */
    public void pushFile(String srcFilename, String dstFilename, boolean deleteSource)
            throws FileNotFoundException, DropboxException
    {
        File file = new File(srcFilename);
        FileInputStream inputStream = new FileInputStream(file);
        mDBApi.putFile(dstFilename, inputStream, file.length(), null, null);
        if (deleteSource)
            file.delete();
    }

    /** Create a folder at the given path. Cannot be called in the main thread. */
    public void makeDirectory(String path) throws DropboxException, IllegalArgumentException {
        try {
            DropboxAPI.Entry existingEntry = mDBApi.metadata(path, 1, null, false, null);
            if (!existingEntry.isDir) // The path points to a file and not a directory
                throw new IllegalArgumentException("The path '" + path + "' points to an existing file!");
        } catch (DropboxException e) {
            // The path doesn't point on an existing entry, we can therefore try to create a directory
            mDBApi.createFolder(path);
        }
    }

    /** Callback interface to get return status from asynchronous operations. */
    public static interface Callback {
        public void onSuccess();
        public void onFailure(Exception e);
    }

    /**
     * Network operations cannot be done in the main thread,
     * therefore we create an asynchronous task to execute them.
     * */
    private class FilePusher extends AsyncTask<Void, Void, Exception> {
        private final Callback mCallback;
        private final String   mSrcFilename;
        private final String   mDstFilename;
        private final boolean  mDelete;

        public FilePusher(Callback callback, String src, String dst, boolean delete) {
            mCallback    = callback;
            mSrcFilename = src;
            mDstFilename = dst;
            mDelete      = delete;
        }

        protected Exception doInBackground(Void ... params) {
            try {
                pushFile(mSrcFilename, mDstFilename, mDelete);
                return null;
            } catch (Exception e) {
                return e;
            }
        }

        protected void onPostExecute(Exception e) {
            if (mCallback != null) {
                if (e != null)
                    mCallback.onFailure(e);
                else
                    mCallback.onSuccess();
            }
        }
    }

    /**
     * Push the given file in a Dropbox location.
     * @param srcFilename Name of the local file
     * @param dstFilename Filename of the destination file to write in the Dropbox.
     *                    Starts with a "/" (root directory)
     * @param callback Callback object to call when the file is pushed or in case of error. May be null.
     * @param deleteSource Indicates if the source file has to be deleted after the operation.
     *                     If the operation fails for any reason, the file is not deleted.
     */
    public void pushFile(String srcFilename, String dstFilename, boolean deleteSource, Callback callback) {
        new FilePusher(callback, srcFilename, dstFilename, deleteSource).execute();
    }


    /**
     * Network operations cannot be done in the main thread,
     * therefore we create an asynchronous task to execute them.
     * */
    private class DirectoryMaker extends AsyncTask<Void, Void, Exception> {
        private final Callback mCallback;
        private final String   mPath;

        public DirectoryMaker(Callback callback, String path) {
            mCallback = callback;
            mPath     = path;
        }

        protected Exception doInBackground(Void ... params) {
            try {
                makeDirectory(mPath);
            } catch (Exception e) {
                return e;
            }
            return null;
        }

        protected void onPostExecute(Exception e) {
            if (mCallback != null) {
                if (e != null)
                    mCallback.onFailure(e);
                else
                    mCallback.onSuccess();
            }
        }
    }

    /** Creates a directory at the given path. */
    public void makeDirectory(String path, Callback callback) {
        new DirectoryMaker(callback, path).execute();
    }

    /** Returns an unique id corresponding to the used device. */
    public String getUniqueId() {
        final TelephonyManager tm =
                (TelephonyManager) mCtx.getSystemService(Context.TELEPHONY_SERVICE);
        final String tmDevice  = tm.getDeviceId().toString();
        final String tmSerial  = tm.getSimSerialNumber().toString();
        final String androidId = android.provider.Settings.Secure.getString(
                mCtx.getContentResolver(),
                android.provider.Settings.Secure.ANDROID_ID);
        UUID deviceUuid = new UUID(
                androidId.hashCode(),
                ((long)tmDevice.hashCode() << 32) | tmSerial.hashCode());
        return deviceUuid.toString();
    }
}

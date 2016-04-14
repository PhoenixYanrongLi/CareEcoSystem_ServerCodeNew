package com.ucsf.demo;

import java.util.Calendar;
import java.util.GregorianCalendar;

/** Help the creation of timestamp. */
public abstract class TimestampMaker {

    /** Returns a timestamp corresponding to the given calendar. */
    private static String getTimestamp(Calendar time) {
        return String.format("%d.%d.%d-%d.%d.%d",
                time.get(Calendar.YEAR),
                time.get(Calendar.MONTH) + 1,
                time.get(Calendar.DAY_OF_MONTH),
                time.get(Calendar.HOUR_OF_DAY),
                time.get(Calendar.MINUTE),
                time.get(Calendar.SECOND));
    }

    /** Returns a timestamp corresponding to the current time. */
    public static String getTimestamp() {
        return getTimestamp(GregorianCalendar.getInstance());
    }

    /**
     * Returns a timestamp from the current time with the given offset.
     * @param offset the desired offset in milliseconds
     */
    public static String getTimestamp(int offset) {
        Calendar time = GregorianCalendar.getInstance();
        time.add(Calendar.MILLISECOND, offset);
        return getTimestamp(time);
    }
}

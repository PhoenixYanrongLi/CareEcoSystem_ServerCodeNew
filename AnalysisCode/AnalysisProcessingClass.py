from datetime import datetime, timedelta

__author__ = 'Brad'
import abc
import multiprocessing
from DatabaseManagementCode.databaseWrapper import DatabaseWrapper


class AnalysisProcessingClass(multiprocessing.Process, DatabaseWrapper):

    def __init__(self, database, patient_id, type_name, table_name):
        """

        :param database: List of the database login info
        :param patient_id: The patientID
        :param type_name: name of the type of analysis (ex. room_locationing)
        :param table_name: The name of the datatype being analyzed
        :return:
        """
        multiprocessing.Process.__init__(self)
        DatabaseWrapper.__init__(self, database)
        self.database_name = '_' + patient_id
        self.typename      = type_name
        self.obj_table     = self.typename + "_obj"
        self.table_name    = table_name

        # Make sure the analysisprofile table exists
        if not self.table_exists(self.database_name, 'analysisprofile'):
            self.create_table(database_name = self.database_name,
                              table_name    = 'analysisprofile',
                              column_names  = ['table_name', 'type_name', 'timestamp'],
                              column_types  = ['VARCHAR(100)', 'VARCHAR(100) NOT NULL PRIMARY KEY', 'BIGINT(20)'])
    @staticmethod
    def datetime_to_utc(timestamp):
        """ Converts the given timestamp to UTC in ms. """

        epoch      = datetime.utcfromtimestamp(0)
        delta      = timestamp-epoch

        return long(delta.total_seconds() * 1000)

    @staticmethod
    def utc_to_datetime(utc):
        seconds = float(utc)/float(1000)
        date = datetime.utcfromtimestamp(seconds)
        return date

    def get_analysis_data(self, start_stamp, end_stamp):
        """
        @param data_type: str of the column selected, pass * for all data in table
        @param table_name: str of the name of the table
        @return: data
        """

        if not self.table_exists(self.database_name, self.table_name):
            return []

        if not self.fetch_from_database(database_name = self.database_name,
                                        table_name    = self.table_name,
                                        where         = [['timestamp', '>=', start_stamp],
                                                         ['timestamp', '<', end_stamp]],
                                        order_by      = ['timestamp', 'ASC']):
            return []
        else:
            analysis_data = self.fetchall()

        if len(analysis_data) == 0:
            return []
        else:
            return zip(*list(zip(*analysis_data)))

    def upload_analysis(self, start_window, end_window, data):
        """
        Upload the analysis to the database
        :param data: in a list: [timestamp serialized object]
        :return:
        """
        if not self.create_table(database_name= self.database_name,
                          table_name   = self.typename,
                          column_names = ['start_window', 'end_window', 'analysis_data'],
                          column_types = ['VARCHAR(100) NOT NULL PRIMARY KEY', 'VARCHAR(100) NOT NULL', 'LONGBLOB']):
            # If table exists, insert the data
            if not self.insert_into_database(database_name = self.database_name,
                                             table_name    = self.typename,
                                             column_names  = ['start_window', 'end_window', 'analysis_data'],
                                             values        = [start_window, end_window, data]):
                return False
            else:
                return True
            # If table can be created, retry insert of data
        else:
            if not self.insert_into_database(database_name = self.database_name,
                                             table_name    = self.typename,
                                             column_names  = ['start_window', 'end_window', 'analysis_data'],
                                             values        = [start_window, end_window, data]):
                return False
            else:
                return True

    @abc.abstractmethod
    def split_to_windows(self, data):
        """
        Split the data into n number of windows
        :param data:
        :return:
        """
        return

    @abc.abstractmethod
    def process_data(self, windowed_data):
        """
        Do the analysis on the data
        :param windowed_data:
        :return:
        """
        return

    def read_start_stamp(self):
        """

        :return: utc time
        """
        if not self.fetch_from_database(database_name     = self.database_name,
                                            table_name    = 'profile',
                                            to_fetch      = 'START',):
                # Case for if no start time recorded
                return None
        else:
                # Return the start time
                start_stamp = self.fetchall()
                start_stamp = list(zip(*start_stamp))[0][0]
                return start_stamp

    def read_timestamp(self):
        """
        Reads in the timestamp of the last processed data
        :return: Timestamp if exists, otherwise NULL
        """
        if not self.fetch_from_database(database_name = self.database_name,
                                        table_name    = 'analysisprofile',
                                        to_fetch      = 'timestamp',
                                        where         = [['table_name', self.table_name], ['type_name', self.typename]]):
            # If no analysisprofile database exists then return the start timestamp
            return self.read_start_stamp()

        else:
            # If timestamp column does exist in analysis profile, return it if it has length,
            # otherwise return the start_stamp
            timestamp = self.fetchall()

            if len(timestamp) == 0:
                # If no timestamp in timestamp column, return start_stamp
                return self.read_start_stamp()

            else:
                # If timestamp exists in timestamp column, return that
                timestamp = list(zip(*timestamp))[0][0]
                return timestamp

    def write_timestamp(self, timestamp):
        """
        Write the latest timestamp, in this case it means the end of a window
        :param timestamp:
        :return:
        """
        return self.insert_into_database(database_name       = self.database_name,
                                         table_name          = 'analysisprofile',
                                         column_names        = ['table_name', 'type_name', 'timestamp'],
                                         values              = [self.table_name, self.typename, timestamp],
                                         on_duplicate_update = [ 2 ])

    def get_latest_data_stamp(self):
        if not self.fetch_from_database(database_name = self.database_name,
                                        table_name    = self.table_name,
                                        to_fetch      = 'timestamp',
                                        order_by      = ['timestamp', 'DESC'],
                                        limit         = 1):
            return []
        else:
            latest_data = self.fetchall()

        if len(latest_data) == 0:
            return []
        else:
            return zip(*list(zip(*latest_data)))[0][0]

    def get_stamp_window_from_utc(self, timestamp):
        """
        Gets the earliest window in utc numerical time
        Windows are as follow:
        Midnight <= time < Noon
        Noon <= time < Next Day Midnight
        :param timestamp: timestamp in numerical utc time
        :return: 2 element list of [start_window, end_window]
        """
        timestamp = self.utc_to_datetime(timestamp)
        return [self.datetime_to_utc(datetime(year  = timestamp.year,
                                              month = timestamp.month,
                                              day   = timestamp.day,
                                              hour  = 0)),
                self.datetime_to_utc(datetime(year  = timestamp.year,
                                              month = timestamp.month,
                                              day   = timestamp.day,
                                              hour  = 0) + timedelta(days=1))]

    def get_latest_stamp_window(self):
        latest_time = self.get_latest_data_stamp()
        return self.get_stamp_window_from_utc(latest_time)

    def get_earliest_stamp_window(self):
        start_time = self.read_timestamp()
        return self.get_stamp_window_from_utc(start_time)

    def get_stamp_windows(self):
        """
        Create a list of timestamp windows -24 from the latest window to insure all data has arrived.

        :return:
        """
        early_window = self.get_earliest_stamp_window()
        late_window  = self.get_latest_stamp_window()
        window_delta = late_window[0] - early_window[0]
        ms_per_metric_window = 86400000
        # Given 12 hour windows, get the number of iterations between them
        iters = window_delta / ms_per_metric_window
        windows = []
        for i in range(0, iters):
            windows.append([early_window[0]+i*ms_per_metric_window, early_window[1]+i*ms_per_metric_window])
        return windows

    def run(self):
        timestamp = self.read_timestamp
        # If no timestamp found, break the analysis code. Bad Profile!
        if timestamp is None: return False

        windows = self.get_stamp_windows()
        for i in windows:
            start_stamp = i[0]
            end_stamp = i[1]
            data = self.get_analysis_data(start_stamp, end_stamp)
            if data:
                windowed_data  = self.split_to_windows(data)
                processed_data = self.process_data(windowed_data)
                self.upload_analysis(start_stamp, end_stamp, processed_data)
                self.write_timestamp(end_stamp)
                                            
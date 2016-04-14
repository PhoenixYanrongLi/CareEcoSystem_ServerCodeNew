__author__ = 'Brad'

import datetime
from datetime import timedelta
import multiprocessing
from DatabaseManagementCode.databaseWrapper import DatabaseWrapper
import abc
from simple_salesforce import Salesforce
from DatabaseManagementCode.dataUploadClass import GenericFileUploader
import logging
from AnalysisCode.AnalysisProcessingClass import AnalysisProcessingClass
import pickle


class MetricsClass(AnalysisProcessingClass):

    def __init__(self, database, patient_id, table_name, metric_type):
        logging.warning('Watch out!')
        super(MetricsClass, self).__init__(database=database,
                                           patient_id=patient_id,
                                           type_name=metric_type,
                                           table_name=table_name)
        self.patient_id = patient_id
        self.metric_type   = self.typename
        self.sf = Salesforce(username='fm-integration@careeco.uat',
                             password='fmr0cks!',
                             security_token='vnWYJMNtLbDPL9NY97JP9tJ5',
                             sandbox=True)

        if not self.table_exists(self.database_name, 'metricsprofile'):
            self.create_table(database_name = self.database_name,
                              table_name    = 'metricsprofile',
                              column_names  = ['table_name', 'type_name', 'timestamp'],
                              column_types  = ['VARCHAR(100)', 'VARCHAR(100) NOT NULL PRIMARY KEY', 'BIGINT(20)'])

    def poll_data(self, start_window):
        """
        Returns the data between the time frame specified
        :return:
        """

        if not self.fetch_from_database(database_name = self.database_name,
                                        table_name    = self.table_name,
                                        to_fetch      = 'analysis_data',
                                        where         = ['start_window', '=', start_window]):
            return []
        else:
            metric_data = self.fetchall()

        if len(metric_data) == 0:
            return []
        else:
            return pickle.loads(zip(*list(zip(*metric_data)))[0][0])

    def get_latest_data_stamp(self):
        if not self.fetch_from_database(database_name = self.database_name,
                                        table_name    = self.table_name,
                                        to_fetch      = 'start_window',
                                        order_by      = ['start_window', 'DESC'],
                                        limit         = 1):
            return []
        else:
            latest_data = self.fetchall()

        if len(latest_data) == 0:
            return []
        else:
            return zip(*list(zip(*latest_data)))[0][0]

    def read_timestamp(self):
        """
        Reads in the timestamp of the last processed data
        :return: Timestamp if exists, otherwise NULL
        """
        if not self.fetch_from_database(database_name = self.database_name,
                                        table_name    = 'metricsprofile',
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
                                         table_name          = 'metricsprofile',
                                         column_names        = ['table_name', 'type_name', 'timestamp'],
                                         values              = [self.table_name, self.typename, timestamp],
                                         on_duplicate_update = [ 2 ])

    def upload_to_database(self, start_window, end_window, metric):
        """
        Uploads the metric to the database ['VARCHAR(100) NOT NULL PRIMARY KEY', 'FLOAT']
        :return:
        """
        self.create_table(database_name= self.database_name,
                          table_name   = self.metric_type,
                          column_names = ['start_window', 'end_window', 'metric'],
                          column_types = ['VARCHAR(100) NOT NULL PRIMARY KEY', 'VARCHAR(100) NOT NULL', 'FLOAT'])
        self.insert_into_database(database_name = self.database_name,
                                  table_name    = self.metric_type,
                                  column_names  = ['start_window', 'end_window', 'metric'],
                                  values        = [start_window, end_window, metric])
        return True

    def upload_to_salesforce(self, timestamp, metric):
        """
        Uploads the metric to salesforce
        :return:
        """
        metric_data = {
            "patientId": self.patient_id,
            "timestamp": self.utc_to_datetime(timestamp).strftime('%x'),
            "metricList":[
            {
                "metric": self.metric_type,
                "metricValue": metric
            }]
        }
        self.sf.apexecute('FMMetrics/insertMetrics', method='POST', data=metric_data)
        return True

    def run(self):
        """

        :return:
        """
        timestamp = self.read_timestamp
        # If no timestamp found, break the analysis code. Bad Profile!
        if timestamp is None: return False

        windows = self.get_stamp_windows()
        for i in windows:
            start_stamp = i[0]
            end_stamp = i[1]
            data = self.poll_data(start_stamp)
            if data != []:
                windowed_data  = self.split_to_windows(data)
                metric = self.process_data(windowed_data)
                self.upload_to_database(start_stamp, end_stamp, metric)
                self.upload_to_salesforce(start_stamp, metric)
                self.write_timestamp(start_stamp)
                return True

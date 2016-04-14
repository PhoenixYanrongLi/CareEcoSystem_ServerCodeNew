__author__ = 'george'

import unittest
import os
import glob
import numpy as np

from real_time_room_estimator import RealTimeRoomEstimator
from training_room_estimator import TrainingRoomEstimator
from DatabaseManagementCode.databaseWrapper import DatabaseWrapper
from DatabaseManagementCode.databaseWrapper import Helper

class RoomEstimatorTestCase2(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(RoomEstimatorTestCase2, self).__init__(*args, **kwargs)
        host = "localhost"
        user = "brad"
        password = "moxie100"
        database = (host, user, password)
        DatabaseWrapper.__init__(self, database)

    @classmethod
    def setUpClass(self):



        database_name = '_george.netscher'
        if not self.fetch_from_database(database_name     = database_name,
                                            table_name    = 'profile',
                                            to_fetch      = 'START',):
                # Case for if no start time recorded
                return None

        print self

    def test_George_accuracy(self):
        # check that total accuracy measure is above 90%

        print self
        # error = train_house_monitoring('george.netscher',)
        # errormsg = "The classifier error rate is too high: error = {:f}".format(error)
        # self.assertGreaterEqual(0.1, error, errormsg)

    def train_house_monitoring(self, patient_id, beaconcoors, start_timestamp, end_timestamp):
        """
        Train the classifier.
        :return: Returns if the operation is successful and the classifier error. Above 10%, it's a failure
        """

        # Retrieve the ground trust entries
        database_name = '_' + patient_id



        if not self.fetch_from_database(database_name = database_name,
                                        table_name    = 'configMMGT',
                                        where         = [['type' , 'CR'],
                                                         ['start', '>=', start_timestamp],
                                                         ['end'  , '<=', end_timestamp]],
                                        order_by      = ['start', 'ASC']):
            return False, 0
        traingtlist = [[row[1], row[2], row[3]] for row in self]  # [[label, start, end], ...]

        # Retrieve the rssi entries
        if not self.fetch_from_database(database_name = database_name,
                                        table_name    = 'dataHMRSSI',
                                        where         = [['timestamp', '>=', start_timestamp],
                                                         ['timestamp', '<=', end_timestamp]],
                                        order_by      = ['timestamp', 'ASC']):
            return False, 0
        trainrssilist = [[row[i] for i in range(0, 2 + 2 * row[1])] for row in self]

        # Train the classifier
        trainer      = TrainingRoomEstimator(beaconcoors)
        clf, sumdict = trainer.train_classifier(trainrssilist, traingtlist)
        error        = sumdict["classifier error"]

        return error

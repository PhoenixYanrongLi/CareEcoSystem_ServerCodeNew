import unittest
from os import getcwd
from os.path import join
import csv

from datetime import datetime, timedelta

from AnalysisCode.roomLocationing import RoomLocationing
from AnalysisCode.gaitSpeedDetection import GaitSpeedDetection
from AnalysisCode.AnalysisLifeSpaceDetection import LifeSpace
from AnalysisCode.AnalysisStepCount import StepCountDetection
import pickle

__author__ = 'Brad'


class MetricsTester(unittest.TestCase):

    def setUp(self):
        host = "localhost"
        user = "brad"
        password = "moxie100"

        self.database = (host, user, password)
    def testAnalysistimestampGrab(self):
        data = []
        tester = RoomLocationing(database=self.database,
                                 patient_id='julien.jacquemot')
        if not tester.fetch_from_database(database_name = tester.database_name,
                                        table_name    = 'AnalysisRoomLocation',
                                        limit         = 1):
            data = []
        else:
            latest_data = tester.fetchall()
            data =  zip(*list(zip(*latest_data)))[0]
        data =  pickle.loads(data[2])
        print data
    def testLifeSpace(self):
        tester = LifeSpace(database=self.database,
                           patient_id='julien.jacquemot')

        h_lat, h_long = tester.get_home_coors()
        windows = tester.get_stamp_windows()
        for i in windows:
            start_stamp = i[0]
            end_stamp = i[1]
            data = tester.get_analysis_data(start_stamp, end_stamp)
            processed_data = tester.process_data(data)
            print pickle.loads(processed_data)
    def testStepCount(self):
        tester = StepCountDetection(database=self.database,
                                    patient_id='alex.bayen')
        windows = tester.get_stamp_windows()
        for i in windows:
            start_stamp = i[0]
            end_stamp = i[1]
            data = tester.get_analysis_data(start_stamp, end_stamp)
            processed_data = tester.process_data(data)
            print pickle.loads(processed_data)
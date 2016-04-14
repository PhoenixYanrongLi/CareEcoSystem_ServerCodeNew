__author__ = 'george'

import numpy as np
from sklearn.datasets import make_blobs
from sklearn.preprocessing import normalize
from TrendDetection.DailyStepCountTrendDetection import DailyStepCountTrendDetection
from AnomalyDetection.HourlyRoomPercentageAnomalyDetection import HourlyRoomPercentageAnomalyDetection
from DatabaseManagementCode.databaseWrapper import DatabaseWrapper
from InHomeMonitoringCode.training_room_estimator import TrainingRoomEstimator
from AnalysisCode.roomLocationing import RoomLocationing
import matplotlib.pyplot as plt
import pickle
import Simulations
from sys import getsizeof
import collections

"""
This file contains analysis of the methods used. Statistics are calculated to measure efficacy
"""


class Analysis(DatabaseWrapper):

    def __init__(self):
        """
        purposely do not call constructor to avoid call to database in super
        :return:
        """
        pass

    def get_data(self, patientid, table, starttime, endtime):

        filename = 'DataFiles/' + patientid + table + str(starttime) + '-' + str(endtime) + '_trainingdata.p'
        try:
            # first try to read from local pickle file
            outData = pickle.load(open(filename, "rb"))
        except IOError as e:

            DatabaseWrapper.__init__(self, user='brad', password='moxie100',
                                     remote_host='169.230.163.198', remote_port=5282)
            tester = RoomLocationing(database=self,
                                 patient_id=patientid)
            if not tester.fetch_from_database(database_name = tester.database_name,
                                            table_name    = table,
                                            where         = [['start_window', '>=', starttime],
                                                             ['end_window'  , '<=', endtime]],
                                            order_by      = ['start_window', 'ASC']):
                data = []
            else:
                latest_data = tester.fetchall()
                data =  zip(*list(zip(*latest_data)))
            outData = []
            for row in data:
                outData.append(pickle.loads(row[2]))

            # store data locally
            pickle.dump(outData, open(filename, "wb"))

        return outData

    def get_step_statistics(self, data):
        stepcounts = []
        for row in data:
            if row.size == 0:
                stepcounts.append(0)
            elif row.size == 2:
                stepcounts.append(row[0])
            else:
                stepcounts.append(sum(row[:, 0]))
            last = stepcounts.pop()
            if last <= 12000:
                stepcounts.append(last)
        print stepcounts
        sim = Simulations.Simulate()
        alarmCount = 0
        for i in range(len(stepcounts) - 30):
            if sim.show_ransac(stepcounts[i:i+30], plotFlag=True):
                alarmCount += 1

        print 'The number of alarming events is {0} in {1}'.format(alarmCount, max(len(stepcounts)-30,0))

    def get_room_statistics(self, data, patientid):
        alexrooms = ['Living Room', 'Main Bathroom', 'Bedroom 1', 'Office', 'Kitchen', 'Dining Room', 'Baby Room', 'Room Not Know']
        eleonorerooms = ['bedroom', 'toilet', 'bathroom', 'Room Not Know']
        georgerooms = ['Bedroom', 'Kitchen', 'Bathroom', 'Living Room', 'Room Not Know']
        julienrooms = ['Kitchen', 'Bedroom', 'Room Not Know']

        patientroomdict = {'alex.bayen': alexrooms, 'eleonore.bayen': eleonorerooms, 'george.netscher': georgerooms, 'julien.jacquemot': julienrooms}
        patientrooms = patientroomdict[patientid]
        batches = []
        d = collections.defaultdict(int)
        counter = 0
        for row in data:
            for nrow in row:
                for nnrow in nrow:
                    room = nnrow[1]
                    d[room] += 1
                    counter += 1
                    if counter % 100 == 0:
                        batches.append(d.copy())
                        d = collections.defaultdict(int)

        roompers = []
        for dd in batches:
            roomlist = []
            for room in patientrooms:
                roomlist.append(dd[room])
            roompers.append(roomlist)
        sim = Simulations.Simulate()
        sim.show_dbscan(np.array(roompers), plotFlag=False)
        print len(roompers)



if __name__ == '__main__':
    anal = Analysis()
    #data = anal.get_data('julien.jacquemot', 'AnalysisGaitSpeedHM', 1449705600000, 1452600000000)
    #anal.get_step_statistics(data)
    patient = 'george.netscher'
    data = anal.get_data(patient, 'AnalysisRoomLocation', 1448193600000 , 1452081600000)
    anal.get_room_statistics(data, patient)
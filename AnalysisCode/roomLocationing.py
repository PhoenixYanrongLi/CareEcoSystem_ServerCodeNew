__author__ = 'Brad'
from AnalysisProcessingClass import AnalysisProcessingClass
from InHomeMonitoringCode.real_time_room_estimator import RealTimeRoomEstimator
import pickle


class RoomLocationing(AnalysisProcessingClass):
    def __init__(self,  database, patient_id):
        super(RoomLocationing, self).__init__(database=database,
                                              patient_id=patient_id,
                                              type_name='AnalysisRoomLocation',
                                              table_name='dataHMRSSI')
        trainer        = self.read_trainer_data()
        self.estimator = RealTimeRoomEstimator(trainer)

    def read_trainer_data(self):
        """
        Reads the trainer obj data from database, otherwise returns nothing
        :return:
        """
        if not self.fetch_from_database(database_name = self.database_name,
                                        table_name    = 'profile',
                                        to_fetch      = 'trainer'):
            print "obj not found in the database"
            return []
        else:
            trainer = self.fetchall()
            trainer = pickle.loads(trainer[0][0])
            return trainer

    def read_clf_data(self):
        """
        Reads the classifier obj data from database, otherwise returns nothing
        :return:
        """

        if not self.fetch_from_database(database_name = self.database_name,
                                        table_name    = 'profile',
                                        to_fetch      = 'clf'):
            print "obj not found in the database"
            return []
        else:
            clf = self.fetchall()
            clf = pickle.loads(clf[0][0])
            return clf

    def split_to_windows(self, data):
        return data

    def process_data(self, windowed_data):
        room_list = []

        clf       = self.read_clf_data()
        room_list.append(self.estimator.classify_room(windowed_data, clf))
        return pickle.dumps(room_list)


__author__ = 'Brad'
import multiprocessing
from DatabaseManagementCode.databaseWrapper import DatabaseWrapper
from DailyStepCount import DailyStepCount
from DailyPercentRoom import DailyPercentRoom
from DailyGaitSpeed import DailyGaitSpeed
from DailyLifeSpace import DailyLifeSpace
from DailyRoomTransitions import DailyRoomTransitions


class RunMetricCalcs(multiprocessing.Process, DatabaseWrapper):

    def __init__(self, database):
        multiprocessing.Process.__init__(self)
        DatabaseWrapper.__init__(self, database)
        self.database = database
        self.metric_launcher_dict = {'step-count'      : DailyStepCount,
                                     'percent-room'    : DailyPercentRoom,
                                     'gait-speed'      : DailyGaitSpeed,
                                     'room-transitions': DailyRoomTransitions,
                                     'life-space'      : DailyLifeSpace}

    def get_patients_list(self):
        if not self.fetch_from_database(database_name      = 'config',
                                        table_name         = 'caregiverPatientPairs',
                                        to_fetch           = 'patient',
                                        to_fetch_modifiers = 'DISTINCT'):
            return []
        return [row[0] for row in self]

    def launch_metric(self, patient_id, metric_type):
        """
        Launches new metrics
        :param patient_id:
        :param metric_type:
            Name of the metric to launch. Options are:
            - step-count
            - percent-room

        :return:
        """
        p = self.metric_launcher_dict[metric_type](self.database, patient_id)
        p.start()
        return True

    def run(self):
        patient_ids = self.get_patients_list()
        for patient in patient_ids:
            for metric in self.metric_launcher_dict:
                self.launch_metric(metric, patient)
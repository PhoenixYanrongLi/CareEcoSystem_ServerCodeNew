__author__ = 'Brad'

import multiprocessing
from FileManagementCode.signalHandler import SignalHandler
import time
import signal
from DatabaseManagementCode.databaseWrapper import DatabaseWrapper
from roomLocationing import RoomLocationing
from gaitSpeedDetection import GaitSpeedDetection
from AnalysisLifeSpaceDetection import LifeSpace
from AnalysisStepCount import StepCountDetection

class AnalysisThreadHandler(multiprocessing.Process, DatabaseWrapper):
    """
    This class handles launching new analysis threads if the config completed boolean is true inside of the
    profile table
    """
    def __init__(self, database):
        multiprocessing.Process.__init__(self)
        DatabaseWrapper.__init__(self, database)
        self.database = database

    def check_config_completion(self, patient_id):
        """
        Checks if the config is complete for a database
        :param patient_id:
        :return: True/False
        """

        if not self.table_exists(database_name='_' + patient_id, table_name='profile'):
            return False

        if not self.fetch_from_database(database_name = '_' + patient_id,
                                        table_name    = 'profile',
                                        to_fetch      = 'VALID'):
            return False
        else:
            valid = self.fetchall()
            return valid

    def launch_analysis(self, patient_id):
        """
        Launches the various analysis routines
        :param patient_id:
        :return:
        """
        room_location = RoomLocationing(database   = self.database,
                                        patient_id = patient_id)
        room_location.start()
        room_location.join()

        gaitSpeedHM   = GaitSpeedDetection(database   = self.database,
                                           patient_id = patient_id,
                                           type_name  = 'AnalysisGaitSpeedHM',
                                           table_name = 'dataHMACC')
        gaitSpeedHM.start()
        gaitSpeedHM.join()

        gaitSpeedMM   = GaitSpeedDetection(database   = self.database,
                                           patient_id = patient_id,
                                           type_name  = 'AnalysisGaitSpeedMM',
                                           table_name = 'dataMMACC')
        gaitSpeedMM.start()
        gaitSpeedMM.join()

        lifespace     = LifeSpace(database  =self.database,
                                  patient_id=patient_id)
        lifespace.start()
        lifespace.join()

        stepcount     = StepCountDetection(database=self.database,
                                           patient_id=patient_id)
        stepcount.start()
        stepcount.join()

        return True

    def get_patients_list(self):
        if not self.fetch_from_database(database_name      = 'config',
                                        table_name         = 'caregiverPatientPairs',
                                        to_fetch           = 'patient',
                                        to_fetch_modifiers = 'DISTINCT'):
            return []
        return [row[0] for row in self]

    def run(self):
        patient_ids = self.get_patients_list()
        for patient_id in patient_ids:
            if self.check_config_completion(patient_id):
               self.launch_analysis(patient_id)
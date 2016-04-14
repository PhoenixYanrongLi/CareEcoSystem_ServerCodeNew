import multiprocessing
from DatabaseManagementCode.databaseWrapper import DatabaseWrapper
from DailyRoomPercentageAnomalyDetection import DailyRoomPercentageAnomalyDetection
from DailyStepCountAnomalyDetection import DailyStepCountAnomalyDetection
from GaitSpeedAnomalyDetection import GaitSpeedAnomalyDetection
from LifeSpaceAnomalyDetection import LifeSpaceAnomalyDetection
from RoomTransitionsAnomalyDetection import RoomTransitionsAnomalyDetection


class RunAnomalyDetection(multiprocessing.Process, DatabaseWrapper):

    def __init__(self, database):
        multiprocessing.Process.__init__(self)
        DatabaseWrapper.__init__(self, database)
        self.database = database
        self.anomaly_table_dict = { ""

        }


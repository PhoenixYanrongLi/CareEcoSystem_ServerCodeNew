__author__ = 'Brad'
from MetricsClass import MetricsClass
import math
import Queue

class DailyRoomTransitions(MetricsClass):

    def __init__(self, database, patient_id):
        MetricsClass.__init__(self,
                              database    = database,
                              patient_id  = patient_id,
                              table_name  = 'AnalysisRoomLocation',
                              metric_type = 'RoomTransitions')

    def split_to_windows(self, data):
        return data[0]

    def process_data(self, data):
        last_values_list = []
        prior_room = ''
        room_trans = 0
        data = [row[1] for row in data]
        for i in data:
            if i != prior_room:
                if len(last_values_list) >= 5:
                    room_trans += 1
                    last_values_list = [i]
                    prior_room = i
                else:
                    last_values_list = [i]
                    prior_room = i
            if i == prior_room:
                last_values_list.append(i)
        return room_trans
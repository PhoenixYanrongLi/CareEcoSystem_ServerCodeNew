__author__ = 'Brad'
from AnalysisProcessingClass import AnalysisProcessingClass
from InHomeMonitoringCode.real_time_room_estimator import RealTimeRoomEstimator
import pickle
import math


class LifeSpace(AnalysisProcessingClass):
    def __init__(self,  database, patient_id):
        super(LifeSpace, self).__init__(database=database,
                                        patient_id=patient_id,
                                        type_name='AnalysisLifeSpace',
                                        table_name='dataMMGPS')

    def split_to_windows(self, data):
        return data

    def get_home_coors(self):
        self.fetch_from_database(database_name = self.database_name,
                                 table_name    = 'profile',
                                 to_fetch      = ['HOME_LATITUDE', 'HOME_LONGITUDE'])
        data = self.fetchall()
        latitude, longitude = zip(*list(zip(*data)))[0]
        return latitude, longitude

    def process_data(self, data):
        life_space_list = []
        h_lat, h_long = self.get_home_coors()
        h_lat = math.radians(h_lat)
        h_long = math.radians(h_long)
        # Radius of Earth (km)
        R = 6371000
        for i in data:
            n_long = math.radians(i[1])
            n_lat  = math.radians(i[2])
            dlong  = n_long - h_lat
            dlat   = n_lat - h_long
            a      = math.sin(dlat/2)**2 + math.cos(h_long)*math.cos(n_lat)*(math.sin(dlong/2))**2
            c      = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
            d      = R*c
            life_space_list.append(d)
        return pickle.dumps(life_space_list)

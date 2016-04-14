__author__ = 'Brad'
from MetricsClass import MetricsClass
import math
from pickle import loads


class DailyLifeSpace(MetricsClass):

    def __init__(self, database, patient_id):
        MetricsClass.__init__(self,
                              database    = database,
                              patient_id  = patient_id,
                              table_name  = 'AnalysisLifeSpace',
                              metric_type = 'max-life-space')


    def split_to_windows(self, data):
        return data

    def process_data(self, data):
        longest_dist = 0
        for i in data:
            if i > longest_dist:
                longest_dist = i
        return longest_dist



__author__ = 'Brad'
from MetricsClass import MetricsClass


class DailyStepCount(MetricsClass):

    def __init__(self, database, patient_id):
        MetricsClass.__init__(self,
                              database    = database,
                              patient_id  = patient_id,
                              table_name  = 'AnalysisStepCount',
                              metric_type = 'step_count')

    def split_to_windows(self, data):
        return data

    def process_data(self, data):
        return data


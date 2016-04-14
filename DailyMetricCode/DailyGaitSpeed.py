from MetricsClass import MetricsClass
from pickle import loads
from numpy import int64
__author__ = 'Brad'


class DailyGaitSpeed(MetricsClass):

    def __init__(self, database, patient_id):
        super(DailyGaitSpeed, self).__init__(database    = database,
                                             patient_id  = patient_id,
                                             table_name  = 'AnalysisGaitSpeedHM',
                                             metric_type = 'DailyGaitSpeed')

    def split_to_windows(self, data):
        return data

    def process_data(self, data):
        total_steps = 0.0
        total_window = 0.0

        if type(data[0]) == int64:
            total_steps = data[0]
            total_window = data[1]
            gaitspeed = total_steps/total_window
            gaitspeed *= 1000
            gaitspeed *= 3600
            return int(gaitspeed)

        for i in data:
            total_steps += i[0]
            total_window += i[1]

        # In form Steps/ms
        # Convert to Steps/Hour

        gaitspeed = total_steps/total_window
        gaitspeed *= 1000
        gaitspeed *= 3600

        return int(gaitspeed)

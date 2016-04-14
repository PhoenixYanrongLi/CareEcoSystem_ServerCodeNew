__author__ = 'Brad'
from AnalysisProcessingClass import AnalysisProcessingClass
import numpy
import pickle

class GaitSpeedDetection(AnalysisProcessingClass):

    def __init__(self, database, patient_id, table_name, type_name):
        super(GaitSpeedDetection, self).__init__(database  = database,
                                                patient_id = patient_id,
                                                type_name  = type_name,
                                                table_name = table_name)

    def split_to_windows(self, data):
        data = zip(*data)
        timestamped_stepcount = list((data[0], data[-1]))
        timestamped_stepcount = zip(*timestamped_stepcount)
        windowed_data = numpy.array([[-1, -1]])
        for i in timestamped_stepcount:
            if i[1] != 0:
                windowed_data = numpy.vstack((windowed_data, i))
            elif i[1] == 0 and windowed_data[-1][1] != -1:
                windowed_data = numpy.vstack((windowed_data, [-1, -1]))
            else:
                pass
        return windowed_data

    def process_data(self, windowed_data):
        processed_data  = numpy.array([])
        old_timestamp   = 0
        first_timestamp = 0
        windowed_steps  = 0
        prior_value = -1
        for i, value in enumerate(windowed_data):
            if value[0] != -1 and prior_value == -1:
                first_timestamp = value[0]
                windowed_steps += value[1]
                prior_value     = value[1]
            elif value[0] != -1 and (i+1 >= len(windowed_data) or windowed_data[i+1][0] == -1):
                window_length = value[0] - first_timestamp
                windowed_steps += value[1]

                if len(processed_data) == 0:
                    processed_data = numpy.array([windowed_steps, window_length])
                else:
                    processed_data = numpy.vstack((processed_data, [windowed_steps, window_length]))
                prior_value = value[1]
                windowed_steps = 0
            elif value[0] != -1:
                windowed_steps += value[1]
                prior_value     = value[1]
            else:
                prior_value = value[1]
        return pickle.dumps(processed_data)

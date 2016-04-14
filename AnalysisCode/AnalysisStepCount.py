from AnalysisProcessingClass import AnalysisProcessingClass
from pickle import dumps


class StepCountDetection(AnalysisProcessingClass):

    def __init__(self, database, patient_id):
        super(StepCountDetection, self).__init__(database  = database,
                                                 patient_id = patient_id,
                                                 type_name  = "AnalysisStepCount",
                                                 table_name = "dataHMACC")

    def split_to_windows(self, data):
        return data

    def process_data(self, windowed_data):
        total_stepcount = 0

        for i in windowed_data:
            total_stepcount += i[9]

        return dumps(total_stepcount)

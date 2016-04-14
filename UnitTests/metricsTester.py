import unittest
from DailyMetricCode.DailyGaitSpeed import DailyGaitSpeed
from DailyMetricCode.DailyLifeSpace import DailyLifeSpace
from DailyMetricCode.DailyPercentRoom import DailyPercentRoom
from DailyMetricCode.DailyRoomTransitions import DailyRoomTransitions
from DailyMetricCode.DailyStepCount import DailyStepCount

class MetricsTester(unittest.TestCase):

    def setUp(self):
        host = "localhost"
        user = "brad"
        password = "moxie100"
        self.database = (host, user, password)

    def test_data_grab_lifespace(self):
        tester = DailyLifeSpace(database=self.database,
                                patient_id="bradley.zylstra")
        windows = tester.get_stamp_windows()
        for i in windows:
            start_stamp = i[0]
            end_stamp = i[1]
            data = tester.poll_data(start_stamp)
            if data:
                windowed_data  = tester.split_to_windows(data)
                metric = tester.process_data(windowed_data)
                tester.upload_to_database(start_stamp, end_stamp, metric)
                tester.upload_to_salesforce(end_stamp, metric)
                tester.write_timestamp(end_stamp)

    def test_data_grab_gaitspeed(self):
        tester = DailyGaitSpeed(database=self.database,
                                patient_id="bradley.zylstra")
        windows = tester.get_stamp_windows()
        for i in windows:
            start_stamp = i[0]
            end_stamp = i[1]
            data = tester.poll_data(start_stamp)
            if data != []:
                windowed_data  = tester.split_to_windows(data)
                try:
                    metric = tester.process_data(windowed_data)
                except:
                    print windowed_data
                tester.upload_to_database(start_stamp, end_stamp, metric)
                tester.upload_to_salesforce(end_stamp, metric)

    def test_data_grab_stepcount(self):
        tester = DailyStepCount(database=self.database,
                                patient_id="bradley.zylstra")
        windows = tester.get_stamp_windows()
        for i in windows:
            start_stamp = i[0]
            end_stamp = i[1]
            data = tester.poll_data(start_stamp)
            if data:
                windowed_data  = tester.split_to_windows(data)
                metric = tester.process_data(windowed_data)
                tester.upload_to_database(start_stamp, end_stamp, metric)
                tester.upload_to_salesforce(end_stamp, metric)
                tester.write_timestamp(end_stamp)

    def test_room_percent(self):
        tester = DailyPercentRoom(database=self.database,
                                  patient_id="bradley.zylstra")
        windows = tester.get_stamp_windows()
        for i in windows:
            start_stamp = i[0]
            end_stamp = i[1]
            data = tester.poll_data(start_stamp)
            if data:
                windowed_data = tester.split_to_windows(data)
                metric = tester.process_data(windowed_data)
                tester.upload_to_database(start_stamp, end_stamp, metric)
                tester.upload_to_salesforce(end_stamp, metric)
                tester.write_timestamp(end_stamp)
    def test_room_trans(self):
        tester = DailyRoomTransitions(database=self.database,
                                      patient_id="bradley.zylstra")
        windows = tester.get_stamp_windows()
        for i in windows:
            start_stamp = i[0]
            end_stamp = i[1]
            data = tester.poll_data(start_stamp)
            if data:
                windowed_data = tester.split_to_windows(data)
                metric = tester.process_data(windowed_data)
                tester.upload_to_database(start_stamp, end_stamp, metric)
                tester.upload_to_salesforce(end_stamp, metric)
                tester.write_timestamp(end_stamp)
if __name__ == '__main__':
    runner = unittest.main()
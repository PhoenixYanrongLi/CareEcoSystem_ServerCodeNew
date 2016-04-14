__author__ = 'Brad'
from MetricsClass import MetricsClass
import json
import ast

class DailyPercentRoom(MetricsClass):

    def __init__(self, database, patient_id):
        super(DailyPercentRoom, self).__init__(database    = database,
                                               patient_id  = patient_id,
                                               table_name  = 'AnalysisRoomLocation',
                                               metric_type = 'DailyPercentRoom')

    def fetch_rooms_list(self):
        if not self.fetch_from_database(database_name = self.database_name,
                                        table_name    = 'rooms',
                                        to_fetch      = 'ROOM_NAME'
                                        ):
            return False
        else:
            data = self.fetchall()
            data = zip(*list(zip(*data)))
            return list(zip(*data)[0])

    def split_to_windows(self, data):
        return data

    def process_data(self, data):
        data = data[0]
        # Fetch the data and the list of room associated with the patient
        rooms_list = self.fetch_rooms_list()
        if not rooms_list:
            raise RuntimeError

        # Create a 2d list n rooms wide initialized to a value of 0
        total_per_room = [0] * len(rooms_list)

        # Get the total number of data points for normalization later
        total_number_points = len(data)

        """
            For each data point, fetch the room that it is associated with in the rooms_list table, and then add
            1 to the total for that room.
            ex:
            rooms_list = ['bathroom', 'living_room', 'bed_room']
            data = ['living_room', 'living_room', 'living_room', 'bed_room', 'bed_room','bathroom']

            Then the total_per_room list will look like this:
            total_per_room = [1, 3, 2]
        """
        for i in data:
            if i[1] == "Room Not Know":
                pass
            else:
                total_per_room[rooms_list.index(i[1])] =  total_per_room[rooms_list.index(i[1])] + 1

        """
            Normalize the total_per_room list
            For our example, it should look something like this:

            total_per_room = [.16, .50, .33]
        """
        normalized = [(x / float(total_number_points))*100 for x in total_per_room]

        """
            Return a list of items in format [metric], [metric_names], example:

            [[.16, .50, .33], ['bathroom', 'living_room', 'bed_room']]
        """
        return [normalized, rooms_list]

    def upload_to_database(self, start_window, end_window, metric):
        """
        Uploads the metric to the database ['VARCHAR(100) NOT NULL PRIMARY KEY', 'FLOAT']
        :return:
        """
        for index, value in enumerate(metric[1]):
            metric[1][index] = value.replace(' ', '_')

        self.create_table(database_name= self.database_name,
                          table_name   = self.metric_type,
                          column_names = ['start_window', 'end_window'] + metric[1],
                          column_types = ['VARCHAR(100) NOT NULL PRIMARY KEY', 'VARCHAR(100) NOT NULL']+['FLOAT']*len(metric[1]))
        self.insert_into_database(database_name = self.database_name,
                                  table_name    = self.metric_type,
                                  column_names  = ['start_window', 'end_window']+ metric[1],
                                  values        = [start_window, end_window]+metric[0])
        return True

    def upload_to_salesforce(self, timestamp, metric):
        """
        Uploads the metric to salesforce
        :return:
        """
        room_list = []
        for i,e in enumerate(metric[0]):
            data = '{"percentage":' + str(e) + ', "room":' + '"' + metric[1][i] + '"' + '}'
            room_list.append(json.loads(data))
        metric_data = {
            "patientId": "DCE-" + self.patient_id,
            "timestamp": self.utc_to_datetime(timestamp).strftime('%x'),
            "metricList": [
            ],
            "roomPercentages":room_list
        }
        print self.sf.apexecute('FMMetrics/insertMetrics', method='POST', data=metric_data)
        return True

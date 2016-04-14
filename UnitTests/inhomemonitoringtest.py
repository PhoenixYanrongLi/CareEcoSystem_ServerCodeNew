__author__ = 'Brad'
from InHomeMonitoringCode.csv_room_reader import CSVRoomReader

roomdict = {'bedroom 1': 1, 'bathroom': 2, 'living room': 3, 'kitchen': 4, 'bedroom 2': 5, 'bedroom 3': 6}
reader = CSVRoomReader(roomdict)
x = reader.read_csv_pair("testData/estimote21.csv", "testData/ground_trust21.csv")

print x
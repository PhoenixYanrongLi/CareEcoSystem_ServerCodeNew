__author__ = 'Brad'
import MySQLdb
from DatabaseManagementCode.databaseWrapper import DatabaseWrapper

host = "localhost"
user = "brad"
password = "moxie100"
database = (host, user, password)
dataB = MySQLdb.connect(host=database[0], user=database[1], passwd=database[2])
cur = dataB.cursor()
data = DatabaseWrapper(database)
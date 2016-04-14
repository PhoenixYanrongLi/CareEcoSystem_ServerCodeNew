__author__ = 'Brad'

from phoneAnalysisMain import FFT_Stepcount, Mag_Acc_Time
import MySQLdb
import sys
import numpy
import datetime


class AnalysisUploader:

    def __init__(self, raw_acc_queue, raw_time_queue, database, database_name):
        self.rawAccQ = raw_acc_queue
        self.rawTQ = raw_time_queue
        self.dataB = MySQLdb.connect(host=database[0], user=database[1], passwd=database[2])
        self.cur = self.dataB.cursor()
        self.window = 512
        self.cutoff = 2.7
        self.w = [.3, .7]
        self.databaseName = database_name
        self.accData = []
        self.UnixTime_ms = []
        self.initTime = ''
        self.acc_data = []
        self.T_convert = []
        self.step_count = 0
        try:
            sql = "CREATE TABLE " + self.databaseName + "." + "step_count (datetime DOUBLE NOT NULL,steps FLOAT, PRIMARY KEY(datetime))"
            self.cur.execute(sql)
            print 'Created step count table for id: ' + self.databaseName
        except MySQLdb.Error:
            print 'Step count table found for database: ' + self.databaseName
            print(sys.exc_info())

    def get_steps(self):
        self.accData = []
        self.UnixTime_ms = numpy.array([])
        self.initTime = ''
        self.accData = self.rawAccQ.get(1)
        self.UnixTime_ms = self.rawTQ.get(1)
        self.accData = numpy.array(self.accData)

        self.UnixTime_ms = self.raw_time_to_unix(self.UnixTime_ms)

        self.UnixTime_ms = self.UnixTime_ms.astype(numpy.float)
        self.UnixTime_ms = numpy.array(self.UnixTime_ms)

        self.acc_data, self.T_convert = Mag_Acc_Time(self.accData, self.UnixTime_ms)
        self.step_count = FFT_Stepcount(self.acc_data, self.T_convert, self.window, self.cutoff)
        self.step_count = numpy.floor(self.step_count)
        
        print("StepCount:"+str(self.step_count))
        print("InitTime:"+str(self.initTime))

    def upload_steps(self):
        try:
            sql = "INSERT INTO " + self.databaseName + "." + "step_count (datetime,steps) VALUES (%s,%s)"
            self.cur.execute(sql, (str(self.initTime),  str(self.step_count)))
        except MySQLdb.Error:
            print ("Step count insert into database: " + self.databaseName + ' failed!')
            print(sys.exc_info())
        self.dataB.commit()

    def raw_time_to_unix(self, times):
        unix_times = []
        for index, time in enumerate(times):
            if index == 0:
                self.initTime = time[0]
            format_str = "%y-%m-%dT%H:%M:%S.%f"
            time_c = datetime.datetime.strptime(time[0], format_str)
            epoch = datetime.datetime.utcfromtimestamp(0)
            delta = time_c-epoch
            delta = delta.total_seconds()*1000
            if index == 0:
                self.initTime = delta/1000

            unix_times.append([delta])
        return numpy.array(unix_times)


def analysis_upload_threaded(rawAccQ, rawTQ, database, databaseName):
    analysis_uploader = AnalysisUploader(rawAccQ, rawTQ, database, databaseName)
    print("Analysis has started on phone "+databaseName+"!")
    while True:
        if rawAccQ.qsize() >= 1:
            analysis_uploader.get_steps()
            analysis_uploader.upload_steps()
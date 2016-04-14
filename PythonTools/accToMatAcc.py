__author__ = 'Brad'
import csv
import datetime

import scipy.io
import numpy


def writeFile(filename):
    writeDict={}
    f=open(filename,'r')
    timeAr=[]
    accAr=[]
    with open(filename, 'r') as f:
        reader = csv.reader(f, delimiter=" ")
        for time, x, y, z, azimuth, pitch, roll in reader:
            formatStr="%y-%m-%dT%H:%M:%S.%f"
            timeC=datetime.datetime.strptime(time,formatStr)
            epoch = datetime.datetime.utcfromtimestamp(0)
            delta=timeC-epoch
            delta=delta.total_seconds()*1000
            if len(timeAr)==0:
                timeAr=[delta]
                accAr=numpy.array([float(x),float(y),float(z)])
            else:
                timeAr=numpy.vstack((timeAr,delta))
                accAr=numpy.vstack([accAr,[float(x),float(y),float(z)]])

    writeDict={'AccData':accAr,'UnixTime_ms':timeAr}
    print accAr
    scipy.io.savemat(filename+'_AccelerometerData.mat',writeDict)



filename='99000213875160_20141113-193740_MM_ACC_1103.txt'
writeFile(filename)


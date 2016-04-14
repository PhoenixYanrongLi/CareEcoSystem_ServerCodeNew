"""

DEPRECATED CLASS

rawDataUpload uploads Acc and GPS data to a database line by line. It uses multithreading to upload all data in semi-real time.

getDTString returns a dateTime from a file string.
uploadAccGPS looks in the cellid directory for acc and gps folders, and launches a thread per folder it finds.
uploadAcc uploads acc data to an SQL database by line and by date
uploadGps decrypts then uploads the data to an SQL database by line and date
uploadRawFiles is the top level, it looks for new cellid folders and launches new uploadAccGPS threads.
"""
__author__ = "Bradley Zylstra"
__version__ = "1.0"
__maintainer__ = "Bradley Zylstra"
__email__ = "bradleybaldwin@gmx.com"
__status__ = "Development"

from multiprocessing import Pipe, Process, Queue
from AnalysisCode.AnalysisCode import analysis_upload_threaded
import MySQLdb
from os import path
from os import listdir
import time
import csv
import traceback
from FileManagementCode.decrypt import decryptDataFiles
import os
import datetime
import numpy


def get_dt_string(date_string):
    date_string = date_string.split("_", 2)[1]
    date = datetime.datetime.strptime(date_string, "%Y%m%d-%H%M%S")
    return date


def uploadAccGPS(cellid, database, dataTopPath, shutdownQ, updatePipe):
    # Upload raw data to
    running = True
    acc = False
    gps = False
    accQ = Queue()
    tQ = Queue()


    #print "Ran"
    while running:
        #print running
        #if(not shutdownQ.empty()):
        #    print shutdownQ.get()
        #    running=False
        if acc and gps:
            pass
        else:
            for f in listdir(dataTopPath):
                if (f.find("acc") >= 0) and (acc != True):
                    acc = True
                    accPath = path.join(dataTopPath, f)
                    p = Process(target=uploadAcc, args=(database, accPath, "_" + cellid, accQ, tQ, shutdownQ, updatePipe,))
                    p.start()
                    analysis = Process(target=analysis_upload_threaded, args=(accQ, tQ, database, "_" + cellid))
                    analysis.start()
                if (f.find("gps") >= 0) and (gps != True):
                    gps = True
                    gpsPath = path.join(dataTopPath, f)
                    g = Process(target=uploadGPS, args=(database, gpsPath, "_" + cellid, shutdownQ,))
                    g.start()
                    #shutdownQ.put(True)
    print "uploadAccGPS ended"


def uploadAcc(database, dataAcc, databaseName, accQ, tQ, shutdownQ, updatePipe):
    running = True
    dataB = MySQLdb.connect(host=database[0], user=database[1], passwd=database[2])
    cur = dataB.cursor()
    try:
        sql = "CREATE TABLE " + databaseName + "." + "acc (datetime VARCHAR(25) NOT NULL,x FLOAT,y FLOAT, z FLOAT, azimuth FLOAT, pitch FLOAT,roll FLOAT, PRIMARY KEY(datetime))"
        cur.execute(sql)
    except MySQLdb.Error:
        pass
    while running:
        file_dates = []
        date_name_dict = {}
        large_acc_array=[]
        large_tq_array=[]
        #if(shutdownQ.qsize()>0):
        #    running=False
        for f in listdir(dataAcc):
            if f.find("MM_ACC") > 0:
                temp_date = get_dt_string(f)
                file_dates.append(temp_date)
                date_name_dict[temp_date] = f
        file_dates.sort()

        #try:
        #    update_pipe.send(file_dates[-1:])
        #except:
        #    print "Pipe no send"
        #print"Here?"
        try:
            if file_dates:
                print "up in here"
                for i in file_dates:
                    with open(path.join(dataAcc, date_name_dict[i]), 'r') as f:
                        reader = csv.reader(f, delimiter=" ")
                        try:
                            for date_time, x, y, z, azimuth, pitch, roll in reader:

                                #Put data into the Accelerometer and time data Queue
                                if len(large_acc_array) == 0:
                                    large_acc_array = [float(x), float(y), float(z)]
                                    large_tq_array = [date_time]
                                else:
                                    large_acc_array = numpy.vstack([large_acc_array,[float(x), float(y), float(z)]])
                                    large_tq_array = numpy.vstack([large_tq_array,[date_time]])

                                #insert acc data into database
                                try:
                                    sql = "INSERT INTO " + databaseName + "." + "acc (datetime,x,y,z,azimuth,pitch,roll) VALUES (%s,%s,%s,%s,%s,%s,%s)"
                                    cur.execute(sql, (date_time, x, y, z, azimuth, pitch, roll))
                                except:
                                    pass
                            tQ.put(large_tq_array)
                            accQ.put(large_acc_array)
                            large_acc_array = []
                            large_tq_array = []
                            dataB.commit()
                            os.remove(path.join(dataAcc, date_name_dict[i]))
                        except ValueError:
                            os.remove(path.join(dataAcc, date_name_dict[i]))
        except:
            traceback.print_exc()


def uploadGPS(database, dataGPS, databaseName, shutdownQ):
    fileDates = []
    dateNameDict = {}
    running = True
    dataB = MySQLdb.connect(host=database[0], user=database[1], passwd=database[2])
    cur = dataB.cursor()
    try:
        sql = "CREATE TABLE " + databaseName + "." + "gps (datetime VARCHAR(25) NOT NULL,latitude FLOAT,longitude FLOAT, batterypct FLOAT, locationspeed FLOAT, locationaccuracy FLOAT,provider INT, PRIMARY KEY(datetime))"
        cur.execute(sql)
    except MySQLdb.Error:
        print 'GPS table found for database: ' + databaseName

    while running:
        #if(shutdownQ.qsize()>0):
        #    running=False
        decryptDataFiles(dataGPS)
        for f in listdir(dataGPS):
            if f.find("MM_GPS") > 0:
                tempDate = get_dt_string(f)
                fileDates.append(tempDate)
                dateNameDict[tempDate] = f
        fileDates.sort()

        for i in fileDates:
            try:
                with open(path.join(dataGPS, dateNameDict[i]), 'rb') as f:
                    stripped = (row.strip() for row in f)
                    reader = csv.reader(stripped, skipinitialspace=True, delimiter=" ")
                    for datetime, latitude, longitude, batterypct, locationspeed, locationaccuracy, provider in reader:
                        try:
                            sql = "INSERT INTO " + databaseName + "." + "gps (datetime,latitude,longitude,batterypct,locationspeed,locationaccuracy,provider) VALUES (%s,%s,%s,%s,%s,%s,%s)"
                            cur.execute(sql, (
                                datetime, latitude, longitude, batterypct, locationspeed, locationaccuracy, provider))
                        except MySQLdb.Error:
                            print "Already Read Data or GPS Table not found"
                    dataB.commit()
                os.remove(path.join(dataGPS, dateNameDict[i]))
            except:
                pass


def uploadRawFiles(pathToDataFiles, host, user, password, shutdownQ, updatePipe):

    fileNames = []
    print "started"
    topDataPath = []
    processNames = []
    updateTimes = {}
    run = True
    database = MySQLdb.connect(host=host, user=user, passwd=password)
    cur = database.cursor()
    databaseParams = (host, user, password)
    cellIDPipeDict = {}
    while run:
    #if(shutdownQ.qsize()>0):
    #   run=False
    #   print shutdownQ.get()
        for f in listdir(pathToDataFiles):
            if (f.find(".") < 0) and (f not in fileNames):
                fileNames.append(f)
                sql = "CREATE DATABASE _" + f
                try:
                    cur.execute(sql)
                except:
                    pass
                topDataPath.append(path.join(pathToDataFiles, f))
                if f not in processNames:
                    recvPipeUpdate, sendPipeUpdate = Pipe(True)
                    testPath = path.join(pathToDataFiles, f)
                    print "" \
                          "process started"
                    pid = Process(target=uploadAccGPS, args=(f, databaseParams, testPath, shutdownQ, sendPipeUpdate,))
                    pid.start()
                    cellIDPipeDict[f] = [recvPipeUpdate]
                    processNames.append(f)



                    #for i in cellIDPipeDict:
                    #    print "here?"
                    #    updateTimes[i]=cellIDPipeDict[i].recv()
                    #update_pipe.send(updateTimes)
    for i in cellIDPipeDict:
        cellIDPipeDict[i][0].send(False)
        cellIDPipeDict[i][0].recv()
    while shutdownQ.qsize() - 1 < len(processNames):
        time.sleep(1)
    for i in range(0, len(processNames)):
        shutdownQ.get()

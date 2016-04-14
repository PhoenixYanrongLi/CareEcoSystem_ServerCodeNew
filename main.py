__author__ = 'Brad'

from HttpServer.httpServer                           import httpServer
from DatabaseManagementCode.dataFileUploaderClass    import DataFileUploader
from DatabaseManagementCode.configFileUploaderClass  import ConfigFileUploader
from DatabaseManagementCode.eventFileUploaderClass   import EventFileUploader
from DatabaseManagementCode.requestFileUploaderClass import RequestFileUploader
from AnalysisCode.AnalysisThreadHandler              import AnalysisThreadHandler
import multiprocessing
import os
import socket
#from DailyMetricCode.runMetricCalcs import RunMetricCalcs
import datetime

#ip = socket.gethostbyname(socket.getfqdn())
ip = '198.199.116.85'
thr = multiprocessing.Process(target=httpServer, args=(ip, 8000))
thr.start()

current_path          = os.getcwd()
path_to_data_files    = os.path.join(current_path, 'HttpServer', 'data')
path_to_config_files  = os.path.join(current_path, 'HttpServer', 'config')
path_to_event_files   = os.path.join(current_path, 'HttpServer', 'events')
path_to_request_files = os.path.join(current_path, "HttpServer", 'requests')

if not os.path.exists(path_to_data_files):
    os.mkdir(path_to_data_files)

if not os.path.exists(path_to_config_files):
    os.mkdir(path_to_config_files)

if not os.path.exists(path_to_event_files):
    os.mkdir(path_to_event_files)

if not os.path.exists(path_to_request_files):
    os.mkdir(path_to_request_files)


host = "198.199.116.85"
user = "root"
password = "mysql"
if __name__ == '__main__':
    shutdownQ = multiprocessing.Queue()
    receiving_pipe, update_pipe = multiprocessing.Pipe()
    database = (host, user, password)

    p = DataFileUploader(database, path_to_data_files)
    p.start()

    p = ConfigFileUploader(database, path_to_config_files)
    p.start()

    p = EventFileUploader(database, path_to_event_files)
    p.start()

    p = RequestFileUploader(database, path_to_request_files)
    p.start()

    p = AnalysisThreadHandler(database, path_to_data_files)
    p.start()

    #p = RunMetricCalcs(database)
    #p.start()

    print datetime.datetime.utcnow()
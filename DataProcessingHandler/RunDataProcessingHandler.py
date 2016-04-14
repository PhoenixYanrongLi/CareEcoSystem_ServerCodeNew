__author__ = 'Brad'
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from pytz import utc
import multiprocessing
from DatabaseManagementCode.databaseWrapper import DatabaseWrapper
from FileManagementCode.signalHandler import SignalHandler
import signal
from time import sleep
from AnalysisCode.AnalysisThreadHandler import AnalysisThreadHandler
from DailyMetricCode.runMetricCalcs import RunMetricCalcs


class RunDataProcessing(multiprocessing.Process):

    def __init__(self, database):
        multiprocessing.Process.__init__(self)
        self.database = database

        executors = {
            'default': ThreadPoolExecutor(20),
        }

        self.scheduler = BackgroundScheduler(executors = executors,
                                             timezone  = utc)

    def run_calcs(self):
        analysis = AnalysisThreadHandler(self.database)
        analysis.start()
        analysis.join()

        metrics = RunMetricCalcs(self.database)
        metrics.start()
        metrics.join()

    def run(self):

        """
            Every 12 Hours, run Analysis Code, then run Metrics Code, finally run Anomaly Detection Code
        :return:
        """

        self.scheduler.start()
        job = self.scheduler.add_job(self.run_calcs,
                                     trigger = 'cron',
                                     hour    = '0,12')

        s = SignalHandler()
        signal.signal(signal.SIGINT, s.handle)
        while s.stop_value:
            sleep(1)

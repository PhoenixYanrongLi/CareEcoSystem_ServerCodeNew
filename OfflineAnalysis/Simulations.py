__author__ = 'george'

import numpy as np
from sklearn.datasets import make_blobs
from sklearn.preprocessing import normalize
from TrendDetection.DailyStepCountTrendDetection import DailyStepCountTrendDetection
from AnomalyDetection.DailyRoomPercentageAnomalyDetection import DailyRoomPercentageAnomalyDetection
from DatabaseManagementCode.databaseWrapper import DatabaseWrapper
from InHomeMonitoringCode.training_room_estimator import TrainingRoomEstimator
import matplotlib.pyplot as plt
import pickle

"""
This file contains simulations of the methods used. Plots are created using fake data to demonstrate how they work.
"""


class Simulate(DatabaseWrapper):
    """
    This class groups together related methods for performing the required simulations
    """
    def __init__(self):
        """
        open up remote database connection (note this must be changed to local if deployed)
        """

    @staticmethod
    def show_ransac(stepcounts=None, plotFlag=True):
        """
        This method demonstrates the RANSAC (RANdom SAmple Consensus) by generating a plot with simulation data
        """

        if stepcounts is None:
            # simulate normal data
            activeday = 10000
            lazyday = 3000
            stepcounts, truelabels = make_blobs(n_samples=31, centers=[[activeday]], cluster_std=750, random_state=8)
            for i in range(len((stepcounts))):
                if (i % 6 == 0) and (i != 0):
                    stepcounts[i] = np.random.normal(loc=lazyday, scale=750)
                    stepcounts[i-1] = np.random.normal(loc=lazyday, scale=750)
        else:
            # process real data
            stepcounts = np.array(stepcounts)
            stepcounts = stepcounts.reshape((len(stepcounts), 1))

        # apply trend detection
        steptrender = DailyStepCountTrendDetection(stepcounts)
        slope = steptrender.normalize_and_fit()

        # output regression slope and whether or not alarming
        alarmflag = steptrender.is_most_recent_trend_alarming()
        if alarmflag:
            print 'The slope is %f which is alarming' % slope
        else:
            print 'The slope is %f which is not alarming' % slope

        if plotFlag == True:
            # plot results
            linex = np.arange(0, len(stepcounts))
            pointsx = range(0, len(stepcounts))
            liney = steptrender.get_model().predict(linex[:, np.newaxis])
            plt.plot(linex, liney, 'r-', label='RANSAC regressor')
            pointsy = normalize(stepcounts, norm='l1', axis=0)
            plt.plot(pointsx, pointsy, 'ko', label='Step Counts')
            plt.legend(loc='upper left')
            plt.xlabel('Days')
            plt.ylabel('Normalized Step Count')

            plt.show()

        return alarmflag

    @staticmethod
    def show_dbscan(roompers=None, plotFlag=True):
        """
        simulate 1 month of normal hourly room percentage data followed by an anomalous percentage
        the normal data is bimodal following most peoples activity patterns in which there is routinely a weekday
        percentage and a weekend percentage. 1 day in which the person spends a large amount of time in the bathroom
        is simulated
        """
        if roompers is None:
            # simulate normal hourly data
            weekday = ([0.05, 0.95], 0.05) #bath, bed
            weekend = ([0.3, 0.7], 0.1)
            roomperwd, truelabelswd = make_blobs(n_samples=23, centers=weekday[0],
                                                 cluster_std=weekday[1], random_state=0)
            roomperwe, truelabelswe = make_blobs(n_samples=8, centers=weekend[0],
                                                 cluster_std=weekend[1], random_state=0)

            # combine modes
            roompers = np.vstack((roomperwd, roomperwe))

            # make positive and sum to one to simulate valid distribution
            for i in range(roompers.shape[0]):
                for j in range(roompers.shape[1]):
                    if roompers[i, j] < 0:
                        roompers[i, j] = 0
            roompersnorm = normalize(roompers, norm='l1')

            # simulate anomaly on most recent day where don't leave bedroom
            roompersnorm[-1, :] = np.array([0.8, 0.2])
        else:
            roompers = np.array(roompers)
            roompersnorm = normalize(roompers, norm='l1')

        print roompers
        print roompersnorm

        # detect outliers
        roompersdetector = DailyRoomPercentageAnomalyDetection(roompersnorm, eps=3, min_samples=3)
        labels = roompersdetector.scale_and_proximity_cluster(eps=3, min_samples=3)
        print roompersdetector.dblabels
        print roompersdetector.get_percent_of_room_percentage_labeled_outliers()

        if plotFlag:
            # plot results
            seenflag1 = False; seenflag2 = False; seenflag3 = False;
            for i, label in enumerate(labels):
                if label == 0:
                    if seenflag1:
                        plt.plot(roompersnorm[i][0], roompersnorm[i][1], 'ro')
                    else:
                        plt.plot(roompersnorm[i][0], roompersnorm[i][1], 'ro', label='Cluster 1')
                        seenflag1 = True
                elif label == 1:
                    if seenflag2:
                        plt.plot(roompersnorm[i][0], roompersnorm[i][1], 'kx')
                    else:
                        plt.plot(roompersnorm[i][0], roompersnorm[i][1], 'kx', label='Cluster 2')
                        seenflag2 = True
                elif label == -1:
                    if seenflag3:
                        plt.plot(roompersnorm[i][0], roompersnorm[i][1], 'b^')
                    else:
                        plt.plot(roompersnorm[i][0], roompersnorm[i][1], 'b^', label='Outlier')
                        seenflag3 = True
            plt.legend(loc='lower left')
            plt.axis([0, 1, 0, 1])
            plt.xlabel('Percentage of Day in Bathroom')
            plt.ylabel('Percentage of Day in Bedroom')
            plt.show()

    def show_klms(self):
        """
        Demonstrate the klms (kernal least mean squares) algorithm on a sample set of 50 RSSI points
        Maximum correntropy criterion (MCC) is used instead of mean square error (MSE)
        """
        # TODO: implement klms in room_estimator.py
        inputRSSI = np.array([-999, -999, -999, -999, -90,  -90, -999, -999, -999, -999,
                              -999, -999, -999, -999, -92,  -92, -999, -999, -999, -999,
                              -999, -999, -91,  -91,  -79,  -77, -82,  -80,  -90,  -94,
                              -92,  -90,  -999, -999, -999, -93, -93,  -93,  -83,  -85,
                              -88,  -89,  -89,  -91,  -73,  -73, -999, -999, -999, -999])

        trainRSSI = np.array([-999, -999, -999, -999, -999, -999, -999, -999, -999, -999,
                              -999, -999, -999, -999, -999, -999, -999, -999, -999, -999,
                              -999, -999, -75,  -75,  -75,  -75,  -75,  -75,  -75,  -75,
                              -75,  -75,  -75,  -75,  -75,  -75,  -75,  -75,  -75,  -75,
                              -75,  -75,  -75,  -75,  -75,  -75,  -999, -999, -999, -999])

    def show_rnn(self):
        """
        Demonstrate the recurrent neural network for sequence labeling
        """

        def train_classifier(trainrssilist, traingtlist):
            """
            train RNN
            :return: trained classifier
            """
            trainer      = TrainingRoomEstimator(None)
            trainedclassifier = trainer.train_classifier2(trainrssilist, traingtlist)

            return trainedclassifier

        def apply_classifier(trainedclassifer, data):
            """
            apply trained RNN and plot results
            :param trainedclassifer: trained RNN
            :param data:             data to be filtered
            """
            # TODO: implement this
            pass

        trainrssilist, traingtlist, predlist = self.read_from_database('alex.bayen', 1449841703000, 1449846805000)
        print 'trainrssilist'
        print trainrssilist
        print 'traingtlist'
        print traingtlist
        print 'predlist'
        print predlist
        train_classifier(trainrssilist, traingtlist)

    def show_particle(self):
        # TODO: implement this
        pass

    def show_UKF(self):
        # TODO: implement this
        pass


    def show_filtlearn(self):

        trainrssilist, traingtlist, predlist = self.read_from_database('george.netscher', 1444594894000, 1444597946000)

        # read in training data
        trainer      = TrainingRoomEstimator(None)
        rssiarray, groundmatchlist = trainer.read_training_pair(trainrssilist, traingtlist)
        predmatcharray = self.read_pred_pair(predlist, traingtlist)

        # convert to numpy array of integers matching the indexes in self.roomlist
        groundmatcharray = np.zeros([rssiarray.shape[0], 1])
        for i, room in enumerate(groundmatchlist):
            groundmatcharray[i] = trainer.roomlist.index(room)
        predarray = np.zeros([len(predmatcharray), 1])
        for i, room in enumerate(predmatcharray):
            predarray[i] = trainer.roomlist.index(room)

        # calculate accuracy
        assert len(predarray) == len(groundmatcharray)
        err = 0
        for pair in zip(predarray, groundmatcharray):
            if pair[0] != pair[1]:
                err += 1
        errrate = err / float(len(predarray))

        print 'The room detection errrate on the training set is %f' % errrate

        badpred = np.argmax(rssiarray, axis=1)
        err = 0
        for pair in zip(badpred, groundmatcharray):
            if pair[0] != pair[1]:
                err += 1
        errrate = err / float(len(predarray))

        print 'The naive room detection errrate on the training set is %f' % errrate

        # plot raw rssi data
        colorlist = ['k', 'r', 'b', 'g']
        for i in range(4):
            if i == 0:
                plt.plot(rssiarray[:, i], colorlist[i] + 's', label='Raw RSSI')
            plt.plot(rssiarray[:, i], colorlist[i] + 's')
        for i in range(len(groundmatcharray)):
            if i == 0:
                plt.plot(i, -50, colorlist[i] + 'o', label='True Room')
            plt.plot(i, -50, colorlist[int(groundmatcharray[i][0])] + 'o')
        for i in range(len(predarray)):
            if i == 0:
                plt.plot(i, -51, colorlist[i] + '^', label='Predicted Room')
            plt.plot(i, -51, colorlist[int(predarray[i][0])] + '^')
        plt.legend(loc='lower left')
        plt.xlabel('Seconds')
        plt.ylabel('Raw RSSI')

        plt.show()

    def read_from_database(self, patientid, starttime, endtime):
        databasename = '_' + patientid
        """
        @:param patientid: str of the patient to get data from
        @:param starttime: int of the timestamp for opening data window (inclusive)
        @:param endtime:   int of the timestamp for closing data window (exclusive)
        @return: rssi list, ground trust list
        """

        filename = 'RoomDataFiles/' + patientid + str(starttime) + '_trainingdata.p'
        try:
            # first try to read from local pickle file
            (trainrssilist, traingtlist, predlist) = pickle.load(open(filename, "rb"))
        except IOError as e:
            # if pickle file doesn't exist, read from remote database and create new pickle file
            if e.errno == 2:
                # read from database
                print e.message

                # Retrieve the ground trust entries
                try:
                    DatabaseWrapper.__init__(self, user='brad', password='moxie100',
                         remote_host='169.230.163.198', remote_port=5282)
                    if not self.fetch_from_database(database_name = databasename,
                                                    table_name    = 'configMMGT',
                                                    where         = [['type' , 'CR'],
                                                                     ['start', '>=', starttime],
                                                                     ['end'  , '<=', endtime]],
                                                    order_by      = ['start', 'ASC']):
                        traingtlist = []
                    else:
                        traingtlist = [[row[1], row[2], row[3]] for row in self]  # [[label, start, end], ...]

                    # Retrieve the rssi entries
                    if not self.fetch_from_database(database_name = databasename,
                                                    table_name    = 'dataHMRSSI',
                                                    where         = [['timestamp', '>=', starttime],
                                                                     ['timestamp', '<=', endtime]],
                                                    order_by      = ['timestamp', 'ASC']):
                        trainrssilist = []
                    else:
                        trainrssilist = []
                        prevrow = [None, None, None, None, None]
                        for row in self:
                            # print prevrow[0], row[0]
                            if row[0] != prevrow[0]:
                                trainrssilist.append(row)
                            prevrow = row

                    # Retrieve predicted results
                    if not self.fetch_from_database(database_name = databasename,
                                                table_name    = 'AnalysisRoomLocation',
                                                where         = [['start_window', '<=', starttime],
                                                                 ['end_window'  , '>=', endtime]],
                                                order_by      = ['start_window', 'ASC']):
                        predlist = []
                    else:
                        latest_data = self.fetchall()
                        data = (zip(*latest_data))
                        predcontlist = pickle.loads(data[2][0])

                        predlist = [row for row in predcontlist[0] \
                                    if row[0] >= starttime and row[0] <= endtime]

                    # store data locally
                    pickle.dump((trainrssilist, traingtlist, predlist), open(filename, "wb"))
                finally:
                    self.__del__() # close sshtunnel

        return trainrssilist, traingtlist, predlist

    @staticmethod
    def read_pred_pair(predlist, traingtlist):
        """
        select the predictions within the ground trust windows and return numpy array
        :param predlist:
        :param traingtlist:
        :return: numpy array containing predictions within ground trust windows
        """
        gtcounter = 0
        outlist = []
        for predrow in predlist:
            if gtcounter == len(traingtlist):
                break
            if predrow[0] >= traingtlist[gtcounter][1] and predrow[0] < traingtlist[gtcounter][2]:
                outlist.append(predrow[1])
            if predrow[0] >= traingtlist[gtcounter][2]:
                gtcounter += 1

        return np.array(outlist)



if __name__ == '__main__':
    # set matplotlib config
    font = {'family' : 'normal',
        'weight' : 'bold',
        'size'   : 16}
    plt.rc('font', **font)

    simulator = Simulate()
    # simulator.show_ransac()
    # simulator.show_dbscan()
    # simulator.show_filtlearn()
    # a = pickle.load(open('/Users/george/Desktop/test2.p', 'rb'))
    # print a.summarymap

    simulator.show_rnn()


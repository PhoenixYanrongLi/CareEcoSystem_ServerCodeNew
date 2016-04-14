__author__ = 'gmn255'

import unittest
import numpy as np
from sklearn.datasets import make_blobs
from sklearn.preprocessing import normalize
from DailyStepCountAnomalyDetection import DailyStepCountAnomalyDetection
from LifeSpaceAnomalyDetection import LifeSpaceAnomalyDetection
from DailyRoomPercentageAnomalyDetection import DailyRoomPercentageAnomalyDetection
from HourlyRoomPercentageAnomalyDetection import HourlyRoomPercentageAnomalyDetection

class RoomEstimatorTestCase(unittest.TestCase):

    def test_daily_step_count(self):
        """
        simulate 1 month of normal step count data followed by an anomalous count
        the normal data is bimodal following most peoples activity patterns in which there is routinely an active day
        (e.g., weekday), and a lazy day (e.g., weekend)
        """

        # simulate normal data
        activeday = 10000
        lazyday = 3000
        stepcounts, truelabels = make_blobs(n_samples=31, centers=[[activeday], [lazyday]], cluster_std=750, random_state=0)

        # simulate anomaly on most recent day
        stepcounts[-1] = 50

        stepdetector = DailyStepCountAnomalyDetection(stepcounts, eps=0.3, min_samples=8)
        outlierflag = stepdetector.is_most_recent_stepcount_an_outlier()
        percentoutliers = stepdetector.get_percent_of_values_labeled_outliers()

        # print stepcounts
        # print stepdetector.get_labels()

        # check that most recent value should be an anomaly
        errormsg = "Anomaly on most recent day not detected"
        self.assertEquals(outlierflag, True, errormsg)

        # check percent of values that are anomalies
        errormsg = "Over 10% of data appears anomalous. Normal data detected as anomalies = {:.2f}%".format(percentoutliers)
        self.assertLessEqual(percentoutliers, 0.1, errormsg)

    def test_daily_lifespace(self):
        """
        simulate 1 month of normal lifespace data followed by an anomalous count
        the normal data is bimodal following most peoples activity patterns in which there is routinely a weekday
        destination (i.e., work), and many types of weekend destinations (i.e., parks, zoos,) with higher variance
        """
        # simulate normal data
        weekday = (6000, 100)
        weekend = (2000, 1000)

        lifespaceswd, truelabelswd = make_blobs(n_samples=23, centers=[weekday[0]],
                                                cluster_std=weekday[1], random_state=0)
        lifespaceswe, truelabelswe = make_blobs(n_samples=8, centers=[weekend[0]],
                                                cluster_std=weekend[1], random_state=0)

        # combine modes
        lifespaces = np.vstack((lifespaceswd, lifespaceswe))

        # simulate anomaly on most recent day
        lifespaces[-1] = 100

        # detect outliers
        lifedetector = LifeSpaceAnomalyDetection(lifespaces, eps=0.7, min_samples=4)
        outlierflag = lifedetector.is_most_recent_lifespace_an_outlier()
        percentoutliers = lifedetector.get_percent_of_values_labeled_outliers()

        # print lifespaces
        # print lifedetector.get_labels()

        # check that most recent value should be an anomaly
        errormsg = "Anomaly on most recent day not detected"
        self.assertEquals(outlierflag, True, errormsg)

        # check percent of values that are anomalies
        errormsg = "Over 10% of data appears anomalous. Normal data detected as anomalies = {:.2f}%".format(percentoutliers)
        self.assertLessEqual(percentoutliers, 0.1, errormsg)

    def test_daily_room_percentage(self):
        """
        simulate 1 month of normal room percentage data followed by an anomalous percentage
        the normal data is bimodal following most peoples activity patterns in which there is routinely a weekday
        percentage and a weekend percentage. 1 day in which an extreme amount of time is spent in a less visited room
        is simulated (e.g., bathroom), and one day in which an extreme amount of time is spent in a more visited room
        (e.g., bedroom) is simulated
        """

        # simulate normal data
        weekday = ([0.5, 0.3, 0.17, 0.01, 0.01, 0.01], 0.02)
        weekend = ([0.3, 0.3, 0.1, 0.1, 0.1, 0.01], 0.1)
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

        # simulate anomaly on most recent day in less visited room (e.g., bathroom)
        roompersnorm[-1, :] = np.array([0.1, 0.01, 0.86, 0.01, 0.01, 0.01])

        # detect outliers
        roompersdetector = DailyRoomPercentageAnomalyDetection(roompersnorm, eps=4.5, min_samples=3)
        outlierflag = roompersdetector.is_most_recent_room_percentage_an_outlier()
        percentoutliers = roompersdetector.get_percent_of_values_labeled_outliers()

        # print roompersnorm
        # print roompersdetector.get_labels()

        # check that most recent value should be an anomaly
        errormsg = "Anomaly on most recent day not detected for less visited room"
        self.assertEquals(outlierflag, True, errormsg)

        # check percent of values that are anomalies
        errormsg = "Over 10% of data appears anomalous for less visited room. " \
                   "Normal data detected as anomalies = {:.2f}%".format(percentoutliers)
        self.assertLessEqual(percentoutliers, 0.1, errormsg)

        # simulate anomaly on most recent day in more visited room (e.g., bedroom)
        roompersnorm[-1, :] = np.array([0.95, 0.01, 0.01, 0.01, 0.01, 0.01])

        # detect outliers
        roompersdetector = DailyStepCountAnomalyDetection(roompersnorm, eps=4.5, min_samples=3)
        outlierflag = roompersdetector.is_most_recent_stepcount_an_outlier()
        percentoutliers = roompersdetector.get_percent_of_values_labeled_outliers()

        # print roompersnorm
        # print roompersdetector.get_labels()

        # check that most recent value should be an anomaly
        errormsg = "Anomaly on most recent day not detected for less visited room"
        self.assertEquals(outlierflag, True, errormsg)

        # check percent of values that are anomalies
        errormsg = "Over 10% of data appears anomalous for less visited room. " \
                   "Normal data detected as anomalies = {:.2f}%".format(percentoutliers)
        self.assertLessEqual(percentoutliers, 0.1, errormsg)

    def test_hourly_room_percentage(self):
        """
        simulate 1 month of normal hourly room percentage data followed by an anomalous percentage
        the normal data is bimodal following most peoples activity patterns in which there is routinely a weekday
        percentage and a weekend percentage. 1 day in which the person doesn't wake up on time is simulated
        """

        # simulate normal hourly data
        weekday = ([0.1, 0.6, 0.2, 0.04, 0.03, 0.03], 0.02)
        weekend = ([0.2, 0.2, 0.2, 0.2, 0.2, 0.0], 0.1)
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
        roompersnorm[-1, :] = np.array([0.95, 0.01, 0.01, 0.01, 0.01, 0.01])

        # detect outliers
        roompersdetector = HourlyRoomPercentageAnomalyDetection(roompersnorm, eps=4, min_samples=3)
        outlierflag = roompersdetector.is_most_recent_room_percentage_an_outlier()
        percentoutliers = roompersdetector.get_percent_of_values_labeled_outliers()

        # print roompersnorm
        # print roompersdetector.get_labels()

        # check that most recent value should be an anomaly
        errormsg = "Anomaly on most recent day not detected for less visited room"
        self.assertEquals(outlierflag, True, errormsg)

        # check percent of values that are anomalies
        errormsg = "Over 10% of data appears anomalous for less visited room. " \
                   "Normal data detected as anomalies = {:.2f}%".format(percentoutliers)
        self.assertLessEqual(percentoutliers, 0.1, errormsg)




if __name__ == '__main__':
    unittest.main()

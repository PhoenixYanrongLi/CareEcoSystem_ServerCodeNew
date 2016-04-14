__author__ = 'gmn255'

from AnomalyDetectionClass import AnomalyDetectionClass

class HourlyRoomPercentageAnomalyDetection(AnomalyDetectionClass):
    """
    This class detects anomalies based on the percentage of time spent in each room
    """

    def __init__(self, datalist, eps=4, min_samples=3):
        """
        constructor
        :param datalist: list of room percentages from the same hour of the day for many days
        """
        super(HourlyRoomPercentageAnomalyDetection, self).__init__(datalist, eps, min_samples)

    def is_most_recent_room_percentage_an_outlier(self):
        """
        Detect outliers in most recent room percentage values
        :param eps: the maximum distance for 2 room percentages to be considered in the same neighborhood
        :param min_samples: the minimum number of room percentages within the neighborhood to form a core point.
        Clusters are created by grouping all room percentages within eps of a core point together
        :return: true if most recent room percentage is an outlier, false if not
        """
        return self.is_most_recent_value_an_outlier()

    def get_percent_of_room_percentage_labeled_outliers(self):
        """
        This function calculates the percent of room percentages that were considered outliers from the datalist given
        :return: percent of values that are outliers as a value in [0,1]
        """
        return self.get_percent_of_values_labeled_outliers()



__author__ = 'gmn255'

from AnomalyDetectionClass import AnomalyDetectionClass

class LifeSpaceAnomalyDetection(AnomalyDetectionClass):
    """
    This class detects anomalies based on the lifespace data stream
    """

    def __init__(self, datalist, eps=0.7, min_samples=4):
        """
        constructor
        """
        super(LifeSpaceAnomalyDetection, self).__init__(datalist, eps, min_samples)

    def is_most_recent_lifespace_an_outlier(self):
        """
        Detect outliers in most recent lifespace values
        :param eps: the maximum distance for 2 lifespaces to be considered in the same neighborhood
        :param min_samples: the minimum number of lifespaces within the neighborhood to form a core point. Clusters are
        created by grouping all lifespaces within eps of a core point together
        :return: true if most recent lifespace is an outlier, false if not
        """
        return self.is_most_recent_value_an_outlier()

    def get_percent_of_lifespace_labeled_outliers(self):
        """
        This function calculates the percent of lifespace that were considered outliers from the datalist given
        :return: percent of values that are outliers as a value in [0,1]
        """
        return self.get_percent_of_values_labeled_outliers()




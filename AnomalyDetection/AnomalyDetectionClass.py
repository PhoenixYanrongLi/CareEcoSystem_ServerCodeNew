__author__ = 'gmn255'

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN

class AnomalyDetectionClass(object):
    """
    This class implements the core algorithms for anomaly detection.
    It is meant to be subclassed for specific data streams (i.e., stepcount, GPS, etc.)
    Anomaly/outlier detection is performed based on density, so real clusters with low density could potentially be
    labeled outliers
    """

    def __init__(self, datalist, eps=0.3, min_samples=8):
        self.datalist = datalist
        self.dblabels = self.scale_and_proximity_cluster(eps, min_samples)

    def get_labels(self):
        """
        :return: the cluster labels where -1 marks an outlier
        """
        return self.dblabels

    def scale_and_proximity_cluster(self, eps=0.3, min_samples=8):
        """
        This method performs clustering based on proximity after scaling input data to have 0 mean and unit variance
        Note that it will perform well only when clusters are of similar density. Clusters are marked with natural
        numbers according to the number of clusters detected and outliers are marked by -1
        :param datalist: the input data to be clustered
        :param eps: the maximum distance for 2 points to be considered in the same neighborhood
        :param min_samples: the minimum number of samples within the neighborhood to form a core point. Clusters are
        created by grouping all samples within eps of a core point together
        :return: a list of the same length as datalist with the value being the cluster label for that point. Outliers
        have value -1
        """
        # make 0 mean and unit variance
        scaledcounts = StandardScaler().fit_transform(self.datalist)

        # perform clustering
        db = DBSCAN(eps=eps, min_samples=min_samples).fit(scaledcounts)

        return db.labels_

    def is_most_recent_value_an_outlier(self):
        """
        This function determines if the most recent value is an outlier. It assumes
        that the most recent value is stored in the last entry of the list
        :param datalist: a list of all values for one patient
        :return: true if most recent day is an outlier, false if not
        """

        # if last value is a -1, the most recent value is an outlier
        return True if self.dblabels[-1] == -1 else False

    def get_percent_of_values_labeled_outliers(self):
        """
        This function calculates the percent of values that were considered outliers from the datalist given to the
        constructor
        :return: percent of values that are outliers as a value in [0,1]
        """

        return float(len([i for i in self.dblabels if i == -1]))/len(self.dblabels)
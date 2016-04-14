__author__ = 'gmn255'

from sklearn.preprocessing import normalize
from sklearn import linear_model
import numpy as np


class TrendDetectionClass(object):
    """
    This class implements the core algorithms for trend detection.
    It is meant to be subclassed for specific data streams (i.e., stepcount, GPS, etc.)
    It fits a simple linear regression line over the last 30 days of data and returns the slope.
    Data is normalized such that the same threshold can be used for all negative trends
    RANSAC regression is used to add robustness to multimodel distributions
    The intent is that negative trends will trigger events
    """

    def __init__(self, datalist):
        self.datalist = datalist
        self.model = None

    def normalize_and_fit(self):
        """
        This method performs robust linear regression after scaling input data to sum to 1
        :return: regression coefficient (negative indicates downward trend)
        :param datalist: the input data to be modeled. Input data must be in order starting with the oldest values and
        ending with the most recent
        """
        # make counts sum to 1
        normalizedcounts = normalize(self.datalist, norm='l1', axis=0)[:, 0]

        # center counts
        centeredcounts = normalizedcounts
        x = range(len(centeredcounts))
        centeredx = np.array(x).reshape(-1, 1)

        # perform regression
        self.model = linear_model.RANSACRegressor(linear_model.LinearRegression())
        self.model.fit(centeredx, centeredcounts)

        # return slope
        return self.model.estimator_.coef_

    def get_model(self):
        """
        After calling the normalize_and_fit method, this will return the fit model
        :return: the model used for regression; None if not yet fit
        """
        return self.model

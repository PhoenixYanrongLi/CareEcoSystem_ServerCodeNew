__author__ = 'gmn255'

"""
This class creates an sklearn classifier for simply picking the beacon with the
least negative received signal strength as the expected room to fit into the sklearn
framework
"""

import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin

class NaiveRSSIClassifier(BaseEstimator, ClassifierMixin):
    """Predicts the room with the least negative RSSI value"""
    def __init__(self, roomlist):
        """

        :param roomlist: list mapping indices to room names
        :return: nothing
        """
        self.roomlist = roomlist

    def fit(self, X, y):
        """
        X and y are taken as arguments only to match sklearn syntax. this function actually
        does nothing because the room identity is given through the roomlist in the constructor
        :param X: data matrix
        :param y: label vector
        :return: trained classifier
        """
        return self

    def predict(self, X):
        """
        for each timestamp, naively pick the room with the least negative RSSI value
        :param X: datapoint as numpy array or list
        :return: numpy array of expected labels
        """

        if isinstance(X, list):
            X = np.array(X)

        # find index list of rooms with highest RSSI ignoring functionals
        idx = np.argmax(X[:, :len(self.roomlist)], axis=1)

        # create list of room labels
        y = [self.roomlist[i] for i in idx]

        return y



__author__ = 'gmn255'

# RealTimeRoomEstimator accepts a trained instance of TrainingRoomEstimator
# The primary function is classify_room. It accepts a trained sci-kit learn classifier
# and a 2D list of strings from the rssi data collection and outputs a 2D list of estimated
# rooms at each timestamp

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.base import BaseEstimator
import training_room_estimator
from room_estimator import RoomEstimator


class RealTimeRoomEstimator(RoomEstimator):

    def __init__(self, trainer):
        # constructor
        super(RealTimeRoomEstimator, self).__init__()
        # trainer = trained instance of TrainingRoomEstimator which contains object information (e.g., beacon coor)
        self.trainer = trainer
        # myhouse = house object with beacon coors
        self.myhouse = trainer.myhouse

        # set values from parent class
        # timearray = the array of time points collected from estimote scanning starting at 0
        self.timearray = trainer.timearray
        # timeref = the actual time at which the first estimote measurement is taken and used as reference
        self.timeref = trainer.timeref
        # roomlist specifies the dictionary mapping rooms to indices (i.e., not beacon minors but internal indices)
        self.roomlist = trainer.roomlist
        # numrooms = the number of rooms
        self.numrooms = trainer.numrooms

    def classify_room(self, rssilist, clf):
        # This is the main function to be used from this class
        # it takes an array of rssi strings in our designated format as rssilist
        # and a pretrained classifier clf.
        # It outputs the room estimate as a matrix of time stamps and room predictions
        # based on the given roomlist in the constructor
        # Inputs:
        #   rssiarray = 2D list of strings
        #   clf = sci-kit learn classifier
        # Outputs:
        #   outputarray = dx2 list of strings where first column is timestamp and second is room

        # convert to proper format
        rssiarray = self.read_rssi_list(rssilist)

        ## filter
        # no filter
        # efilt = rssiarray

        # simple LPF
        # efilt = self.moving_average_erssi_filter(rssiarray)

        # Kalman with respect to time and no prior model
        # efilt = self.kalman_time_erssi_filter(rssiarray, np.eye(6))

        # state transition matrix for time prior built from LPF coefficients
        filter_coeff = np.array([0.0525, 0.1528, 0.2947, 0.2947, 0.1528, 0.0525])
        A = np.zeros([len(filter_coeff), len(filter_coeff)])
        A[:, 0] = filter_coeff
        A[1:, 1] = filter_coeff[:5]
        A[2:, 2] = filter_coeff[:4]
        A[3:, 3] = filter_coeff[:3]
        A[4:, 4] = filter_coeff[:2]
        A[5:, 5] = filter_coeff[:1]

        # Kalman with respect to time and LPF coefficients used as prior
        # efilt = self.kalman_time_erssi_filter(rssiarray, A)

        # A priori estimated gradient adaptive filter
        # efilt = self.adaptive_grad_erssi_filter(rssiarray)

        # A priori estimated momentum adaptive filter
        # efilt = self.adaptive_momen_erssi_filter(rssiarray)

        # A priori estimated Newton adaptive filter
        # efilt = self.adaptive_newt_erssi_filter(rssiarray)

        # LMS gradient adaptive filter
        # efilt = self.LMS_grad_erssi_filter(rssiarray)

        # LMS HB adaptive filter
        # efilt = self.LMS_HB_erssi_filter(rssiarray)

        # LMS momentum adaptive filter
        efilt = self.LMS_momen_erssi_filter(rssiarray, restarts=True)

        # LMS Newtwon adaptive filter (stochastic 2nd order)
        # efilt = self.LMS_newt_erssi_filter(rssiarray)

        # RLS sliding window filter
        # efilt = self.RLS_erssi_filter(rssiarray)

        # LMS gradient adaptive filter with l1 error function
        # efilt = self.LMS_l1_grad_erssi_filter(rssiarray)

        # LMS momentum adaptive filter with l1 error function
        # efilt = self.LMS_l1_momen_erssi_filter(rssiarray)

        # state transition matrix for Kalman - power law distribution (fat tailed)
        gamma = 0.1
        A = np.array([
            [gamma, gamma**2, gamma**2, gamma**2, gamma**3, gamma**3],
            [gamma**2, gamma, gamma**2, gamma**2, gamma**2, gamma**2],
            [gamma**2, gamma**2, gamma, gamma**2, gamma**2, gamma**2],
            [gamma**2, gamma**2, gamma**2, gamma, gamma**3, gamma**3],
            [gamma**3, gamma**2, gamma**2, gamma**3, gamma, gamma**2],
            [gamma**3, gamma**2, gamma**2, gamma**3, gamma**2, gamma]
        ])
        # normalize each row
        for i in range(A.shape[0]):
            rownorm = np.linalg.norm(A[i, :], ord=1)
            for j in range(A.shape[1]):
                A[i, j] /= rownorm

        # Kalman with simple diffusion model of room transitions
        # efilt = self.kalman_space_erssi_filter(rssiarray, A)

        # find WPL functionals
        ecoor = self.myhouse.get_coor_from_rssi(efilt)

        # create total feature vector
        etotal = np.hstack([efilt,  ecoor])

        # standardize features by removing the mean and scaling to unit variance
        # etotal = StandardScaler().fit_transform(etotal)

        # apply previously learned classifier
        roompredict = clf.predict(etotal)

        # if all rssi values are less than -200, assume out of house
        minrssi = -200
        for i, row in enumerate(rssiarray):
            if(all(row < minrssi)):
                roompredict[i] = "Room Not Known"


        outputlist = []
        for i in range(len(roompredict)):
            # append [timestamp, room]
            room = roompredict[i]
            outputlist.append([rssilist[i][0], room])

        return outputlist
__author__ = 'gmn255'

# RoomEstimator provides an abstract class for room estimator classes to subclass
# It implements the core methods that are necessary for both the estimator training
# and the real time estimation based on the trained classifier

from parse import parse
import string as string
import numpy as np
from sys import maxint

class RoomEstimator(object):

    def __init__(self):
        # timearray = the array of time points collected from estimote scanning starting at 0
        self.timearray = np.empty(0, dtype='i8')
        # timeref = the actual time at which the first estimote measurement is taken and used as reference
        self.timeref = 0
        # roomlist specifies the dictionary mapping rooms to indices (i.e., not beacon minors but internal indices)
        self.roomlist = []
        # numrooms = the number of rooms
        self.numrooms = 0

    def _get_time(self, timestamp):
        # 6/9/15: timestamp is now expected to be in long format when pulled from database
        # Convert the timestamp into time in seconds
        # the input is in format 15-04-01T08:12:33.000
        # and the output is a natural number based on a 5-year cycle

        # if isinstance(timestamp, basestring):
        #     # if timestamp is a string, perform appropriate conversion
        #     # use relative time since first data point as time index
        #     timeholder = parse("{:d}-{:d}-{:d}T{:d}:{:d}:{:d}.000", timestamp)
        #     t = (3110400*timeholder.fixed[0] + 1036800*timeholder.fixed[1] + 86400*timeholder.fixed[2] +
        #          3600*timeholder.fixed[3] + 60*timeholder.fixed[4] + timeholder.fixed[5]) - self.timeref
        # elif isinstance(timestamp, (int, long)):
            # if timestamp is an int (or long), return as is
            # t = timestamp - self.timeref
        if isinstance(timestamp, basestring):
            timestamp = long(timestamp)
        t = timestamp - self.timeref
        return t

    def _get_rssi(self, rssiline):
        # Convert one line strings from the dequeued array into a numpy array with
        # indexes determined from roomlist mapping and values read from strings

        rssiarray = np.empty(self.numrooms)
        rssiarray.fill(-999)
        for i in range(self.numrooms):
            rssi = int(float(rssiline[2*i + 3]))
            rssiarray[i] = rssi

        return rssiarray

    def _get_room(self, roomstring):
        # translate a room string from the database (e.g., bedroom 1) to an index (e.g. 1)
        roomstring = string.strip(roomstring, '"[]')  # may contain quotes (") on each end
        return roomstring
        # # remove spaces from previous format
        # rs = string.split(roomstring)
        # rd = ""
        # for c in rs:
        #     rd = rd + c
        # return rd

    def read_rssi_list(self, rssilist):
        # read raw array and convert strings to an array of
        # usuable values and update self.timearray accordingly
        # Input:
        #   rssilist = 2d list of strings
        # Output:
        #   outputarray = dxr numpy array of d data points and r rssi values
        #   self.timearray = numpy array of timestamps used

        estilist = []
        for i in range(len(rssilist)):
            if i == 0:
                # on first iteration need to define time reference, create roomlist, and read first entry
                self.timeref = 0
                self.timeref = self._get_time(rssilist[i][0])

                self.numrooms = int(rssilist[i][1])
                for j in range(self.numrooms):
                    room = string.strip(rssilist[0][2*j + 2], '[]')
                    self.roomlist.append(room)

                self.timearray = np.array(self._get_time(rssilist[i][0]))
                estilist.append(self._get_rssi(rssilist[i][:]))
                continue
            time = self._get_time(rssilist[i][0])
            self.timearray = np.append(self.timearray, time)

            rssisubarray = self._get_rssi(rssilist[i][:])
            estilist.append(rssisubarray)

        #print np.array(estilist)
        outputarray = np.array(estilist)  # return list as numpy array
        return outputarray

    @staticmethod
    def moving_average_erssi_filter(erssiarray):
        # take an estimote RSSI matrix of mxn data points where m refers to time and n refers to room
        # assumes sampling rate = 0.1 Hz, passband cutoff = 0.04 Hz, stopband attenuation = 60 dB (see LPF.m)
        # return a filtered version of the raw data array

        filter_coeff = [0.0525, 0.1528, 0.2947, 0.2947, 0.1528, 0.0525]

        filtmat = np.empty(erssiarray.shape)  # filtered matrix
        for j in range(erssiarray.shape[1]):
            # do column by column
            for i in range(erssiarray.shape[0]):
                value = 0
                for counter in range(len(filter_coeff)):
                    if i-counter < 0:
                        # warm start with -999 values (i.e., no sensor detected)
                        value -= filter_coeff[counter] * 999
                    else:
                        value += filter_coeff[counter] * erssiarray[i-counter, j]
                filtmat[i, j] = value
        return filtmat

    @staticmethod
    def kalman_space_erssi_filter(erssiarray, A):
        # filter rssi data using Kalman filtering technique with Gaussian emission matrix and state transition matrix A
        # erssiarray = raw rssi data
        # A = state transition matrix
        # return a filtered version of the initial rssi array
        st = 30 # soft thresholding parameter

        # emission matrix - Gaussian
        def gaussian(dist, sigma):
            return (1.0/(sigma*np.sqrt(2*np.pi)))*np.exp(-(dist**2)/(2*sigma**2))

        sig = 0.3
        C = np.array([
            [gaussian(0, sig), gaussian(1, sig), gaussian(1, sig), gaussian(1, sig), gaussian(2, sig), gaussian(2, sig)],
            [gaussian(1, sig), gaussian(0, sig), gaussian(1, sig), gaussian(1, sig), gaussian(1, sig), gaussian(1, sig)],
            [gaussian(1, sig), gaussian(1, sig), gaussian(0, sig), gaussian(1, sig), gaussian(1, sig), gaussian(1, sig)],
            [gaussian(1, sig), gaussian(1, sig), gaussian(1, sig), gaussian(0, sig), gaussian(2, sig), gaussian(2, sig)],
            [gaussian(2, sig), gaussian(1, sig), gaussian(1, sig), gaussian(2, sig), gaussian(0, sig), gaussian(1, sig)],
            [gaussian(2, sig), gaussian(1, sig), gaussian(1, sig), gaussian(2, sig), gaussian(1, sig), gaussian(0, sig)],
        ])
        # normalize each row
        for i in range(C.shape[0]):
            rownorm = np.linalg.norm(C[i, :], 1)
            for j in range(C.shape[1]):
                C[i, j] /= rownorm

        # print C

        sizeyfull = erssiarray.shape
        sizey = sizeyfull[1]  # number of rooms
        sizex = sizey
        length = sizeyfull[0]  # number of data points
        S = 0.1*np.eye(sizex)  # state error covariance (x_est=rssi filtered)
        R = 0.1*np.eye(sizey)   # measurement error covariance (erssiarray=rssi measured)
        G = np.eye(sizex)  # kalman gain matrix

        # initialize state estimate and info matrix
        x_est = np.zeros([sizex, length])
        for i in range(sizey):
            x_est[i, 0] = erssiarray[0, i]  # initial rssi is first measured
        P = 0.1*np.eye(sizex)  # initial info matrix

        #filter
        #A = np.eye(6)
        #C = np.eye(6)
        for i in range(0, length-1):
            x_est[:, i+1] = A.dot(x_est[:, i])  # state update extrapolation
            P = A.dot(P.dot(A.T)) + S  # info matrix extrapolation
            G = (P.dot(C.T)).dot(np.linalg.inv((C.dot(P.dot(C.T))+R))) # kalman gain
            x_est[:, i+1] = x_est[:, i+1]+G.dot((erssiarray[i+1, :].T-C.dot(x_est[:, i+1])))  # state update
            P = (np.eye(sizex)-G.dot(C)).dot(P)  # error covariance update
            # apply soft thresholding
            # for j in range(len(x_est[:, i+1])):
            #     if (x_est[j, i+1]+999) > st:
            #         x_est[j, i+1] -= st
            #     elif (x_est[j, i+1]+999) < -st:
            #         x_est[j, i+1] += st
            #     else:
            #         x_est[j, i+1] = -999


            #print erssiarray[i, :].T
            #print x_est[:, i]
            #print P

        return x_est.T # filtered estimate and error covariance

    @staticmethod
    def kalman_time_erssi_filter(erssiarray, A):
        # filter rssi data using Kalman filtering technique with Gaussian emission matrix and state transition matrix A
        # erssiarray = raw rssi data
        # A = state transition matrix
        # return a filtered version of the initial rssi array

        filtlen = 6

        # emission matrix - Gaussian
        def gaussian(dist, sigma):
            return (1.0/(sigma*np.sqrt(2*np.pi)))*np.exp(-(dist**2)/(2*sigma**2))

        sig = 25
        C = np.array([
            [gaussian(0, sig), gaussian(1, sig), gaussian(1, sig), gaussian(1, sig), gaussian(2, sig), gaussian(2, sig)],
            [gaussian(1, sig), gaussian(0, sig), gaussian(1, sig), gaussian(1, sig), gaussian(1, sig), gaussian(1, sig)],
            [gaussian(1, sig), gaussian(1, sig), gaussian(0, sig), gaussian(1, sig), gaussian(1, sig), gaussian(1, sig)],
            [gaussian(1, sig), gaussian(1, sig), gaussian(1, sig), gaussian(0, sig), gaussian(2, sig), gaussian(2, sig)],
            [gaussian(2, sig), gaussian(1, sig), gaussian(1, sig), gaussian(2, sig), gaussian(0, sig), gaussian(1, sig)],
            [gaussian(2, sig), gaussian(1, sig), gaussian(1, sig), gaussian(2, sig), gaussian(1, sig), gaussian(0, sig)],
        ])
        # normalize each row
        for i in range(C.shape[0]):
            rownorm = np.linalg.norm(C[i, :], 1)
            for j in range(C.shape[1]):
                C[i, j] /= rownorm

        # print C


        S = 0.1*np.eye(filtlen)  # state error covariance (x_est=rssi filtered)
        R = 0.1*np.eye(filtlen)   # measurement error covariance (erssiarray=rssi measured)
        G = np.eye(filtlen)  # kalman gain matrix

        filtmat = np.empty(erssiarray.shape)  # filtered matrix
        for j in range(erssiarray.shape[1]):
            # do column by column
            # initialize state estimate and info matrix
            x_est = np.zeros([filtlen, 1])
            x_raw = np.zeros([filtlen, 1])
            P = 0.1*np.eye(filtlen)  # initial info matrix

            for i in range(erssiarray.shape[0]):
                for k in range(filtlen):
                    if i-k < 0:
                        x_raw[k] = -999
                    else:
                        x_raw[k] = erssiarray[i-k, j]
                x_est = A.dot(x_raw)  # state update extrapolation
                P = A.dot(P.dot(A.T)) + S  # info matrix extrapolation
                G = (P.dot(C.T)).dot(np.linalg.inv((C.dot(P.dot(C.T))+R))) # kalman gain
                x_est = x_est+G.dot((x_raw-C.dot(x_est)))  # state update
                P = (np.eye(filtlen)-G.dot(C)).dot(P)  # error covariance update
                filtmat[i, j] = x_est[0]
        return filtmat

    @staticmethod
    def adaptive_grad_erssi_filter(erssiarray):
        # learn coefficients with prior estimates for statistics
        # rdx = E[d*x] = d*E[x] = 999^2
        # Rx = E[x*x^H] = sigmax^2*I + mx^2 = 25^2*I + 999^2

        # constants
        filtlen = 6
        d = -999
        rdx = d**2*np.ones([filtlen, 1])
        Rx = 25**2*np.eye(filtlen) + d**2*np.ones([filtlen, filtlen])
        w = 0.1*np.ones([filtlen, 1])
        mu = 0.00000001


        filtmat = np.empty(erssiarray.shape)  # filtered matrix
        for j in range(erssiarray.shape[1]):
            # do column by column
            for i in range(erssiarray.shape[0]):
                w = (np.eye(filtlen) - mu*Rx)*w + mu*rdx
                value = 0
                for counter in range(len(w)):
                    if i-counter < 0:
                        # warm start with -999 values (i.e., no sensor detected)
                        value -= w[counter, 0] * 999
                    else:
                        value += w[counter, 0] * erssiarray[i-counter, j]
                filtmat[i, j] = value
        return filtmat

    @staticmethod
    def adaptive_momen_erssi_filter(erssiarray):
        # adding momentum to give Nesterov's optimal method
        # learn coefficients with prior estimates for statistics
        # rdx = E[d*x] = d*E[x] = 999^2
        # Rx = E[x*x^H] = sigmax^2*I + mx^2 = 25^2*I + 999^2

        # constants
        filtlen = 6
        d = -999
        b = 0.47
        rdx = d**2*np.ones([filtlen, 1])
        Rx = 25**2*np.eye(filtlen) + d**2*np.ones([filtlen, filtlen])
        w = np.zeros([filtlen, 1])
        wp = np.zeros([filtlen, 1])
        wn = np.zeros([filtlen, 1])
        mu = 0.00000001


        filtmat = np.empty(erssiarray.shape)  # filtered matrix
        for j in range(erssiarray.shape[1]):
            # do column by column
            for i in range(erssiarray.shape[0]):
                # wn = w + mu*(rdx - (1+2*b-2*b**2)*Rx.dot(w) + b*(1+b)*(Rxn+Rxp).dot(w)) + b*(w-wp)
                wn = w + mu*rdx - mu*(w - b*w + b*wp).T.dot(Rx) + b*(w-wp)
                wp = w
                w = wn
                value = 0
                for counter in range(len(w)):
                    if i-counter < 0:
                        # warm start with -999 values (i.e., no sensor detected)
                        value -= w[counter, 0] * 999
                    else:
                        value += w[counter, 0] * erssiarray[i-counter, j]
                filtmat[i, j] = value
        return filtmat

    @staticmethod
    def adaptive_newt_erssi_filter(erssiarray):
        # adding estimate of Hessian (P=Rx^-1) to improve convergence
        # learn coefficients with prior estimates for statistics
        # rdx = E[d*x] = d*E[x] = 999^2
        # Rx = E[x*x^H] = sigmax^2*I + mx^2 = 25^2*I + 999^2

        # constants
        filtlen = 6
        d = -999
        rdx = d**2*np.ones([filtlen, 1])
        Rx = 25**2*np.eye(filtlen) + d**2*np.ones([filtlen, filtlen])
        P = np.linalg.inv(Rx)
        w = P.dot(rdx)  # note filter coefficients are constant because using prior and Newton's method gives
                        # convergence in one step for quadratic functions


        filtmat = np.empty(erssiarray.shape)  # filtered matrix
        for j in range(erssiarray.shape[1]):
            # do column by column
            for i in range(erssiarray.shape[0]):
                value = 0
                for counter in range(len(w)):
                    if i-counter < 0:
                        # warm start with -999 values (i.e., no sensor detected)
                        value -= w[counter, 0] * 999
                    else:
                        value += w[counter, 0] * erssiarray[i-counter, j]
                filtmat[i, j] = value
        return filtmat

    @staticmethod
    def LMS_grad_erssi_filter(erssiarray):

        d=-999
        muinit = 0.0000000001
        w = np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1]) #initial filter coefficients

        filtmat = np.empty(erssiarray.shape)  # filtered matrix
        for j in range(erssiarray.shape[1]):
            # do column by column
            mucount = 0
            munext  = 2
            mu      = muinit
            for i in range(erssiarray.shape[0]):
                # update filter coefficients
                x = np.zeros(len(w))
                for k in range(len(w)):
                    if i-k < 0:
                        x[k] = -999
                    else:
                        x[k] = erssiarray[i-k, j]

                if x[0] != x[1]:
                    mu = muinit
                    mucount = 0
                    munext = 2
                else:
                    mucount += 1
                    if mucount == munext:
                        # approximate 1/k decrease in step size
                        mu = mu/2
                        munext = mucount*2

                e = d - w.T.dot(x)
                w = w + muinit*e*x

                # apply filter
                value = 0
                for counter in range(len(w)):
                    if i-counter < 0:
                        # warm start with -999 values (i.e., no sensor detected)
                        value -= w[counter] * 999
                    else:
                        value += w[counter] * erssiarray[i-counter, j]
                filtmat[i, j] = value
        return filtmat

    @staticmethod
    def LMS_momen_erssi_filter(erssiarray, restarts=True):
        d=-999
        muinit = 0.000000001
        b = 0.38
        filtlen = 6
        w = np.zeros(filtlen)  #initial filter coefficients
        w.fill(1.0/filtlen)
        wp = np.zeros(filtlen)
        wp.fill(1.0/filtlen)
        ep = maxint
        epochs = False


        filtmat = np.empty(erssiarray.shape)  # filtered matrix
        for j in range(erssiarray.shape[1]):
            # do column by column
            mucount = 0
            munext  = 2
            mu      = muinit

            for i in range(erssiarray.shape[0]):
                # update filter coefficients
                x = np.zeros(len(w))
                for k in range(len(w)):
                    if i-k < 0:
                        x[k] = -999
                    else:
                        x[k] = erssiarray[i-k, j]
                if epochs == True:
                    if x[0] != x[1]:
                        mu = muinit
                        mucount = 0
                        munext = 2
                    else:
                        mucount += 1
                        if mucount == munext:
                            # approximate 1/k decrease in step size
                            mu = mu/2
                            munext = mucount*2
                else:
                    mu = muinit

                e = (d-(w + b*(w-wp)).T.dot(x))
                wn = w + mu*e*(x.T) + b*(w-wp)
                if abs(e) > abs(ep) and restarts is True:
                    # restart momentum
                    wp = wn
                    w = wn
                else:
                    # perform regular update
                    wp = w
                    w = wn
                ep = e

                # apply filter
                value = 0
                for counter in range(len(w)):
                    if i-counter < 0:
                        # warm start with -999 values (i.e., no sensor detected)
                        value -= w[counter] * 999
                    else:
                        value += w[counter] * erssiarray[i-counter, j]
                filtmat[i, j] = value
        return filtmat

    @staticmethod
    def LMS_HB_erssi_filter(erssiarray):
        d=-999
        muinit = 0.000000001
        b = 0.38
        w = np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1]) #initial filter coefficients
        wp = np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1])
        epochs = False

        filtmat = np.empty(erssiarray.shape)  # filtered matrix
        for j in range(erssiarray.shape[1]):
            # do column by column
            mucount = 0
            munext  = 2
            mu      = muinit
            for i in range(erssiarray.shape[0]):
                # update filter coefficients
                x = np.zeros(len(w))
                for k in range(len(w)):
                    if i-k < 0:
                        x[k] = -999
                    else:
                        x[k] = erssiarray[i-k, j]
                if epochs == True:
                    if x[0] != x[1]:
                        mu = muinit
                        mucount = 0
                        munext = 2
                    else:
                        mucount += 1
                        if mucount == munext:
                            # approximate 1/k decrease in step size
                            mu = mu/2
                            munext = mucount*2
                else:
                    mu = muinit

                wn = w + mu*(d-w.T.dot(x))*(x.T) + b*(w-wp)
                wp = w
                w = wn

                # apply filter
                value = 0
                for counter in range(len(w)):
                    if i-counter < 0:
                        # warm start with -999 values (i.e., no sensor detected)
                        value -= w[counter] * 999
                    else:
                        value += w[counter] * erssiarray[i-counter, j]
                filtmat[i, j] = value
        return filtmat

    @staticmethod
    def LMS_newt_erssi_filter(erssiarray):

        d=-999
        w = np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1]) #initial filter coefficients
        Rx = 25**2*np.eye(len(w)) + d**2*np.ones([len(w), len(w)])
        P = np.linalg.inv(Rx)
        #P = 0.1*np.eye(len(w)) # initial inverse autocorrelation estimate

        filtmat = np.empty(erssiarray.shape)  # filtered matrix
        for j in range(erssiarray.shape[1]):
            # do column by column
            for i in range(erssiarray.shape[0]):
                # prepare data vectors
                x = np.zeros([len(w), 1]) # new data at front of sliding window
                xp= np.zeros([len(w), 1]) # old data at back of sliding window
                for k in range(len(w)):
                    if i-k < 0:
                        x[k, 0] = -999
                        xp[k, 0]= -999
                    elif i-k-len(w)-1 < 0:
                        x[k, 0] = erssiarray[i-k, j]
                        xp[k, 0]= -999
                    else:
                        x[k, 0] = erssiarray[i-k, j]
                        xp[k, 0]= erssiarray[i-k-len(w)-1, j]

                # matrix inversion lemma to include new data
                Pn = P - (P.dot(x.dot(x.T.dot(P)))) / (1+x.T.dot(P.dot(x)))

                # matrix inversion lemma to remove data from back of sliding window
                #P = Pn - (Pn.dot(xp.dot(xp.T.dot(Pn)))) / (1+xp.T.dot(Pn.dot(xp)))

                # attempt using Hayes, problem 9.4
                # P = (np.eye(len(w)) - x.dot(x.T)).dot(P) + np.eye(len(w))

                # calculate new filter coefficients
                w = d*Pn.dot(x)

                # apply filter
                value = 0
                for counter in range(len(w)):
                    if i-counter < 0:
                        # warm start with -999 values (i.e., no sensor detected)
                        value -= w[counter] * 999
                    else:
                        value += w[counter] * x[counter, 0]
                filtmat[i, j] = value
        #print filtmat
        #print erssiarray
        return filtmat

    @staticmethod
    def RLS_erssi_filter(erssiarray):
        # sliding window RLS

        d=-999
        w = np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1]) #initial filter coefficients
        P = 0.1*np.eye(len(w)) # initial inverse autocorrelation estimate

        filtmat = np.empty(erssiarray.shape)  # filtered matrix
        for j in range(erssiarray.shape[1]):
            # do column by column
            for i in range(erssiarray.shape[0]):
                # prepare data vectors
                x = np.zeros([len(w), 1]) # new data at front of sliding window
                xp= np.zeros([len(w), 1]) # old data at back of sliding window
                for k in range(len(w)):
                    if i-k < 0:
                        x[k, 0] = -999
                        xp[k, 0]= -999
                    elif i-k-len(w) < 0:
                        x[k, 0] = erssiarray[i-k, j]
                        xp[k, 0]= -999
                    else:
                        x[k, 0] = erssiarray[i-k, j]
                        xp[k, 0]= erssiarray[i-k-len(w), j]

                # introduce new data
                z = P.dot(x)
                g = z / (1+x.T.dot(z))
                a = d - w.T.dot(x)
                w = w + a*g
                P = P - g.dot(z.T)

                # remove stale data
                z = P.dot(xp)
                g = z / (1+xp.T.dot(z))
                a = d - w.T.dot(xp)
                w = w - a*g
                P = P + g.dot(z.T)

                # apply filter
                value = 0
                for counter in range(len(w)):
                    if i-counter < 0:
                        # warm start with -999 values (i.e., no sensor detected)
                        value -= w[counter, 0] * 999
                    else:
                        value += w[counter, 0] * x[counter, 0]
                filtmat[i, j] = value
        return filtmat


    @staticmethod
    def LMS_l1_grad_erssi_filter(erssiarray):

        d=-999
        muinit = 0.0000000001
        w = np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1]) #initial filter coefficients

        filtmat = np.empty(erssiarray.shape)  # filtered matrix
        for j in range(erssiarray.shape[1]):
            # do column by column
            mucount = 0
            munext  = 2
            mu      = muinit
            for i in range(erssiarray.shape[0]):
                # update filter coefficients
                x = np.zeros(len(w))
                for k in range(len(w)):
                    if i-k < 0:
                        x[k] = -999
                    else:
                        x[k] = erssiarray[i-k, j]

                if x[0] != x[1]:
                    mu = muinit
                    mucount = 0
                    munext = 2
                else:
                    mucount += 1
                    if mucount == munext:
                        # approximate 1/k decrease in step size
                        mu = mu/2
                        munext = mucount*2

                w = w + muinit*x

                # apply filter
                value = 0
                for counter in range(len(w)):
                    if i-counter < 0:
                        # warm start with -999 values (i.e., no sensor detected)
                        value -= w[counter] * 999
                    else:
                        value += w[counter] * erssiarray[i-counter, j]
                filtmat[i, j] = value
        return filtmat

    @staticmethod
    def LMS_l1_momen_erssi_filter(erssiarray):
        d=-999
        muinit = 0.000000001
        b = 0.38
        w = np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1]) #initial filter coefficients
        wp = np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1])
        epochs = False

        filtmat = np.empty(erssiarray.shape)  # filtered matrix
        for j in range(erssiarray.shape[1]):
            # do column by column
            mucount = 0
            munext  = 2
            mu      = muinit
            for i in range(erssiarray.shape[0]):
                # update filter coefficients
                x = np.zeros(len(w))
                for k in range(len(w)):
                    if i-k < 0:
                        x[k] = -999
                    else:
                        x[k] = erssiarray[i-k, j]
                if epochs == True:
                    if x[0] != x[1]:
                        mu = muinit
                        mucount = 0
                        munext = 2
                    else:
                        mucount += 1
                        if mucount == munext:
                            # approximate 1/k decrease in step size
                            mu = mu/2
                            munext = mucount*2
                else:
                    mu = muinit

                wn = w + mu*x + b*(w-wp)
                wp = w
                w = wn

                # apply filter
                value = 0
                for counter in range(len(w)):
                    if i-counter < 0:
                        # warm start with -999 values (i.e., no sensor detected)
                        value -= w[counter] * 999
                    else:
                        value += w[counter] * erssiarray[i-counter, j]
                filtmat[i, j] = value
        return filtmat

    # @staticmethod
    # def KLMS(erssiarray, groundtruth=None, restarts=True,
    #          kernel=lambda x, y, s: np.exp((-np.linalg.norm(x-y)**2)/(2*s**2))):
    #     """
    #     This method implements NKLMS-NC or normalized KLMS with the novelty criterion
    #     :param erssiarray: the rssi data array
    #     :param groundtruth: the ground truth array if available
    #     :param restarts: if true, resets momentum term periodically
    #     :param kernel: the kernal function to be used. Gaussian kernel used by default
    #     """
    #     d=-999
    #     muinit = 0.000000001
    #     b = 0.38
    #     filtlen = 6
    #     w = np.zeros(filtlen)  #initial filter coefficients
    #     w.fill(1.0/filtlen)
    #     wp = np.zeros(filtlen)
    #     wp.fill(1.0/filtlen)
    #     ep = maxint
    #     epochs = False
    #
    #     filtmat = np.empty(erssiarray.shape)  # filtered matrix
    #     for j in range(erssiarray.shape[1]):
    #         # do column by column
    #         mucount = 0
    #         munext  = 2
    #         mu      = muinit
    #
    #         for i in range(erssiarray.shape[0]):
    #             # update filter coefficients
    #             x = np.zeros(len(w))
    #             for k in range(len(w)):
    #                 if i-k < 0:
    #                     x[k] = -999
    #                 else:
    #                     x[k] = erssiarray[i-k, j]
    #             if epochs == True:
    #                 if x[0] != x[1]:
    #                     mu = muinit
    #                     mucount = 0
    #                     munext = 2
    #                 else:
    #                     mucount += 1
    #                     if mucount == munext:
    #                         # approximate 1/k decrease in step size
    #                         mu = mu/2
    #                         munext = mucount*2
    #             else:
    #                 mu = muinit
    #
    #             e = (d-(w + b*(w-wp)).T.dot(x))
    #             wn = w + mu*e*(x.T) + b*(w-wp)
    #             if abs(e) > abs(ep) and restarts is True:
    #                 # restart momentum
    #                 wp = wn
    #                 w = wn
    #             else:
    #                 # perform regular update
    #                 wp = w
    #                 w = wn
    #             ep = e
    #
    #             # apply filter
    #             value = 0
    #             for counter in range(len(w)):
    #                 if i-counter < 0:
    #                     # warm start with -999 values (i.e., no sensor detected)
    #                     value -= w[counter] * 999
    #                 else:
    #                     value += w[counter] * erssiarray[i-counter, j]
    #             filtmat[i, j] = value
    #     return filtmat
__author__ = 'gmn255'

# TrainingRoomEstimator accepts a house object
# The primary function is train_classifier. It outputs a trained sci-kit learn classifier
# based on the given estimote training set and ground trust data

import numpy as np
from sys import maxint, getsizeof
from sklearn import svm, tree, linear_model, neighbors
from sklearn.lda import LDA
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, GradientBoostingClassifier, AdaBoostClassifier, BaggingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.grid_search import GridSearchCV
from NaiveRSSIClassifier import NaiveRSSIClassifier
import operator

from room_estimator import RoomEstimator
from house import House

import lasagne
import theano.tensor as T
import theano
from lasagne.nonlinearities import softmax
from lasagne.layers import InputLayer, DenseLayer, get_output, RecurrentLayer, ReshapeLayer
from lasagne.regularization import regularize_layer_params_weighted, regularize_layer_params, l1, l2

class TrainingRoomEstimator(RoomEstimator):

    def __init__(self, beaconcoordict):
        # constructor
        super(TrainingRoomEstimator, self).__init__()
        # beaconcoordict = dictionary mapping room names to (x,y,z) tuples with location
        self.beaconcoordict = beaconcoordict
        # summarymap = map for description:value containing summary results from training
        self.summarymap = {}
        # myhouse = house object for WPL functionals
        self.myhouse = None

    def get_highest_rssi(self, erssiarray):
        # create an array where the room is estimated from the highest rssi value
        # erssiarray = estimote rssi array (d data points by n beacons)
        # output = n x 1 array of expected rooms from each data point
        eroom = []
        for erssi in erssiarray:
            maxerssi = -1000
            room = 0
            for i in range(0, len(erssi)):
                if erssi[i] > maxerssi:
                    maxerssi = erssi[i]
                    room = i
            eroom.append(self.roomlist[room])
        return np.array(eroom)

    def read_ground_match_single_point_window(self, earray, gtlist):
        """
        read the ground truth list where each entry is (roomname, starttime, endtime)
        create list of ground truth values at matching times for the estimote rssi array
        using self.timearray
        :param erray: estimote array at all initially collected values
        :param gtlist: ground truth as list of (roomname, starttime, endtime) values
        :return: ground truth at times matching estimote rssi array and estimote array of actual values used
        """

        gformat = []
        for row in gtlist:
            # [room, start, end] -> [[start, room], [end, room]]
            gformat.append([row[1], row[0]])
            gformat.append([row[2], row[0]])

        rawarray = np.array(gformat)

        gtimer = []
        for timestamp in rawarray[:, 0]:
            graw = self._get_time(timestamp)
            gtimer.append(graw)
        gtime = np.array(gtimer)

        # get ground truth at matching times
        groomarray = []
        gcounter = 0  # marks progression in ground truth array
        i = 0
        while i < len(self.timearray):
            # define bounds within the ground truth is known
            gtimelower = gtime[gcounter]
            if self.timearray[i] > (int(rawarray[-1, 0]) - int(rawarray[0, 0])):
                earray[i-1:-1, :].fill(-1)
                break
            elif gcounter < len(gtime):
                gtimeupper = gtime[gcounter+1]
            else:
                 gtimeupper = maxint
            # append NULL if before the first ground truth has been acquired
            if gcounter == 0 and self.timearray[i] < gtimelower:
                groomarray.append('NULL')
            elif self.timearray[i] >= gtimeupper:
                # increase bounding box once self.timearray has progressed past it
                # cannot simply increment because estimote may miss a whole room
                # if the watch wearer just walks through
                for j in range(gcounter, len(gtime)):
                    if gtime[j] > self.timearray[i]:
                        gcounter = j-1
                        break
                # check if still within window of matching ground truth room names
                if self._get_room(rawarray[gcounter, 1]) != self._get_room(rawarray[gcounter+1, 1]):
                    gtimeupper = gtime[gcounter+1]
                    while self.timearray[i] < gtimeupper:
                        # set to -1 to identify value should be removed (cannot removed yet because of indexing)
                        self.timearray[i] = -1
                        earray[i, :].fill(-1)
                        i += 1
                    gcounter += 1

                groomarray.append(self._get_room(rawarray[gcounter, 1]))
                i += 1
            else:
                groomarray.append(self._get_room(rawarray[gcounter, 1]))
                i += 1

        # remove unused values from self.timearray
        timelist = self.timearray.tolist()
        timelistf = [time for time in timelist if time != -1]
        self.timearray = np.array(timelistf)

        # remove unused values from estimote array
        elist = earray.tolist()
        erowlist = [row for row in elist if row[0] != -1]
        errayfinal = np.array(erowlist)

        # remove unused values from ground trust array
        estimoteRSSIarray, groundmatcharray = self._remove_NULL(errayfinal, groomarray)

        return estimoteRSSIarray, groundmatcharray

    def read_ground_match_windowed(self, earray, gtlist):
        # read the ground truth 2D list and create array at time points
        # matching the estimote measurement points. assumes estimote values fall within a window of ground
        # truth values with the same room name
        # Input:
        #   earray = dxr numpy array of estimote rssi values where r is number of rooms
        #   gtlist = dx2 list of strings with timestamp in first column and room in second
        # Output:
        #   groundmatcharray = numpy array of ground truth rooms at times matching the estimote data collection times
        #            in the training set -- may contain 'NULL' values at the start if the first estimote value
        #            appears before the first ground trust value
        #   estimoteRSSIarray = numpy array of estimote rssi values

        rawarray = np.array(gtlist)

        rawarray = np.vstack([rawarray, [rawarray[-1, 0], maxint]])
        gtimer = []
        for timestamp in rawarray[:, 0]:
            graw = self._get_time(timestamp)
            gtimer.append(graw)
        gtime = np.array(gtimer)

        # get ground truth at matching times
        groomarray = []
        gcounter = 0  # marks progression in ground truth array
        i = 0
        while i < len(self.timearray):
            # define bounds within the ground truth is known
            gtimelower = gtime[gcounter]
            if gcounter < len(gtime):
                gtimeupper = gtime[gcounter+1]
            else:
                 gtimeupper = maxint
            # append NULL if before the first ground truth has been acquired
            if gcounter == 0 and self.timearray[i] < gtimelower:
                groomarray.append('NULL')
            elif self.timearray[i] >= gtimeupper:
                # increase bounding box once self.timearray has progressed past it
                # cannot simply increment because estimote may miss a whole room
                # if the watch wearer just walks through
                for j in range(gcounter, len(gtime)):
                    if gtime[j] > self.timearray[i]:
                        gcounter = j-1
                        break
                # check if still within window of matching ground truth room names
                if self._get_room(rawarray[gcounter, 1]) != self._get_room(rawarray[gcounter+1, 1]):
                    gtimeupper = gtime[gcounter+1]
                    while self.timearray[i] < gtimeupper:
                        # set to -1 to identify value should be removed (cannot removed yet because of indexing)
                        self.timearray[i] = -1
                        earray[i, :].fill(-1)
                        i += 1
                    gcounter += 1

                groomarray.append(self._get_room(rawarray[gcounter, 1]))
                i += 1
            else:
                groomarray.append(self._get_room(rawarray[gcounter, 1]))
                i += 1

        # remove unused values from self.timearray
        timelist = self.timearray.tolist()
        timelistf = [time for time in timelist if time != -1]
        self.timearray = np.array(timelistf)

        # remove unused values from estimote array
        elist = earray.tolist()
        erowlist = [row for row in elist if row[0] != -1]
        errayfinal = np.array(erowlist)

        # remove unused values from ground trust array
        estimoteRSSIarray, groundmatcharray = self._remove_NULL(errayfinal, groomarray)

        return estimoteRSSIarray, groundmatcharray

    def read_ground_match_general(self, gtlist):
        # read the ground truth 2D list and create array at time points
        # matching the estimote measurement points
        # if ground truth is not yet known at an estimote measurement point,
        # the room value is set 'NULL' and removed by _remove_NULL()
        # Input:
        #   gtlist = dx2 list of strings with timestamp in first column and room in second
        # Output:
        #   groomarray = numpy array of ground truth rooms at times matching the estimote data collection times
        #                in the training set -- may contain 'NULL' values at the start if the first estimote value
        #                appears before the first ground trust value

        rawarray = np.array(gtlist)

        rawarray = np.vstack([rawarray, [rawarray[-1, 0], maxint]])
        gtimer = []
        for timestamp in rawarray[:, 0]:
            graw = self._get_time(timestamp)
            gtimer.append(graw)
        gtime = np.array(gtimer)

        # get ground truth at matching times
        groomarray = []
        gcounter = 0  # marks progression in ground truth array
        for i in range(len(self.timearray)):
            # define bounds within the ground truth is known
            gtimelower = gtime[gcounter]
            if gcounter < len(gtime):
                gtimeupper = gtime[gcounter+1]
            else:
                 gtimeupper = maxint
             # append NULL if before the first ground truth has been acquired
            if gcounter == 0 and self.timearray[i] < gtimelower:
                groomarray.append('NULL')
            elif self.timearray[i] >= gtimeupper:
                # increase bounding box once self.timearray has progressed past it
                # cannot simply increment because estimote may miss a whole room
                # if the watch wearer just walks through
                for j in range(gcounter, len(gtime)):
                    if gtime[j] > self.timearray[i]:
                        gcounter = j-1
                        break
                #groomarray[i] = self._get_room(rawarray[gcounter, 1])
                groomarray.append(self._get_room(rawarray[gcounter, 1]))
            else:
                #groomarray[i] = self._get_room(rawarray[gcounter, 1])
                groomarray.append(self._get_room(rawarray[gcounter, 1]))
                #print (groomarray[i], self.timearray[i])

        return groomarray

    def read_training_pair(self, rssilist, gtlist):
        # this method reads an rssi 2D list and the matching ground truth 2D list
        # it returns 3 numpy arrays
        #   self.timearray - array of time points when estimote measurements taken
        #   estimoteRSSIarray - matrix of estimote RSSI values (measurements x rooms)
        #   groundmatcharray - ground truth array of equal length with ground truth
        #                      value at each point in timearray

        estimoteRSSIarray = self.read_rssi_list(rssilist)
        estimoteRSSIarray, groundmatcharray = self.read_ground_match_single_point_window(estimoteRSSIarray, gtlist)

        # if data is not contained within ground trust windows, use the following two lines
        # estimoteRSSIarray = self.read_ground_match_general(gtlist)
        # estimoteRSSIarray, groundmatcharray = self._remove_NULL(estimoteRSSIarray, groundmatcharray)

        # quick sanity checking
        if len(self.timearray) == 0:
            raise ValueError('{timearray} cannot be size zero'.format(
                timearray=repr(self.timearray)))
        elif len(self.timearray) != len(groundmatcharray) or len(self.timearray) != len(estimoteRSSIarray):
            raise ValueError('timearray: {tlen} or estimoteRSSIarray: {elen} '
                'or groundmatcharray: {glen} is not the right size'.format(
                tlen=repr(len(self.timearray)), elen=len(estimoteRSSIarray),
                glen=len(groundmatcharray)))
        return estimoteRSSIarray, groundmatcharray

    def _remove_NULL(self, erssiarray, gmatcharray):
        """
        this method removes NULL values that may be at the start of the gmatcharray and
        shifts the erssiarray and self.timearray appropriately
        :param erssiarray: the numpy array of estimote rssi data
        :param gmatcharray: the ground truth list at matching time points that may contain NULL values
        :return: processed rssi, ground trust, and time arrays
        """
        idx = 0
        for room in gmatcharray:
            if room != 'NULL':
                idx = gmatcharray.index(room)
                break

        toffset = self.timearray[idx]

        rfinal = np.zeros([erssiarray.shape[0]-idx, erssiarray.shape[1]])
        gfinal = []
        tfinal = []
        for i in range(idx, len(gmatcharray)):
            rfinal[i-idx, :] = erssiarray[i, :]
            gfinal.append(gmatcharray[i])
            tfinal.append(self.timearray[i] - toffset)

        self.timearray = np.array(tfinal)
        return rfinal, gfinal


    def train_classifier(self, rssilist, gtlist):
        # this is the main function to be used from this class
        # it trains a classifier based on the raw rssi and ground trust data
        # Inputs:
        #   rssilist - 2D list of rssi data in the raw format as rows of strings
        #   gtlist   - 2D list of ground trust data in the raw format as rows of strings
        # Outputs:
        #   trainedclassifier - sci-kit learn classifier object trained on data set
        #   self.summarymap   - map of description:value pairs that summarize training results

        # read in training data
        rssiarray, groundmatcharray = self.read_training_pair(rssilist, gtlist)

        # create house object
        self.myhouse = House(self.beaconcoordict, self.roomlist)

        # create numeric mapping (roomname: beacon coordinates) for regression
        # groundmatchnumeric = np.zeros([len(groundmatcharray), 3])
        # for i in range(len(groundmatcharray)):
        #     groundmatchnumeric[i, :] = self.beaconcoordict[groundmatcharray[i]]

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

        # separate training and test sets
        SETBREAK1 = len(self.timearray)/3
        SETBREAK2 = 2*len(self.timearray)/3

        t0 = self.timearray[:SETBREAK1]
        e0 = efilt[:SETBREAK1, :]
        g0 = groundmatcharray[:SETBREAK1]
        #g0n= groundmatchnumeric[:SETBREAK1, :]

        t1 = self.timearray[SETBREAK1:SETBREAK2]
        e1 = efilt[SETBREAK1:SETBREAK2, :]
        g1 = groundmatcharray[SETBREAK1:SETBREAK2]
        #g1n= groundmatchnumeric[SETBREAK1:SETBREAK2, :]

        t2 = self.timearray[SETBREAK2:]
        e2 = efilt[SETBREAK2:, :]
        g2 = groundmatcharray[SETBREAK2:]
        #g2n= groundmatchnumeric[SETBREAK2:, :]

        tset = [t0, t1, t2]
        eset = [e0, e1, e2]
        gset = [g0, g1, g2]
        #gsetn= [g0n, g1n, g2n]

        # create error dictionary with mapping {errorname: [(error value 1, trained classifier 1), ...]}
        errordict = {'logistic regression': [], 'SVMl': [], 'SVMr': [], 'LDA': [], 'decision tree': [],
                     'random forest': [], 'extra trees': [], 'ada boosting': [], 'gradient boosting': [],
                     'filtered RSSI error': [], 'KNN': [], 'KNNb': []}

        # iterate over each fold of cross validation
        for idx in range(len(tset)):

            print "Starting iteration " + str(idx+1) + " of 3"

            ttrain = np.hstack((tset[idx], tset[(idx+1) % (len(tset))]))
            ttest  = tset[(idx+2) % (len(tset))]
            etrain = np.vstack((eset[idx], eset[(idx+1) % (len(eset))]))
            etest  = eset[(idx+2) % (len(eset))]
            gtrain = np.hstack((gset[idx], gset[(idx+1) % (len(gset))]))
            gtest  = gset[(idx+2) % (len(gset))]
            #gtrainn= np.vstack((gsetn[idx], gsetn[(idx+1) % (len(gsetn))]))
            #gtestn = gsetn[(idx+2) % (len(gsetn))]

            # find WPL functionals
            ecoortrain = self.myhouse.get_coor_from_rssi(etrain)
            ecoortest = self.myhouse.get_coor_from_rssi(etest)

            # create total data vector + functionals
            etotaltrain = np.hstack([etrain, ecoortrain])
            etotaltest = np.hstack([etest,  ecoortest])

            # # standardize features by removing mean and scaling to unit variance
            # etotaltrain = StandardScaler().fit_transform(etotaltrain)
            # etotaltest = StandardScaler().fit_transform(etotaltest)

            # grab highest rssi as indicator of current room for baseline comparison
            efcompare = self.get_highest_rssi(etest)

            # logistic regression
            logclf = linear_model.LogisticRegression().fit(etotaltrain, gtrain)
            logepredict = logclf.predict(etotaltest)

            # SVM with hyperparameter optimization
            #C_range = np.logspace(-2, 10, 13)
            #gamma_range = np.logspace(-9, 3, 13)
            #param_grid = dict(gamma=gamma_range, C=C_range)
            #grid = GridSearchCV(svm.SVC(kernel='rbf'), param_grid=param_grid)
            #svmrclf = grid.fit(etotaltrain, gtrain)
            svmrclf = svm.SVC(kernel='rbf', C=100, gamma=10**-6).fit(etotaltrain, gtrain)
            svmrepredict = svmrclf.predict(etotaltest)

            #print grid.best_params_

            # SVM with linear kernel
            # svmlclf = svm.SVC(kernel='linear').fit(etotaltrain, gtrain)
            # svmlepredict = svmlclf.predict(etotaltest)

            # LDA
            ldaclf = LDA(solver='svd').fit(etotaltrain, gtrain)
            ldaepredict = ldaclf.predict(etotaltest)

            # decision tree - seems to work very well; extensions below
            dtclf = tree.DecisionTreeClassifier().fit(etotaltrain, gtrain)
            dtepredict = dtclf.predict(etotaltest)

            # random forest (ensemble of decision trees)
            rfclf = RandomForestClassifier(n_estimators=1000, criterion='entropy', bootstrap=False, n_jobs=-1).fit(etotaltrain, gtrain)
            rfepredict = rfclf.predict(etotaltest)

            # extra trees (ensemble of decision trees)
            etclf = ExtraTreesClassifier(n_estimators=1000, n_jobs=-1).fit(etotaltrain, gtrain)
            etepredict = etclf.predict(etotaltest)

            # AdaBoost (ensemble of decision trees)
            abclf = AdaBoostClassifier(n_estimators=100, learning_rate=0.075).fit(etotaltrain, gtrain)
            abepredict = abclf.predict(etotaltest)

            # gradient boost (ensemble of decision trees)
            # n_estf=np.logspace(0,3,6)
            # n_esti=[int(a) for a in n_estf]
            # hyperparam = dict(n_estimators=n_esti, learning_rate=np.logspace(-3,0,6))
            # hypergrid = GridSearchCV(GradientBoostingClassifier(), hyperparam)
            # gbclf = hypergrid.fit(etotaltrain, gtrain)
            gbclf = GradientBoostingClassifier(n_estimators=100, learning_rate=0.075).fit(etotaltrain, gtrain)
            gbepredict = gbclf.predict(etotaltest)
            #print hypergrid.best_params_

            # LASSO - READ: tested LASSO and removed because no gain and requires second step in testing to pin to beacon
            # lsclf = linear_model.Lasso(alpha=10).fit(etotaltrain, gtrainn)
            # lsenpredict = lsclf.predict(etotaltest)
            # # works with numeric values -- pin result to closest beacon
            # lsenclf = neighbors.KNeighborsClassifier(n_neighbors=1).fit(self.beaconcoordict.values(), self.beaconcoordict.keys())
            # lsepredict = lsenclf.predict(lsenpredict)

            # k-nearest neighbors
            knnclf = neighbors.KNeighborsClassifier(n_neighbors=10).fit(etotaltrain, gtrain)
            knnepredict = knnclf.predict(etotaltest)

            # k-nearest neighbors
            knnbclf = BaggingClassifier(neighbors.KNeighborsClassifier(n_neighbors=10), n_estimators=100, n_jobs=-1).fit(etotaltrain, gtrain)
            knnbepredict = knnbclf.predict(etotaltest)

            # determine error of all classifiers
            logecount = 0
            srcount = 0
            slcount = 0
            ldacount = 0
            dtcount = 0
            rfcount = 0
            etcount = 0
            abcount = 0
            gbcount = 0
            efcount = 0
            knncount = 0
            knnbcount = 0
            for i in range(len(svmrepredict)):
                #print (gtest[i], ecompare[i], svm1epredict[i], svm2epredict[i], ldaepredict[i], dtepredict[i])
                #print (gtest[i], ecompare[i], svm1epredict[i])
                if efcompare[i] != gtest[i]:
                    efcount = efcount + 1
                if logepredict[i] != gtest[i]:
                    logecount = logecount + 1
                if svmrepredict[i] != gtest[i]:
                    srcount = srcount + 1
                #if svmlepredict[i] != gtest[i]:
                    #slcount = slcount + 1
                if ldaepredict[i] != gtest[i]:
                    ldacount = ldacount + 1
                if dtepredict[i] != gtest[i]:
                    dtcount = dtcount + 1
                if rfepredict[i] != gtest[i]:
                    rfcount = rfcount + 1
                if etepredict[i] != gtest[i]:
                    etcount = etcount + 1
                if abepredict[i] != gtest[i]:
                    abcount = abcount + 1
                if gbepredict[i] != gtest[i]:
                    gbcount = gbcount + 1
                if knnepredict[i] != gtest[i]:
                    knncount = knncount + 1
                if knnbepredict[i] != gtest[i]:
                    knnbcount = knnbcount + 1

            errordict['logistic regression'].append(float(logecount) / len(gtest))
            errordict['SVMr'].append(float(srcount) / len(gtest))
            #errordict['SVMl'].append(float(slcount) / len(gtest))
            errordict['LDA'].append(float(ldacount) / len(gtest))
            errordict['decision tree'].append(float(dtcount) / len(gtest))
            errordict['random forest'].append(float(rfcount) / len(gtest))
            errordict['extra trees'].append(float(etcount) / len(gtest))
            errordict['ada boosting'].append(float(abcount) / len(gtest))
            errordict['gradient boosting'].append(float(gbcount) / len(gtest))
            errordict['KNN'].append(float(knncount) / len(gtest))
            errordict['KNNb'].append(float(knnbcount) / len(gtest))
            errordict['filtered RSSI error'].append(float(efcount) / len(gtest))

        # average over cross validation values
        ferrordict = {}
        for key in errordict.keys():
            ferrordict[key] = np.mean(errordict[key])


        # determine minimal error classifier and store summary data
        sorted_error = sorted(ferrordict.items(), key=operator.itemgetter(1))
        # sorted_error is tuple sorted low to high by error rate so that the first element is the one with minimum error

        # create summary
        self.summarymap['size of training set'] = len(ttrain)
        self.summarymap['size of test set'] = len(ttest)
        self.summarymap['classifier used'] = sorted_error[0][0]
        self.summarymap['classifier error'] = sorted_error[0][1]
        self.summarymap['filtered RSSI error'] = ferrordict['filtered RSSI error']
        self.summarymap['error dictionary'] = ferrordict

        # retrain on all of the data (i.e., include test set)
        ttrain = self.timearray
        etrain = efilt
        gtrain = groundmatcharray

        # find WPL functionals
        self.myhouse = House(self.beaconcoordict, self.roomlist)
        ecoortrain = self.myhouse.get_coor_from_rssi(etrain)

        # create total data vector + functionals
        etotaltrain = np.hstack([etrain, ecoortrain])

        print "Training final classifier"

        trainedclassifier = {
            'logistic regression': linear_model.LogisticRegression().fit(etotaltrain, gtrain),
            'SVMr': svm.SVC(kernel='rbf').fit(etotaltrain, gtrain),
            #'SVMl': svm.SVC(kernel='linear').fit(etotaltrain, gtrain),
            'LDA': LDA(solver='svd').fit(etotaltrain, gtrain),
            'decision tree': tree.DecisionTreeClassifier().fit(etotaltrain, gtrain),
            'random forest': RandomForestClassifier(n_estimators=100, criterion='entropy', bootstrap=False, n_jobs=-1).fit(etotaltrain, gtrain),
            'extra trees': ExtraTreesClassifier(n_estimators=100, n_jobs=-1).fit(etotaltrain, gtrain),
            'ada boosting': AdaBoostClassifier(n_estimators=100, learning_rate=0.075).fit(etotaltrain, gtrain),
            'gradient boosting': GradientBoostingClassifier(n_estimators=100, learning_rate=0.075).fit(etotaltrain, gtrain),
            'KNN': neighbors.KNeighborsClassifier(n_neighbors=10).fit(etotaltrain, gtrain),
            'KNNb': BaggingClassifier(neighbors.KNeighborsClassifier(n_neighbors=10), n_estimators=100, n_jobs=-1).fit(etotaltrain, gtrain),
            'filtered RSSI error': NaiveRSSIClassifier(roomlist=self.roomlist).fit(etotaltrain, gtrain)
        }[self.summarymap['classifier used']]

        self.summarymap['classifier size'] = getsizeof(trainedclassifier)

        #
        # with open('groundmatcharray.txt', 'wb') as file:
        #     for room in groundmatcharray:
        #         file.write('%s\n' % room)
        #
        # np.savetxt('rssiarray.txt', rssiarray, fmt='%.d', delimiter=',')

        # trainedclassifier = linear_model.LogisticRegression().fit(etotaltrain, gtrain)

        print "classifier used", self.summarymap['classifier used']
        print "classifier error", self.summarymap['classifier error']

        return trainedclassifier, self.summarymap

    def train_classifier2(self, rssilist, gtlist):
        # this is the main function to be used from this class
        # it trains a classifier based on the raw rssi and ground trust data
        # Inputs:
        #   rssilist - 2D list of rssi data in the raw format as rows of strings
        #   gtlist   - 2D list of ground trust data in the raw format as rows of strings
        # Outputs:
        #   trainedclassifier - sci-kit learn classifier object trained on data set
        #   self.summarymap   - map of description:value pairs that summarize training results

        # read in training data
        rssiarray, groundmatcharray = self.read_training_pair(rssilist, gtlist)

        # convert to numpy array
        groundmatcharray = np.array(groundmatcharray)

        # ignore beacon coordinate locations for now and use raw data only
        #self.myhouse = House(self.beaconcoordict, self.roomlist)

        SEQLENGTH, NUMROOMS, BATCHSIZE = 6, 7, 128
        LEARNING_RATE, GRAD_CLIP = 0.01, 100
        def gen_sequences(data, labels, p=0, seqlength=SEQLENGTH, numrooms=NUMROOMS, batchsize=BATCHSIZE):
            """
            Create semi-redundant sequences from data

            :param data:
            :param labels:
            :return:
            """
            assert len(rssiarray) == len(groundmatcharray)
            x = np.zeros((batchsize, seqlength, numrooms))
            y = np.zeros(batchsize)

            # TODO: create mapping from rooms to indexes instead of passing string names
            # TODO: finish loop below
            for n in range(batchsize):
                ptr = n
                for i in range(seqlength):
                    x[n, i, char_to_ix[data[p+ptr+i]]] = 1.
                if(return_target):
                    y[n] = char_to_ix[data[p+ptr+seqlength]]
            return x, np.array(y, dtype='int32')

        def build_network():
            """
            define network architecture
            :return:
            """
            print "Building network ..."
            num_inputs, num_units, num_classes = 7, 12, 7
            # By setting the first two dimensions as None, we are allowing them to vary
            # They correspond to batch size and sequence length, so we will be able to
            # feed in batches of varying size with sequences of varying length.
            l_inp = InputLayer((None, None, num_inputs))
            # We can retrieve symbolic references to the input variable's shape, which
            # we will later use in reshape layers.
            batchsize, seqlen, _ = l_inp.input_var.shape
            l_rnn = RecurrentLayer(l_inp, num_units=num_units)
            # In order to connect a recurrent layer to a dense layer, we need to
            # flatten the first two dimensions (our "sample dimensions"); this will
            # cause each time step of each sequence to be processed independently
            l_shp = ReshapeLayer(l_rnn, (-1, num_units))
            l_dense = DenseLayer(l_shp, num_units=num_classes)
            # To reshape back to our original shape, we can use the symbolic shape
            # variables we retrieved above.
            l_out = ReshapeLayer(l_dense, (batchsize, seqlen, num_classes))

        # iterate over training data


        return l_out




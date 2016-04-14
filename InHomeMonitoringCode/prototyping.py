__author__ = 'gmn255'

# This class has been deprecated. It is kept here only for reference

from csv_room_reader import CSVRoomReader
from house import House

from sklearn import svm, tree, neighbors, linear_model
from sklearn.lda import LDA
from sklearn.multiclass import OneVsRestClassifier
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, GradientBoostingClassifier, AdaBoostClassifier
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import glob
import os
from warnings import simplefilter, catch_warnings


def get_highest_rssi(erssiarray):
    # create an array where the room is estimated from the highest rssi value
    # erssiarray = estimote rssi array (d data points by n beacons)
    # output = n x 1 array of expected rooms from each data point
    eroom = []
    for erssi in erssiarray:
        maxerssi = -1000
        room = 0
        for i in range(0, len(erssi)):
            if erssi[i] == 0:
                continue
            elif erssi[i] > maxerssi:
                maxerssi = erssi[i]
                room = i+1
        eroom.append(room)
    return np.array(eroom)

def moving_average_erssi_filter(erssiarray, numsamples):
    # take an estimote RSSI matrix of mxn data points where m refers to time and n refers to room
    # numsamples specifies the number of points to include in the moving average
    # return a filtered version of the raw data array
    filtmat = np.empty(erssiarray.shape)  # filtered matrix
    sumarray = np.zeros(erssiarray.shape[1])  # running running sum for each room
    for i in range(erssiarray.shape[0]):
        for j in range(erssiarray.shape[1]):
            if i < numsamples:
                if erssiarray[i, j] == 0:
                    addval = -999
                else:
                    addval = erssiarray[i, j]
                sumarray[j] = sumarray[j] + addval
                filtmat[i, j] = sumarray[j]/(i+1.0)  # until hit running sum count, just average over what has been seen
            else:
                # average over most recent values
                if erssiarray[i, j] == 0:
                    addval = -999
                else:
                    addval = erssiarray[i, j]
                if erssiarray[i-numsamples, j] == 0:
                    subval = -999
                else:
                    subval = erssiarray[i-numsamples, j]
                sumarray[j] = sumarray[j] - subval + addval
                filtmat[i, j] = sumarray[j]/numsamples
    return filtmat

def kalman(erssiarray):
    # state transition matrix - just trying out normalized diffusion model here (power law = fat tail),
    # function should be generalized
    # in the future this matrix will be weighted by the prior before normalizing - learned by Baum Welch alg
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

    # print A

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
        rownorm = np.linalg.norm(C[i, :],1)
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
        #print erssiarray[i, :].T
        #print x_est[:, i]
        #print P

    return x_est.T, P  # filtered estimate and error covariance


# control script for testing room estimation mechanisms
roomdict = {'bedroom1': 1, 'bathroom': 2, 'living room': 3, 'kitchen': 4, 'bedroom2': 5, 'bedroom3': 6}
reader = CSVRoomReader(roomdict)

# concatenate together however many csv files make up the data set - based on server upload mechasnism,
# the dataset can be arbitrarily sliced

if os.path.isfile("./CSVs/estimoteT.csv"):
    os.remove("./CSVs/estimoteT.csv")
efiles = glob.glob("./CSVs/estimote*.csv")
elist = []
for file in efiles:
    df = pd.read_csv(file, skiprows=0)
    elist.append(df)
frame = pd.concat(elist)
efinal = frame.to_csv("./CSVs/estimoteT.csv", columns=['patient', 'rssilist', 'timestamp'])

# create most recent file totaling estimote and ground truth CSVs
if os.path.isfile("./CSVs/ground_trustT.csv"):
    os.remove("./CSVs/ground_trustT.csv")
gfiles = glob.glob("./CSVs/ground_trust*.csv")
glist = []
for file in gfiles:
    df = pd.read_csv(file, skiprows=0)
    glist.append(df)
frame = pd.concat(glist)
gfinal = frame.to_csv("./CSVs/ground_trustT.csv", columns=['patient', 'room', 'timestamp'])

# read estimote / ground truth pair into numpy arrays
(t, e, g) = reader.read_csv_pair("CSVs/estimoteT.csv", "CSVs/ground_trustT.csv")

## filter
# LPF for comparison
e_filt_lpf = moving_average_erssi_filter(e, 5)

# Kalman (linear)
e_filt_kalman, kalman_error_cov = kalman(e)
#print e_filt_kalman

# final filter chosen
e_filt = e_filt_lpf

# for i in range(len(e_filt_lpf)):
#     print (e[i,1], e_filt_lpf[i,1], g[i])

# map RSSI values to approximate location in house
beaconcoors = {'bedroom 1': (18, 6, 10), 'bathroom': (20, 18, 10), 'living room': (6, 25, 10),
                 'kitchen': (5, 10, 8), 'bedroom 2': (22, 27, 3), 'bedroom 3': (6, 45, 10)}
myhouse = House(beaconcoors, roomdict)


# separate into training and test sets
# first 1000 elements define training set
TRAIN_LIMT = 2*len(t)/3

ttrainr = t[:TRAIN_LIMT]
etrainr = e_filt[:TRAIN_LIMT]
gtrainr = g[:TRAIN_LIMT]
# clean training set
(ttrain, etrain, gtrain) = CSVRoomReader.clean_teg(ttrainr, etrainr, gtrainr)
# find WPL functionals
ecoortrain = myhouse.get_coor_from_rssi(etrain)

ttestr = t[TRAIN_LIMT:] - t[TRAIN_LIMT]
etestr = e_filt[TRAIN_LIMT:]
gtestr = g[TRAIN_LIMT:]
# clean test set
(ttest, etest, gtest) = CSVRoomReader.clean_teg(ttestr, etestr, gtestr)
reducedttest = []
reducedetest = []
reducedgtest = []

print "full test set: " + str(len(ttest))
for i in range(len(ttest)):
    if i%10 == 0:
        reducedttest.append(ttest[i])
        reducedetest.append(etest[i, :])
        reducedgtest.append(gtest[i])

ttest = np.array(reducedttest)
etest = np.array(reducedetest)
gtest = np.array(reducedgtest)
print "reduced test set: " + str(len(ttest))


# find WPL functionals
ecoortest = myhouse.get_coor_from_rssi(etest)

# grab highest rssi as indicator of current room for baseline comparison
efcompare = get_highest_rssi(etest)  # filtered
(tr, er, gr) = CSVRoomReader.clean_teg(t[TRAIN_LIMT:], e[TRAIN_LIMT:], g[TRAIN_LIMT:])
ercompare = get_highest_rssi(er)  # raw

# create total feature vector
etotaltrain = np.hstack([etrain, ecoortrain])
etotaltest = np.hstack([etest,  ecoortest])

# logistic regression
logepredict = linear_model.LogisticRegression().fit(etotaltrain, gtrain).predict(etotaltest)

# SVM with RBF 1v1
clf = svm.SVC()
clf.fit(etotaltrain, gtrain)
#dec = clf.decision_function([[1]])
#print dec.shape[1]
svm1epredict = clf.predict(etotaltest)

# SVM with RBF 1vall
with catch_warnings():
    simplefilter("ignore")
    # 1vall classifier uses a deprecated numpy rank function--warning acknowledged
    svm2epredict = OneVsRestClassifier(svm.SVC()).fit(etotaltrain, gtrain).predict(etotaltest)

# k nearest neighbors
# knn = neighbors.KneighborsClassifier
# knnepredict = neighbors.KneighborsClassifier(n_neighbors=1).fit(etotaltrain, gtrain).predict(etotaltest)

# LDA
ldaepredict = LDA().fit(etotaltrain, gtrain).predict(etotaltest)

# decision tree - seems to work very well; extensions below
dtepredict = tree.DecisionTreeClassifier().fit(etotaltrain, gtrain).predict(etotaltest)

# random forest (ensemble of decision trees)
rfepredict = RandomForestClassifier().fit(etotaltrain, gtrain).predict(etotaltest)

# extra trees (ensemble of decision trees)
etepredict = ExtraTreesClassifier().fit(etotaltrain, gtrain).predict(etotaltest)

# AdaBoost (ensemble of decision trees)
abepredict = AdaBoostClassifier(n_estimators=10).fit(etotaltrain, gtrain).predict(etotaltest)

# gradient boost (ensemble of decision trees)
gbepredict = GradientBoostingClassifier(n_estimators=10).fit(etotaltrain, gtrain).predict(etotaltest)


logecount = 0
s1count = 0
s2count = 0
ldacount = 0
dtcount = 0
rfcount = 0
etcount = 0
abcount = 0
gbcount = 0
efcount = 0
ercount = 0
kcount = 0
for i in range(0, len(svm1epredict)):
    #print (gtest[i], ecompare[i], svm1epredict[i], svm2epredict[i], ldaepredict[i], dtepredict[i])
    #print (gtest[i], ecompare[i], svm1epredict[i])
    if efcompare[i] != gtest[i]:
         efcount = efcount + 1
    if ercompare[i] != gtest[i]:
         ercount = ercount + 1
    if logepredict[i] != gtest[i]:
        logecount = logecount + 1
    if svm1epredict[i] != gtest[i]:
        s1count = s1count + 1
    if svm2epredict[i] != gtest[i]:
        s2count = s2count + 1
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
    # if knnepredict[i] != gtest[i]:
    #     kcount = kcount + 1

eferror = float(efcount) / len(gtest)
ererror = float(ercount) / len(gtest)
logeerror = float(logecount) / len(gtest)
s1error = float(s1count) / len(gtest)
s2error = float(s2count) / len(gtest)
ldaerror = float(ldacount) / len(gtest)
dterror = float(dtcount) / len(gtest)
rferror = float(rfcount) / len(gtest)
eterror = float(etcount) / len(gtest)
aberror = float(abcount) / len(gtest)
gberror = float(gbcount) / len(gtest)
# kcount = float(kcount) / len(kcount)

print 'log accuracy:  ' + str(1-logeerror)
print 'svm1 accuracy: ' + str(1-s1error)
print 'svm2 accuracy: ' + str(1-s2error)
print 'lda accuracy:  ' + str(1-ldaerror)
print 'dt accuracy:   ' + str(1-dterror)
print 'rf accuracy:   ' + str(1-rferror)
print 'et accuracy:   ' + str(1-eterror)
print 'ab accuracy:   ' + str(1-aberror)
print 'gb accuracy:   ' + str(1-gberror)
print 'efilt accuracy:' + str(1-eferror)
print 'eraw accuracy: ' + str(1-ererror)
# print kcount







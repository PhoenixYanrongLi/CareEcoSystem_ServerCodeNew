__author__ = 'gmn255'

# This class is used to test and debug the room estimator before including them in the final
# server code

from csv_room_reader import CSVRoomReader
from house import House
from real_time_room_estimator import RealTimeRoomEstimator
from training_room_estimator import TrainingRoomEstimator

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

# control script for debugging

# read CSV files to test classes
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

# ACTUAL CALLS ON SERVER WILL RESEMBLE CODE FROM HERE DOWN
# (above simply reads in arrays from CSV files for testing purposes

myroomdict = {'bedroom 1': 1, 'bathroom': 2, 'living room': 3, 'kitchen': 4, 'bedroom 2': 5, 'bedroom 3': 6}

# map RSSI values to approximate location in house
beaconcoors = {'bedroom 1': (18, 6, 10), 'bathroom': (20, 18, 10), 'living room': (6, 25, 10),
                 'kitchen': (5, 10, 8), 'bedroom 2': (22, 27, 3), 'bedroom 3': (6, 45, 10)}
myhouse = House(beaconcoors, myroomdict)

trainer = TrainingRoomEstimator(myroomdict, myhouse)
clf, sumdict = trainer.train_classifier(e, g)

estimator = RealTimeRoomEstimator(myroomdict, myhouse)
#estimator.classify_room(newe, clf)
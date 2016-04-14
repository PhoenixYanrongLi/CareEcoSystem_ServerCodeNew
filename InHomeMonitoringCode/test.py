import unittest
import os
import glob
import pandas as pd
import numpy as np

from csv_room_reader import CSVRoomReader
from real_time_room_estimator import RealTimeRoomEstimator
from training_room_estimator import TrainingRoomEstimator

class RoomEstimatorTestCase(unittest.TestCase):

    myroomdict = {'bedroom 1': 0, 'bathroom': 1, 'living room': 2, 'kitchen': 3, 'bedroom 2': 4, 'bedroom 3': 5}
    testrssilist = []
    testgtlist = [["15-03-15T17:52:52.000", "[bedroom 1]"],
                  ["15-03-15T17:56:45.000", "[bedroom 1]"],
                  ["15-03-15T17:57:05.000",  "[kitchen]"],
                  ["15-03-15T17:59:14.000",  "[kitchen]"],
                  ["15-03-15T17:59:34.000",  "[bathroom]"],
                  ["15-03-15T18:01:43.000",  "[bathroom]"],
                  ["15-03-15T18:02:23.000",  "[living room]"],
                  ["15-03-15T18:04:20.000",  "[living room]"],
                  ["15-03-15T18:04:40.000",  "[bedroom 2]"],
                  ["15-03-15T18:06:51.000",  "[bedroom 2]"],
                  ["15-03-15T18:07:11.000",  "[living room]"],
                  ["15-03-15T18:07:12.000",  "[living room]"],
                  ["15-03-15T18:07:32.000",  "[bedroom 3]"],
                  ["15-03-15T18:09:51.000",  "[bedroom 3]"],
                  ["15-03-15T18:10:11.000",  "[living room]"],
                  ["15-03-15T18:11:57.000",  "[living room]"],
                  ["15-03-15T18:12:17.000",  "[bedroom 2]"],
                  ["15-03-15T18:14:08.000",  "[bedroom 2]"],
                  ["15-03-15T18:14:28.000",  "[living room]"],
                  ["15-03-15T18:14:33.000",  "[living room]"],
                  ["15-03-15T18:14:53.000",  "[kitchen]"],
                  ["15-03-15T18:16:43.000",  "[kitchen]"],
                  ["15-03-15T18:17:03.000",  "[bathroom]"],
                  ["15-03-15T18:19:23.000",  "[bathroom]"],
                  ["15-03-15T18:19:57.000",  "[bedroom 1]"],
                  ["15-03-15T18:24:06.000",  "[bedroom 1]"],
                  ["15-03-15T18:24:26.000",  "[kitchen]"],
                  ["15-03-15T18:26:29.000",  "[kitchen]"],
                  ["15-03-15T18:26:49.000",  "[bathroom]"],
                  ["15-03-15T18:28:38.000",  "[bathroom]"],
                  ["15-03-15T18:28:58.000",  "[kitchen]"],
                  ["15-03-15T18:28:59.000",  "[kitchen]"],
                  ["15-03-15T18:29:19.000",  "[living room]"],
                  ["15-03-15T18:31:25.000",  "[living room]"],
                  ["15-03-15T18:31:45.000",  "[bedroom 2]"],
                  ["15-03-15T18:33:54.000",  "[bedroom 2]"],
                  ["15-03-15T18:34:14.000",  "[living room]"],
                  ["15-03-15T18:34:18.000",  "[living room]"],
                  ["15-03-15T18:34:38.000",  "[bedroom 3]"],
                  ["15-03-15T18:36:21.000",  "[bedroom 3]"],
                  ["15-03-15T18:36:41.000",  "[living room]"],
                  ["15-03-15T18:37:21.000",  "[living room]"],
                  ["15-03-15T18:37:41.000",  "[kitchen]"],
                  ["15-03-15T18:37:51.000",  "[kitchen]"],
                  ["15-03-15T18:38:11.000",  "[bedroom 1]"],
                  ["15-03-15T18:39:38.000",  "[bedroom 1]"]]

    @staticmethod
    def __clean_teg(rawt, rawe, rawg):
        # DEPRECATED with new input method using windowed ground truth values
        # clean data from CSV files
        #   - remove +- BUFFER data points at room transitions to avoid human error
        #   - remove data before first ground truth value is seen
        # rawt = numpy dx1 array of d time values
        # rawe = numpy dxn matrix of d data points of n beacon rssi values
        # rawg = numpy dx1 array of manually collected ground truth values

        BUFFER = 10
        t = []
        e = []
        g = []
        for i in range(BUFFER, len(rawt)-BUFFER):
            validflag = True
            for j in range(i-BUFFER, i+BUFFER):
                if rawg[i] != rawg[j]:
                    # check room transitions
                    validflag = False
                    break
                if rawg[i] == 0:
                    # check times when ground truth not known
                    validflag = False
                    break
            if validflag:
                t.append(rawt[i])
                e.append(rawe[i])
                g.append(rawg[i])

        return np.array(t), np.array(e), np.array(g)

    @classmethod
    def setUpClass(self):
        # read in test files

        # read previously created CSV files to test classes
        reader = CSVRoomReader(self.myroomdict)
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
        # (t, e, g) = self.__clean_teg(tr, er, gr)

        # convert to format of 2D lists expected
        # 15-03-15T17:52:58.000 1 [h] -999.0
        for i in range(e.shape[0]):
            time = t[i]
            rssi = e[i, :]
            # print time, rssi
            hour = time/3600
            min  = (time-(hour*3600))/60
            sec  = (time-(hour*3600)-(min*60))
            fsec = (58+sec) % 60
            fmin = (52+min+((58+sec)/60)) % 60
            fhour= (17+hour+(52+min+(58+sec)/60)/60) % 24
            # no need to continue because test set is only on one day

            timestring = "15-03-15T" + '{0:02d}'.format(fhour) + ":" + "{0:02d}".format(fmin) + ":" + \
                         "{0:02d}".format(fsec) +".000"
            rssistringlist = [timestring, str(6), "[bedroom 1]", str(float(rssi[0])), "[bathroom]",
                              str(float(rssi[1])), "[living room]", str(float(rssi[2])), "[kitchen]",
                              str(float(rssi[3])), "[bedroom 2]", str(float(rssi[4])), "[bedroom 3]",
                              str(float(rssi[5]))]
            self.testrssilist.append(rssistringlist)

        # map RSSI values to approximate location in house
        beaconcoors = {'bedroom 1': (18, 6, 10), 'bathroom': (20, 18, 10), 'living room': (6, 25, 10),
                       'kitchen': (5, 10, 8), 'bedroom 2': (22, 27, 3), 'bedroom 3': (6, 45, 10)}


        trainer = TrainingRoomEstimator(beaconcoors)
        self.clf, self.sumdict = trainer.train_classifier(self.testrssilist, self.testgtlist)
        self.estimator = RealTimeRoomEstimator(trainer)

        # report classifier statistics
        for outerkey in self.sumdict:
            if outerkey == 'error dictionary':
                for key in self.sumdict[outerkey].keys():
                    print key + ": " + str(self.sumdict['error dictionary'][key])
                print ""
            else:
                print outerkey + ": " + str(self.sumdict[outerkey])


    def test_total_accuracy(self):
        # check that total accuracy measure is above 90%
        error = self.sumdict['classifier error']
        errormsg = "The classifier error rate is too high: error = {:f}".format(error)
        self.assertGreaterEqual(0.1, error, errormsg)

    def test_rawRSSI_accuracy(self):
        # sanity check that raw RSSI values should be greater than 70%
        errormsg = "The raw RSSI error rate is too high: error = {:f}".format(self.sumdict['filtered RSSI error'])
        self.assertLessEqual(self.sumdict['filtered RSSI error'], 0.3, errormsg)


if __name__ == '__main__':
    unittest.main()

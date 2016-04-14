__author__ = 'gmn255'

# This class has been deprecated. It is kept here only for reference

from parse import parse
import string as string
import csv
import numpy as np
from sys import maxint

class CSVRoomReader(object):

    def __init__(self, roomdict):
        # roomdict specifies the dictionary mapping rooms to indices
        # each house has the same estimote major value, then each room is
        # assigned a new estimote minor value starting from index 1
        self.roomdict = roomdict
        # numrooms = the number of rooms
        self.numrooms = len(roomdict)
        # timearray = the array of time points collected from estimote scanning starting at 0
        self.timearray = np.empty(0, dtype='i8')
        # timeref = the actual time at which the first estimote measurement is taken and used as reference
        self.timeref = 0


    def __get_time(self, timestamp):
        # Convert the timestamp into time in seconds
        # the input is in format year.month.day-hour.min.sec' (e.g., '2015.1.26-13.5.57')
        # and the output is a natural number based on a 5-year cycle

        # use relative time since first data point as time index
        timeholder = parse("{:d}.{:d}.{:d}-{:d}.{:d}.{:d}", timestamp)
        t = (3110400*timeholder.fixed[0] + 1036800*timeholder.fixed[1] + \
            86400*timeholder.fixed[2] + 3600*timeholder.fixed[3] + \
            60*timeholder.fixed[4] + timeholder.fixed[5]) - self.timeref
        return t

    def __get_rssi(self, rssistamp):
        # Convert the rssistring into sparse matrix
        # parse RSSI in format 'beacon-value:' (e.g.,'1--69:4--96:')
        # where only non-zero values are transmitted

        rssistrings = string.split(rssistamp, ':')
        rssiarray = np.zeros(self.numrooms)
        for rssistring in rssistrings:
            rssiholder = parse("{:d}-{:d}", rssistring)
            if rssiholder is None:
                continue
            else:
                rssiarray[rssiholder.fixed[0]-1] = rssiholder.fixed[1]
        #print(rssiarray)
        return rssiarray

    def __get_room(self, roomstring):
        # translate a room string from the database (e.g., bedroom 1)
        roomstring = string.strip(roomstring, '"')  # may contain quotes (") on each end

        # # remove spaces from previous format
        # rs = string.split(roomstring)
        # rd = ""
        # for c in rs:
        #     rd = rd + c
        return self.roomdict[roomstring]

    def __zero_to_999(self, erssiarray):
        # send all 0 values to -999, so largest value indicates most likely room
        for i in range(erssiarray.shape[0]):
            for j in range(erssiarray.shape[1]):
                if erssiarray[i, j] == 0:
                    erssiarray[i, j] = -999

    def read_estimote(self, filename):
        # read estimote CSV file -- have to use csv import instead of numpy
        # because rssi string breaks up from 1 item to numRooms items

        estilist = []
        firstflag = True
        with open(filename, 'rb') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')
            for row in reader:
                if firstflag:
                    # on first iteration need to define time reference
                    firstflag = False
                    self.timeref = 0
                    self.timeref = self.__get_time(row['timestamp'])
                    self.timearray = np.array(self.__get_time(row['timestamp']))
                    estilist.append(self.__get_rssi(row['rssilist']))
                    continue
                #print(row['rssilist'], row['timestamp'])
                time = self.__get_time(row['timestamp'])
                self.timearray = np.append(self.timearray, time)

                rssiarray = self.__get_rssi(row['rssilist'])
                estilist.append(rssiarray)

        #print np.array(estilist)
        return np.array(estilist)  # return list as numpy array

    def read_ground_match(self, filename):
        # read the ground truth csv file and create array at time points
        # matching the estimote measurement points
        # if ground truth is not yet known at an estimote measurement point,
        # the room value is set to 0 and dropped in clean_teg()

        # THIS FUNCTION REQUIRES NUMERICAL VALUES
        rawlist = np.loadtxt(open(filename, "rb"), delimiter=",", dtype='i8', \
                  converters={2: self.__get_room, 3: self.__get_time}, skiprows=1, usecols=(2, 3))

        rawlist = np.vstack([rawlist, [rawlist[-1, 0], maxint]])
        gtime = rawlist[:, 1]

        # get ground truth at matching times
        groomarray = np.zeros(len(self.timearray))
        gcounter = 0  # marks progression in ground truth array
        for i in range(0, len(self.timearray)):
            # define bounds within the ground truth is known
            gtimelower = gtime[gcounter]
            if gcounter < len(gtime):
                gtimeupper = gtime[gcounter+1]
            else:
                 gtimeupper = maxint
             # mark room as 0 when unknown value before the first ground truth has been acquired
            if gcounter == 0 and self.timearray[i] < gtimelower:
                groomarray[i] = 0
            elif self.timearray[i] >= gtimeupper:
                # increase bounding box once self.timearray has progressed past it
                # cannot simply increment because estimote may miss a whole room
                # if the watch wearer just walks through
                for j in range(gcounter, len(gtime)):
                    if gtime[j] > self.timearray[i]:
                        gcounter = j-1
                        break
                groomarray[i] = rawlist[gcounter, 0]
            else:
                groomarray[i] = rawlist[gcounter, 0]
                #print (groomarray[i], self.timearray[i])
        return groomarray

    def read_csv_pair(self, estifilename, groundfilename):
        # this is the main function to be used from this class
        # it reads an estimote csv file and the matching ground truth csv file
        # it returns 3 numpy arrays
        #   timearray - array of time points when estimote measurements taken
        #   estimoteRSSIarray - matrix of estimote RSSI values (measurements x rooms)
        #   groundmatcharray - ground truth array of equal length with ground truth
        #                      value at each point in timearray

        estimoteRSSIarray = self.read_estimote(estifilename)
        self.__zero_to_999(estimoteRSSIarray)
        # print(self.timearray)
        # print(estimoteRSSIarray)
        groundmatcharray = self.read_ground_match(groundfilename)
        # print groundmatcharray

        #(t, e, g) = self.clean_teg(self.timearray, estimoteRSSIarray, groundmatcharray)
        (t, e, g) = (self.timearray, estimoteRSSIarray, groundmatcharray)

        # quick sanity checking
        if len(t) == 0:
            raise ValueError('{timearray} cannot be size zero'.format( \
                timearray=repr(t)))
        elif len(t) != len(g) or \
             len(t) != len(e):
            raise ValueError('timearray: {tlen} or estimoteRSSIarray: {elen} '
                'or groundmatcharray: {glen} is not the right size'.format( \
                tlen=repr(len(t)), elen=len(e), \
                glen=len(g)))
        return t, e, g

    @staticmethod
    def clean_teg(rawt, rawe, rawg):
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




# test script
# roomdict = {'bedroom 1': 1, 'bathroom': 2, 'living room': 3, 'kitchen': 4, 'bedroom 2': 5, 'bedroom 3': 6}
# reader = CSVRoomReader(roomdict)
# print reader.read_csv_pair("CSVs/estimote21.csv", "CSVs/ground_trust21.csv")




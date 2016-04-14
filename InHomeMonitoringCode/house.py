__author__ = 'gmn255'

import numpy as np
from sys import maxint

# can have x, y, and z (multiple floors)
# don't actually need wall locations, just train on room-labeled data to learn class labels

class House(object):
    # a house object defines the information we need to know about the house to perform
    # proper room estimation, and functions for mapping between RSSI values and approximate locations
    def __init__(self, beaconcoordict, roomlist):
        # set estimote locations as (x,y,z) position in feet with (0,0,0)
        # coordinate defined as the northeast corner of the house at 0 elevation
        # beaconcoordict = dictionary mapping beacons names to (x,y,z) tuple (e.g., {'bathroom': (2, 15, 10)}
        # roomlist = list mapping rooms to indices
        self.beaconlocations = np.empty([len(beaconcoordict), 3])
        for beacon in beaconcoordict:
            self.beaconlocations[roomlist.index(beacon)] = np.array(beaconcoordict[beacon])
        self.roomlist = roomlist
        # print self.beaconlocations

    def get_coor_from_rssi(self, erssiarray):
        # Convert rssi into x,y,z position in house using weighted path loss (WPL) model
        # erssiarray is a d*m numpy array of d data points with m possible beacons
        # the output maps this rssi to a location in a floorplan


        coorarray = np.empty([len(erssiarray), 3])

        for j in range(len(erssiarray)):
            d = np.empty(len(erssiarray[j]))
            for i in range(len(erssiarray[j])):
                if erssiarray[j, i] == 0:
                    d[i] = maxint
                else:
                    # signal loss model from Han Zou 2013
                    d[i] = (10**((erssiarray[j, i]+52.4)/-35.8))

            sumd = 0  # note calling this a sum is a bit of notation abuse
            for dist in d:
                sumd = sumd + 1/dist;
            weight = np.empty(len(d))
            for i in range(len(weight)):
                weight[i] = (1/d[i])/sumd

            x = 0
            y = 0
            z = 0
            for i in range(len(erssiarray[j])):
                # x,y,z are inferred from rssi value and weighted path loss model
                x = x + weight[i]*self.beaconlocations[i, 0]
                y = y + weight[i]*self.beaconlocations[i, 1]
                z = z + weight[i]*self.beaconlocations[i, 2]


            coor = np.array([x, y, z])
            coorarray[j] = coor
        return coorarray



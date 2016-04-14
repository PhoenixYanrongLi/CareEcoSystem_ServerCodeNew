__author__ = 'Brad'
from eventProcessingClass import EventProcessing
import numpy

class LifeSpaceDetection(EventProcessing):

    def get_max_distance(self, home_location, locations_list):

        max_distance = 0

        for i in locations_list:
            dist = numpy.sqrt((home_location[0]-i[0])**2 + (home_location[1]-i[1])**2)
            if dist > max_distance:
                max_distance = dist

        return max_distance

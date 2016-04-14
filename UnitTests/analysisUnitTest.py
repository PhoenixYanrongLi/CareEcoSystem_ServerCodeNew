__author__ = "Bradley Zylstra"
__version__ = "1.0"
__maintainer__ = "Bradley Zylstra"
__email__ = "bradleybaldwin@gmx.com"
__status__ = "Development"
import unittest
import scipy.io
import numpy
import os
from AnalysisCode.phoneAnalysisMain import Mag_Acc_Time,Acc_Filter,FFT_Stepcount,RMSCalculator
import matplotlib.pyplot as plt
from PythonTools import peakCounter


class AnalysisTester(unittest.TestCase):

    def setUp(self):
        filepath = os.path.dirname(os.path.realpath(__file__))
        #self.analysisTestDataOut = scipy.io.loadmat(os.path.join(filepath,'testData','outputDataphoneAnalysis.mat'))
        #self.analysisTestDataIn = scipy.io.loadmat(os.path.join(filepath ,'testData','0424to0429.txt_AccelerometerData.mat'))
        self.analysisTestDataIn = scipy.io.loadmat(os.path.join(filepath ,'testData','99000213875160_20141113-193740_MM_ACC_1103.txt_AccelerometerData.mat'))
        self.accData = self.analysisTestDataIn['AccData']
        self.UnixTime_ms = self.analysisTestDataIn['UnixTime_ms']

    def testdata(self):
        self.Acc_Data, self.T_convert = Mag_Acc_Time(self.accData, self.UnixTime_ms)
        #self.Raw_Acc=Acc_Filter(self.acc_data)
        self.window = 512
        self.cutoff = 2.7
        self.w = [.3, .7]
        self.stepCount = FFT_Stepcount(self.Acc_Data, self.T_convert, self.window, self.cutoff)
        #self.RMS_Box,self.RMS_Ratio=RMSCalculator(self.acc_data)
        print self.stepCount




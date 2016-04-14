"""
rbfUnitTest.py is a collection of unit tests that validate Matlab algorithms ported over to Python have the
same behavior

rbfTester is a class that contains all of the unit tests.
setUp imports test data and assigns them to variables.
TtoN is a test that verifies it can find 1s in a matrix.


"""
__author__ = "Bradley Zylstra"
__version__ = "1.0"
__maintainer__ = "Bradley Zylstra"
__email__ = "bradleybaldwin@gmx.com"
__status__ = "Development"


import unittest
import scipy.io
import numpy as np
import numpy
from InHomeMonitoringCode.rbfMain import TtoN,rbfnn_raw,rMeans, pnnHuer,radial,decide,initialize


class rbfTester(unittest.TestCase):
    def setUp(self):
        self.rkmeansInTestData = scipy.io.loadmat(
            'C:\Users\Brad\Desktop\Programming\InHomeMonitoring\PythonServerCode\UnitTests\\testData\\rkmeansInTestData.mat')
        self.rkmeansOutTestData = scipy.io.loadmat(
            'C:\Users\Brad\Desktop\Programming\InHomeMonitoring\PythonServerCode\UnitTests\\testData\\rkmeansOutTestData.mat')
        self.exampleKmeansData = scipy.io.loadmat(
            'C:\Users\Brad\Desktop\Programming\InHomeMonitoring\PythonServerCode\UnitTests\\testData\\seeds.mat')
        #self.examplePnnData=scipy.io.loadmat('C:\Users\Brad\Desktop\Programming\InHomeMonitoring\PythonServerCode\UnitTests\\testData\\')
        self.testData=scipy.io.loadmat('C:\Users\Brad\Desktop\RSSI Localization with path resolution - Jul 9 2014\MATLAB\exportedData.mat')
        #self.X = self.rkmeansInTestData['X']
        self.R=self.testData['R']
        self.X=self.testData['X']
        self.ET=self.testData['Et']
        self.Y=self.testData['Y']
        self.L=self.testData['L']
        #self.X,self.R=initialize(self.X,self.R,self.ET,self.Y,self.L)
        #print(self.X)
        self.k = self.rkmeansInTestData['k']
        #self.Y=self.exampleKmeansData['Y']
        self.Stest = self.rkmeansOutTestData['S']
        self.Ctest = self.rkmeansOutTestData['C']
        self.seeds = self.exampleKmeansData['Seeds']

        #self.C, self.S = rMeans(self.seeds, self.X)
        #self.B = pnnHuer(self.Ctest, self.k[0][0]-1)
        #self.G=radial(self.X,self.k[0][0],self.Ctest,self.B)
        #self.V=numpy.dot(numpy.linalg.pinv(self.G),self.Y)
        #self.That=numpy.dot(radial(self.R,33.0,self.C,self.B),self.V)
        #self.Yhat=decide(self.That)
        #self.Yhat=rbfnn_raw(self.R,self.X,self.Y,self.k,self.seeds)
        #print self.Yhat
        initialize('C:\Users\Brad\Desktop\Programming\InHomeMonitoring\PythonServerCode\UnitTests\\testData\\exportedData.mat')
    #def tests(self):
     #   self.assertEqual(1, 1)
    def testTtoN(self):
        AF=numpy.zeros((3,3))
        AF[0,1]=1
        AF[1,2]=1
        AF[2,0]=1
        print AF
        print TtoN(AF)

if __name__ == '__main__':
    runner = unittest.main()

    #unittest.main()
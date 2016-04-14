"""
Mag_Acc_Time Calculates the magnitude of the ACC data and the time of all the data
Acc_Filter runs a bandpass filter on the data, not currently used
FFT_Stepcount calculates the number of steps taken in the data using the FFT approach to calculating steps
RMS_Calculator calculates the RMS for a window, not currently used, will be for activity classification in the future.
"""
__author__ = "Bradley Zylstra"
__version__ = "1.0"
__maintainer__ = "Bradley Zylstra"
__email__ = "bradleybaldwin@gmx.com"
__status__ = "Development"

import numpy
import math
#from scipy.fftpack import fft
from scipy.signal import butter,lfilter
import sys

def Mag_Acc_Time(Acc_data,timeData):

    #convert time to seconds
    timeData=numpy.divide(timeData,1000)

    #convert from 9.8g to 64g ?Nokia phone did this, it is now magical
    Acc_data = numpy.multiply(Acc_data,(64/9.8))
    x_Acc = Acc_data[:,0]
    y_Acc = Acc_data[:,1]
    z_Acc = Acc_data[:,2]
    Acc = numpy.sqrt(numpy.square(x_Acc)+numpy.square(y_Acc)+numpy.square(z_Acc))
    T_convert = timeData-timeData[0]
    Acc = Acc[~numpy.isnan(Acc)]
    T_convert = T_convert[~numpy.isnan(T_convert)]
    return Acc,T_convert

def Acc_Filter(Raw_Acc):
    w = [.3,.7]
    b, a = butter(10,[.3,.7],btype="bandpass")
    Acc_Filtered = lfilter(b,a,Raw_Acc)
    return Acc_Filtered

def FFT_Stepcount(Quality_Acc,T_convert,window,Cutoff):
    Len = len(Quality_Acc)
    Firstwindow_stepdetection = 0
    count = []
    count2 = []
    count3 = []
    frequency = numpy.zeros((1,5))
    portion = 0.0
    Box = []
    Box2 = []
    power = numpy.array([])
    Time = []
    for i in range(0,Len-window,window):

        if i==0:
            Time = T_convert[i]
        else:
            Time = numpy.vstack([Time,T_convert[i]])

        for n in range(0,window):

            if Quality_Acc[i+n] < 66 and Quality_Acc[i+n+1]>66:
                Firstwindow_stepdetection += 1

        if Firstwindow_stepdetection < 8:
            count.append(0)
        else:
            for j in range(i,i+window-38,38):
                A = numpy.msort(numpy.array(Quality_Acc[j:j+39]))
                #print A
                if A[-6]<66:
                    pass
                else:
                    portion = float(portion)+float(38.0/window)

            T = T_convert[i+window]-T_convert[i]

            p = numpy.abs(numpy.fft.fft(Quality_Acc[i:i+window+1])/(window/2.0))
            p = p[0:window/2]**2

            freq = numpy.arange(0,window/2)/T
            freq = numpy.transpose(freq)

            Power_and_Freq = numpy.c_[p,freq]
            Power_and_Freq = Power_and_Freq[Power_and_Freq[:,0].argsort()]

            if Power_and_Freq[0,1]>Cutoff:
                Power_and_Freq[0,1]=0
            count.append(Power_and_Freq[-2,1]*T*portion)
            Box2.append(portion)
            portion=0.0
            Box.append(Firstwindow_stepdetection)
            Firstwindow_stepdetection=0

        Power_and_Freq = []
        freq = []
        p = []

    count = numpy.transpose(count)
    count = numpy.sum(count)
    return count

def RMSCalculator(Acc):
    RMS_Value = 0
    RMS_Box = []
    RMS_Box_Avg = []
    Len = len(Acc)
    RMS_Up_Value = 0
    RMS_Up = []
    RMS_Down_Value = 0
    RMS_Down = []
    RMS_Up_Avg = []
    RMS_Down_Avg = []
    window = 128
    for i in range(0,Len-window,window):
        Mean = numpy.mean(Acc[i:i+window+1])

        for j in range(0,window):
            RMS_Value += (Acc[i + j] - Mean) ** 2

            if Acc[i+j]>59:
                RMS_Up_Value += (Acc[i + j] - 59) ** 2
            else:
                RMS_Down_Value += (Acc[i + j] - 59) ** 2

        RMS_Value = numpy.sqrt(RMS_Value/float(window))
        RMS_Up_Value = numpy.sqrt(RMS_Up_Value/float(window))
        RMS_Down_Value = numpy.sqrt(RMS_Down_Value/float(window))

        if i ==0:
            RMS_Box = RMS_Value
            RMS_Up = RMS_Up_Value
            RMS_Down = RMS_Down_Value
        else:
            RMS_Box = numpy.vstack([RMS_Box, RMS_Value])
            RMS_Up = numpy.vstack([RMS_Up, RMS_Up_Value])
            RMS_Down = numpy.vstack([RMS_Down, RMS_Down_Value])

        RMS_Value = 0
        RMS_Up_Value = 0
        RMS_Down_Value = 0

    for i in range(0,len(RMS_Box),2):
        if i ==0:
            RMS_Box_Avg = numpy.mean(RMS_Box[i:i+1])
            RMS_Up_Avg = numpy.mean(RMS_Up[i:i+1])
            RMS_Down_Avg = numpy.mean(RMS_Down[i:i+1])
        else:
            RMS_Box_Avg = numpy.vstack([RMS_Box_Avg, numpy.mean(RMS_Box[i:i+1])])
            RMS_Up_Avg = numpy.vstack([RMS_Up_Avg, numpy.mean(RMS_Up[i:i+1])])
            RMS_Down_Avg = numpy.vstack([RMS_Down_Avg, numpy.mean(RMS_Down[i:i+1])])
            
    RMS_Ratio = numpy.divide(RMS_Up,RMS_Down)

    return RMS_Box, RMS_Ratio












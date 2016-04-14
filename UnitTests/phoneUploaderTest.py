__author__ = 'Brad'
import csv
import dateutil
import datetime
import random
import time
import os

def genfileName(phoneID,date,inc):
    filename=''
    filename+=phoneID+"_"
    dateString=''
    for i in range(0,3):
        if len(str(date[i]))<2:
            dateString+="0"+str(date[i])
        else:
            dateString+=str(date[i])
    dateString+='-'
    for i in range(3,6):
        if len(str(date[i]))<2:
            dateString+="0"+str(date[i])
        else:
            dateString+=str(date[i])

    #dateString=str(date[0])+str(date[1])+str(date[2])+'-'+str(date[3])+str(date[4])+str(date[5])
    restString='_MM_ACC_'+str(inc)+'.txt'
    filename+=dateString+restString
    return filename


def genPhoneID():
    phoneIDString=''
    for i in range(0,14):
        phoneIDString+=str(random.randint(0,9))
    return phoneIDString

if __name__=="__main__":
    for k in range(0,500):
        phoneID=genPhoneID()
        upload_dir=os.path.join(os.path.dirname(__file__),phoneID)
        if not os.path.exists(upload_dir):
            os.mkdir(upload_dir)
        date=[]
        upload_dir=os.path.join(upload_dir,'acc')
        if not os.path.exists(upload_dir):
            os.mkdir(upload_dir)
        date.append(random.randint(2000,2014))
        date.append(random.randint(1,13))
        date.append(random.randint(1,31))
        date.append(random.randint(1,25))
        date.append(random.randint(1,60))
        date.append(random.randint(1,60))
        for i in range(0,1000):
            fileName=genfileName(phoneID,date,i)
            writer=open(os.path.join(upload_dir,fileName),"w+")
            for i in range(0,1000):
                miliString=str(i)
                if len(miliString)<2:
                    miliString += '00'
                elif len(miliString)<3:
                    miliString += '0'
                year=str(date[0])[2:4]
                month=str(date[1])
                if len(month)<2:
                    month += '0'
                day=str(date[2])
                if len(day)<2:
                    day += '0'
                hour=str(date[3])
                if len(hour)<2:
                    hour += '0'
                min=str(date[4])
                if len(min)<2:
                    min += '0'
                sec=str(date[5])
                if len(sec)<2:
                    sec += '0'
                dateString=str(year+'-'+month+'-'+day+'T'+hour+':'+min+':'+sec+":"+miliString)
                x=random.random()
                y=random.random()
                z=random.random()
                azimuth=random.random()
                pitch=random.random()
                roll=random.random()
                writer.write(dateString+' '+str(x)[0:8]+' '+str(y)[0:8]+' '+str(z)[0:8]+' ' +str(azimuth)[0:8]+' '+str(pitch)[0:8]+' '+str(roll)[0:8]+'\n')
            date[5]+=1
            if date[5]==59:
                date[5]=0
                date[4]+=1
            print fileName


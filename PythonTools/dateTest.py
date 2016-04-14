__author__ = 'Brad'
import datetime
# formatStr="%y-%m-%dT%H:%M:%S.%f"
# format2="%H:%M:%S.%f"
# timeC=datetime.datetime.strptime(time,formatStr)
# print timeC
# epoch = datetime.datetime.utcfromtimestamp(0)
# delta=timeC-epoch
# print delta.total_seconds()*1000

time2='14-11-13T19:37:40.307'

formatStr="%y-%m-%dT%H:%M:%S.%f"
timeC=datetime.datetime.strptime(time2,formatStr)
epoch = datetime.datetime.utcfromtimestamp(0)
delta1=timeC-epoch
delta1=delta1.total_seconds()*1000

time1="14-08-05T13:27:05.168"
formatStr="%y-%m-%dT%H:%M:%S.%f"
timeC=datetime.datetime.strptime(time1,formatStr)
epoch = datetime.datetime.utcfromtimestamp(0)
delta2=timeC-epoch
delta2=delta2.total_seconds()*1000

# delta3=delta1-delta2
# delta3=delta3/86400000
# print delta3

print delta1
print delta2

currentDate=datetime.datetime.now()
deltaCur=currentDate-epoch
deltaCur=deltaCur.total_seconds()

print deltaCur
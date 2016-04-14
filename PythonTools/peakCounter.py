__author__ = 'Brad'
def peakCounter(data,threshold):
    counts=0
    for i,z in enumerate(data):
        if i-1>=0 and i+1<len(data) and data[i-1]<z and data[i+1]<z and z>threshold:
            counts += 1
    return counts


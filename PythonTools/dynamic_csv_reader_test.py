__author__ = 'Brad'
import csv
f = open('csvtst.txt', 'r')
reader = csv.reader(f, delimiter=' ')

print reader.next()
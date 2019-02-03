#PerformanceCalculator.py
#Authored:Shreyas Ramakrishna
#Last Edited: 08/14/2018
#Description: Performance measure of the model. Measures the MSE for predicted and estimated outputs.

import csv
from sklearn.metrics import mean_squared_error
from math import sqrt
import numpy as np

data1=[]
data2=[]
with open('kerasvalidation.csv','r') as csvfile:
    plots = csv.reader(csvfile)
    for row in plots:
        data1.append(float(row[0]))#predicted
        data2.append(float(row[1]))#manual
mse = mean_squared_error(data1,data2)
print(mse)

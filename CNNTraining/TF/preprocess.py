#preprocess.py
#Authored: Shreyas Ramakrishna
#Reference: https://github.com/mbechtel2/DeepPicar-v2
#Last Edited: 08/14/2018
#Description: Preprocessing images as batches for batch training of data.


import random
import os
import sys
import cv2
import csv
import glob
from collections import OrderedDict

#image dimensions
img_height = 66
img_width =  200
img_channels = 3
batch_size = 32

train_set = ['Trial10']
inputs = OrderedDict()
outputs = OrderedDict()

input1 = []
input2 = []
output1 = []
output2 = []

for i in train_set:
    inputs[i] = []
    outputs[i] = []

#Loading data seperately for training and validation
def load_data(data):

    global inputs
    global outputs
    global input1
    global output1

    miny= 10
    maxy= 20

    if(data == 'Trial10'):

        #print('Loading data from {} dataset'.format(data))
        numFiles = len(glob.glob1('/home/scope/Shreyas/Car/TF/0310/Trial10','*.jpg'))
        #print("Total number of images in training dataset: %d" %numFiles)
        for j in range(0,numFiles-1):
            image=cv2.imread('/home/scope/Shreyas/Car/TF/0310/Trial10/frame%d.jpg'%j)
            img = cv2.resize(image, (200, 66))
            img = img / 255.
            inputs[i].append(img)
        input1 = inputs[i]

        with open('/home/scope/Shreyas/Car/TF/0310/Trial10/ProcessData.csv') as File:
            reader=csv.reader(File)
            for row in reader:
                output1=[]
                x=(float(row[1])-miny)/(maxy-miny)
                output1.append(x)
                outputs[i].append(output1)
            output1 = outputs[i]

    if(data == 'Trial5'):

        #print('Loading data from {} dataset'.format(data))
        numFiles = len(glob.glob1('/home/scope/Shreyas/Car/TF/Trial5','*.jpg'))
        #print("Total number of images in training dataset: %d" %numFiles)
        for j in range(0,numFiles-1):
            image=cv2.imread('/home/scope/Shreyas/Car/TF/Trial5/frame%d.jpg'%j)
            img = cv2.resize(image, (200, 66))
            img = img / 255.
            inputs[i].append(img)
            input1 = inputs[i]

        with open('/home/scope/Shreyas/Car/TF/Trial5/ProcessData.csv') as File:
            reader=csv.reader(File)
            for row in reader:
                output=[]
                x=(float(row[1])-miny)/(maxy-miny)
                output.append(x)
                outputs[i].append(output)
                output1 = outputs[i]

    return input1, output1


def load_batch_data(data):
    #Loading batch training data
    if(data == 'Trial10'):
        print("Loading {} shuffled images from {} dataset".format(batch_size, data))
        input1, output1 = load_data('Trial10')
        assert len(input1) == len(output1)
        n = len(input1)
        #print(n)
        #n1 = len(input1)
        #print(n1)

        value = random.sample(range(0, n), batch_size)
        #print(value)
        #assert len(value) == batch_size

        x, y = [], []
        for i in value:
            x.append(input1[i])
            y.append(output1[i])

    #Loading batch validation data
    if(data == 'Trial5'):
        print("Loading {} shuffled images from {} dataset".format(batch_size, data))
        input1, output1 = load_data('Trial5')
        #assert len(input1) == len(output1)
        n = len(input1)
        print(n)
        n1 = len(input1)
        print(n1)


        value = random.sample(range(0, n), batch_size)
        #print(value)
        assert len(value) == batch_size

        x, y = [], []
        for i in value:
            x.append(input1[i])
            y.append(output1[i])

    return x, y


if __name__ == '__main__':
    x,y = load_batch_data()

#imagesprocess.py
#Authored: Shreyas Ramakrishna
#Reference: https://github.com/mbechtel2/DeepPicar-v2
#Last Edited: 08/14/2018
#Description: Preprocessing images for single trials of data

import random
import os
import sys
import cv2
import csv
import glob

img_height = 66
img_width =  200
img_channels = 3

#Load complete input images without shuffling
def load_training_images():
    miny = 10
    maxy = 20
    minS = 15
    maxS = 15.7
    Y = []
    A = []
    inputs=[]
    numFiles = len(glob.glob1('/home/scope/Shreyas/Car/TF/Trial7','*.jpg'))
    print("Total number of images in training dataset: %d" %numFiles)
    for i in range(0,numFiles):
        image=cv2.imread('/home/scope/Shreyas/Car/TF/Trial7/frame%d.jpg'%i)
        img = cv2.resize(image, (200, 66))
        img = img / 255.
        inputs.append(img)

    with open('/home/scope/Shreyas/Car/TF/Trial7/ProcessData.csv') as File:
        reader=csv.reader(File)
        for row in reader:
            output1=[]
            x=(float(row[2])-minS)/(maxS-minS)
            output1.append(x)
            A.append(output1)

    with open('/home/scope/Shreyas/Car/TF/Trial6/ProcessData.csv') as File:
        reader=csv.reader(File)
        for row in reader:
            output=[]
            x=(float(row[1])-miny)/(maxy-miny)
            output.append(x)
            Y.append(output)

    return inputs, A, Y

#Load complete output data without shuffling
def read_training_output_data():
    miny= 10
    maxy= 20
    Y=[]
    with open('/home/ubuntu/car/Trial2/ProcessData.csv') as File:
        reader=csv.reader(File)
        for row in reader:
            output=[]
            x=(float(row[1])-miny)/(maxy-miny)
            output.append(x)
            Y.append(output)
    return Y

#Load shuffled batch input images
def load_validation_images():
    inputs=[]
    numFiles = len(glob.glob1('/home/ubuntu/car/Trial2','*.jpg'))
    print("Total number of images in validation dataset: %d" %numFiles)
    for i in range(0,numFiles):
        image=cv2.imread('/home/ubuntu/car/Trial2/frame%d.jpg'%i)
        img = cv2.resize(image, (200, 66))
        img = img / 255.
        inputs.append(img)
    return inputs

#Load output shuffled batch_data
def read_validation_output_data():
    miny= 9.82
    maxy= 19.82
    Y=[]
    with open('/home/ubuntu/car/Trial2/ProcessData.csv') as File:
        reader=csv.reader(File)
        for row in reader:
            output=[]
            x=(float(row[1])-miny)/(maxy-miny)
            output.append(x)
            Y.append(output)
    return Y


if __name__ == '__main__':

    load_training_images()
    read_training_output_data()
    load_validation_images()
    read_validation_output_data()

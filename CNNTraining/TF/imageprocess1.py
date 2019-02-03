#imagesprocess1.py
#Authored: Matthew Burruss
#Reference: https://github.com/mbechtel2/DeepPicar-v2
#Last Edited: 08/14/2018
#Description: Preprocessing images for multiple Trials of data

import random
import os
import sys
import cv2
import csv
import glob

# image dimensions
img_height = 66
img_width =  500
img_channels = 3
# steering range
steering = (10,20)

# path to USB
USBPath = "/home/scope/Shreyas/Car/TF/0310/"
# list of folders used in training
trainingFolders = ["Trial11","1114"]
# list of folders used in validation
validationFolders = ["Trial1"]


#Load complete input images without shuffling
def load_images(paths,datatype):
    # initialize loop variables
    numImages = 0
    inputs = []
    Y = []
    for path in paths:
        processDataPath = path+"ProcessData.csv"
        if not os.path.isfile(processDataPath):
            print('ProcessData.csv must be in folder %s' %path)
            return
        # read images in ProcessData.csv and append to input
        with open(processDataPath, 'rt') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                numImages = numImages+1

                if not os.path.isfile(path + (row[0].lower())):
                    print('%s not found.' %(path+(row[0].lower())))
                    return
                image=cv2.imread(path + (row[0].lower()))
                #image = image[100:239, 0:319]
                img = cv2.resize(image, (200, 66))
                img = img / 255.
                inputs.append(img)
    print("Total number of images in %s: %d" %(datatype,numImages))
    return inputs

#Load complete output data without shuffling
def read_output_data(paths):
    # initialize loop variables
    Y=[]
    A=[]
    # ensure path exists
    for path in paths:
        processDataPath = path+"ProcessData.csv"
        if not os.path.isfile(processDataPath):
            print('ProcessData.csv not found in %s.' %path)
            return
        # open ProcessData.csv and append steering values to Y
        with open(processDataPath, 'rt') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                output = []
                y=(float(row[1])-steering[0])/(steering[1]-steering[0])
                output.append(y)
                Y.append(output)
    
    return Y

def createFolderPaths(folders):
    paths = []
    for folder in folders:
        path = USBPath + folder + '/'
        paths.append(path)
    return paths

def isValidListOfPaths(paths):
    for path in paths:
        if not os.path.isdir(path):
            print('%s not found.' %path)
            return False
        if not os.path.isfile(path + 'ProcessData.csv'):
            print('ProcessData.csv not found in %s' %path)
            return False
    return True

def load_training_images():
    paths = createFolderPaths(trainingFolders)
    if isValidListOfPaths(paths):
        return load_images(paths,'training')

def read_training_output_data():
    paths = createFolderPaths(trainingFolders)
    if isValidListOfPaths(paths):
        return read_output_data(paths)

def load_validation_images():
    paths = createFolderPaths(validationFolders)
    if isValidListOfPaths(paths):
        return load_images(paths,'validation')

def read_validation_output_data():
    paths = createFolderPaths(validationFolders)
    if isValidListOfPaths(paths):
        return read_output_data(paths)

if __name__ == '__main__':
    load_training_images()
    read_training_output_data()
    load_validation_images()
    read_validation_output_data()

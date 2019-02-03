# ProcessTrialData.py
# author: Matthew P. Burruss
# last update: 8/14/2018

import csv
from collections import defaultdict
import datetime
import operator
#import cv2
#import numpy as np
#import imageprocess
#import model
#import tensorflow as tf
import os
import math

# preprocess()
# Descrption: resizes and normalizes image
def preprocess(img):
    img = cv2.resize(img, (200, 66))
    img = img / 255.
    return img

# denormalization()
# Summary: Uses global variables miny and maxy to denormalize output from CNN
# Parameter: steer => normalized steering duty cycle [0,1]
# returnVal: denormalized steering value [miny,maxy]
def denormalization(steer):
    assert(maxy - miny == 10),'Error denormalizing: Difference between miny and maxy is not 10.'
    return (float(steer)*(maxy-miny))+miny

# join()
# Descrption: joins directory with file path
def join(dirpath, filename):
    return os.path.join(dirpath, filename)

# process_data()
# Reads DutyCycleData.csv and ImageCountData.csv and writes ProcessData.csv which contains
# the image file name and associated duty cycles
# Parameters:
#   path => path to folder containing DutyCycleData.csv and ImageCountData.csv
def process_data(path):
    # used in error and FPS calculation
    error = 0
    timeaccu = 0
    # open duty cycles file
    with open(path+"DutyCycleData.csv", 'rt') as csvfile:
        reader = csv.reader(csvfile)
        timestamps = next(reader)
        dutyCycleTimeStamps = [datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S.%f") for time in timestamps]
        steeringDutyCycles = next(reader)
        accelerationDutyCycles = next(reader)

    # open image file
    with open(path+"ImageCountData.csv", 'rt') as csvfile:
        reader = csv.reader(csvfile)
        timestamps = next(reader)
        imageTimeStamps = [datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S.%f") for time in timestamps]
        images = next(reader)

    # Process data and write to ProcessData.csv
    with open(path + "ProcessData.csv", 'w',newline = '') as output:
        writer = csv.writer(output)
        # for each image, find closest duty cycls
        for i in range(len(images)):

            currentTime = imageTimeStamps[i]
            # accumulate FPS
            if (i+1 < len(images)):
                deltatime = imageTimeStamps[i+1]-currentTime
                timeaccu = timeaccu + float(deltatime.microseconds)/1000000

            # find closest duty cycle index
            diff = [abs(timestamp - currentTime) for timestamp in dutyCycleTimeStamps]
            index, min_value = min(enumerate(diff), key=operator.itemgetter(1))

            # PATH TO IMAGE | STEEERING DC | ACCELERATION DC | ERROR
            col1 = "frame" + images[i] + ".jpg"
            col2 = steeringDutyCycles[index]
            col3 = accelerationDutyCycles[index]
            col4 = float(min_value.microseconds)/1000000

            # accumulate error
            error = error + col4

            # write to csv
            row = [col1,col2,col3,col4]
            writer.writerow(row)

    # print results
    print('Average error: ')
    print(error/len(images))
    print('Average FPS: ')
    print(1/(timeaccu/(len(images)-1)))

# laneDetection()
# Allows user to test lane detection algorithm. Load validation data set using paths defined in imageprocess.py
# perform lane detection and display image processing pipeline
def laneDetection():
    images = imageprocess.load_validation_images()
    #output = imageprocess.read_validation_output_data()
    for image in images:
        cv2.imshow('Original', image)
        image = image * 255
        image=image.astype(np.uint8)
        # convert to gray
        gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
        # mask out all but white
        mask_white = cv2.inRange(gray, 240, 255)
        # filter noise from canny edge
        gauss_gray = cv2.GaussianBlur(mask_white,(25,25),0)
        cv2.imshow('Mask white/Gauss filter ', gauss_gray)
        # apply canny edge
        low_threshold = 50
        high_threshold = 125
        canny_edges = cv2.Canny(gauss_gray,low_threshold,high_threshold)
        cv2.imshow('Edge detection', canny_edges)
        cv2.imshow('Lines', canny_edges)
        #cv2.waitKey(1)
        # mask region of interest
        mask = np.zeros((66,200), np.uint8)
        pts = np.array([[0,20],[0,40],[60,40],[60,20]])
        cv2.drawContours(mask, np.int32([pts]),0, 255, -1)
        pts = np.array([[199,20],[199,40],[139,40],[139,20]])
        cv2.drawContours(mask, np.int32([pts]),0, 255, -1)
        # hough line transform
        canny_edges = cv2.bitwise_or(canny_edges, canny_edges, mask=mask)
        cv2.imshow('ROI', canny_edges)
        leftSide = canny_edges[20:40,0:60].copy()
        rightSide = canny_edges[20:40,139:199].copy()
        #skel = skeleton(canny_edges)
        linesLeft = cv2.HoughLines(leftSide,3,np.pi/180,23)
        linesRight = cv2.HoughLines(rightSide,3,np.pi/180,23)
        if (linesRight is not None and linesLeft is not None):
            print("We are straight")
        elif (linesRight is None and linesLeft is not None):
            print("Turn right")
        elif (linesLeft is None and linesRight is not None):
            print("Turn left")
        else:
            print("STOP")
        cv2.imshow('Lines', rightSide)
        cv2.imshow('Lines2',leftSide)
        cv2.waitKey(0)

# findBlurrinessThreshold()
# Systematically blurs image to find a threshold in which to reduce speed if given a blurry image
# Parameters:
#   errorThresh => error to find threshold
def findBlurThreshold(errorThresh):

    images = imageprocess.load_validation_images()
    output = imageprocess.read_validation_output_data()

     #LOAD CNN
    sess = tf.InteractiveSession()
    saver = tf.train.Saver()
    model_name = 'test.ckpt'
    save_dir = os.path.abspath('/home/ubuntu/car/trial0809')
    model_path = join(save_dir, model_name)
    saver.restore(sess, model_path)

    count = 0
    laplacians = []
    sizes = []
    for image in images:
        data = []
        img = image.copy()
        image = image * 255
        image=image.astype(np.uint8)
        steer = model.y.eval(feed_dict={model.x: [img]})[0][0]
        steeringoriginal = denormalization(steer)
        steering = steeringoriginal
        out = denormalization(output[count][0])
        fm =  0
        add = False
        sizeOfBlurKernel = 3
        while (abs(steering - out) < errorThresh):
            add = True
            kernel_motion_blur = np.zeros((sizeOfBlurKernel, sizeOfBlurKernel))
            kernel_motion_blur[:,int((sizeOfBlurKernel-1)/2)] = np.ones(sizeOfBlurKernel)
            kernel_motion_blur = kernel_motion_blur / 1
            blurred = cv2.filter2D(image, -1, kernel_motion_blur)
            gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
            fm = cv2.Laplacian(gray,cv2.CV_32F).var()
            sizeOfBlurKernel = sizeOfBlurKernel + 2
            #image = blurred
            if (sizeOfBlurKernel > 20):
                add = False
                break
            blurryCopy = blurred.copy()
            img = preprocess(blurred)
            image = blurryCopy
            steer = model.y.eval(feed_dict={model.x: [img]})[0][0]
            steering = denormalization(steer)
        if (add):
            data.append(fm)
            data.append(sizeOfBlurKernel)
            data.append(count)
            data.append(out)
            data.append(steeringoriginal)
            data.append(steering)
            writer = csv.writer(csvfile)
            writer.writerow(data)
    count = count+1
    csvfile.close()

if __name__ == '__main__':
    # path to data collection folder
    path = "/home/scope/Shreyas/Car/TF/0310/TrialNN3/"
    process_data(path)
    # errorThresh = 2
    #findBlurrinessThreshold(errorThresh)
    #laneDetection()

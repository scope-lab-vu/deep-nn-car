# SafetyManager.py
# author: Matthew P. Burruss
# last update: 02/25/2019
# Description
# Defines functions to evaluate the lanedetection and assigns discreet steering values


import cv2
import numpy as np
import os
import math
import numpy as np
import time
import psutil
import zmq

# laneDetect()
# Description: process image to determine if off track
# parameters:  image => image matrix
# returnVal    -1 => no track found
#              0  => track found
def laneDetect(image):
        # mask out all but white
        # filter noise from canny edge
        gauss_gray = cv2.GaussianBlur(image,(5,5),0)
        mask_white = cv2.inRange(gauss_gray, 215, 255)
        # apply canny edge
        low_threshold = 50
        high_threshold = 125
        canny_edges = cv2.Canny(mask_white,low_threshold,high_threshold)
        # mask region of interest
        mask = np.zeros((66,200), np.uint8)
        pts = np.array([[0,30],[0,60],[60,60],[60,30]])
        cv2.drawContours(mask, np.int32([pts]),0, 255, -1)
        pts = np.array([[199,30],[199,60],[139,60],[139,30]])
        cv2.drawContours(mask, np.int32([pts]),0, 255, -1)
        # hough line transform
        canny_edges = cv2.bitwise_or(canny_edges, canny_edges, mask=mask)
        leftSide = canny_edges[30:60,0:60].copy()
        rightSide = canny_edges[30:60,139:199].copy()
        linesLeft = cv2.HoughLines(leftSide,3,np.pi/180,23)
        linesRight = cv2.HoughLines(rightSide,3,np.pi/180,23)
        if (linesRight is not None and linesLeft is not None):
            #print('Straight')
            return 3
        elif (linesRight is None and linesLeft is not None):
            #print('Turning Right')
            return 2
        elif (linesLeft is None and linesRight is not None):
            #print('Turning Left')
            return 1
        else:
            #print('Stop')
            return -1

# measureBlurrienss()
# Description: returns blurriness measurement (variance of laplacian)
# parameters:  frame => image matrix
# returnVal    higher value indicates less blurry image
def measureBlurriness(frame):
    gauss_gray = cv2.GaussianBlur(frame,(3,3),0)
    fm = cv2.Laplacian(gauss_gray,cv2.CV_64F).var()
    return fm

# run()
# Description: Returns the results from the Safety manager
# parameters: frame => image matrix
# returnVal: lane detection result, image blurriness, previous prediction cycle time
def runSafetyManager(frame,mysocket):
    blur = measureBlurriness(frame)
    lanedetection = laneDetect(frame)
    #Discrete steering calculation from lanedetection values
    if (lanedetection == 3):
        steeringSS = 15
    elif(lanedetection == 2):
        steeringSS = 20
    elif(lanedetection == 1):
        steeringSS = 10
    else:
        steeringSS = 0

    return lanedetection,blur,steeringSS

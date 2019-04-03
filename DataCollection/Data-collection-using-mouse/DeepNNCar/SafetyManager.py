from threading import Thread, Lock
import threading
import cv2
import numpy as np
import csv
import time
import sys
import os
class SafetyManager():

    def __init__(self,lanedetect = False, blurrinessMeasurement = False, offloadTasks = False):
        self.laneDetect = lanedetect
        self.blurrinessMeasurement = blurrinessMeasurement
        self.offloadTasks = offloadTasks

    def runImageAnalysis(self,image,temp):
        self.ldResult = self.bmResult = -1
        if (self.laneDetect):
            ld = Thread(target = self.performLaneDetection, args = (image.copy(),))
            ld.start()
        if (self.blurrinessMeasurement):
            bm = Thread(target = self.performBlurrinessMeasurement, args = (image,))
            bm.start()
        #################################################################################3 Add offload task here
        if (temp > 50 and self.offloadTasks):
            print("Temp %0.2f: Would offload" %temp)
        ######################################################################
        if (self.laneDetect): ld.join()
        if (self.blurrinessMeasurement): bm.join()
        return self.ldResult,self.bmResult

    def performLaneDetection(self,image):
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
        #skel = skeleton(canny_edges)
        linesLeft = cv2.HoughLines(leftSide,3,np.pi/180,23)
        linesRight = cv2.HoughLines(rightSide,3,np.pi/180,23)
        if (linesRight is not None and linesLeft is not None):
            # print('Straight')
            self.ldResult = 15
        elif (linesRight is None and linesLeft is not None):
            #  print('Turning Right')
            self.ldResult =  20
        elif (linesLeft is None and linesRight is not None):
            #  print('Turning Left')
            self.ldResult = 10
        else:
            #print('Stop')
            self.ldResult = 0

    def performBlurrinessMeasurement(self,frame):
        # apply gaussian blur
        gauss_gray = cv2.GaussianBlur(frame,(3,3),0)
        # find variance of the Laplacian (2nd derivative of intensities of pixels)
        fm = cv2.Laplacian(gauss_gray,cv2.CV_64F).var()
        self.bmResult = fm
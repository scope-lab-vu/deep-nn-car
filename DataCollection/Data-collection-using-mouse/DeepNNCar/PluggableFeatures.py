# PluggableFeatures.py
# author: Matthew P. Burruss
# last update: 2/15/2019
# Features that can configured by the client to provide additional feedback

import math
import sys
import logging
import time
import cv2
import numpy as np
#import psutil
from threading import Thread, Lock
class PathTracker:
    def __init__(self):
        self.x = 0.0 # x coordinate
        self.y = 0.0 # y coordinate
        self.heading = 0.0 # heading
        self.totalDistanceCovered = 0.0 # total distance covered
        self.t1 = -1 # time when previous new velocity detected
        self.v1 = 0 # initial velocity
        self.deltaT = 0.03 # timestep between t2 and t1
        self.deltaTs = []
        self.timeSinceLastThetaAdded = 0
        self.thetas = [] # array of theta values indicating steering angle
        self.myMutex = Lock()
    def updatePositionAndHeading(self,deltaX,deltaTheta):
        if (deltaX>0.0):
            self.totalDistanceCovered = deltaX + self.totalDistanceCovered
            self.heading = self.heading + deltaTheta
            self.heading = self.heading%360
            headingInRadians = math.radians(self.heading) # converts degrees to radians
            self.x = self.x + deltaX*math.cos(headingInRadians)
            self.y = self.y + deltaX*math.sin(headingInRadians)
    def estimator(self,v2):
        t2 = time.time()
        # find t2-t1
        time_difference = float(t2-self.t1)
        self.t1 = t2
        # find n and assert length
        n = len(self.thetas)
        m = len(self.deltaTs)
        if (n != len(self.deltaTs)+1): print("Error: This message should not appear.\n")
        # find total distance covered using middle estimator
        #displacement = float((v2+self.v1)/2.0)*time_difference
        displacement = v2*time_difference
        # allocate distance to thetas[n-1]
        for i in range(len(self.deltaTs)):
            dt = self.deltaTs[i]
            dx = dt/time_difference*displacement
            deltaTheta = self.thetas[i]*dt
            self.updatePositionAndHeading(dx,deltaTheta)
        lastTheta = self.thetas[-1]
        self.thetas = []
        self.deltaTs = []
        self.thetas.append(lastTheta)
        self.timeSinceLastThetaAdded = time.time()
        self.v1 = v2

    def updateMe(self,speed,steering):
        if (speed != -1):
            self.addTheta(steering)
            self.estimator(speed)
            #self.printLocation()
        else:
            self.addTheta(steering)

    def printLocation(self):
        print("X: %0.2f\nY: %0.2f\nHeading: %0.2f\nTotal Distance: %0.2f" %(self.x, self.y,self.heading,self.totalDistanceCovered))

    def setTimestep(self,timestep):
        self.deltaT = timestep
    
    # returns current x and y position
    def addTheta(self,steer):
        # convert duty cycle to degrees of steering
        normalized = (steer - 10.0)/(20.0-10.0)
        # let dc = 20 be a -30 degree turn and dc = 10 a 30 degree turn
        normalized = 1 - normalized
        theta = normalized*(30.0+30.0) - 30.0
        self.myMutex.acquire()
        if (self.t1 == -1):
            self.t1 = time.time()
            self.v1 = 0
            self.thetas.append(theta)
            self.timeSinceLastThetaAdded = time.time()
            self.myMutex.release()
            return self.x,self.y,self.totalDistanceCovered,self.heading
        dt = time.time() - self.timeSinceLastThetaAdded
        if (dt > self.deltaT):
            self.thetas.append(theta)
            self.timeSinceLastThetaAdded = time.time()
            self.deltaTs.append(dt)
        self.myMutex.release()
        return self.x,self.y,self.totalDistanceCovered,self.heading

# PID.py
# author: Matthew P. Burruss
# last update: 2/16/2019
class PID:
    def __init__(self,setSpeed = 0.1, maxSpeed = 1.0,maxThrottle = 16.2):
        if (setSpeed > maxSpeed):
            print("Set speed cannot exceed maxSpeed of %0.2f" %maxSpeed)
            setSpeed = maxSpeed
        self.setSpeed = setSpeed # m/s
        self.maxSetSpeed = maxSpeed
        self.maxThrottle = maxThrottle
        self.KP = 0.013
        self.KI = 0.0001
        self.KD = 0.0002
        self.error = 0
        self.prevError = 0 
        self.accumError = 0
        self.acc = 15.8

    def update(self,speed,acc):
        self.prevError = self.error
        self.error = self.setSpeed - speed
        self.accumError = self.accumError + self.error
        deriv = self.error - self.prevError
        pid = self.KP*self.error + self.KI*self.accumError + self.KD*deriv
        self.acc = acc + pid
        if (self.acc > self.maxThrottle):
            self.acc = self.maxThrottle
    def getAcceleration(self):
        return self.acc

    def changeSetSpeed(self,newSpeed):
        if (newSpeed <= self.maxSetSpeed):
            self.setSpeed = newSpeed
        else:
            print("ERROR: Set speed must be less than max speed.\n")
            self.setSpeed = self.maxSetSpeed
    def changeMaxSpeed(self,newMaxSpeed):
        self.maxSetSpeed = newMaxSpeed

def laneDetect(image):
    # mask out all but white
    # filter noise from canny edge
    gauss_gray = cv2.GaussianBlur(image,(5,5),0)
    mask_white = cv2.inRange(gauss_gray, 215, 255)
    #cv2.imshow('Mask white/Gauss filter ', mask_white)
    
    # apply canny edge
    low_threshold = 50
    high_threshold = 125
    canny_edges = cv2.Canny(mask_white,low_threshold,high_threshold)
    #cv2.imshow('Edge detection', canny_edges)
    # mask region of interest 
    mask = np.zeros((66,200), np.uint8)
    pts = np.array([[0,30],[0,60],[60,60],[60,30]])
    cv2.drawContours(mask, np.int32([pts]),0, 255, -1)
    pts = np.array([[199,30],[199,60],[139,60],[139,30]])
    cv2.drawContours(mask, np.int32([pts]),0, 255, -1)
    # hough line transform
    canny_edges = cv2.bitwise_or(canny_edges, canny_edges, mask=mask)
    # cv2.imshow('ROI', canny_edges)
    leftSide = canny_edges[30:60,0:60].copy()
    rightSide = canny_edges[30:60,139:199].copy()
    # cv2.imshow('ROI Left',leftSide)
    # cv2.imshow('ROI Right',rightSide)
    # cv2.waitKey(0)
    #skel = skeleton(canny_edges)
    linesLeft = cv2.HoughLines(leftSide,3,np.pi/180,23)
    linesRight = cv2.HoughLines(rightSide,3,np.pi/180,23)
    if (linesRight is not None and linesLeft is not None):
        # print('Straight')
        return 3
    elif (linesRight is None and linesLeft is not None):
        #  print('Turning Right')
        return 2
    elif (linesLeft is None and linesRight is not None):
        #  print('Turning Left')
        return 1
    else:
        #print('Stop')
        return -1
# Controller.py
# author: Matthew P. Burruss
# last update: 2/15/2019

import zmq as zmq
import ctypes
import logging
import math
import signal
import sys
import threading
import time
from threading import Thread,Lock
from HelperFunctions import sendToGoogleDrive,displayTitle,selectOperationMode,selectAccelerationProtocol,configureAutonomousMode,configureConstantDC,configureConstantDC,configureFeedback,configureDataCollection,configureCruiseControl
#import psutil
import cv2
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from CommunicationProtocol import CommunicationProtocol
import csv
import os
from pynput import mouse

class DeepNNCarController:
    def on_move(self,x,y):
        self.mouse_pos = { "x": x, "y": y}
    def __init__(self,IP,Port,maxForwardRange):
        self.idle = [15,15]
        self.maxForwardRange = maxForwardRange
        context = zmq.Context()
        print("Connecting to DeepNNCar...")
        self.steering = 15
        self.sock = context.socket(zmq.REQ)
        self.sock.connect("tcp://%s:%s" %(IP,Port))
        self.deepNNCarIP = IP
        # initialize screen types

        listener = mouse.Listener(
            on_move = self.on_move
        )
        self.mouse_pos = { "x": 0.0, "y": 0.0}
        listener.start()
        self.maxXPos = 1919
        self.maxYPos = 1079
        self.minXPos = 0.0
        self.minYPos = 0.0
        # initialize helper classes
        self.messageDecoder = CommunicationProtocol()
        # lists holding relative location of car from where it started
        self.lx = []
        self.ly = []
        # initialize feedback info
        self.speed = 0
        self.displacement = 0.0
        self.heading = 0.0
        self.steeringAngle = 0
        self.accelerationDutyCycle = 15
        self.temp = 0.0
        self.cpuUtil = 0.0
        signal.signal(signal.SIGINT, self.signal_handler) # looks for control-c
    def start(self):
        # begin communication thread
        print("Starting communication thread")
        self.deepNNCarCommunicationThread = Thread(target = self.communicationThread)
        self.deepNNCarCommunicationThread.daemon = True
        self.terminate = False
        self.deepNNCarCommunicationThread.start()
        # start thread to display animated graph if pathTracker enabled
        if (self.speedSensorEnabled and self.pathTrackerEnabled):
            self.graphThread = Thread(target = self.animateGraph)
            self.graphThread.daemon = True
            self.graphThread.start()
        if (self.operationMode == "LIVESTREAM"):
            self.liveStreamThread = Thread(target = self.liveStream)
            self.liveStreamThread.daemon = True
            self.liveStreamThread.start()

    def liveStream(self):
        context = zmq.Context()
        print("Connecting to DeepNNCar livestream...")
        sock = context.socket(zmq.REQ)
        sock.connect("tcp://%s:%s" %(self.deepNNCarIP,"5002"))
        while 1:
            message = "1"
            sock.send(message.encode())
            data = sock.recv()
            #data = data.decode()
            nparr = np.fromstring(data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            #print(frame.shape)
            frame_resized = cv2.resize(frame, (200, 66))
            gray = cv2.cvtColor(frame_resized,cv2.COLOR_BGR2GRAY)
            self.performLaneDetection(gray)
            cv2.imshow('Live Feed',frame)
            cv2.waitKey(33)
        
    
    def performLaneDetection(self,image):
        # mask out all but white
        # filter noise from canny edge
        #gauss_gray = cv2.GaussianBlur(image,(9,9),0)
        #cv2.imshow('Blur',gauss_gray)
        #mask_not_white = cv2.inRange(gauss_gray, 215, 255)
        #mask_not_white = cv2.inRange(image, 0, 15)
        image=cv2.bitwise_not(image)
        #cv2.imshow('Invert',image)
        #image = cv2.GaussianBlur(image,(9,9),0)
        mask_not_white = cv2.inRange(image, 175, 255)
        #cv2.imshow('Mask',mask_not_white)
        # apply canny edge
        low_threshold = 50
        high_threshold = 125
        canny_edges = cv2.Canny(mask_not_white,low_threshold,high_threshold)
        #cv2.imshow('Mask White',canny_edges)
        # mask region of interest 
        mask = np.zeros((66,200), np.uint8)
        pts = np.array([[0,30],[0,60],[60,60],[60,30]])
        cv2.drawContours(mask, np.int32([pts]),0, 255, -1)
        pts = np.array([[199,30],[199,60],[139,60],[139,30]])
        cv2.drawContours(mask, np.int32([pts]),0, 255, -1)
        # hough line transform
        canny_edges = cv2.bitwise_or(canny_edges, canny_edges, mask=mask)
        leftSide = canny_edges[30:60,0:60].copy()
        cv2.imshow('Left',leftSide)
        rightSide = canny_edges[30:60,139:199].copy()
        cv2.imshow('Right',rightSide)
        #skel = skeleton(canny_edges)
        #left = np.where(leftSide == [255])
        #right = np.where(rightSide == [255])
        
        linesLeft = cv2.HoughLines(leftSide,3,np.pi/180,23)
        linesRight = cv2.HoughLines(rightSide,3,np.pi/180,23)
        if (linesRight is not None and linesLeft is not None):
            print("straight")
            #return 15
            #ldResult = 15
        elif (linesRight is None and linesLeft is not None):
            print('Turning Right')
            #return 20
            #self.ldResult =  20
        elif (linesLeft is None and linesRight is not None):
            print('Turning Left')
            #return 10
            #self.ldResult = 10
        else:
            print('Stop')
            #return 15
            #self.ldResult = 0
        """
        if (len(right[0]) != 0 and len(left[0]) != 0):
            #print("straight")
            self.steering =  15
            #ldResult = 15
        elif (len(right[0]) == 0 and len(left[0]) != 0):
            #print('Turning Right')
            self.steering = 20
            #self.ldResult =  20
        elif (len(left[0]) == 0 and len(right[0]) != 0):
            #print('Turning Left')
            self.steering = 10
            #return 10
            #self.ldResult = 10
        else:
            print('Stop')
            self.steering = 15
            #return 15
            #self.ldResult = 0
        """
    def selectCapabilities(self, operationMode,operationModeFeatures,accMode,accModeFeatures,tempEnabled,pathTrackingEnabled,speedSensorEnabled,cpuUtilEnabled):
        self.speedSensorEnabled = speedSensorEnabled # true or false
        self.pathTrackerEnabled = pathTrackingEnabled # true or false
        self.tempTrackingEnabled = tempEnabled
        self.cpuTrackingEnabled = cpuUtilEnabled
        self.accelerationMode = accMode # CRUISE or CONSTANT or USER
        self.operationMode = operationMode # either NORMAL,DATACOLLECTION,AUTONOMOUS,LIVESTREAM
        # send message telling DeepNNCar what to do
        initialized = False
        while (not initialized):
            message = "TYPE=CONFIGURATION;"
            message += "SPEEDSENSOR="+str(speedSensorEnabled)
            message += ";PATHTRACKER="+str(pathTrackingEnabled)
            message += ";TEMPTRACKER="+str(tempEnabled)
            message += ";CPUTRACKER=" + str(cpuUtilEnabled)
            message += ";ACCMODE=" + accMode
            message += ";MODE=" + operationMode
            message += ";NUMOPERATIONMODEFEATURE=" + str(len(operationModeFeatures))
            i = 0
            for feature in operationModeFeatures:
                message += ";OPERATIONMODEFEATURE" + str(i) + "=" + str(feature)
                i=i+1
            message += ";ACCMODEFEATURES=" + str(accModeFeatures)
            self.sock.send(message.encode())
            message = self.sock.recv()
            self.messageDecoder.decodeMessage(message.decode())
            status = self.messageDecoder.getStatus()
            if (status == "CONFIGURED"): initialized = True
        # show data
        print("Configuration complete")
    
    def printStatistics(self):
        print("DEEPNNCAR STATS")
        if (self.speedSensorEnabled):
            print("SPEED: %0.2f" %self.speed)
            if (self.pathTrackerEnabled):
                print("DISPLACEMENT: %0.2f" %self.displacement)
                print("HEADING: %0.2f" %self.heading)
            else:
                print("PATHTRACKER: DISABLED")
        else:
            print("SPEEDSENSOR: DISABLED")
            print("PATHTRACKER: DISABLED")
        if (self.cpuTrackingEnabled):
            print("CPUTRACKER: %0.2f" %self.cpuUtil)
        else:
            print("CPUTRACKER: DISABLED")
        if (self.tempTrackingEnabled):
            print("TEMPTRACKER: %0.2f" %self.temp)
        else:
            print("TEMPTRACKER: DISABLED")
        print("\n")
    
    # return filename of csv file of trial
    def handleDataCollection(self,numberOfTrials):
        trialTimes = []
        trialAcc = []
        trialSteer = []
        time = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')[:-3]
        fileName = "Data" + time + ".csv"
        csvfile = open(fileName, "w")
        writer=csv.writer(csvfile)
        writer.writerow([numberOfTrials])
        for i in range(numberOfTrials):
            print("Received sample: %d" %i)
            message = "READY"
            self.sock.send(message.encode())
            image_encoded = self.sock.recv()
            frame = np.fromstring(image_encoded, np.uint8)
            frame = np.resize(frame,(240,320,3))
            frame = cv2.resize(frame, (200, 66))
            frame = np.reshape(frame,(3,13200)) # maximum excel sheet is 16384 columns and 1,048,576 rows
            frame_as_list = frame.tolist()
            writer.writerows(frame_as_list)
            self.sock.send(message.encode())
            response = self.sock.recv()
            self.messageDecoder.decodeMessage(response.decode())
            timestamp = self.messageDecoder.getTimestamp()
            acc,steer = self.messageDecoder.getControl()
            trialTimes.append(timestamp)
            trialAcc.append(acc)
            trialSteer.append(steer)
        writer.writerow(trialTimes)
        writer.writerow(trialAcc)
        writer.writerow(trialSteer)
        filePath = os.path.realpath(csvfile.name)
        csvfile.close()
        return fileName,filePath

    def communicationThread(self):
        stopped = False
        stopSignalSent = False
        while not stopped:
            steering,acceleration = self.mousePosToDutyCycle()
            #steering = self.steering
            if (not self.terminate):
                message = "STEERING="+str(steering)+";ACCELERATION="+str(acceleration)
                message += ";STOP=FALSE"
            else:
                message = "STEERING=15;ACCELERATION=15"
                message += ";STOP=TRUE"
                stopSignalSent = True
            self.sock.send(message.encode())
            response = self.sock.recv()
            self.messageDecoder.decodeMessage(response.decode())
            status = self.messageDecoder.getStatus()
            if (status == "COLLECTIONDONE"): ## collect data
                numberOfTrials = self.messageDecoder.getTrialNumber()
                filename,filepath = self.handleDataCollection(numberOfTrials)
                sendToGoogleDrive(filename,filepath)
                print("Saved to googled drive.")
                continue
            if (self.speedSensorEnabled): 
                self.speed = float(self.messageDecoder.getSpeed())
                if (self.pathTrackerEnabled):
                    x,y = self.messageDecoder.getPositionCoordinates()
                    self.displacement = round(float(self.messageDecoder.getDisplacement()),2)
                    self.heading = round(float(self.messageDecoder.getHeading()),2)
                    self.lx.append(x)
                    self.ly.append(y)
            if (self.tempTrackingEnabled):
                self.temp = self.messageDecoder.getTemperature()
            if (self.cpuTrackingEnabled):
                self.cpuUtil = self.messageDecoder.getCPUUtilization()
            if (stopSignalSent):
                stopped = True
            time.sleep(0.03)


    def mousePosToDutyCycle(self):
        # flip y
        y_flipped = self.maxYPos - self.mouse_pos['y']
        normX = (self.mouse_pos['x']-self.minXPos)/(self.maxXPos-self.minXPos)
        normY = (y_flipped - self.minYPos)/(self.maxYPos-self.minYPos)
        # denormalize to steering
        steering = round((20-10)*normX + 10,2)
        # set bounds
        if (steering > 20): steering = 20
        if (steering < 10): steering = 10
        acceleration = round(self.maxForwardRange*normY + self.idle[1],2)
        return steering,acceleration

    def getLocation(self):
        return self.lx,self.ly

    def animateGraph(self):
        global fig
        fig = plt.figure()
        ax1 = fig.add_subplot(1,1,1)
        # animate()
        # Description: Every 200 ms, get speed, steering angle, and displacement estimate and update dynamic graph
        def animate(i):
            lx,ly = self.getLocation()
            try:
                ax1.clear()
                ax1.plot(lx,ly)
                ax1.set_title("2D position estimate")
                ax1.set_ylabel(" Y displacement (m)")
                ax1.set_xlabel(" X displacement (m)")
            except:
                print('s')
        plt.grid(True)
        plt.subplots_adjust(hspace = 1,wspace = 0.6)
        ani = animation.FuncAnimation(fig, animate, interval=200)
        plt.show()

    def signal_handler(self,sig, frame):
        print('Stopping DeepNNCar...')
        self.terminate=True
        while(self.deepNNCarCommunicationThread.is_alive()):
            pass
        print("Terminating")
        sys.exit(0)
        print("Terminated DEEPNNCar")

    def configure(self):
        displayTitle()
        operationMode = selectOperationMode()
        operationModeFeatues = (None,)
        if (operationMode == "AUTO"):
            operationModeFeatues = configureAutonomousMode()
        elif (operationMode == "DATACOLLECTION"):
            operationModeFeatues = configureDataCollection()
        accMode = selectAccelerationProtocol()
        accModeFeatures = None
        if (accMode == "CRUISE"):
            accModeFeatures = configureCruiseControl()
        elif(accMode == "CONSTANT"):
            accModeFeatures = configureConstantDC()
        tempEnabled,pathTrackingEnabled,speedSensorEnabled,cpuUtilEnabled = configureFeedback()
        return (operationMode,operationModeFeatues,accMode,accModeFeatures,tempEnabled,pathTrackingEnabled,speedSensorEnabled,cpuUtilEnabled)
        
    def __del__(self):
        self.sock.close() # clean up socket


if __name__=="__main__":
    controller = DeepNNCarController(IP = "10.66.233.62",Port = "5001", maxForwardRange = 1)
    config = controller.configure()
    controller.selectCapabilities(config[0],config[1],config[2],config[3],config[4],config[5],config[6],config[7])
    controller.start()
    updateIn = 5 # seconds
    delay = time.time() + updateIn
    while (True):
        curTime = time.time()
        if (curTime > delay):
            controller.printStatistics()
            delay = time.time() + updateIn

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
from ctypes import Structure, byref, c_long, windll
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

class POINT(Structure):
    _fields_ = [("x", c_long), ("y", c_long)]

class DeepNNCarController:
    def __init__(self,IP,Port,maxForwardRange):
        self.idle = [15,15]
        self.maxForwardRange = maxForwardRange
        context = zmq.Context()
        print("Connecting to DeepNNCar...")
        self.sock = context.socket(zmq.REQ)
        self.sock.connect("tcp://%s:%s" %(IP,Port))
        self.deepNNCarIP = IP
        # initialize screen types
        user32 = ctypes.windll.user32
        self.maxXPos = float(user32.GetSystemMetrics(0))
        self.maxYPos = float(user32.GetSystemMetrics(1))
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
            cv2.imshow('Live Feed',frame)
            cv2.waitKey(33)
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
        csvfile = open(fileName, "wb")
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

    def queryMousePosition(self):
        pt = POINT()
        windll.user32.GetCursorPos(byref(pt))
        return { "x": pt.x, "y": pt.y}

    def mousePosToDutyCycle(self):
        pos = self.queryMousePosition()
        # flip y
        pos['y'] = self.maxYPos - pos['y']
        normX = (pos['x']-self.minXPos)/(self.maxXPos-self.minXPos)
        normY = (pos['y'] - self.minYPos)/(self.maxYPos-self.minYPos)
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
    controller = DeepNNCarController(IP = "10.66.234.14",Port = "5001", maxForwardRange = 1)
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

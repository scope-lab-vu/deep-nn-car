# DeepNNCar.py
# author: Matthew P. Burruss
# last update: 2/15/2019

#import tensorflow as tf
import zmq as zmq
import numpy as np
from datetime import datetime
import time
from threading import Thread, Lock
import threading
from ast import literal_eval as make_tuple
import math
import cv2
import csv
import psutil
import sys
import logging
from queue import Queue
from CommunicationProtocol import CommunicationProtocol
from Peripherals import PWM,SpeedSensor,Camera,SystemMonitor
from SafetyManager import SafetyManager
from PluggableFeatures import PathTracker,PID
import os
import tensorflow as tf

class DeepNNCar:
    def __init__(self,port):
        context = zmq.Context()
        self.sock = context.socket(zmq.REP)
        self.sock.bind("tcp://*:%s" % port)
        print('starting up on port %s' % port)
        # initialize helper classes
        self.pwm = PWM()
        self.messageDecoder = CommunicationProtocol()
        self.camera = Camera()
        # initialize acceleration and steering duty cycles
        self.steering = 15
        self.acceleration = 0
        self.terminateMainThread = False
        self.mutex = Lock()
        self.temp = 0
        self.cpuUsage = 0
    def configure(self):
        # obtain configurations
        configured = False
        # receive configuration message
        while (not configured):
            message = self.sock.recv()
            self.messageDecoder.decodeMessage(message.decode())
            type = self.messageDecoder.getType()
            if (type == "CONFIGURATION"): configured = True
        # get mode
        self.modeOfOperation = self.messageDecoder.getMode() # either AUTO,DATACOLLECT,LIVESTREAM, or NORMAL
        modeFeatures = self.messageDecoder.getOperationModeFeatures()
        self.laneDetectionEnabled = self.offloadingTasksEnabled = self.blurrinessMeasurementEnabled = False
        if (self.modeOfOperation == "AUTO"):
            if (modeFeatures[0] == "True"):
                self.laneDetectionEnabled = True
                print("Lane detection enabled")
            else:
                self.laneDetectionEnabled = False
                print("Lane detection disabled")
            if (modeFeatures[1] == "True"):
                self.offloadingTasksEnabled = True
                print("Offloading tasks enabled")
            else:
                self.offloadingTasksEnabled = False
                print("Offloading tasks disabled")
            if (modeFeatures[2] == "True"):
                self.blurrinessMeasurementEnabled = True
                print("Blurriness measurement enabled")
            else:
                self.blurrinessMeasurementEnabled = False
                print("Blurriness measurement disabled")
        elif (self.modeOfOperation == "DATACOLLECTION"):
            count = self.numberOfTrials = 0
            for i in modeFeatures:
                self.numberOfTrials = self.numberOfTrials + int(i)*10**(len(modeFeatures)-1-count)
                count = count + 1
            print(self.numberOfTrials)
            self.numberOfTrials = int(self.numberOfTrials)
            print("Configured to collect %d trials" %self.numberOfTrials)
        # set booleans
        self.temperatureTrackerEnabled = self.messageDecoder.isTempTrackerEnabled()
        if (self.temperatureTrackerEnabled or self.offloadingTasksEnabled): print("Temperature tracking enabled")
        self.speedSensorEnabled = self.messageDecoder.isSpeedSensorEnabled()
        if (self.speedSensorEnabled): print("Speed sensor enabled")
        self.pathTrackerEnabled = self.messageDecoder.isPathTrackerEnabled()
        if (self.pathTrackerEnabled): print("Path tracking enabled")
        self.CPUTrackerEnabled = self.messageDecoder.isCPUTrackerEnabled()
        if (self.CPUTrackerEnabled): print("CPU tracking enabled")
        # create system monitor
        self.systemMonitor = SystemMonitor(2,self.CPUTrackerEnabled,(self.temperatureTrackerEnabled or self.offloadingTasksEnabled))
        # select acceleration protocol
        self.accelerationMode = self.messageDecoder.getAccelerationMode()
        features = self.messageDecoder.getAccelerationFeatures()
        if (self.accelerationMode == "CRUISE"):
            setSpeed = float(features)
            self.PID_Controller = PID(setSpeed=setSpeed)
        elif (self.accelerationMode == "CONSTANT"):
            self.acceleration = float(features)
        # update configurations
        if (self.speedSensorEnabled):
            self.speedSensor = SpeedSensor()
            self.DeepNNCarspeed = 0
            if (self.pathTrackerEnabled):
                self.pathTracker = PathTracker()
        elif (self.pathTrackerEnabled):
            print("Speed sensor must be enabled for path tracking to work.\n")
            self.pathTrackerEnabled = False
        message = "STATUS=CONFIGURED"
        # respond to client. Because this UDP, it is not guaranteed, but this is ok
        self.sock.send(message.encode())
        # initialize engine
        delay = time.time()+0.5
        self.pwm.changeDutyCycle(15,15)
        while(time.time()<delay):
            pass
        print("CONFIGURED")

    # terminate
    def collectData(self):
        count = 0
        frames = []
        timestamps = []
        accelerations = []
        steerings = []
        print("Starting to collect data")
        while (count < self.numberOfTrials):
            # capture image and timestamp
            frame = self.camera.captureImage()
            frames.append(frame)
            if (count % 5 == 0):
                print(count)
            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            timestamps.append(timestamp)
            # get acceleration and steering values
            accelerations.append(str(self.acceleration))
            steerings.append(str(self.steering))
            count = count + 1
        self.pwm.changeDutyCycle(15.0,15.0)
        print("Completed data collection of %d samples\n" %self.numberOfTrials)
        self.mutex.acquire()
        self.sock.recv() # ignore message
        message = "STATUS=COLLECTIONDONE;TRIALS="+str(self.numberOfTrials)
        self.sock.send(message.encode())
        # send frames
        for i in range(self.numberOfTrials):
            self.sock.recv()
            frame = np.array(frames[i])
            image_data = frame.tostring()
            self.sock.send(image_data)
            self.sock.recv()
            time = ("TIME="+timestamps[i])
            time = time.encode()
            acc = (";ACCELERATION="+accelerations[i])
            acc = acc.encode()
            steer = (";STEERING=" + steerings[i])
            steer = steer.encode()
            message = time + acc + steer
            self.sock.send(message)            

        print("All data sent.")
        self.mutex.release()

    def start(self):
        clientCommunicationThread = Thread(target = self.communicationThread)
        updateDeepNNCarThread = Thread(target = self.updateDeepNNCar)
        updateDeepNNCarThread.daemon = True
        # check to see what mode of operation
        if (self.modeOfOperation != "NORMAL"):
            if (self.modeOfOperation == "DATACOLLECTION"):
                operationThread = Thread(target= self.collectData)
                operationThread.daemon = True
                operationThread.start()
            elif (self.modeOfOperation == "LIVESTREAM"):
                operationThread = Thread(target= self.liveStream)
                operationThread.daemon = True
                operationThread.start()
            elif (self.modeOfOperation == "AUTO"):
                clientCommunicationThread = Thread(target = self.auto)
        clientCommunicationThread.start()
        updateDeepNNCarThread.start()

    def auto(self):
        print("importing model...")
        import model
        print("model imported....")
        self.safetyManager = SafetyManager(self.laneDetectionEnabled,self.blurrinessMeasurementEnabled,self.offloadingTasksEnabled)
        sess = tf.InteractiveSession()
        saver = tf.train.Saver()
        model_name = 'test.ckpt'
        save_dir = os.path.abspath('/media/pi/USB DRIVE/trial1610r')
        model_path = os.path.join(save_dir, model_name)
        saver.restore(sess, model_path)
        while 1:
            ########################### Receive message
            message = self.sock.recv()
            self.messageDecoder.decodeMessage(message.decode())
            acc,steer = self.messageDecoder.getControl()
            if (self.accelerationMode == "CRUISE"):
                acc = self.PID_Controller.getAcceleration()
            elif (self.accelerationMode == "CONSTANT"):
                acc = self.acceleration
            ########################### Take image
            frame = self.camera.captureImage()
            frame_resized = cv2.resize(frame, (200, 66))
            ########################## start safety manager thread
            ldResult, bmResult = self.safetyManager.runImageAnalysis(frame_resized.copy(),self.temp)
            frame_normalized = frame_resized / 255.
            steer_normalized = model.y.eval(feed_dict={model.x: [frame_normalized]})[0][0]
            steer = steer_normalized*10+10 # range of 10-20
            steer = float("{0:.2f}".format(steer))
            ########################### Set Steering and accelerations
            self.pwm.changeDutyCycle(acc,steer)
            self.steering = steer
            self.acceleration = acc
            ############################ respond to client
            message = "STATUS=GOOD"
            if (self.pathTrackerEnabled):
                x,y,displacement,heading = self.pathTracker.addTheta(steer)
                message += ";XCOORD=" + str(x)
                message += ";YCOORD=" + str(y)
                message += ";DISPLACEMENT=" + str(displacement)
                message += ";HEADING=" + str(heading)
            if (self.CPUTrackerEnabled):
                message += ";CPU=" + str(self.cpuUsage)
            if (self.temperatureTrackerEnabled or self.offloadingTasksEnabled):
                message += ";TEMP=" + str(self.temp)
            # send response
            if (self.speedSensorEnabled):
                message += ";SPEED=" + str(self.DeepNNCarspeed)
            # append steering and acceleration duty cycles to message
            message += ";ACC=" + str(self.acceleration)
            message += ";STEER=" + str(self.steering)
            self.sock.send(message.encode())
            if (self.messageDecoder.shouldStop()):
                print("Stopping DeepNNCar")
                self.pwm.changeDutyCycle(15,15)
                self.terminateMainThread = True
                return
            #deepNNCar.updateDeepNNCar()
        print("Add later")

    def liveStream(self):
        port= "5002"
        context = zmq.Context()
        sock = context.socket(zmq.REP)
        sock.bind("tcp://*:%s" % port)
        print("Starting livestream")
        while 1:
            message = sock.recv()
            frame = self.camera.captureImage()
            image_data = cv2.imencode('.jpg', frame)[1].tostring()
            sock.send(image_data)

    def communicationThread(self):
        while 1:
            # receive data
            self.mutex.acquire()
            message = self.sock.recv()
            # decode data into readable values
            self.messageDecoder.decodeMessage(message.decode())
            # extract speed and acceleration from message
            acc,steer = self.messageDecoder.getControl()
            # change acc if acceleration protocol is CRUISE or CONSTANT
            if (self.accelerationMode == "CRUISE"):
                acc = self.PID_Controller.getAcceleration()
            elif (self.accelerationMode == "CONSTANT"):
                acc = self.acceleration
            self.pwm.changeDutyCycle(acc,steer)
            self.steering = steer
            self.acceleration = acc
            message = "STATUS=GOOD"
            if (self.pathTrackerEnabled):
                x,y,displacement,heading = self.pathTracker.addTheta(steer)
                message += ";XCOORD=" + str(x)
                message += ";YCOORD=" + str(y)
                message += ";DISPLACEMENT=" + str(displacement)
                message += ";HEADING=" + str(heading)
            if (self.CPUTrackerEnabled):
                message += ";CPU=" + str(self.cpuUsage)
            if (self.temperatureTrackerEnabled or self.offloadingTasksEnabled):
                message += ";TEMP=" + str(self.temp)
            # send response
            if (self.speedSensorEnabled):
                message += ";SPEED=" + str(self.DeepNNCarspeed)
            # append steering and acceleration duty cycles to message
            message += ";ACC=" + str(self.acceleration)
            message += ";STEER=" + str(self.steering)
            self.sock.send(message.encode())
            self.mutex.release()
            if (self.messageDecoder.shouldStop()):
                print("Stopping DeepNNCar")
                self.pwm.changeDutyCycle(15,15)
                self.terminateMainThread = True
                return
            #deepNNCar.updateDeepNNCar()

    def getDeepNNCarSpeed(self):
        return self.DeepNNCarspeed

    def printPosition(self):
        self.pathTracker.printLocation()

    def __del__(self):
        self.sock.close() # clean up socket
        self.camera.release()

    def updateDeepNNCar(self):
        while(1):
            time.sleep(0.01)
            if (self.speedSensorEnabled):
                speed = self.speedSensor.getSpeed()
                if (speed != -1): # if -1, this means the speed hasn't changed since last polled
                    self.DeepNNCarspeed = speed
                    if (self.accelerationMode == "CRUISE"):
                        self.PID_Controller.update(speed,self.acceleration)
                if (self.pathTrackerEnabled):
                    self.pathTracker.updateMe(speed,self.steering)
            self.temp,self.cpuUsage = self.systemMonitor.run()
            if (self.terminateMainThread):
                exit(0)
        
if __name__=="__main__":
    deepNNCar = DeepNNCar(port = "5001") # start DeepNNCar on port 5001
    deepNNCar.configure() # client communicates configurations
    deepNNCar.start() # begin threads based on configurations

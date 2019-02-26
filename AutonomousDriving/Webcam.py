# Webcam.py
# author: Matthew P. Burruss
# last update: 8/14/2018
# Description: interface for webcam for the various modes

import numpy as np
import cv2
from datetime import datetime
import csv
import socket
import sys
import time

liveStreamServerAddress = ('10.66.229.241',5003)

# release()
# Summary: Cleans up camera.
# Parameter: cap => USB camera object
def release(cap):
    print('Releasing')
    cap.release()

# configureCamera()
# Summary: Configures camera to take images at a designated height, width, and FPS.
# Parameter: freq   => frequency of PWM signal
#            dcAcc  => duty cycle for acceleration at idle
def configureCamera(width,height,fps):
    cap = cv2.VideoCapture(-1)
    cap.set(3,width)
    cap.set(4,height)
    cap.set(5,fps)
    cap.set(16,1)
    return cap


# There are three modes for the camera thread: mode 1 = data collection camera mode
#                                              mode 2 = autonomous driving camera mode (in Server.py)
#                                              mode 3 = live stream driving camera mode

# MODE 1
# dataCollectionCamera()
# Initializes webcam and stores footage on external USB
# Timestamps/Labels are stored on Rpi
# Resolution: 320x240, FPS: 30
# Parameter: stop_event   => event listening for termination of camera
#            newpath      => USB path to write camera images.
def dataCollectionCamera(stop_event,newpath):
    csvfile=open("ImageCount.csv", "w")
    cap = configureCamera(320,240,30)
    ret=True
    count = 0
    value1=[]
    value2=[]
    images = []
    # while the user has not signalled to stop camera, take footage and store on external drive
    while ret and not stop_event.is_set() and count < 3000:
        ret, frame = cap.read()
        Imagetimestamp=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        images.append(frame)
        #cv2.imwrite("%s/frame%d.jpg" % (newpath,count),frame)
        value1.append(Imagetimestamp)
        value2.append(count)
        count += 1
        print(count)
    release(cap)
    for i in range(len(images)):
        cv2.imwrite("%s/frame%d.jpg"%(newpath,i),images[i])
    writer=csv.writer(csvfile)
    writer.writerow(value1)
    writer.writerow(value2)
    csvfile.close()

# MODE 3
# liveStreamCamera()
# creates socket connection over PORT 5002 and sends over camera footage in real time.
# Parameter: stop_event   => event listening for termination of camera
def liveStreamCamera(stop_event):
    sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM,0)
    sock2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock2.bind(liveStreamServerAddress)
    sock2.listen(1)
    cap = configureCamera(320,240,30)
    ret = True
    connection,client_address = sock2.accept()
    while ret and not stop_event.is_set():
        # save frame as JPEG file
        ret, frame = cap.read()
        #frame = frame[0:239,0:319]
        frame = cv2.resize(frame,(200,66))
        data = cv2.imencode('.jpg', frame)[1].tostring()
        size = str(sys.getsizeof(data))
        connection.sendall(size.encode())
        connection.recv(16)
        connection.sendall(data)
        connection.recv(10)
    release(cap)
    sock2.close()

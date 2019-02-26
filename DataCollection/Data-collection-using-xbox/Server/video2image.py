# video2image.py
# author: Matthew P. Burruss
# last update: 8/14/2018
# Description: initializes webcam (resolution 320x240, fps 30)
# collects and records webcam footage

import numpy as np
import cv2
from datetime import datetime
import csv
import socket
import sys

server_address = ('10.66.109.130',5002)
#server_address = ('129.59.105.119',5002)
# cleans up camera space on Rpi
def release(cap):
    print('Releasing')
    cap.release()
    #cv2.destroyAllWindows()
# configures camera to
# params: width, height, and fps
def configureCamera(width,height,fps):
    cap = cv2.VideoCapture(0)
    cap.set(int(3),width)
    cap.set(int(4),height)
    cap.set(int(5),fps)
    return cap


# There are three modes for the camera thread: mode 1 = data collection camera mode
#                                              mode 2 = autonomous driving camera mode (in TCP_Server.py)
#                                              mode 3 = live stream driving camera mode

# MODE 1
# Initializes webcam and stores footage on external USB
# Timestamps/Labels are stored on Rpi
# Resolution: 320x240, FPS: 30
# params: event listener that is False by default and controls image capturing
def dataCollectionCamera(stop_event,newpath):
    # file to write image timestamps
    csvfile=open("ImageCount.csv", "w")    
    #Configure web cam: width = 320, height = 240, fps = 50
    cap = configureCamera(320,240,50)
    #initialize loop variables
    ret=True
    count = 0
    value1=[]
    value2=[]
    # while the user has not signalled to stop camera, take footage and store on external drive
    while ret and not stop_event.is_set():
        # save frame as JPEG file
        ret, frame = cap.read()
        Imagetimestamp=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        cv2.imwrite("%s/frame%d.jpg" % (newpath,count),frame)
        # append timestamp and label
        value1.append(Imagetimestamp)
        value2.append(count)
        count += 1
    release(cap)
    # write time stamps and labels to .csv
    writer=csv.writer(csvfile)
    writer.writerow(value1)
    writer.writerow(value2)
    csvfile.close()

# MODE 3
# sets up a livestream thread
# params: stop_event => end of thread
# TCP_IP refers to IP address of client
# and TCP_PORT cannot be the same port that duty cycles
# are being communicated across
def liveStreamCamera(stop_event):
    sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM,0)
    sock2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock2.bind(server_address)
    sock2.listen(1)
    cap = configureCamera(320,240,50)
    ret = True
    connection,client_address = sock2.accept()
    while ret and not stop_event.is_set():
        # save frame as JPEG file
        ret, frame = cap.read()
        data = cv2.imencode('.jpg', frame)[1].tostring()
        size = str(sys.getsizeof(data))
        connection.sendall(size.encode())
        connection.sendall(data)
        connection.recv(10)
    release(cap)
    sock2.close()
 





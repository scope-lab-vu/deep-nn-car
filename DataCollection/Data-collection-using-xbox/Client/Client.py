# Client.py
# author: Matthew P. Burruss
# last update: 8/14/2018
# Description: Provides methods to initialize/communicate with RPi server.
# PORT 5001: The client sends duty cycle information, mode selection, or termination
# and the RPi sends speed (m/s)
# PORT 5002: If livestream selected, client receives image size and image and acknowledges reception of each.

import socket
import sys
import logging
import cv2
import numpy as np
import math 
import SafetyManager

speed = 0

# initializeConnection()
# Summary: Tries to set up communication with RPi by sending over minimum and maximum steering values.
# Parameter: server_address => TCP/IP socket address
#            idle_dcTUple => (idle steering, idle acc)
#            steering_Range => 10
def initializeConnection(server_address,idle_dcTuple,steering_Range):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    miny = 10
    maxy = 20
    signal = (miny,maxy)
    message = str(signal)
    sock.sendall(message)
    data = sock.recv(16)
    
# send()
# Summary: Sends data to Rpi over TCP/IP   
# Parameter: signal         => tuple type
#            server_address => port 5001
# returnVal: data           => speed response (m/s)
def send(signal,server_address):
    if (len(signal)==2):
        signal = (float("{0:.2f}".format(signal[0])),float("{0:.2f}".format(signal[1])))    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    message = str(signal)
    sock.sendall(message)
    data = sock.recv(32)
    return data

# liveStreamReceiver()
# Summary: Receives live stream footage and displays steering direction in real-time.   
# Parameter: sock       => port 5002
#            dcTuple    => Current duty cycles for steering and acc
#            nullEvents => Accumulated null events
# returnVal: number of null events received indicating connection terminated/failure
def liveStreamReceiver(sock,dcTuple,nullEvents):
    # receive size of iamge
    img_size = sock.recv(32)
    if not img_size:
        sock.sendall("1")
        sock.recv(10)
        sock.sendall("1")
        return (1+nullEvents)
    try:
        img_len = int(img_size)-21
    except Exception as e:
        sock.sendall("1")
        sock.recv(10)
        sock.sendall("1")
        return (1+nullEvents)
    sock.sendall(img_size)
    e=0
    data = ''
    d = "default"
    # Receive image data from rpi and store in data
    while e < img_len and len(d) != 0:
        d = sock.recv(16000)
        e += len(d)
        data += d
    nparr = np.fromstring(data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    cv2.imshow('Live Feed', frame)
    cv2.waitKey(100)
    #frame = SafetyManager.preprocess(frame)
    #fm = SafetyManager.measureBlurriness(frame)
    #lanedecision = SafetyManager.laneDetect(frame)
    response = "1"
    sock.sendall(response)
    return 0
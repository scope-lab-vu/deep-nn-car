# Server.py
# author: Matthew P. Burruss
# last update: 8/14/2018
# Description: Main function, collects images, speed and steering data and upon termination writes it to a USB stick. There are several operating modes that can be selected.
# In this mode, an xbox controller is used to control the speed or steering of the car. The speed can also be controlled using a PID controller. 
# Live stream mode where images are relayed to the client and is relayed as live stream video.

import socket
import sys
import os
import shutil
import time
import datetime
from datetime import datetime
from threading import Thread
import threading
import tensorflow as tf
import atexit
from Pin_Controller import changePins,init,terminate,getSpeed
from video2image import dataCollectionCamera,liveStreamCamera,configureCamera,release
from ast import literal_eval as make_tuple
import logging
import math
#import model
import cv2
import csv
NUM_CORES = 3
server_address = ('10.12.100.130',5001)
liveStreamPort = 5002
miny=9.82
maxy=19.82
# closes TCP/IP socket, conection, and cleans up GPIO on Rpi
speed = 0

def cleanup(sock,connection=0):
    terminate()
    sock.close()
    if (connection != 0):
        connection.close()

def join(dirpath, filename):
    return os.path.join(dirpath, filename)

def preprocess(img):
    cv2.imwrite("media/pi/USB DRIVE/original.jpg",img)
    img = cv2.resize(img, (200, 66))
    cv2.imwrite("media/pi/USB DRIVE/resized.jpg",img)
    img = img / 255.
    cv2.imwrite("media/pi/USB DRIVE/normalized.jpg",img)
    return img

def denormalization(steer):
    return (float(steer)*(maxy-miny))+miny

# Establishes connection and controls Traxxas RC car until a mode is selected
# params: TCP_IP => IP address of client
#         TCP_PORT => port to connect
# return: socket connection, p12 (acc), p27 (steering), mode
def SelectMode(TCP_IP,TCP_PORT):
    global speed     
    # Create a TCP/IP sconnection
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM,0)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_address = (TCP_IP , TCP_PORT)
    print('starting up on %s port %s' % server_address)
    sock.bind((TCP_IP,TCP_PORT))
    sock.listen(1)
    # inititialize function variables
    logging.basicConfig(filename='scheduler.log', level=logging.DEBUG, filemode='w') 
    init(100,0,0)
    modeSelected = False
    mode = 0  
    
    # loop until client sends a START signal
    # otherwise control motor
    print('Establishing initial connection')
    connection, client_address = sock.accept()
    data = connection.recv(16)
    connection.sendall(data)
    print('Waiting for mode to be selected')
    while not modeSelected:
        try:
            sock.settimeout(3)
            connection, client_address = sock.accept()
            data = connection.recv(20)
        except socket.timeout:
            print('Connection timed out')
            sock.close()
            terminate()
            sys.exit()
        # check if special signal received
        if (data.decode() == "(1,)"):
            modeSelected = True
            message = "Starting data collection mode."
            message = message.encode()
            connection.sendall(message)
            mode = 1
        elif (data.decode() == "(2,)"):
            modeSelected = True
            modeSelected = True
            message = "Starting autonomous driving mode."
            message = message.encode()
            connection.sendall(message)
            mode = 2
        elif (data.decode() == "(3,)"):
            message = "STOP signal received exiting and cleaning connection.""Starting autonomous driving mode."
            message = message.encode()
            connection.sendall(message)
            sock.close()
            terminate()
            sys.exit()
        elif (data.decode() == "(4,)"):
            modeSelected = True
            message = "Starting live stream mode."
            message = message.encode()
            connection.sendall(message)
            mode = 3
        else:
            data_decoded = data.decode()
            # data_decoded contains duty cycles, p12 is used to control acceleration
            # and p27 is used to control steering
            changePins(data_decoded)   
        # check to make sure data received
        if data:
            speed = getSpeed()
            speed = float("{0:.2f}".format(speed))
            speed = str(speed)
            connection.sendall(speed.encode())
        else:
            sock.close()
            terminate()
            sys.exit()               
    return sock,mode

# PWM controller for dataCollect Mode
# Waits until a STOP signal ('B') is sent from client
# otherwise continues to change acceleration and
# steering parameters of traxxas RC car
# params: sock => socket connection
#         p12 => GPIO acceleration
#         p27 => GPIO steering
def dataCollectionDriving(sock,csvfile):
    global speed
    # initialize function variables
    connection = 0
    timestamps=[]
    accDCs = []
    steerDCs = []
    while True:   
        try:
            sock.settimeout(3)
            connection, client_address = sock.accept()
            data = connection.recv(20)
        except sock.timeout:
            print('Connection timed out')
            cleanup(sock,connection)
            break
        dc = make_tuple(data.decode())
        # if a STOP signal is sent, data collection is terminated
        if (data.decode() == "(3,)"):
            message = "Data collection terminated"
            message = message.encode()
            connection.sendall(message)
            break
        # if other special signal is sent, send signal back
        if (len(dc)==1):
            connection.sendall(data)
            continue
        # append timestamp, duty cycle for acceleration, and duty cycle for steering
        timestamps.append(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
        accDCs.append(dc[0])
        steerDCs.append(dc[1])
        # decode client data and change pin values
        data_decoded = data.decode()
        changePins(data_decoded)
        # acknowledge client
        speed = getSpeed()
        speed = float("{0:.2f}".format(speed))
        speed = str(speed)
        connection.sendall(speed.encode())
    # write to .csv and close
    writer=csv.writer(csvfile)
    writer.writerow(timestamps)
    writer.writerow(accDCs)
    writer.writerow(steerDCs)
    csvfile.close()    
    # cleans up processes)
    print('Cleaning up')
    cleanup(sock,connection)

# PWM controller for autonomousDriving Mode
# Waits until a STOP signal ('B') is sent from client
# otherwise used CNN model to generate steering
# and steering control values
# params: sock => socket connection
#         p12 => GPIO acceleration
#         p27 => GPIO steering
def autonomousDriving(sock):
    global speed
    # initialize loop variables
    connection = 0
   # config = tf.ConfigProto(intra_op_parallelism_threads=NUM_CORES, inter_op_parallelism_threads=NUM_CORES, \
       #                 allow_soft_placement=True, device_count = {'CPU': NUM_CORES})
   # sess = tf.InteractiveSession(config = config)
    #sess = tf.Session(config=tf.ConfigProto(intra_op_parallelism_threads=NUM_CORES))
    sess = tf.InteractiveSession()
    saver = tf.train.Saver()
    model_name = 'test.ckpt'
    save_dir = os.path.abspath('/home/pi/Desktop/PiCar/model0710')
    model_path = join(save_dir, model_name)
    saver.restore(sess, model_path)
    cap = configureCamera(320,240,50)
    ret = True
    while ret:   
        try:
            sock.settimeout(3)
            connection, client_address = sock.accept()
            data = connection.recv(20)
        except sock.timeout:
            print('Connection timed out')
            cleanup(sock,connection)
            break
        dc = make_tuple(data.decode())
        if (data.decode() == "(3,)"):
            message = "Autonomous driving terminated"
            message = message.encode()
            connection.sendall(message)
            break
        if (len(dc)==1):
            connection.sendall(data)
            continue
        
        ret, frame = cap.read()
        # save frame as JPEG file
        img = preprocess(frame)
        steer = model.y.eval(feed_dict={model.x: [img]})[0][0]
        steering = denormalization(steer)
        steering = float("{0:.2f}".format(steering))
        print(steering)
        dutyCycle = str((steering,dc[1]))
        changePins(dutyCycle)
        speed = getSpeed()
        speed = float("{0:.2f}".format(speed))
        speed = str(speed)
        connection.sendall(speed.encode())
        #time2 = datetime.now()
        #dif = time2-time1
        #print('%f'%(dif.microseconds/1000000))
    release(cap)
        # acknowledge client
    print('Cleaning up')
    cleanup(sock,connection)

# PWM controller for LiveStream Mode
# Waits until a STOP signal ('B') is sent from client
# otherwise continues to change acceleration and
# steering parameters of traxxas RC car
# params: sock => socket connection
#         p12 => GPIO acceleration
#         p27 => GPIO steering
def liveStreamDriving(sock):
    global speed
    connection = 0
    while True:   
        try:
            sock.settimeout(3)
            connection, client_address = sock.accept()
            data = connection.recv(20)
        except sock.timeout:
            print('Connection timed out')
            cleanup(sock,connection)
            break
        dc = make_tuple(data.decode())
        # if a STOP signal is sent, data collection is terminated
        if (data.decode() == "(3,)"):
            message = "Live Stream terminated"
            message = message.encode()
            connection.sendall(message)
            break
        if (len(dc)==1):
            connection.sendall(data)
            continue
        data_decoded = data.decode()
        changePins(data_decoded)
        speed = getSpeed()
        speed = float("{0:.2f}".format(speed))
        speed = str(speed)
        connection.sendall(speed.encode())
    print('Cleaning up')
    cleanup(sock,connection)

# Thread function:
# Initialize webcam thread
# params: stop_event set to true if user sends STOP signal ('B' on Xbox controller)
#         cameraMode determines which type of thread to start based on the 3 types of modes
def camera(stop_event,cameraMode,newpath):
    if (cameraMode == 1):
        dataCollectionCamera(stop_event,newpath)        
    elif (cameraMode == 2):
        autonomousCamera(stop_event)
    elif (cameraMode ==3):
        liveStreamCamera(stop_event)

# secondary main methods for each mode
# Mode 1: Data Collection Mode
# Mode 2: Autonomous Driving Mode
# Mode 3: Livefeed Mode

# Mode 1
def dataCollectionMode(sock):
    # name of file containing timestamps and duty cycles
    newTrialCreated = False
    trialNumber = 1
    while not newTrialCreated:
        newpath = '/media/pi/USB DRIVE/Trial{0}'.format(trialNumber)
        if not os.path.exists(newpath): 
            os.makedirs(newpath)
            newTrialCreated = True
        else:
            trialNumber = trialNumber + 1
    csvfile = open("Data.csv", "w")
    pill2kill = threading.Event()
    print('Starting camera')
    thread = Thread(target=camera,args=(pill2kill,1,newpath,))
    thread.start()
    # begin recording movements
    print('Collecting duty cycles and images.')
    dataCollectionDriving(sock,csvfile)
    # after client sends STOP signal, terminates camera
    pill2kill.set()
    thread.join()
    # moves .csv files from Rpi to external USB then deletes from Rpi+
    print('Copying files to USB')
    shutil.copy2('/home/pi/Desktop/PiCar/ImageCount.csv', newpath + '/ImageCountData.csv')
    shutil.copy2('/home/pi/Desktop/PiCar/Data.csv', newpath + '/DutyCycleData.csv')

# Mode 2
def autonomousDrivingMode(sock):
    print('Driving autonomously')
    # begin recording movements
    print('Camera started.')   
    autonomousDriving(sock)

# Mode 3
def liveStreamMode(sock):
    print('Live Streaming')
    pill2kill = threading.Event()
    thread = Thread(target=camera,args=(pill2kill,3,0,))
    thread.start()
    # begin recording movements
    print('Live stream started.')   
    liveStreamDriving(sock)
    # after client sends STOP signal, terminates camera
    pill2kill.set()
    thread.join()

# MAIN
if __name__=="__main__":
    
    # establish connection
    sock,mode=SelectMode(server_address[0],server_address[1])
    # begin webcam thread
    if (mode == 1):
        dataCollectionMode(sock)
    elif(mode == 2):
        autonomousDrivingMode(sock)
    elif(mode ==3):
        liveStreamMode(sock)

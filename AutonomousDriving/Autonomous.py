#Autonomous.py
#Authored: Shreyas Ramakrishna
#Last Edited: 02/25/2019
#Description: Autonomous script which runs on the RPi3, which allows to run different Simplex architectures
#AMSimplex or RLSimplex

import socket
import sys
import os
import shutil
import time
import datetime
import numpy as np
from datetime import datetime
from threading import Thread
import threading
import tensorflow as tf
from ast import literal_eval as make_tuple
import logging
import math
import cv2
import csv
import psutil
import IO
import Webcam
import CPU
import model
import SafetyManagerAutonomousClient
from queue import Queue
import base64
import zmq
from keras.models import model_from_json
import RLCar
import pickle

# mutable parameters
port1 = '5005'
port2 = '5006'
port3 = '5007'
port4 = '5008'
port5 = '5009'
port6 = '5010'
port7 = '5011'
port8 = '5012'

#immutable parameters
miny=10
maxy=20
speed=0
w1 = 0.5
w2 = 0.5
speed,seq_number,x,j,k,l,m,n,p = (0,0,0,0,0,0,0,0,0)
ret = True

#preprocess speed data
def preprocess_speed(acc):
    minS=15.0
    maxS=15.75
    speed_acc = (acc-minS)/(maxS-minS)
    return speed_acc

#Cleanup function to close all used sockets
def cleanup(mysocket):
    #IO.cleanGPIO()
    for i in range (0,13):
        mysocket[i].close()

#function to join files
def join(dirpath, filename):
    return os.path.join(dirpath, filename)

#preprocess images
def preprocess(img):
   # image = image[100:239,0:319]
    img = cv2.resize(img, (200, 66))
    #img = img / 255.
    return img

#denormalize the predicting steering
def denormalization(steer):
    global maxy,miny
    return (float(steer)*(maxy-miny))+miny
	
#Connecting RPi3 to client(laptop)
def clientConnection(server_address):
    context = zmq.Context()
    socket15 = context.socket(zmq.REP)
    socket15.bind("tcp://*:%s"%port7)
    print('starting up on %s port %s' % server_address)
    print('Waiting for client...')
    msg = socket15.recv()
    print(msg)
    socket15.send_string("Hello From server")
    return socket15
	
#Creating ZMQ Publisher socket
def pubSocket(port1,port5,port8):
    context = zmq.Context()
    socket1= context.socket(zmq.PUB)
    socket13= context.socket(zmq.PUB)
    socket16= context.socket(zmq.PUB)
    socket1.bind("tcp://*:%s"%port1)
    socket13.bind("tcp://*:%s"%port5)
    socket16.bind("tcp://*:%s"%port8)
    return socket1,socket13,socket16
	
#Creating ZMQ Subscriber socket
def subSocket(port1,port5,port8):
    context = zmq.Context()
    socket2= context.socket(zmq.SUB)
    socket3= context.socket(zmq.SUB)
    socket4= context.socket(zmq.SUB)
    socket14= context.socket(zmq.SUB)
    socket17= context.socket(zmq.SUB)
    socket2.connect("tcp://localhost:%s" % port1)
    socket3.connect("tcp://localhost:%s" % port1)
    socket4.connect("tcp://localhost:%s" % port1)
    socket14.connect("tcp://localhost:%s" %port5)
    socket17.connect("tcp://localhost:%s" %port8)
    return socket2,socket3,socket4,socket14,socket17
	
#Creating ZMQ Reply socket
def RepSocket(port2,port3,port4,port6):
    context = zmq.Context()
    socket5 = context.socket(zmq.REP)
    socket5.bind("tcp://*:%s"%port2)
    socket6 = context.socket(zmq.REP)
    socket6.bind("tcp://*:%s"%port3)
    socket7 = context.socket(zmq.REP)
    socket7.bind("tcp://*:%s"%port4)
    socket8 = context.socket(zmq.REP)
    socket8.bind("tcp://*:%s"%port6)
    return socket5, socket6, socket7,socket8
	
#Creating ZMQ Request socket
def ReqSocket(port2,port3,port4,port6):
    context = zmq.Context()
    socket9 = context.socket(zmq.REQ)
    socket10 = context.socket(zmq.REQ)
    socket11 = context.socket(zmq.REQ)
    socket12 = context.socket(zmq.REQ)
    socket9.connect("tcp://localhost:%s" % port2)
    socket10.connect("tcp://localhost:%s" % port3)
    socket11.connect("tcp://localhost:%s" % port4)
    socket12.connect("tcp://localhost:%s" % port6)
    return socket9,socket10,socket11,socket12

def autonomousDriving(mysocket,explore,simplex,rounds,exploration_steps):

    #Buffer actor to store image and speed
    def Buffer(mysocket,cameraQ,rounds):
        global seq_number,j
        while (j<rounds):
            frame = cameraQ.get()
            tick = mysocket[7].recv_string()
            mysocket[7].send_string(str(seq_number))
            j+=1
            if (tick == '1'):
                frame = preprocess(frame)
                image = cv2.imencode('.jpg', frame)[1].tostring()
                mysocket[0].send(base64.b64encode(image))
                seq_number += 1
        return


    #Keras Neural Network model
    def KerasNNController(frame, speed_acc, kerasmodel):
        inputs = np.array(img)[np.newaxis]
        speed_acc =  np.array(speed_acc)[np.newaxis]
        outputs = model.predict([inputs,speed_acc], batch_size=1)
        return float(outputs[0][0])

    #LEC actor which predicts the steering
    def LEC(mysocket,model,sess,acc,rounds):
        global k
        while(k<rounds):
            k+=1
            msg = mysocket[4].recv_string()
            mysocket[1].setsockopt(zmq.SUBSCRIBE, b'')
            data = mysocket[1].recv_string()
            img = base64.b64decode(data)
            npimg = np.fromstring(img, dtype=np.uint8)
            frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
            with sess.as_default():
                steer = model.y.eval(feed_dict={model.x: [frame]})[0][0]
            steering = denormalization(steer)
            steeringNN = float("{0:.2f}".format(steering))
            mysocket[4].send_string(str(steeringNN))
        return


    #SafetySupervisor actor which computes lanedetection and steering
    def SafetySupervisor(mysocket,rounds):
        global l
        while(l<rounds):
            l+=1
            msg = mysocket[5].recv_string()
            mysocket[2].setsockopt(zmq.SUBSCRIBE, b'')
            data = mysocket[2].recv_string()
            img = base64.b64decode(data)
            npimg = np.fromstring(img, dtype=np.uint8)
            frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
            laneDetection,blur,steeringSS = SafetyManagerAutonomousClient.runSafetyManager(frame,mysocket)
            mysocket[5].send_string(str(steeringSS))
            mysocket[12].send_string(str(laneDetection))
        return



    #RL Actor which computes the arbitration weights and the throttle for the car
    def RLCarrun(mysocket,acc,exploration_steps,explore,Qtable,rounds):
        global w1,w2,m
        while(m<rounds):
            m+=1
            msg = mysocket[6].recv_string()
            mysocket[13].setsockopt(zmq.SUBSCRIBE, b'')
            laneDetection = mysocket[13].recv_string()
            acc = round(acc,4)
            laneDetection = int(laneDetection)
            w1,w2,acc = RLCar.run(acc,laneDetection,w1,w2,exploration_steps,explore,Qtable)
            mysocket[6].send_string("%s %s %s" %(str(w1),str(w2),str(acc)))
            exploration_steps -=1
        return


    #Decision Manager which computes the steering of the car
    #Allows the user to choose different simplex architectures
    #AMSimplex => 0 and RLSimplex => 1
    def DecisionManager(mysocket,acc,simplex,rounds):
        global x,n
        while(n<rounds):
            n+=1
            if(simplex == "1"):#RLSimplex
                tick = '1' #make tick equal to one once value has been sent to gpio
                mysocket[8].send(b"send LEC steering") #request the three components to send data
                mysocket[9].send(b"send SS steering")
                mysocket[10].send(b"send RL data")
                mysocket[11].send_string(tick)#send tick to buffer, so that it publishes data
                sequence = mysocket[11].recv_string()# current sequence number that will be sent by the buffer
                steeringNN = mysocket[8].recv_string()
                steeringSS = mysocket[9].recv_string()
                RLmsg = mysocket[10].recv_string()
                w1,w2,acc = RLmsg.split()
                w1 = float(w1)
                w2 = float(w2)
                acc = float(acc)
                steering = w1*float(steeringSS) + w2*float(steeringNN)

            elif(simplex == "0"):#AMSimplex
                tick = '1' #make tick equal to one once value has been sent to gpio
                mysocket[8].send(b"send LEC steering") #request the three components to send data
                mysocket[9].send(b"send SS steering")
                mysocket[11].send_string(tick)#send tick to buffer, so that it publishes data
                sequence = mysocket[11].recv_string()# current sequence number that will be sent by the buffer
                steeringNN = mysocket[8].recv_string()
                steeringSS = mysocket[9].recv_string()
                if((float(steeringNN) - float(steeringSS)) > 2.0):
                    w1 = 0.2
                    w2 = 0.8
                    steering = w1*float(steeringSS) + w2*float(steeringNN)
                    acc = acc - 0.00002
                    x += 1
                    if(x>=5):
                        acc = acc - 0.0004
                else:
                    steering = steeringNN
                    acc = acc + 0.00008
                    x = 0
            acc = round(acc,4)
            print("rounds:%d steeringNN:%s steeringSS:%s acceleration:%f steering:%s w1:%f w2:%f"%(n,steeringNN,steeringSS,acc,steering,w1,w2))
            steering = float("{0:.2f}".format(steering))
            mysocket[14].send_string("%s %s %f" %(str(w1),str(w2),acc))
            IO.changeDutyCycle((steering, acc))
            tick = '0'
        return

    #Camera actor which continuously captures images
    def cameraThread(cap,cameraQ):
        global ret
        while ret:
            ret, frame = cap.read()
            cameraQ.put(frame)

    #Opto-coupler actor which gets speed
    def OptoCoupler(OptoQ,):
        while 1:
            speed = IO.speed
            speed = float("{0:.2f}".format(speed))
            OptoQ.put(speed)

	#Data Accumulator for collecting data		
    def DataAccumulator(csvfile,writer,rounds):
        global p
        while(p<rounds):
            data = []
            p+=1
            mysocket[15].setsockopt(zmq.SUBSCRIBE, b'')
            msg = mysocket[15].recv_string()
            w1,w2,acc = msg.split()
            data.append(float(w1))
            data.append(float(w2))
            data.append(acc)
            writer.writerow(data)
        newTrialCreated = False
        trialNumber = 1
        print("copying data ..............")
        while not newTrialCreated:
            newpath = '/media/pi/USB DRIVE/data{0}.csv'.format(trialNumber)
            if not os.path.isfile(newpath):
                 shutil.move('/home/pi/Desktop/PiCar/Components/data.csv',newpath)
                 newTrialCreated = True
            else:
                trialNumber = trialNumber + 1
        print("Done writing data")
        return

    #RL exploration or exploitation
    if(explore == "0"):
        Qtable = RLCar.initQTable()
    elif(explore == "1"):
        Qtable = RLCar.pickletable()
    else:
        print("AMSimplex chosen")

    #CSV to store data for plotting and analysis
    csvfile = open('data.csv','w')
    writer = csv.writer(csvfile)

    # load tensorflow model
    sess = tf.InteractiveSession()
    saver = tf.train.Saver()
    model_name = 'test.ckpt'
    save_dir = os.path.abspath('/media/pi/USB DRIVE/trial1610r')
    model_path = join(save_dir, model_name)
    saver.restore(sess, model_path)

    #configure camera
    cap = Webcam.configureCamera(320,240,30)
    DMQ = Queue()
    cameraQ = Queue(maxsize=1)
    OptoQ = Queue(maxsize=1)
    acc = 15.58
    IO.changeDutyCycle((15, 15))
    time.sleep(2)

	#Camera Thread
    cameraThread = Thread(target = cameraThread,args = (cap,cameraQ))
    cameraThread.daemon = True
    cameraThread.start()

    #Opto-Coupler Thread
    OptoThread = Thread(target = OptoCoupler,args = (OptoQ,))
    OptoThread.daemon = True
    #OptoThread.start()

    try:
        #Data actor for accumulating data
        DataActorThread = Thread(target = DataAccumulator,args = (csvfile,writer,rounds))
        DataActorThread.daemon = True
        DataActorThread.start()

        #Decision Manager Thread
        DMThread = Thread(target = DecisionManager,args = (mysocket,acc,simplex,rounds))
        DMThread.daemon = True
        DMThread.start()

        #LEC Thread
        LECThread = Thread(target = LEC,args = (mysocket,model,sess,acc,rounds))
        LECThread.daemon = True
        LECThread.start()

        #SafetySupervisor Thread
        SafetySupervisorThread = Thread(target = SafetySupervisor,args = (mysocket,rounds))
        SafetySupervisorThread.daemon = True
        SafetySupervisorThread.start()

        #RL Thread
        RLThread = Thread(target = RLCarrun,args = (mysocket,acc,exploration_steps,explore,Qtable,rounds))
        RLThread.daemon = True
        RLThread.start()

        #Buffer Thread
        BufferActorThread = Thread(target = Buffer,args = (mysocket,cameraQ,rounds))
        BufferActorThread.daemon = True
        BufferActorThread.start()

        #Join threads
        LECThread.join()
        SafetySupervisorThread.join()
        BufferActorThread.join()
        DMThread.join()
        DataActorThread.join()

        #Cleaning up the sockets and terminating the process
        print('Cleaning up and terminating the script')
        time.sleep(3)
        cap.release()
        cleanup(mysocket)
        csvfile.close()
        sys.exit()

    except KeyboardInterrupt:

        print('Cleaning up and terminating the script')
        time.sleep(3)
        cap.release()
        cleanup(mysocket)
        sys.exit()


# MAIN
if __name__=="__main__":
    #socket15 = clientConnection(server_address)
    socket1,socket13,socket16 = pubSocket(port1,port5,port8)#Publisher sockets
    socket2,socket3,socket4,socket14,socket17 = subSocket(port1,port5,port8)#subscriber sockets
    socket5,socket6,socket7,socket8 = RepSocket(port2,port3,port4,port6)#Reply sockets
    socket9,socket10,socket11,socket12 = ReqSocket(port2,port3,port4,port6)#Request sockets
    #List all sockets under mysocket
    mysocket = [socket1,socket2,socket3,socket4,socket5,socket6,socket7,socket8,socket9,socket10,socket11,socket12,socket13,socket14,socket16,socket17]

    #Some options to be chosen by the user
    print("Do you want to use AMSimplex or RLSimplex")
    simplex = input("AMSimplex => 0 \t RLSimplex => 1:")
    if(simplex == "1"):
        print("Do you want to explore or exploit")
        explore = input("explore => 0 \t exploit => 1:")
        if(explore == "0"):
            exploration_steps = int(input("Enter the number of exploration steps:"))
        elif(explore == "1"):
            exploration_steps = 0
    elif(simplex == "0"):
        explore = "0"
        exploration_steps = 0
    rounds = int(input("Enter the number of trial runs (integer):"))
    IO.initGPIO(100,0,0)#Initialize the GPIO pins
    IO.beginGettingSpeed()#Initialize the opto-coupler to get code
    logging.basicConfig(filename='scheduler.log', level=logging.DEBUG, filemode='w')
    autonomousDriving(mysocket,explore,simplex,rounds,exploration_steps)

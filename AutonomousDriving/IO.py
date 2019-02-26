# IO.py
# author: Matthew P. Burruss
# last update: 8/14/2018

# PWM Control for Raspberry 3pi acceleration
# GPIO18: acceleration
# Reverse:  DC<15%
# Forward:  15%<DC
# GPIO19: steering
# Left:  DC<15%
# Right:  15%<DC
# GPIO21: Input for IR sensor

import datetime
from datetime import datetime
import time
from ast import literal_eval as make_tuple
import pigpio
import RPi.GPIO as GPIO
import math
import csv
import shutil
import os
import signal

# initialize a pigpiod object
pi = pigpio.pi()

# Duty Cycle parameters (adjustable (not recommended))
freq = 100
steering = 0
acceleration = 0

# RPM parameters (adjustable)
sensor = 21 # define the GPIO pin our sensor is attached to
diameter = 110 # mm

# RPM parameters (non-adjustable)
elapse = 0
maxElapse = 1
rpm = 0
speed = 0
start_timer = time.time()
timestamps = []
speeds = []

# calculate_elapse()
# description: Calculates the speed based on digital signal from IR opto-coupler. 
def calculate_elapse(channel):				# callback function
    global start_timer, elapse,speed
    global timestamps,speeds
    elapse = time.time() - start_timer		# elapse for every 1 complete rotation made!
    if elapse != 0:							# to avoid DivisionByZero error
        rpm = (1 / elapse)*60 
        circumference = math.pi * diameter
        speed = (rpm*circumference/60)/1000
        speeds.append(speed)
        timestamps.append(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
    start_timer = time.time()				# let current time equals to start_timer

# zeroDetectionHandler()
# description: Detects when speed = 0 m/s
def zeroDetectionHandler(signum,frame):
    global start_timer,maxElapse,speed
    global speeds,timestamps
    elapsed = time.time() - start_timer
    if (elapsed > maxElapse):
        speed = 0
        speeds.append(speed)
        timestamps.append(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
    #start_timer = time.time()
    signal.signal(signal.SIGALRM,zeroDetectionHandler)
    signal.alarm(maxElapse)


# init()
# Summary: Initializes GPIO
# Parameter: freq   => frequency of PWM signal
#            dcAcc  => duty cycle for acceleration at idle 
def initGPIO(freq,dcAcc,dcSteer):
    pi.hardware_PWM(18,freq,int(dcAcc*10000))
    pi.hardware_PWM(19,freq,int(dcSteer*10000))
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(sensor,GPIO.IN,GPIO.PUD_UP)

# beginGettingSpeed()
# Description: Upon a successful connection, initialize software interrupt for IR sensor
def beginGettingSpeed():
    GPIO.add_event_detect(sensor, GPIO.FALLING, callback = calculate_elapse, bouncetime = 20) # execute the get_rpm function when a LOW signal is detected
    signal.signal(signal.SIGALRM,zeroDetectionHandler)
    signal.alarm(maxElapse)

# changeDutyCycle()
# Summary: Changes PWM duty cycles for steering and acceleration 
# Parameter: data => tuple of doubles containing the duty cycles (%) for steering and acceleration
def changeDutyCycle(dc):
    global steering, acceleration
    if (steering != dc[0]):
        steering = dc[0]
        pi.hardware_PWM(19,freq,int(dc[0]*10000))
    if (acceleration != dc[1]):
        acceleration = dc[1]
        pi.hardware_PWM(18,freq,int(dc[1]*10000))     

# cleanGPIO()
# Summary: Writes speed data to a Speed.csv, turns off Traxxas, and clears GPIO. 
def cleanGPIO():
    global timestamps,speeds
    signal.alarm(0)
    print('Cleaning up GPIO and writing to csv file')
    GPIO.cleanup()
    pi.hardware_PWM(18,freq,0)
    pi.hardware_PWM(19,freq,0)
    pi.stop()
    
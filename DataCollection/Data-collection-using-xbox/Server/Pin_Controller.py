# IO.py
# author: Matthew P. Burruss
# last update: 8/14/2018
# PWM Control for Raspberry 3pi acceleration
# Pin12 (PWM0): acceleration
# Reverse:  DC<15%
# Forward:  15%<DC
# Pin13 (PWM1): steering
# Left:  DC<15%
# Right:  15%<DC

#import RPi.GPIO as GPIO
import datetime
from datetime import datetime
import time
from ast import literal_eval as make_tuple
from os import system
system("sudo pigpiod")
import pigpio
import RPi.GPIO as GPIO
import math
import csv
import shutil
import os

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
rpm = 0
speed = 0
start_timer = time.time()
timestamps = []
speeds = []
elapses = []
def calculate_elapse(channel):				# callback function
    global start_timer, elapse,speed
    global timestamps,speeds,elapses
    elapse = time.time() - start_timer		# elapse for every 1 complete rotation made!
    if elapse != 0:							# to avoid DivisionByZero error
        rpm = (1 / elapse)*60 
        circumference = math.pi * diameter
        speed = (rpm*circumference/60)/1000
        speeds.append(speed)
        elapses.append(elapse)
        timestamps.append(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
    print(speed)
    start_timer = time.time()				# let current time equals to start_timer

#getSpeed()
def getSpeed():
    global speed
    return speed

# initializes output pins on Rpi for motor control
# params: frequency (Hz), duty cycle acceleration (PIN 12)
# duty cycle steering (PIN 35)
def init(freq,dcAcc,dcSteer):
    pi.hardware_PWM(18,freq,int(dcAcc*10000))
    pi.hardware_PWM(19,freq,int(dcSteer*10000))
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(sensor,GPIO.IN,GPIO.PUD_UP)
    GPIO.add_event_detect(sensor, GPIO.FALLING, callback = calculate_elapse, bouncetime = 20) # execute the get_rpm function when a LOW signal is detected

# changes duty cycles of pins 12 & 35
# params: tuple containing duty cycle (steering,acceleration)
def changePins(data):
    # method
    global steering, acceleration
    dc = make_tuple(data)
    if (steering != dc[0]):
        steering = dc[0]
        pi.hardware_PWM(19,freq,int(dc[0]*10000))
    if (acceleration != dc[1]):
        acceleration = dc[1]
        pi.hardware_PWM(18,freq,int(dc[1]*10000))     

# Cleans up GPIO of Rpi
def terminate():
    global timestamps,speeds,elapses
    print('Cleaning up GPIO and writing to csv file')
    # write to csv SpeedData.csv 
    csvfile=open("Speed.csv", "w")  
    writer=csv.writer(csvfile)
    writer.writerow(speeds)
    writer.writerow(timestamps)
    writer.writerow(elapses)
    csvfile.close()
    # write to USB Drive
    newTrialCreated = False
    trialNumber = 1
    while not newTrialCreated:
        newpath = '/media/pi/USB DRIVE/SpeedData{0}.csv'.format(trialNumber)
        if not os.path.isfile(newpath):
             shutil.copy2('/home/pi/Desktop/PiCar/Speed.csv',newpath)
             newTrialCreated = True
        else:
            trialNumber = trialNumber + 1
    # clean up GPIO
    GPIO.cleanup()
    pi.hardware_PWM(18,freq,0)
    pi.hardware_PWM(19,freq,0)
    pi.stop()


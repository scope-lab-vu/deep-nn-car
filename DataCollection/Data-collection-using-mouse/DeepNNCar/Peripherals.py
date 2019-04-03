import pigpio
import RPi.GPIO as GPIO
import signal
import time
import math
import cv2
import os
import psutil
# author: Matthew P. Burruss
# last Updated 2/15/2019
# Controls the slot type IR sensor
# calculates the speed readings
class SpeedSensor:
    def __init__(self):
        self.gpioPinIRSensor = 21
        self.diameterOfWheel = 73.44 #mm
        # init gpio pin for IR sensor
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.gpioPinIRSensor,GPIO.IN,GPIO.PUD_UP)
        # speed calculation parameters
        self.speed = -1 # -1 indicates no speed received yet
        self.timeElapsed = 0
        self.start_timer = time.time()
        self.zeroDetectionTime = 1 # after 1 second of not reading a speed, the speed = 0
        signal.signal(signal.SIGALRM,self.zeroDetectionHandler)
        signal.alarm(self.zeroDetectionTime)
        # ignore boolean
        self.ignoreSpeed = True
        GPIO.add_event_detect(self.gpioPinIRSensor, GPIO.FALLING, callback = self.calculateSpeed, bouncetime = 100)

    def zeroDetectionHandler(self,signum,frame):
        elapsed = time.time() - self.start_timer
        if (elapsed > self.zeroDetectionTime):
            self.speed = 0
            self.ignoreFirstSpeed = True
        signal.signal(signal.SIGALRM,self.zeroDetectionHandler)
        signal.alarm(self.zeroDetectionTime)

    def calculateSpeed(self,channel):
        GPIO.remove_event_detect(self.gpioPinIRSensor)
        self.timeElapsed = time.time() - self.start_timer		# elapse for every 1 complete rotation made!
        if (self.timeElapsed > 0.1 and not self.ignoreSpeed):						# to avoid DivisionByZero error
            rpm = (1 / self.timeElapsed)*60 
            circumference = math.pi * self.diameterOfWheel
            self.speed = (rpm*circumference/60)/1000
        self.ignoreSpeed = False
        self.start_timer = time.time()				# let current time equals to start_timer
        GPIO.add_event_detect(self.gpioPinIRSensor, GPIO.FALLING, callback = self.calculateSpeed, bouncetime = 100)

    # toggles between -1 and an actual speed
    def getSpeed(self):
        if (self.speed != -1):
            tmp = self.speed
            self.speed = -1
            return tmp
        else:
            return -1

# author: Matthew P. Burruss
# Last Updated: 2/4/2019
# PWM Control for Raspberry 3pi acceleration
# GPIO18: acceleration
# GPIO19: steering where [10,15] left and [15,20] right
class PWM:
    def __init__(self):
        self.pi = pigpio.pi()
        self.freq = 100
        self.steering = 0
        self.acceleration = 0
        self.gpioPinAcceleration = 18
        self.gpioPinSteering = 19
        # init hardware. Car should be faced forwards and not moving
        self.pi.hardware_PWM(self.gpioPinAcceleration,self.freq,int(14.5*10000))
        self.pi.hardware_PWM(self.gpioPinSteering,self.freq,int(15*10000))

    # changeDutyCycle()
    # Summary: Changes PWM duty cycles for steering and acceleration 
    # Parameter: data => tuple of doubles containing the duty cycles (%) for steering and acceleration
    def changeDutyCycle(self,acc,steer):
        if (self.steering != steer):
            self.steering = steer
            #print(steer)
            self.pi.hardware_PWM(self.gpioPinSteering,self.freq,int(steer*10000))
        if (self.acceleration != acc):
            self.acceleration = acc
            #print(acc)
            self.pi.hardware_PWM(self.gpioPinAcceleration,self.freq,int(acc*10000))     

    # cleans GPIO
    def __del__(self):
        print('Cleaning up GPIO...')
        GPIO.cleanup()

# author: Matthew P. Burruss
# Last Updated: 2/16/2019
# Camera class
class Camera:
    def __init__(self,width=320,height=240,fps=30):
        self.cap = cv2.VideoCapture(-1)
        self.cap.set(int(3),width)
        self.cap.set(int(4),height)
        self.cap.set(int(5),fps)
        self.cap.set(int(12),100)
        #self.cap.set(int(7),100)

    def release(self):
        print("Cleaning camera...")
        self.cap.release()

    def captureImage(self):
        ret, frame = self.cap.read()
        if (ret == False): print("ERROR: Unable to capture frame.")
        return frame

class SystemMonitor:
    # delay controls how often it actually reads
    # by decreasing delay, the temperature and CPU will be read
    # more often but their will be additional overhead
    def __init__(self,delay,cpuTrackingEnabled,tempTrackingEnabled):
        self.nextRead = time.time() + delay
        self.delay = delay
        self.temp = self.getCPUtemperature()
        self.cpuUsage = self.getCPUuse()
        self.cpuTrackingEnabled = cpuTrackingEnabled
        self.tempTrackingEnabled = tempTrackingEnabled

    def run(self):
        if (self.nextRead < time.time()):
            if (self.tempTrackingEnabled): self.temp = self.getCPUtemperature()
            if (self.cpuTrackingEnabled): self.cpuUsage = self.getCPUuse()
            self.nextRead = time.time() + self.delay
        return self.temp,self.cpuUsage
    # Return CPU temperature as a character string                                      
    def getCPUtemperature(self):
        res = os.popen('vcgencmd measure_temp').readline()
        return float(res.replace("temp=","").replace("'C\n",""))

    # Return % of CPU used by user as a character string                                
    def getCPUuse(self):
        return float(os.popen("top -n1 | awk '/Cpu\(s\):/ {print $2}'").readline().strip(\
    ))
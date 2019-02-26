# PID.py
# author: Matthew P. Burruss
# last update: 9/6/2018
#Description: PID controller to drive the car.

setSpeed = 0.35 # m/s
maxSetSpeed = 1
maxThrottle = 15.8
KP = 0.013
KI = 0.0001
KD = 0.0002
previousSpeed = error = prevError = accum = 0
def PIDController(speed,acc):
    global previousSpeed, error, prevError, accum,setSpeed,maxSetSpeed
    if (setSpeed > maxSetSpeed):
        setSpeed = maxSetSpeed
    if (speed == 0):
        acc = acc + 0.002
    if (speed != previousSpeed):
        prevError = error
        previousSpeed = speed 
        error = setSpeed - speed
        accum = accum + error
        deriv = error - prevError
        PID = KP*error + KI*accum + KD*deriv
        acc = acc + PID
    if (acc > maxThrottle):
        acc = maxThrottle
    return acc

# Author: Matthew P. Burruss
# Last Updated: 2/14/2019
# Deciphers network messages
import numpy as np
class CommunicationProtocol:
    def __init__(self):
        self.messageComponents = {}
    def getControl(self):
        steer = float(self.messageComponents["STEERING"])
        acc = float(self.messageComponents["ACCELERATION"])
        return acc,steer
    def getType(self):
        return self.messageComponents["TYPE"]
    def getTrialNumber(self):
        return int(self.messageComponents["TRIALS"])
    def getSpeed(self):
        return self.messageComponents["SPEED"]
    def getCPUUtilization(self):
        return self.messageComponents["CPU"]
    def getTemperature(self):
        return self.messageComponents["TEMP"]
    def getDisplacement(self):
        return self.messageComponents["DISPLACEMENT"]
    def getHeading(self):
        return self.messageComponents["HEADING"]
    def shouldStop(self):
        if (self.messageComponents["STOP"]=="TRUE"):
            return True
        else:
            return False
    def getStatus(self):
        return self.messageComponents["STATUS"]
    def getPositionCoordinates(self):
        x = float(self.messageComponents["XCOORD"])
        y = float(self.messageComponents["YCOORD"])
        return x,y
    def decodeMessage(self,message):
        self.messageComponents = {}
        components = message.count('=')
        keyStart = 0
        for i in range(components):
            keyEnd = message.find('=',keyStart)
            valueStart = keyEnd+1
            valueEnd = message.find(';',valueStart)
            if (valueEnd == -1):
                valueEnd = len(message)
            self.messageComponents[message[keyStart:keyEnd]]=message[valueStart:valueEnd]
            keyStart=valueEnd+1
    # following used in data collection
    def getTimestamp(self):
        timestamp = self.messageComponents["TIME"]
        return timestamp
        
    # Following are used by DeepNNCar during configuration
    def getAccelerationMode(self):
        return self.messageComponents["ACCMODE"]
    def getAccelerationFeatures(self):
        return self.messageComponents["ACCMODEFEATURES"]
    def getMode(self):
        return self.messageComponents["MODE"]
    def getOperationModeFeatures(self):
        return self.messageComponents["OPERATIONMODEFEATURES"]

    def isSpeedSensorEnabled(self):
        enabled = self.messageComponents["SPEEDSENSOR"]
        if (enabled == "True"):
            return True
        else:
            return False
            
    def isPathTrackerEnabled(self):
        enabled = self.messageComponents["PATHTRACKER"]
        if (enabled == "True"):
            return True
        else:
            return False

    def isTempTrackerEnabled(self):
        enabled = self.messageComponents["TEMPTRACKER"]
        if (enabled == "True"):
            return True
        else:
            return False

    def isCPUTrackerEnabled(self):
        enabled = self.messageComponents["CPUTRACKER"]
        if (enabled == "True"):
            return True
        else:
            return False
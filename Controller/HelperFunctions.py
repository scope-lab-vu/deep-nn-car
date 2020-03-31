from pydrive.drive import GoogleDrive
from pydrive.auth import GoogleAuth
import os
def sendToGoogleDrive(fileName,filePath,pathToClientSecrets="/home/burrussmp/Documents/DeepNNCar/credentials.json"):
    gauth = GoogleAuth()
    gauth.LoadClientConfigFile(pathToClientSecrets)  # <-----

    drive = GoogleDrive(gauth)

    folder_id = '1OqZVOYfXlEPRKfL1Q_mPWAmEUBlzlt7C'
    file1 = drive.CreateFile({
        'title': 'anomaly.csv',
        "mimeType": "text/csv",
        'parents': [{'id': folder_id}]
    })  # Create GoogleDriveFile instance with title 'Hello.txt'.
    file1.SetContentFile(filePath)
    file1.Upload()
    print("Dataset uploaded")
    print(filePath)
    #os.remove(filePath)
    #print("Dataset removed from local machine")
def displayTitle():
    print("##############################################")
    print("                 DEEPNNCAR                    ")
    print("##############################################")

def selectOperationMode():
    selectedMode = False
    while(not selectedMode):
        print("A: NORMAL Operation")
        print("B: LIVESTREAM Operation")
        print("C: DATACOLLECTION Operation")
        print("D: AUTONOMOUS Operation")
        userInput = input()
        userInput = userInput.lower()
        selectedMode = True
        if (userInput == "a"):
            operationMode = "NORMAL"
        elif (userInput == "b"):
            operationMode = "LIVESTREAM"
        elif(userInput == "c"):
            operationMode = "DATACOLLECTION"
        elif(userInput == "d"):
            operationMode = "AUTO"
        else:
            print("Invalid selection")
            selectedMode = False
    return operationMode

def configureDataCollection():
    trialNumber = input("Enter the number of trials: ")
    return (trialNumber)

def configureAutonomousMode():
    finished = False
    lanedetection = False
    blurrinessmeasurement = False
    offloading = False
    while not finished:
        if not lanedetection: print("A: Enable lane detection")
        if not offloading: print("B: Enable offloading")
        if not blurrinessmeasurement: print("C: Enable blurriness measurement")
        print("1: Enable all features")
        print("2: Finished")
        userInput = input()
        userInput = userInput.lower()
        if (userInput == "a"):
            lanedetection = True
        elif (userInput == "b"):
            offloading = True
        elif(userInput == "c"):
            blurrinessmeasurement = True
        elif(userInput == "1"):
            lanedetection = True
            offloading = True
            blurrinessmeasurement = True
            finished = True
        elif(userInput == "2"):
            finished = True
        else:
            print("Invalid selection")
    return (lanedetection,offloading,blurrinessmeasurement)

def selectAccelerationProtocol():
    selectedMode = False
    while(not selectedMode):
        print("A: USER Controlled")
        print("B: CRUISE Controlled")
        print("C: CONSTANT (duty cycle) controlled")
        userInput = input()
        userInput = userInput.lower()
        selectedMode = True
        if (userInput == "a"):
            accMode = "USER"
        elif (userInput == "b"):
            accMode = "CRUISE"
        elif(userInput == "c"):
            accMode = "CONSTANT"
        else:
            print("Invalid selection")
            selectedMode = False
    return accMode

def configureCruiseControl():
    return input("Enter set speed: ")

def configureConstantDC():
    return input("Enter duty cycle: ")

def configureFeedback():
    finished = False
    temperature = False
    pathtracking = False
    speedsensor = False
    CPU = False 
    while not finished:
        if not temperature: print("A: Enable temperature feedback")
        if not pathtracking: print("B: Enable pathtracking feedback")
        if not speedsensor: print("C: Enable speed sensor feedback")
        if not CPU: print("D: Enable CPU utilization feedback")
        print("1: Enable all features")
        print("2: Finished")
        userInput = input()
        userInput = userInput.lower()
        if (userInput == "a"):
            temperature = True
        elif (userInput == "b"):
            pathtracking = True
            speedsensor = True
        elif(userInput == 'c'):
            speedsensor = True
        elif(userInput == 'd'):
            CPU = True
        elif(userInput == "1"):
            temperature = True
            pathtracking = True
            speedsensor = True
            CPU = True
            finished = True
        elif(userInput == "2"):
            finished = True
        else:
            print("Invalid selection")
    return temperature,pathtracking,speedsensor,CPU
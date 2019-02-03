#test.py
#Authored: Shreyas Ramakrishna
#Last Edited: 10/12/2018
#Description: Script to validate the trained CNN


import numpy as np
from keras.models import model_from_json
import csv
import glob
import cv2
import os
import time
import imageprocess

# Trained CNN
def nncontroller(img, speed, model):
    inputs = np.array(img)[np.newaxis]
    speed =  np.array(speed)[np.newaxis]
    outputs = model.predict([inputs,speed], batch_size=1)
    return float(outputs[0][0])

#File to save the predicted steering values
csvfile = open("kerasvalidation.csv", "w")


def main():
        miny=10  #configured steering PWM
        maxy=20  #configured steering PWM
        minS=14.75 #configured speed PWM
        maxS=15.75 #configured speed PWM
        A = []
        writer = csv.writer(csvfile)
        with open('/home/scope/Shreyas/Car/kerasModel/Trial2/ProcessData.csv') as File:
            reader=csv.reader(File)
            for row in reader:
                output1=[]
                x=(float(row[2])-minS)/(maxS-minS)
                output1.append(x)
                A.append(output1)

        numFiles = len(glob.glob1('/home/scope/Shreyas/Car/kerasModel/Trial2','*.jpg'))
        print("Total number of images collected: %d" %numFiles)
        for i in range(0,numFiles-1):
            x=[]
            image=cv2.imread('/home/scope/Shreyas/Car/kerasModel/Trial2/frame%d.jpg'%i)
            img = cv2.resize(image, (200, 66))
            speed = A[i]
            img = img / 255.
            steer = nncontroller(img, speed, model)
            steering=(float(steer)*(maxy-miny))+miny
            steering=round(steering, 2)
            writer.writerow([steering])

if __name__ == '__main__':
        #Loading the nn model
    with open('model.json', 'r') as jfile:
        model = model_from_json(jfile.read())
    model.load_weights('weights.best.hdf5')

    main()

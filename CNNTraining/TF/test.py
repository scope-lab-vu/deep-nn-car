#train.py
#Authored: Shreyas Ramakrishna
#Reference: https://github.com/mbechtel2/DeepPicar-v2
#Last Edited: 08/14/2018
#Description: Script to validate the trained CNN model.

import cv2
import math
import numpy as np
import time
import os
import model
import imageprocess
import tensorflow as tf
import glob
import csv

save_dir = os.path.abspath('trial1610r')

csvfile = open("validation.csv", "w")

def join(dirpath, filename):
    return os.path.join(dirpath, filename)

def main():
        miny=10
        maxy=20
        #prevsteering=15.73
        sess = tf.InteractiveSession()
        saver = tf.train.Saver()
        model_name = 'test.ckpt'
        model_path = join(save_dir, model_name)
        saver.restore(sess, model_path)
        writer = csv.writer(csvfile)
        numFiles = len(glob.glob1('/home/scope/Shreyas/Car/TF/0310/Trial10','*.jpg'))
        print("Total number of images collected: %d" %numFiles)
        for i in range(0,numFiles-1):
            x=[]
            data=[]
            image=cv2.imread('/home/scope/Shreyas/Car/TF/0310/Trial10/frame%d.jpg'%i)
            img = cv2.resize(image, (200, 66))
            img = img / 255.
            steer = model.y.eval(feed_dict={model.x: [img]})[0][0]
            steering=(float(steer)*(maxy-miny))+miny
            steering=round(steering, 2)
            data.append(pred_time)
            data.append(steering)
            writer.writerow(data)
            
if __name__ == '__main__':
         main()

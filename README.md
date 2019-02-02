# DeepNNCar

![DeepNNCar](https://github.com/scope-lab-vu/deep-nn-car/blob/master/car.png=centerme)

An RC car built to work autonomously, which steers based on end-to-end learning, i.e. the car uses a front camera to make decisions on steering. DeepNNCar has an onboard raspberry pi which acts as the server for the car control. A ZMQ communication is set up between the server (RPi) and the client (laptop) for controlling the car for non-autonomous purposes. Speed of the car is measured using an optocoupler which is attached to the chasis near the rear wheel of the car. Both the speed and steering are controlled interms of internal pwm values of the RPi.

The steering is controlled using a Convolutional Neural Network model which takes in images from the camera at 30FPS and generate steering pwm values for the raspberry pi on board. 

There are two modes of operation which includes, a manual mode for training data collection , and the autonomous mode for testing the end-to-end learning. Besides these two modes there are other features like ACC controller with variable set speed control, live stream mode to see the car path.

**Sensors**
*****
1) Webcamera - To collect front facing images at 30 FPS with a resolution of (320x240x3).
2) IR Opto-Coupler speed sensor - Attached at the rear wheel of the RC car to count the number of revolutions, which is used for speed calculations. 

**Actuation controls**
*****
1) Speed pwm\
2) Steering pwm

**Hardware Components**
*****
Raspberry Pi 3B\
Creative camera\
xbox one controller

Please refer to the Bill of Material for building DeepNNCar  https://docs.google.com/spreadsheets/d/1azQ_Xp9dUmQdm99CKqNXR3qQcVDEEUmMNGrfDghjG6c/edit?usp=sharing

**Installation**
*****
Install the following packages

Install Raspbian stretch using ```https://www.raspberrypi.org/downloads/```

Follow the link to install opencv 3.4 
```
https://www.alatortsev.com/2018/04/27/installing-opencv-on-raspberry-pi-3-b/
```

Install Tensorflow v 1.9
```
sudo apt install libatlas-base-dev
pip3 install tensorflow
```




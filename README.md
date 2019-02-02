# DeepNNCar

![DeepNNCar]()

An RC car built to work autonomously, which steers based on end-to-end learning, i.e. the car uses a front camera to make decisions on steering. DeepNNCar has an onboard raspberry pi which acts as the server for the car control. A ZMQ communication is set up between the server (RPi) and the client (laptop) for controlling the car for non-autonomous purposes. Speed of the car is measured using an optocoupler which is attached to the chasis near the rear wheel of the car. Both the speed and steering are controlled interms of internal pwm values of the RPi.

The steering is controlled using a Convolutional Neural Network model which takes in images from the camera at 30FPS and generate steering pwm values for the raspberry pi on board. 

There are two modes of operation which includes, a manual mode for training data collection , and the autonomous mode for testing the end-to-end learning. Besides these two modes there are other features like ACC controller with variable set speed control, live stream mode to see the car path.

**Inputs**
1)Images from a front facing camera.
2)Speed measurements from optocoupler attached to the rear wheel. 

**Output controls**

1) Throttle Position:
2) Speed
3) Steering:

**Hardware Components**

Raspberry Pi 3B\
Creative camera\
xbox one controller

**Software Required**

Raspbian stretch\
opencv 3.4 / opencv 2.4\
Tensorflow v

**Installing Opencv 2.4 on Raspberry Pi 3B**

http://bennycheung.github.io/raspberry-pi-3-for-computer-vision

sudo apt-get upate\
sudo apt-get upgrade\
sudo apt-get install python-setuptools\
sudo apt-get install python-pip\
sudo apt-get install ipython python-opencv python-scipy python-numpy python-pygame

**Installing Opencv 3.4 on Raspberry Pi 3B**

https://github.com/ys7yoo/PiOpenCV

**Startup**

SSH to Rpi\
Run sudo python TCP_Server.py on server\
Run sudo python XBOX-360-Controller.py on client\
Click START on controller to begin data collection


The Bill of Material for building DeepNNCar is available at https://docs.google.com/spreadsheets/d/1azQ_Xp9dUmQdm99CKqNXR3qQcVDEEUmMNGrfDghjG6c/edit?usp=sharing

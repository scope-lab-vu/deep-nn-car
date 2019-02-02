# DeepNNCar

<p align="center">
   <img src="https://github.com/scope-lab-vu/deep-nn-car/blob/master/images/car.png" align="center" width="600" height="400">
</p>

An RC car built to work autonomously by taking in images from a front facing camera and predicting the steering using CNN (modified version of NVIDIA's DAVE II model). DeepNNCar has an onboard raspberry pi which acts as the server for the car control. A ZMQ communication is set up between the server (RPi) and the client (laptop) for controlling the car for non-autonomous purposes. 

We also introduce a middleware framework which allow for seamless integration of safety controllers and different
simplex strategies to aid the LEC driven system. 

# Video

The video shows DeepNNCar using CNN to autonomously drive along with a PID controller to run at different speeds. From the video it can be seen that DeepNNCar cuts the track at higher speeds of (~0.5 m/s - 0.6 m/s).

<div align="center">
  <a href="https://youtu.be/t85WKP4ReVk"><img src="https://github.com/scope-lab-vu/deep-nn-car/blob/master/images/track1a.png" alt="DeepNNCar driving with CNN"></a>
</div>

Videos of DeepNNCar running with different controllers, and simplex strategies (AM-Simplex, RL-Simplex) on different tracks can be found at https://drive.google.com/drive/folders/1R1zYEBODPiILqDugScLen24LZi1txLj9?usp=sharing 

# Operating Modes

The different operating modes of DeepNNCar are:
1) **Data collection mode**: This mode allows us to control the car using xbox controller. We collect images, steering (pwm) and speed (pwm) for training the CNN.
2) **Live stream mode**: This modes allows us to relay images taken by the car as a video stream to the laptop. In addition we have live plotting of speed, steering and 2D position of the car.
3) **Autonomous mode**: The trained CNN model is used to predict the steering, and speed can be controlled by a PID controller. Alternatively we have introduced different simplex strategies (AM-Simplex, RL-Simplex) which can be used to drive the car autonomously.

# Sensors and Actuations

**Sensors**

1) **Webcamera**: To collect front facing images at 30 FPS with a resolution of (320x240x3).
2) **IR Opto-Coupler speed sensor**: Attached at the rear wheel of the RC car to count the number of revolutions, which is used for speed calculations. 

**Actuation controls**

1) Speed pwm
2) Steering pwm

# Components for building DeepNNCar

Please refer to the Bill of Material for building DeepNNCar  https://docs.google.com/spreadsheets/d/1azQ_Xp9dUmQdm99CKqNXR3qQcVDEEUmMNGrfDghjG6c/edit?usp=sharing

# Installation

Install the following packages and dependencies

```
sudo apt-get install python3
sudo apt-get install python3-pip
```

Follow the link to download the Raspbian stretch image and copy it onto an SD card.

```https://www.raspberrypi.org/documentation/installation/installing-images/```

Follow the link to install opencv 3.4 
```
https://www.alatortsev.com/2018/04/27/installing-opencv-on-raspberry-pi-3-b/
```

Install Tensorflow v1.9
```
sudo apt install libatlas-base-dev
pip3 install tensorflow
```
Install the latest version of keras
```
sudo apt-get install python3-numpy
sudo apt-get install libblas-dev
sudo apt-get install liblapack-dev
sudo apt-get install python3-dev 
sudo apt-get install libatlas-base-dev
sudo apt-get install gfortran
sudo apt-get install python3-setuptools
sudo apt-get install python3-scipy
sudo apt-get update
sudo apt-get install python3-h5py
sudo pip3 install keras 
```

Follow the link to install pigpio library for configuring the hardware interrupts.
```
http://abyz.me.uk/rpi/pigpio/download.html
```

# Acknowledgement

Some of the source code and the Tensorflow version of NVIDIA's CNN model were taken from DeepPiCar (https://github.com/mbechtel2/DeepPicar-v2) and MIT's deeptesla (https://github.com/lexfridman/deeptesla).


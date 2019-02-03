# DeepNNCar: Testbed for Autonomous driving

<p align="center">
   <img src="https://github.com/scope-lab-vu/deep-nn-car/blob/master/images/car.png" align="center" width="600" height="400">
</p>

DeepNNCar is built upon the chassis of Traxxas Slash 2WD 1/10 Scale RC car which uses Raspberry Pi 3b (RPi3) as the onboard computing unit. It works autonomously by using a CNN (modified version of NVIDIA's DAVE II model) which takes in images from a front facing camera, speed (PWM) from an IR opto-coupler speed sensor to predict the steering (PWM). The onboard RPi3 which acts as the server for the car control, and a ZMQ communication is set up between the server (RPi3) and the client (laptop) for controlling the car for non-autonomous purposes. 

We have also implemented a middleware framework which allow for seamless integration of safety controllers and different
simplex strategies to aid the LEC driven system. Some other additional features of the framework is resource management, and dynamic task offloading.

***Tracks***
Different indoor tracks were designed using 10x12 blue tarps. These tracks were used for training and testing during our experiments.

<p align="center">
   <img src="https://github.com/scope-lab-vu/deep-nn-car/blob/master/images/tracks.png" align="center" width="500" height="300">
</p>

# Video

The video shows DeepNNCar using CNN to autonomously drive along with a PID controller to run at different speeds. From the video it can be seen that DeepNNCar cuts the track at higher speeds of (~0.5 m/s - 0.6 m/s).

<div align="center">
  <a href="https://youtu.be/t85WKP4ReVk"><img src="https://github.com/scope-lab-vu/deep-nn-car/blob/master/images/track1a.png" alt="DeepNNCar driving with CNN"></a>
</div>

Videos of DeepNNCar running with different controllers, and simplex strategies (AM-Simplex, RL-Simplex) on different tracks can be found at https://drive.google.com/drive/folders/1R1zYEBODPiILqDugScLen24LZi1txLj9?usp=sharing

# Operating Modes

The different operating modes of DeepNNCar are:
1) **Data collection mode**: In this mode the car is manually driven using xbox controller to collect images, steering (PWM) and speed (PWM) for training the CNN.
2) **Live stream mode**: This modes allows us to relay images taken by the car as a video stream to the laptop. In addition we have live plotting of speed, steering and 2D position of the car.
3) **Autonomous mode**: The trained CNN model is used to predict the steering, and speed can be controlled by a PID controller. Alternatively we have introduced different simplex strategies (AM-Simplex, RL-Simplex) which can be used to drive the car autonomously.

# Sensors and Actuations

**Sensors**

1) **Webcamera**: To collect front facing images at 30 FPS with a resolution of (320x240x3).
2) **IR Opto-Coupler speed sensor**: Attached at the rear wheel of the RC car to count the number of revolutions, which is used for speed calculations. 

**Actuation controls**

1) **Speed PWM**: PWM ranges from (15,15.8) which corresponds to speed (0,1) m/s.
2) **Steering PWM**: PWM ranges from (10,20) which corresponds to an angle range of (-30,30) degrees.

# Components for building DeepNNCar

Please refer to the Bill of Material for building DeepNNCar https://docs.google.com/spreadsheets/d/1azQ_Xp9dUmQdm99CKqNXR3qQcVDEEUmMNGrfDghjG6c/edit?usp=sharing

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


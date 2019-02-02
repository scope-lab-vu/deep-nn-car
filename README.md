# DeepNNCar

![DeepNNCar](https://github.com/scope-lab-vu/deep-nn-car/blob/master/car.png =200x100)

An RC car built to work autonomously by taking in images from a front facing camera and predicting the steering using CNN (modified version of NVIDIA's DAVE II model). DeepNNCar has an onboard raspberry pi which acts as the server for the car control. A ZMQ communication is set up between the server (RPi) and the client (laptop) for controlling the car for non-autonomous purposes. 

We also introduce a middleware framework which allow for seamless integration of safety controllers and different
simplex strategies to aid the LEC driven system. 

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

Install Tensorflow v 1.9
```
sudo apt install libatlas-base-dev
pip3 install tensorflow
```
Follow the link to install pigpio library for configuring the hardware interrupts.
```
http://abyz.me.uk/rpi/pigpio/download.html
```


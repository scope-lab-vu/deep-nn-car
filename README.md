# DeepNNCar: A Testbed for Autonomous driving

<p align="center">
   <img src="https://github.com/scope-lab-vu/deep-nn-car/blob/master/images/new-car1.pdf" align="center" width="600" height="400">
</p>

DeepNNCar is built upon the chassis of Traxxas Slash 2WD 1/10 Scale RC car which uses Raspberry Pi 3b (RPi3) as the onboard computing unit. It works autonomously by using a CNN (modified version of NVIDIA's DAVE II model) which takes in images from a front facing camera, speed (PWM) from an IR opto-coupler speed sensor to predict the steering (PWM). The onboard RPi3 which acts as the server for the car control, and a ZMQ communication is set up between the server (RPi3) and the client (laptop) for controlling the car for non-autonomous purposes. 

We have also implemented a middleware framework which allow for seamless integration of safety controllers and different
simplex strategies to aid the LEC driven system. Some other additional features of the framework is resource management, and dynamic task offloading.

***Tracks***
Different indoor tracks were designed using 10x12 blue tarps. These tracks were used for training and testing during our experiments. These tracks can be designed for experimentation using blue tarps and white tape to design the lanes.

<p align="center">
   <img src="https://github.com/scope-lab-vu/deep-nn-car/blob/master/images/tracks.png" align="center" width="600" height="200">
</p>

# Video

The video shows DeepNNCar using CNN to autonomously drive along with a PID controller to run at different speeds. From the video it can be seen that DeepNNCar cuts the track at higher speeds of (~0.5 m/s - 0.6 m/s).

<div align="center">
  <a href="https://youtu.be/t85WKP4ReVk"><img src="https://github.com/scope-lab-vu/deep-nn-car/blob/master/images/track1a.png" alt="DeepNNCar driving with CNN"></a>
</div>

Videos of DeepNNCar running with different controllers, and simplex strategies (AM-Simplex, RL-Simplex) on different tracks can be found at https://drive.google.com/drive/folders/1R1zYEBODPiILqDugScLen24LZi1txLj9?usp=sharing

# Operating Modes

The different operating modes of DeepNNCar are:
1) **Data collection mode**: In this mode the car is manually driven using xbox controller (old method) or a mouse (new method) to collect images, steering (PWM) and speed (PWM) for training the CNN. The scripts for setting up the data collection mode can be found in [Data Collection](https://github.com/scope-lab-vu/deep-nn-car/tree/master/DataCollection)
2) **Live stream mode**: This modes allows us to relay images taken by the car as a video stream to the laptop. In addition we have live plotting of speed, steering and 2D position of the car. The live stream option is integrated with the manual driving or data collection mode. The commands to execute the live stream option can be found in [Data Collection](https://github.com/scope-lab-vu/deep-nn-car/tree/master/DataCollection)
3) **Autonomous mode**: Drives DeepNNCar autonomously using the [trained CNN](https://github.com/scope-lab-vu/deep-nn-car/tree/master/CNNTraining) model. THe user can use different simplex strategies (AM-Simplex, RL-Simplex) to drive the car autonomously. The scripts and instructions for autonomous mode excution can be found at [Autonomous mode](https://github.com/scope-lab-vu/deep-nn-car/tree/master/AutonomousDriving)

# Sensors and Actuations

**Sensors**

1) **Webcamera**: To collect front facing images at 30 FPS with a resolution of (320x240x3).
2) **IR Opto-Coupler speed sensor**: Attached at the rear wheel of the RC car to count the number of revolutions, which is used for speed calculations. 

**Actuation controls**

1) **Speed PWM**: PWM ranges from (15,15.8) which corresponds to speed (0,1) m/s.
2) **Steering PWM**: PWM ranges from (10,20) which corresponds to an angle range of (-30,30) degrees.

# Important Links

Components and assembly of DeepNNCar can be found at: [Components and Assembly](https://github.com/scope-lab-vu/deep-nn-car/wiki/Components-and-Assembly)

Configuring the server and client setup for DeepNNCar can be performed by following the instructions at [Configuring server and client](https://github.com/scope-lab-vu/deep-nn-car/wiki/Configuring-the-Server-and-Client)

Some Safety features implemented on DeepNNCar are discussed in [DeepNNCar Safety Features](https://github.com/scope-lab-vu/deep-nn-car/wiki/DeepNNCar-features)

DIfferent acceleration protocols implemented in DeepNNCar can be found at [Acceleration protocols](https://github.com/scope-lab-vu/deep-nn-car/blob/master/acceleration.pdf) the code for which is [Controller.py](https://github.com/scope-lab-vu/deep-nn-car/blob/master/DataCollection/Client/controller.py)

Some common errors we encountered during our experiments is discussed in [Troubleshooting common errors](https://github.com/scope-lab-vu/deep-nn-car/wiki/Troubleshooting)

# Components for building DeepNNCar

Please refer to the Bill of Material for building DeepNNCar https://docs.google.com/spreadsheets/d/1azQ_Xp9dUmQdm99CKqNXR3qQcVDEEUmMNGrfDghjG6c/edit?usp=sharing

# Research with DeepNNCar

The paper using DeepNNCar platform "Augmenting Learning Components for Safety in Resource Constrained Autonomous Robots" can be found at https://ieeexplore.ieee.org/abstract/document/8759270

Citation

```
@inproceedings{ramakrishna2019augmenting,
  title={Augmenting learning components for safety in resource constrained autonomous robots},
  author={Ramakrishna, Shreyas and Dubey, Abhishek and Burruss, Matthew P and Hartsell, Charles and Mahadevan, Nagabhushan and Nannapaneni, Saideep and Laszka, Aron and Karsai, Gabor},
  booktitle={2019 IEEE 22nd International Symposium on Real-Time Distributed Computing (ISORC)},
  pages={108--117},
  year={2019},
  organization={IEEE}
}
```

# Acknowledgement

Some of the source code and the Tensorflow version of NVIDIA's CNN model were taken from DeepPiCar (https://github.com/mbechtel2/DeepPicar-v2) and MIT's deeptesla (https://github.com/lexfridman/deeptesla).

Some interesting papers used during our work.

1) DeepPicar: A Low-cost Deep Neural Network-based Autonomous Car (https://arxiv.org/abs/1712.08644)

2) Arguing Machines: Human Supervision of Black Box AI Systems That Make Life-Critical Decisions (https://arxiv.org/abs/1710.04459)

3) A Component-Based Simplex Architecture for High-Assurance Cyber-Physical Systems (https://arxiv.org/abs/1704.04759)

4) Application of software health management techniques (https://dl.acm.org/citation.cfm?id=1988010)





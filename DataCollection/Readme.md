# Data collection using xbox controller

Images, steer(PWM) and speed(PWM) data is collected using xbox controller. This mode works using the client-server shown below. 
Note: This part of the data collection mode uses TCP for wireless communication, however for the rest of the autonomous driving we have moved to ZMQ.

<p align="center">
   <img src="https://github.com/scope-lab-vu/deep-nn-car/blob/master/images/architecture.png" align="center" width="600" height="300">
</p>

# Different buttons of the xbox controller

The different buttons configured on the xbox controller are shown in the figure.

<p align="center">
   <img src="https://github.com/scope-lab-vu/deep-nn-car/blob/master/images/Xbox%20Controller.PNG" align="center" width="600" height="300">
</p>

# Client and Server

***Client***
It has all the scripts needed to be run on the client side. The controller.py script has all the buttons configured to control the car. The code used for the xbox controller is compatible for windows and hence this can be run on any editor in windows. The PlotTools.py script is used for live plotting of the speed, steering and 2d trajectory of the car. (which can be seen on the laptop)
Note: Add the correct RPi3 ip address to start the wireless communication.

***Server***
Has all the scripts to be run on the RPi3. Server.py is the main script which connects with the client and it has all the funtions to collect sensor data and storing them onboard till the script is terminated. On termination the data is writen to a folder in the USB. Along with the main scripts there are other dependecy scripts for GPIO configuration, RPM measurement and speed calculations, image capture from webcam, etc.

***Startup***

SSH to Rpi\
Run sudo python Server.py on server (run on RPi3)\ 
Run python controller.py on client (run on windows)\ 
Click START on controller to begin data collection. (X button on the xbox controller)


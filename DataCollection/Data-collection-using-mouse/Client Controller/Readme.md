# Data collection using mouse control (new method)
Images, steer(PWM) and speed(PWM) data is collected using mouse control. 


# Data collection using xbox controller (old method)

Images, steer(PWM) and speed(PWM) data is collected using xbox controller. This mode works using the client-server shown below. 
Note: This part of the data collection mode uses TCP for wireless communication, however for the rest of the autonomous driving we have moved to ZMQ.

<p align="center">
   <img src="https://github.com/scope-lab-vu/deep-nn-car/blob/master/images/architecture2.png" align="center" width="600" height="300">
</p>

***Different buttons of the xbox controller***

The different buttons configured on the xbox controller are shown in the figure.

<p align="center">
   <img src="https://github.com/scope-lab-vu/deep-nn-car/blob/master/images/Xbox%20Controller.PNG" align="center" width="600" height="300">
</p>

***Client and Server scripts***

***Client***
It has all the scripts needed to be run on the client side. The controller.py script has all the buttons configured to control the car. The code used for the xbox controller is compatible for windows and hence this can be run on any editor in windows. The PlotTools.py script is used for live plotting of the speed, steering and 2d trajectory of the car. (which can be seen on the laptop)
***Note***: Add the correct RPi3 ip address to start the wireless communication. Also, scripts on the client use python2, because of the way we have configured the image transfer on the client side. However, we are updating the code base to use python3.

***Server***
Has all the scripts to be run on the RPi3. Server.py is the main script which connects with the client and it has all the funtions to collect sensor data and storing them onboard till the script is terminated. On termination the data is writen to a folder in the USB. Along with the main scripts there are other dependecy scripts for GPIO configuration, RPM measurement and speed calculations, image capture from webcam, etc.
***Note***: All scripts on the RPi3 uses python3.

***Startup***
To run the data collection mode to collect data, you need to run the following scripts on the server and the client.

First SSH into the RPi3. Configuring SSH on RPi3 has been discussed in our design manual. You will have to use your password to ssh into RPi3.
```
SSH pi@IP
```
Once you could ssh into the device, you will have to run the pigpiod library. Then you will have to navigate to the directory where all the scripts are saved.
```
sudo pigpiod
```
Now you could run the main script on the RPi3.
```
sudo python3 Server.py
```
Now, prepare the client for the server-client setup. The xbox configuration uses a windows supported code and hence we need to run the client scripts on any windows based editor. (We use pycharm as our editor)
```
python controller.py
```
After both the scripts are started on the two devices, you will have the DeepNNCar ready to run. Initially if no mode is selected, the car will run in a manual mode, where you can control the steering and speed of the car and drive it around the track. Then you can start the data collection mode.
```
Press X on the xbox controller to begin data collection.
```

***Note***: Before executing the Server.py script on the RPi3, you will need to turn on the DeepNNCar as we have some part of the script which initializes the motors. If you do not turn on the DeepNNCar before executing the Server.py script, then the car will not move.

# Data collection using xbox controller

Images, steer(PWM) and speed(PWM) data is collected using xbox controller. This mode works using the client-server shown below.

<p align="center">
   <img src="https://github.com/scope-lab-vu/deep-nn-car/blob/master/images/architecture.png" align="center" width="600" height="300">
</p>

# Different buttons of the xbox controller

The different buttons configured on the xbox controller are shown in the figure.

<p align="center">
   <img src="https://github.com/scope-lab-vu/deep-nn-car/blob/master/images/Xbox%20Controller.PNG" align="center" width="600" height="300">
</p>

# Startup

SSH to Rpi\
Run sudo python Server.py on server\
Run sudo python controller.py on client\
Click START on controller to begin data collection. (X button on the xbox controller)


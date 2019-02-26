# Autonomous Driving Mode

This mode allows you to drive DeepNNCar using the trained CNN. It allows you to select any one of the Simplex Architectures which includes the AM-Simplex or RL-Simplex (explained in https://arxiv.org/abs/1902.02432)

The code base uses the component based architecture shown below.

<p align="center">
   <img src="https://github.com/scope-lab-vu/deep-nn-car/blob/master/images/Blockdiagram.png" align="center" width="500" height="300">
</p>


[Autonomous.py](https://github.com/scope-lab-vu/deep-nn-car/blob/master/AutonomousDriving/Autonomous.py) is the main script that has to be run on the RPi3 (use python3). 

```
sudo python3 Autonomous.py
```

As you execute the script, you will be prompted to select various options. 



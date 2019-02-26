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
```
Select the Simplex Architecture you want to run

AM-Simplex => 0

RL-Simplex => 1
```
Use the prompt to select the simplex architecture you want to run. In AM-Simplex the weights are fixed (for our track and scenario), which has to be determined through various trials. However, for RL-Simplex the weights have to be determied using Q-learning exploration. 

If you select AM-Simplex you will be prompted to select
```
rounds: Number of rounds you want the car to run
```

If you select RL-Simplex, you will be asked to select the options below
```
Exploration => 0

Exploitation => 1
```

If you further select exploration, you will be asked for
```
exploration_steps: Number of exploration steps

rounds: Number of rounds you want the car to run
```

If you select exploitation, you will be asked for
```
rounds: Number of rounds you want the car to run
```



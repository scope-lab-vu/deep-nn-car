#RLCar.py
#Authored: Shreyas Ramakrishna
#Last Edited: 02/25/2019
#Description: RL Actor which computes the arbitration weights and the throttle value


import numpy as np
import random
import csv
import pickle

gamma  = 0.4
alpha = 0.1
epsilon = 0.1
penalties,reward,i,x,k,maxQ = (0,0,0,0,0,0)

# STATES
Qtable = {}
weight = [0.0,0.05,0.10,0.15,0.20,0.25,0.30,0.35,0.40,0.45,0.50,0.55,0.60,0.65,0.70,0.75,0.80,0.85,0.90,0.95,1.0]
speed = [15.5800,15.5810,15.5820,15.5830,15.5840,15.5850,15.5860,15.5870,15.5880,15.5890,15.5900,15.5910,
15.5920,15.5930,15.5940,15.5950,15.5960,15.5970,15.5980,15.5990,15.6000,15.6010,15.6020,15.6030,15.6040,
15.6050,15.6060,15.6070,15.6080,15.6090,15.6100, 15.6110,15.6120,15.6130,15.6140,15.6150,15.6160,15.6170,15.6180,15.6190,15.6200,15.6210, 15.6220,15.6230,15.6240,15.6250,15.6260,15.6270,15.6280,15.6290,15.6300]
deltaSpeed = 0.0010
deltaWeight = 0.05

# ACTIONS
changeSpeed = np.array([0,deltaSpeed,-deltaSpeed]) #speed can either increase/decrease by 0.0025, or remain same
changeWeight = np.array([0,deltaWeight,-deltaWeight]) #weights can either increase/decrease by 0.20, or remain same

# Initializes Q table with state-action as keys (w1,w2,speed,deltaSpeed,deltaWeight) and value 0
# We have a total of 918 state-action pairs
# 102 states x 9 actions
def initQTable():
  global Qtable,weight,speed,changeSpeed,changeWeight
  for i in range(21):
    for k in range(51):
      # actions
      for l in range(changeSpeed.size):
        for m in range(changeWeight.size):
          Qtable[(weight[i],round(1.0-weight[i],2),speed[k],changeSpeed[l],changeWeight[m])] = 0.0

  return Qtable

# load the trained Q table
def pickletable():
    file = open('Qtable.pkl', 'rb')
    Qtable = pickle.load(file)
    return Qtable


# Given a state and all potential next actions
# Return the optimal next state and the action that would result in that state
# There are 9 actions to explore
# Qtable => table containing state-action pair values
# state => current state
def searchOptimalNextState(state, lanedetection,Qtable):
    global weight,changeSpeed,changeWeight,speed,deltaSpeed,deltaWeight,maxQ,k,j
    maxQ_old = maxQ # Q value of the current state
    
    # by default, set next state to current state and action to not change weights/speed
    nextState = state
    maxQ = Qtable[(state[0],state[1],state[2],changeSpeed[0],changeWeight[0])]
    maxQ = round(maxQ,2)
    action = (changeSpeed[0],changeWeight[0])

    # search all possible next states
    if(state[0]==1):
        possibleWeights = np.array([state[0],round(state[0]-deltaWeight,2)])
        actionWeight = np.array([0,-deltaWeight])
    elif(state[0]==0):
        possibleWeights = np.array([state[0],round(state[0]+deltaWeight,2)])
        actionWeight = np.array([0,deltaWeight])
    else:
        possibleWeights = np.array([state[0],round(state[0]+deltaWeight,2),round(state[0]-deltaWeight,2)])
        actionWeight = np.array([0,deltaWeight,-deltaWeight])

    if(state[2] == speed[0]):
        possibleSpeeds = np.array([state[2],round(state[2]+deltaSpeed,4)])
        actionSpeed = np.array([0,deltaSpeed])
    elif((state[2] == speed[40]) or (lanedetection==1 or lanedetection==2)):
        possibleSpeeds = np.array([round(state[2]-deltaSpeed,4)])
        actionSpeed = np.array([-deltaSpeed])
    else:
        possibleSpeeds = np.array([state[2],round(state[2]+deltaSpeed,4),round(state[2]-deltaSpeed,4)])
        actionSpeed = np.array([0,deltaSpeed,-deltaSpeed])

    for i in range(possibleWeights.size):
        for j in range(possibleSpeeds.size):
            # if we find a Q-value > than current best, set to next state and save action
            if(Qtable[(possibleWeights[i],round(1.0-possibleWeights[i],2),round(possibleSpeeds[j],4),actionSpeed[j],actionWeight[i])] > maxQ):
              if(bool(random.getrandbits(1))):
                  maxQ = Qtable[(possibleWeights[i],round(1.0-possibleWeights[i],2),round(possibleSpeeds[j],4),actionSpeed[j],actionWeight[i])]#next state maxQ
                  nextState = (possibleWeights[i],round(1.0-possibleWeights[i],2),round(possibleSpeeds[j],4))
                  action = (actionSpeed[j],actionWeight[i])
            # if we find a Qvalue equal to our own, select action increase speed > maintain speed > decrease speed
            elif(Qtable[(possibleWeights[i],round(1.0-possibleWeights[i],2),round(possibleSpeeds[j],4),actionSpeed[j],actionWeight[i])] == maxQ):

                # if current best action has the same speed as new best action, choose action with 50/50 probability
                if(action[0] == actionSpeed[j]):
                    if(bool(random.getrandbits(1))):
                      nextState = (possibleWeights[i],round(1.0-possibleWeights[i],2),round(possibleSpeeds[j],4))
                      action = (actionSpeed[j],actionWeight[j])

                # if the new state-action pair has a preferred speed action, again increase > maintain > decrease
                # then select new state-action pair as the best state-action pair
                elif((action[0]==0 and actionSpeed[j] == deltaSpeed) or (action[0]==-deltaSpeed and actionSpeed[j]==0) or (action[0]==0 and actionSpeed[j] == -deltaSpeed) ):
                    #possibleSpeeds[j]=random.choice(possibleSpeeds)
                    #maxQ = Qtable[(possibleWeights[i],round(1.0-possibleWeights[i],2),round(possibleSpeeds[j],2),actionSpeed[j],actionWeight[j])]
                    nextState = (possibleWeights[i],round(1.0-possibleWeights[i],2),round(possibleSpeeds[j],4))
                    action = (actionSpeed[j],actionWeight[i])


    return nextState,action, maxQ_old, maxQ

#environment function to evaluate the position of the car on the trackself.
#Also assign reward values based on the position
def env(lanedetection):
    #if car is out of track
    if(lanedetection == -1):
        reward_val = 100
    #straight gets highest reward
    elif(lanedetection == 3):
        reward_val = 0 #-1
    #left or right gets slightly low reward
    elif(lanedetection == 2 or lanedetection == 1):
        reward_val = 1/2
    return reward_val


#Function which is run every stepself.
def run(acc,lanedetection,w1,w2,exploration_steps,explore,Qtable):
    global gamma, alpha, epsilon, episode_count,penalties,reward,i,x
    #define current state which includes weights and acc
    state = (w1,w2,acc)
    #Explore the possible states for defined exploration state numbers
    newState,action, maxQ_old, maxQ = searchOptimalNextState(state,lanedetection,Qtable)

    if(exploration_steps >= 1):
        print('exploring %d'%exploration_steps)
        if(epsilon - (1.0 / exploration_steps)) > 0:
            #update the value calculated depending on the reward
            #Reward value evaluated based on the position of the car in the track
            reward_val = env(lanedetection)
            # Reward as a function of speed
            # So, if you go straight, you get higher speed as compared to left, right or center of track
            #if car in center reward = acc
            #if car not in center/left/Right reward = acc/2
            #if car out of track reward = 0
            reward = acc - acc*reward_val
            new_value = (1-alpha) * maxQ_old + alpha * ( reward + gamma * maxQ)
            new_value = round(new_value,3)
            Qtable[state,action]=new_value

            # Setup penalties for each episode
            if (reward_val == 100):
                penalties +=1
            else:
                penalties = 0

            if (penalties == 10):
                print("end episode: %d" %i)


            state = newState

        #Save the Q-table as pickle file
        if(exploration_steps==11):
            with open('Qtable.pkl', 'wb') as file:
                pickle.dump(Qtable, file)

    else:
        # exploitation
        print("exploiting")
        state = newState


    return newState[0],newState[1],newState[2]

    if __name__ == '__main__':
        initQTable()

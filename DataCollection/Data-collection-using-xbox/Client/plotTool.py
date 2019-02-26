# plotTool.py
# author: Matthew P. Burruss
# last update: 8/14/2018i
# Description
# defines functions to display real-time feedback from server in an animated graph

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time

# IMMUTABLE
vx = [0]
vy = [0]
setSpeeds = [0]
sx = [0]
sy = [0]
lx = [0]
ly = [0]

# MUTABLE
truncate = True
MAXARRAYSIZE = 100

# truncateGraph()
# Description: If truncate is True, then move animated graph to maxArraySize
def truncateGraph():
    global vx,vy,sx,sy,setSpeeds
    if (len(vx)>MAXARRAYSIZE):
        vx= vx[len(vx)-MAXARRAYSIZE:len(vx)]
    if (len(vy)>MAXARRAYSIZE):
        vy= vy[len(vy)-MAXARRAYSIZE:len(vy)]
    if (len(setSpeeds)>MAXARRAYSIZE):
        setSpeeds = setSpeeds[len(setSpeeds)-MAXARRAYSIZE:len(setSpeeds)]
    if (len(sx)>MAXARRAYSIZE):
        sx= sx[len(sx)-MAXARRAYSIZE:len(sx)]
    if (len(sy)>MAXARRAYSIZE):
        sy = sy[len(sy)-MAXARRAYSIZE:len(sy)]

# Add input functions
# Description: Controller.py calls these functions in realtime
def addLocationInput(xn,yn):
    global lx, ly
    lx.append(xn)
    ly.append(yn)
def addSpeedInput(xn,yn,setSpeed):
    global vx,vy,setSpeeds
    vx.append(xn)
    vy.append(yn)
    setSpeeds.append(setSpeed)
def addSteerInput(xn,yn):
    global sx,sy
    sx.append(xn)
    sy.append(yn)
    
# get input functions
# Description: Called by animate function to update dynamic graph
def getSpeedInput():
    global vx,vy,setSpeeds
    return vx,vy,setSpeeds
def getSteerInput():
    global sx,sy
    return sx,sy
def getLocationInput():
    global lx,ly
    return lx,ly

# animateGraph()
# Description: Creates 3 subplots displaying speed (m/s), steering angle (deg), and 2D position estimate 
def animateGraph():
    global fig
    fig = plt.figure()
    ax1 = fig.add_subplot(3,1,1)
    ax2 = fig.add_subplot(3,1,2)
    ax3 = fig.add_subplot(3,1,3)
    # animate()
    # Description: Every 200 ms, get speed, steering angle, and displacement estimate and update dynamic graph
    def animate(i):
        if (truncate): truncateGraph()
        (vx,vy,setSpeeds) = getSpeedInput()
        (sx,sy) = getSteerInput()
        (lx,ly) = getLocationInput()
        try:
            ax1.clear()
            ax1.set_ylim(-0.5,1.5)
            ax1.plot(vx,vy,label = "Current Speed")
            ax1.plot(vx,setSpeeds,label = "Set Speed")
            ax1.set_title("Speed Time Series")
            ax1.set_ylabel("Speed (m/s)")
            ax1.set_xlabel("Time (s)")
            ax1.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3, ncol=2, mode="expand", borderaxespad=0.)
            ax2.clear()
            ax2.set_ylim(-35,35)
            ax2.plot(sx,sy)
            ax2.set_title("Steering Time Series")
            ax2.set_ylabel("Steering Angel (deg)")
            ax2.set_xlabel("Time (s)")
            ax3.clear()
            ax3.plot(lx,ly)
            ax3.set_title("2D position estimate")
            ax3.set_ylabel(" Y displacement (m)")
            ax3.set_xlabel(" X displacement (m)")
        except:
            print('s')
    plt.grid(True)
    plt.subplots_adjust(hspace = 1,wspace = 0.6)
    ani = animation.FuncAnimation(fig, animate, interval=200)
    plt.show()



# Controller.py
# author: Matthew P. Burruss
# Adapted from Jason R. Coombs' code here: http://pydoc.net/Python/jaraco.input/1.0.1/jaraco.input.win32.xinput/ under the MIT licence terms
# last update: 8/14/2018
# Description:
# Provides XBOX controller interface to communicate with DeepNNCar
# BUTTON LAYOUT
# Right trigger => acceleration forward
# Left trigger => acceleration reverse
# Left joystick => movement left/right
# X button => Data collection mode
# A button => Autonomous driving mode
# B button => STOP signal
# Y button => live stream mode
# Up (directional pad) => increment ref speed of PID controller
# Down (directional pad) => decrement ref speed of PID controller

import ctypes
import sys
import time
import socket
from threading import Thread
import threading
import logging
import sys
from operator import itemgetter, attrgetter
from itertools import count, starmap
from pyglet import event
import pyformulas as pf
import matplotlib.pyplot as plt
import numpy as np
import time
import math
import Client
import plotTool

# IMMUTABLE
liveStreamPort = 5002
mainPort = 5001
idle_dcTuple = (
15, 15)  # (steering,acceleration) # note steering may need to be adjusted, yet the range should stay at 10.
dcTuple = idle_dcTuple
# MUTABLE
server_address = ('10.66.204.190', mainPort)#204
forward_Range = 1.0  # %python
reverse_Range = 0.8  # %
steering_Range = 12  # %
constantDCEnabled =False
steeringBasedDCEnabled = False
steeringBasedSpeedModeConstant = 0.05
# PID Parameters
cruiseControlEnabled = False
setSpeed = 0.25  # m/s
maxSetSpeed = 1.5
delta = 0.05  # increment/decrement speed by delta using D pad (user controlled)
KP = 0.013
KI = 0.0001
KD = 0.0002


class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ('buttons', ctypes.c_ushort),  # wButtons
        ('left_trigger', ctypes.c_ubyte),  # bLeftTrigger
        ('right_trigger', ctypes.c_ubyte),  # bLeftTrigger
        ('l_thumb_x', ctypes.c_short),  # sThumbLX
        ('l_thumb_y', ctypes.c_short),  # sThumbLY
        ('r_thumb_x', ctypes.c_short),  # sThumbRx
        ('r_thumb_y', ctypes.c_short),  # sThumbRy
    ]


class XINPUT_STATE(ctypes.Structure):
    _fields_ = [
        ('packet_number', ctypes.c_ulong),  # dwPacketNumber
        ('gamepad', XINPUT_GAMEPAD),  # Gamepad
    ]


class XINPUT_VIBRATION(ctypes.Structure):
    _fields_ = [("wLeftMotorSpeed", ctypes.c_ushort),
                ("wRightMotorSpeed", ctypes.c_ushort)]


class XINPUT_BATTERY_INFORMATION(ctypes.Structure):
    _fields_ = [("BatteryType", ctypes.c_ubyte),
                ("BatteryLevel", ctypes.c_ubyte)]


xinput = ctypes.windll.xinput1_4


def struct_dict(struct):
    get_pair = lambda field_type: (
        field_type[0], getattr(struct, field_type[0]))
    return dict(list(map(get_pair, struct._fields_)))


def get_bit_values(number, size=32):
    res = list(gen_bit_values(number))
    res.reverse()
    # 0-pad the most significant bit
    res = [0] * (size - len(res)) + res
    return res


def gen_bit_values(number):
    number = int(number)
    while number:
        yield number & 0x1
        number >>= 1


ERROR_DEVICE_NOT_CONNECTED = 1167
ERROR_SUCCESS = 0


class XInputJoystick(event.EventDispatcher):
    max_devices = 4
    dcTuple = idle_dcTuple

    def get_dcTuple(self):
        return XInputJoystick.dcTuple

    def __init__(self, device_number, normalize_axes=True):
        values = vars()
        del values['self']
        self.__dict__.update(values)

        super(XInputJoystick, self).__init__()

        self._last_state = self.get_state()
        self.received_packets = 0
        self.missed_packets = 0

        # Set the method that will be called to normalize
        #  the values for analog axis.
        choices = [self.translate_identity, self.translate_using_data_size]
        self.translate = choices[normalize_axes]

    def translate_using_data_size(self, value, data_size):
        # normalizes analog data to [0,1] for unsigned data
        #  and [-0.5,0.5] for signed data
        data_bits = 8 * data_size
        return float(value) / (2 ** data_bits - 1)

    def translate_identity(self, value, data_size=None):
        return value

    def get_state(self):
        "Get the state of the controller represented by this object"
        state = XINPUT_STATE()
        res = xinput.XInputGetState(self.device_number, ctypes.byref(state))
        if res == ERROR_SUCCESS:
            return state
        if res != ERROR_DEVICE_NOT_CONNECTED:
            raise RuntimeError(
                "Unknown error %d attempting to get state of device %d" % (res, self.device_number))
            # else return None (device is not connected)

    def is_connected(self):
        return self._last_state is not None

    @staticmethod
    def enumerate_devices():
        "Returns the devices that are connected"
        devices = list(
            map(XInputJoystick, list(range(XInputJoystick.max_devices))))
        return [d for d in devices if d.is_connected()]

    def set_vibration(self, left_motor, right_motor):
        "Control the speed of both motors seperately"
        # Set up function argument types and return type
        XInputSetState = xinput.XInputSetState
        XInputSetState.argtypes = [ctypes.c_uint, ctypes.POINTER(XINPUT_VIBRATION)]
        XInputSetState.restype = ctypes.c_uint

        vibration = XINPUT_VIBRATION(
            int(left_motor * 65535), int(right_motor * 65535))
        XInputSetState(self.device_number, ctypes.byref(vibration))

    def get_battery_information(self):
        "Get battery type & charge level"
        BATTERY_DEVTYPE_GAMEPAD = 0x00
        BATTERY_DEVTYPE_HEADSET = 0x01
        # Set up function argument types and return type
        XInputGetBatteryInformation = xinput.XInputGetBatteryInformation
        XInputGetBatteryInformation.argtypes = [ctypes.c_uint, ctypes.c_ubyte,
                                                ctypes.POINTER(XINPUT_BATTERY_INFORMATION)]
        XInputGetBatteryInformation.restype = ctypes.c_uint

        battery = XINPUT_BATTERY_INFORMATION(0, 0)
        XInputGetBatteryInformation(self.device_number, BATTERY_DEVTYPE_GAMEPAD, ctypes.byref(battery))
        batt_type = "Unknown" if battery.BatteryType == 0xFF else ["Disconnected", "Wired", "Alkaline", "Nimh"][
            battery.BatteryType]
        level = ["Empty", "Low", "Medium", "Full"][battery.BatteryLevel]
        return batt_type, level

    def dispatch_events(self):
        "The main event loop for a joystick"
        state = self.get_state()

        if not state:
            raise RuntimeError(
                "Joystick %d is not connected" % self.device_number)
        if state.packet_number != self._last_state.packet_number:
            # state has changed, handle the change
            self.update_packet_count(state)
            self.handle_changed_state(state)
        self._last_state = state

    def update_packet_count(self, state):
        "Keep track of received and missed packets for performance tuning"
        self.received_packets += 1
        missed_packets = state.packet_number - \
                         self._last_state.packet_number - 1
        if missed_packets:
            self.dispatch_event('on_missed_packet', missed_packets)
        self.missed_packets += missed_packets

    def handle_changed_state(self, state):
        "Dispatch various events as a result of the state changing"
        self.dispatch_event('on_state_changed', state)
        self.dispatch_axis_events(state)
        self.dispatch_button_events(state)

    def dispatch_axis_events(self, state):
        dcTuple = idle_dcTuple
        # axis fields are everything but the buttons
        axis_fields = dict(XINPUT_GAMEPAD._fields_)
        axis_fields.pop('buttons')
        for axis, type in list(axis_fields.items()):
            old_val = getattr(self._last_state.gamepad, axis)
            new_val = getattr(state.gamepad, axis)
            data_size = ctypes.sizeof(type)
            old_val = self.translate(old_val, data_size)
            new_val = self.translate(new_val, data_size)

            if ((old_val != new_val and (new_val > 0.08000000000000000 or new_val < -0.08000000000000000) and abs(
                        old_val - new_val) > 0.00000000500000000) or
                            (axis == 'right_trigger' or axis == 'left_trigger') and new_val == 0 and abs(
                            old_val - new_val) > 0.00000000500000000):
                self.dispatch_event('on_axis', axis, new_val)
            if (axis == 'right_trigger'):
                dcTuple = (dcTuple[0],
                           dcTuple[1] + new_val * forward_Range)
            if (axis == 'left_trigger'):
                dcTuple = (dcTuple[0],
                           dcTuple[1] - new_val * reverse_Range)
            if (axis == 'l_thumb_x'):
                dcTuple = (dcTuple[0] + new_val * steering_Range,
                           dcTuple[1])
            if (dcTuple[0] > 20):
                dcTuple = (20, dcTuple[1])
            if (dcTuple[0] < 10):
                dcTuple = (10, dcTuple[1])
        XInputJoystick.dcTuple = dcTuple

    def dispatch_button_events(self, state):
        changed = state.gamepad.buttons ^ self._last_state.gamepad.buttons
        changed = get_bit_values(changed, 16)
        buttons_state = get_bit_values(state.gamepad.buttons, 16)
        changed.reverse()
        buttons_state.reverse()
        button_numbers = count(1)
        changed_buttons = list(
            filter(itemgetter(0), list(zip(changed, button_numbers, buttons_state))))
        tuple(starmap(self.dispatch_button_event, changed_buttons))

    def dispatch_button_event(self, changed, number, pressed):
        self.dispatch_event('on_button', number, pressed)

    # stub methods for event handlers
    def on_state_changed(self, state):
        pass

    def on_axis(self, axis, value):
        pass

    def on_button(self, button, pressed):
        pass

    def on_missed_packet(self, number):
        pass


list(map(XInputJoystick.register_event_type, [
    'on_state_changed',
    'on_axis',
    'on_button',
    'on_missed_packet',
]))


# printMenu()
# Description: Displays buttons to press
def printMenu():
    print('Select a mode...')
    print('\tX:\tBegin collecting and recording data.')
    print('\tA:\tBegin driving autonomously.')
    print('\tB:\tSTOP signal that terminates program.')
    print('\tY:\tBegin live streaming.')


# liveStreamThread()
# Description: Creates the livestream thread to receive images from the RPi
# Parameter: stop_event => an event-handler that when set to false indicates to break the thread
#            j          => the joystick object that allows the current direction to be displayed on the camera.
def liveStreamThread(stop_event, j):
    global setSpeed
    logging.basicConfig(filename='scheduler.log', level=logging.DEBUG, filemode='w')
    sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    sock2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock2.connect((server_address[0], liveStreamPort))
    sock2.settimeout(10)
    nullEvents = 0
    while not stop_event.is_set() and nullEvents < 20:
        dcTuple = j.get_dcTuple()
        (nullEvents) = Client.liveStreamReceiver(sock2, dcTuple, nullEvents)
    sock2.close()


# plotVelocity
# Creates a thread event that displays a dynamic plot of the speed.
def plotVelocity():
    print('animating')
    plotTool.animateGraph()


# assertSafety()
# Description: asserts safety of environment
# Parameters: dcTuple => (steering,acc) duty cycle
def assertSafety(dcTuple):
    global setSpeed, maxSetSpeed, forward_Range, reverse_Range, idle_dcTuple
    # assert(idle_dcTuple[1] + forward_Range >= dcTuple[1]),'forward_Range UNSAFE: duty cycle should not exceed 17%%. If error message incorrect, comment out.'
    # assert(idle_dcTuple[1] - reverse_Range <= dcTuple[1]),'reverse_Range UNSAFE: duty cycle should not decrease past 13%%. If error message incorrect, comment out.'
    assert (
    setSpeed < maxSetSpeed), 'set_speed UNSAFE: set_speed should not exceed 1.5 m/s. If error message incorrect, comment out.'
    assert (maxSetSpeed < 2), 'Max set speed UNSAFE: Should not exceed 1.5. Comment out if warning unnecessary.'


# ControlDeepNNCar()
# Description: Dispatches XBOX events and sends messages to DeepNNCar
# Parameter: server_address => port 5001
def ControlDeepNNCar(server_address):
    # initialize joysticks
    joysticks = XInputJoystick.enumerate_devices()
    device_numbers = list(map(attrgetter('device_number'), joysticks))
    print('found %d devices: %s' % (len(joysticks), device_numbers))
    if not joysticks:
        sys.exit(0)
    j = joysticks[0]
    print('using %d' % j.device_number)
    Client.initializeConnection(server_address, idle_dcTuple, steering_Range)

    @j.event
    def on_button(button, pressed):
        global chosenMode, killThread, pill2kill, setSpeed, delta, forward_Range
        # X => collect duty cycle and image data
        if (button == 15 and pressed == 1 and not chosenMode):
            print('Sending COLLECTING DATA signal...')
            signal = (1,)
            chosenMode = True
            message = Client.send(signal, server_address)
            print(message)
        # A => turn on autonomous driving mode
        elif (button == 13 and pressed == 1 and not chosenMode):
            print('Sending AUTONOMOUS DRIVE signal...')
            signal = (2,)
            chosenMode = True
            message = Client.send(signal, server_address)
            print(message)
        # Y => Turn on live feed
        elif (button == 16 and pressed == 1 and not chosenMode):
            pill2kill = threading.Event()
            thread = Thread(target=liveStreamThread, args=(pill2kill, j,))
            thread.start()
            signal = (3,)
            chosenMode = True
            killThread = True
            # send the signal and print the message
            message = Client.send(signal, server_address)
            print(message)
            # B => Stop
        elif (button == 14 and pressed == 1):
            print('sending STOP signal...')
            signal = (4,)
            message = Client.send(signal, server_address)
            if (killThread == True):
                time.sleep(2)
                pill2kill.set()
            print(message)
            # UP => increase setSpeed
        elif (button == 1 and pressed == 1):
            if (cruiseControlEnabled):
                setSpeed = setSpeed + delta
                if (setSpeed > maxSetSpeed):
                    setSpeed = maxSetSpeed
                signal = (5,)
                message = Client.send(signal, server_address)
                print('Cruise Control: %f m/s' % setSpeed)
            elif (constantDCEnabled):
                forward_Range = forward_Range + 0.025
                print('Forward range decreased: %f ' % forward_Range)
        # DOWN => decrease set speed
        elif (button == 2 and pressed == 1):
            if (cruiseControlEnabled):
                setSpeed = setSpeed - delta
                if (setSpeed < 0):
                    setSpeed = 0
                signal = (6,)
                message = Client.send(signal, server_address)
                print('Cruise Control: %f m/s' % setSpeed)
            elif (constantDCEnabled):
                forward_Range = forward_Range - 0.025
                print('Forward range decreased: %f ' % forward_Range)

    # Event called if joystick is toggled
    # the left joystick controls the movement of the Traxxas RC car
    @j.event
    def on_axis(axis, value):
        left_speed = 0
        right_speed = 0
        if axis == "left_trigger":
            left_speed = value
        elif axis == "right_trigger":
            right_speed = value
        j.set_vibration(left_speed, right_speed)

    previousSpeed = prevError = prevT = 0
    error = accum = speed = 0
    theta = sumTheta = lengthTheta = 0
    acc = 15.5
    coord = [0, 0]
    start = time.time()
    thread = Thread(target=plotVelocity)
    #thread.start()
    # initialize motor
    Client.send(idle_dcTuple, server_address)
    time.sleep(2)
    print('Motor initialized.')
    printMenu()

    while joysticks:
        assertSafety(j.get_dcTuple())
        try:
            # send over dc values with selected protocol
            if (constantDCEnabled):
                previousSpeed = speed
                # ACC = ACC + forwardRange
                speed = Client.send((j.get_dcTuple()[0], idle_dcTuple[1] + forward_Range), server_address)
                speed = float(speed.decode())
                print(speed)
            elif (steeringBasedDCEnabled):
                # ACC = ACC + forwardRange - |idle steering - steering|
                previousSpeed = speed
                acc = idle_dcTuple[1] + forward_Range - abs(
                    idle_dcTuple[0] - j.get_dcTuple()[0]) * steeringBasedSpeedModeConstant
                speed = Client.send((j.get_dcTuple()[0], acc), server_address)
                speed = float(speed.decode())
            elif (cruiseControlEnabled):
                if (speed == 0):
                    acc = acc + 0.001
                if (speed != previousSpeed and speed < maxSetSpeed):
                    prevError = error
                    previousSpeed = speed 
                    error = setSpeed - speed
                    accum = accum + error
                    deriv = error - prevError
                    PID = KP*error + KI*accum + KD*deriv
                    acc = acc + PID
                if (acc > idle_dcTuple[1]+forward_Range):
                    print('setSpeedExceeding max duty cycle')
                    acc = idle_dcTuple[1]+forward_Range
                if (acc < idle_dcTuple[1]):
                    print('Exceeding min duty cycle (idle).')
                    acc = idle_dcTuple[1]
                speed = Client.send((j.get_dcTuple()[0], acc), server_address)
                print("Speed: ")
                print(speed)
            
                # speed = float(speed.decode())
            else:
                # default acceleration protocol
                previousSpeed = speed
                speed = Client.send(j.get_dcTuple(), server_address)
                speed = float(speed.decode())
                print(speed)
            # plot steering (degrees),speed(m/s),and location
            if (speed < maxSetSpeed):
                t = time.time() - start
                deltatheta = (j.get_dcTuple()[0] - idle_dcTuple[0]) / (steering_Range / 2) * 30
                sumTheta = sumTheta + deltatheta
                lengthTheta = lengthTheta + 1
                plotTool.addSteerInput(t, deltatheta)
                plotTool.addSpeedInput(t, speed, setSpeed)
                if (prevT == 0):
                    prevT = time.time()
                if (speed != previousSpeed):
                    theta = theta + (sumTheta / lengthTheta)
                    deltaT = time.time() - prevT
                    coord[0] = coord[0] + deltaT * speed * math.cos(math.radians(theta))
                    coord[1] = coord[1] + deltaT * speed * math.sin(math.radians(theta))
                    sumTheta = 0
                    lengthTheta = 0
                    prevT = time.time()
                    plotTool.addLocationInput(coord[0], coord[1])
            # check controller for events
            j.dispatch_events()
            # sleep
            time.sleep(.007)
        except Exception as e:
            print('Stopping traxxas...')
            print(e)
            break


# checkMutableParameters()
# Summary: Ensure parameters are safe
def checkParameters():
    global chosenMode, killThread, pill2kill
    assert (liveStreamPort == 5002), 'liveStreamPort: Must be 5002.'
    assert (mainPort == 5001), 'mainPort: must be 5001.'
    assert (idle_dcTuple == (15, 15)), 'idle_dcTuple: Must be (14.82,15). If calibration needed, change this.'
    assert (steering_Range == 12), 'steering_Range: should be 12. If calibratio needed, change this.'
    assert (not chosenMode), 'chosenMode: must be false.'
    assert (not killThread), 'killThread: must be false.'
    assert (not pill2kill), 'pill2kill: must be false.'
    assert (idle_dcTuple[
                1] + forward_Range < 17), 'forward_Range UNSAFE: duty cycle should not exceed 17%%. If error message incorrect, comment out.'
    assert (idle_dcTuple[
                1] - reverse_Range > 13), 'reverse_Range UNSAFE: duty cycle should not decrease past 13%%. If error message incorrect, comment out.'
    assert (
    setSpeed < maxSetSpeed), 'set_speed UNSAFE: set_speed should not exceed 1.5 m/s. If error message incorrect, comment out.'
    assert (maxSetSpeed < 2), 'Max set speed UNSAFE: Should not exceed 1.5. Comment out if warning unnecessary.'
    assert (not (cruiseControlEnabled and constantDCEnabled)), 'Cannot enable cruise control and constant DC mode.'
    assert (
    not (cruiseControlEnabled and steeringBasedDCEnabled)), 'Cannot enable cruise control and steering based DC mode.'
    assert (
    not (constantDCEnabled and steeringBasedDCEnabled)), 'Cannot enable steering based DC mode and constant DC mode.'


# MAIN
if __name__ == "__main__":
    # IMMUTABLE
    chosenMode = False  # indicate when mode has been selected
    killThread = False  # indicates if LS should be killed
    pill2kill = False  # stop event for LS mode
    #checkParameters()
    ControlDeepNNCar(server_address)

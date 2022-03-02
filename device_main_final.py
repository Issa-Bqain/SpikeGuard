import smbus2
import time
import paho.mqtt.client as mqtt
import threading
import requests
from gpiozero import RGBLED
import ssl
import sys
import urllib
import urllib.request
import numpy as np
import math
from math import copysign

# Initialise constants
MEASURE_INTERVAL = 0.1
FILTER_WINDOW_SIZE = 4
ARRAY_SIZE = 16
NUMBER_OF_PACKETS = 32
REMOVE_GRAVITY_OFFSET = True

# Initialise flags
ARMED_FLAG = False
SPIKED_FLAG = False

# establish RGB LED connections
led = RGBLED(26,19,13)
led.on()
led.color = (1, 0, 1)


# Setup MQTT connection
class MqttThread(threading.Thread):
    def __init__(self, thread_id, name):
        threading.Thread.__init__(self)
        self.threadID = thread_id
        self.name = name
        self.client = mqtt.Client("vici_raspi")
        # SSL connection when connecting to port 8884 with encryption and client authentication
        #self.client.tls_set(ca_certs="domain name", certfile="client.cer", keyfile="client.key",
        #             tls_version=ssl.PROTOCOL_TLSv1_2)
        self.client.connect("ec2-xx-xx-xx-xxx.eu-west-2.compute.amazonaws.com", port=1883, keepalive= 3600)

    def run(self):
        self.client.on_message = self.on_message
        self.client.subscribe("VICI/test/arm")
        self.client.subscribe("VICI/test/disarm")
        self.client.loop_forever()

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        command = msg.payload.decode()
        global ARMED_FLAG
        # arm when you want to sense for spike events
        if topic == "VICI/test/arm":
            time.sleep(1)
            client.publish("VICI/test/armed", "armed")
            led.color = (1,1,0)
            ARMED_FLAG = True
        # disarm when you want to stop sensing for spike events
        if topic == "VICI/test/disarm":
            time.sleep(1)
            client.publish("VICI/test/disarmed", "disarmed")
            led.color = (1,0,1)
            ARMED_FLAG = False
    # send spike event when detected
    def send_spike_message(self):
        self.client.publish("VICI/test/spike", "spike")

# Class implementing a real-time moving average filter used to reduce the noise in accelerometer readings
class StreamingMovingAverage:
    def __init__(self, window_size):
        self.window_size = window_size
        self.values = []
        self.sum = 0

    def process(self, value):
        self.values.append(value)
        self.sum += value
        if len(self.values) > self.window_size:
            self.sum -= self.values.pop(0)
        return float(self.sum) / len(self.values)

# read data from accelerometer 1
def get_data_acc1(bus):
    # Get X axis acceleration
    xdata0 = bus.read_byte_data(0x18, 0x28)
    xdata1 = bus.read_byte_data(0x18, 0x29)
    xaccl = xdata1 * 256 + xdata0
    if xaccl > 32767:
        xaccl -= 65536
    xaccl = (xaccl / 16300) * 9.806
    x_out = x_filter_18.process(xaccl)

    # Fill the X axis packet
    global x_arr_18
    x_arr_18.append(x_out)

    # Check array overflow
    if len(x_arr_18) > ARRAY_SIZE:
        x_arr_18.pop(0)

    # Get Y axis acceleration
    ydata0 = bus.read_byte_data(0x18, 0x2A)
    ydata1 = bus.read_byte_data(0x18, 0x2B)
    yaccl = ydata1 * 256 + ydata0
    if yaccl > 32767:
        yaccl -= 65536
    yaccl = (yaccl / 16300) * 9.806
    y_out = y_filter_18.process(yaccl)

    # Fill the Y axis packet
    global y_arr_18
    y_arr_18.append(y_out)

    # Check array overflow
    if len(y_arr_18) > ARRAY_SIZE:
        y_arr_18.pop(0)

    # Get Y axis acceleration
    zdata0 = bus.read_byte_data(0x18, 0x2C)
    zdata1 = bus.read_byte_data(0x18, 0x2D)
    zaccl = zdata1 * 256 + zdata0
    if zaccl > 32767:
        zaccl -= 65536
    zaccl = (zaccl / 16300) * 9.806
    if REMOVE_GRAVITY_OFFSET:
        zaccl -= 9.806
    z_out = z_filter_18.process(zaccl)

    # Fill the Z axis packet
    global z_arr_18
    z_arr_18.append(z_out)

    # Check array overflow
    if len(z_arr_18) > ARRAY_SIZE:
        z_arr_18.pop(0)

# read data from accelerometer 2
def get_data_acc2(bus):
    # Get X axis acceleration
    xdata0 = bus.read_byte_data(0x19, 0x28)
    xdata1 = bus.read_byte_data(0x19, 0x29)
    xaccl = xdata1 * 256 + xdata0
    if xaccl > 32767:
        xaccl -= 65536
    xaccl = (xaccl / 16300) * 9.806
    x_out = x_filter_19.process(xaccl)

    # Fill the X axis packet
    global x_arr_19
    x_arr_19.append(x_out)

    # Check array overflow
    if len(x_arr_19) > ARRAY_SIZE:
        x_arr_19.pop(0)

    # Get Y axis acceleration
    ydata0 = bus.read_byte_data(0x19, 0x2A)
    ydata1 = bus.read_byte_data(0x19, 0x2B)
    yaccl = ydata1 * 256 + ydata0
    if yaccl > 32767:
        yaccl -= 65536
    yaccl = (yaccl / 16300) * 9.806
    y_out = y_filter_19.process(yaccl)

    # Fill the Y axis packet
    global y_arr_19
    y_arr_19.append(y_out)

    # Check array overflow
    if len(y_arr_19) > ARRAY_SIZE:
        y_arr_19.pop(0)

    # Get Y axis acceleration
    zdata0 = bus.read_byte_data(0x19, 0x2C)
    zdata1 = bus.read_byte_data(0x19, 0x2D)
    zaccl = zdata1 * 256 + zdata0
    if zaccl > 32767:
        zaccl -= 65536
    zaccl = (zaccl / 16300) * 9.806
    if REMOVE_GRAVITY_OFFSET:
        zaccl -= 9.806
    z_out = z_filter_19.process(zaccl)

    # Fill the Z axis packet
    global z_arr_19
    z_arr_19.append(z_out)

    # Check array overflow
    if len(z_arr_19) > ARRAY_SIZE:
        z_arr_19.pop(0)


# Initialise the filters for each axis readings
x_filter_18 = StreamingMovingAverage(FILTER_WINDOW_SIZE)
y_filter_18 = StreamingMovingAverage(FILTER_WINDOW_SIZE)
z_filter_18 = StreamingMovingAverage(FILTER_WINDOW_SIZE)

x_filter_19 = StreamingMovingAverage(FILTER_WINDOW_SIZE)
y_filter_19 = StreamingMovingAverage(FILTER_WINDOW_SIZE)
z_filter_19 = StreamingMovingAverage(FILTER_WINDOW_SIZE)

# Initialise containers for the accelerometer
x_arr_18 = [0]
y_arr_18 = [0]
z_arr_18 = [0]

x_arr_19 = [0]
y_arr_19 = [0]
z_arr_19 = [0]

# Get I2C bus
bus = smbus2.SMBus(1)

# Setup the accelerometer 1 for reading in interval -2g/2g
bus.write_byte_data(0x18, 0x20, 0x27)
bus.write_byte_data(0x18, 0x23, 0x00)
time.sleep(0.5)

# Setup the accelerometer 2 for reading in interval -2g/2g
bus.write_byte_data(0x19, 0x20, 0x27)
bus.write_byte_data(0x19, 0x23, 0x00)
time.sleep(0.5)

# Starting MQTT thread
mqtt_thread = MqttThread(1, "MQTT-Thread")
mqtt_thread.start()

# Calculate tilt angles
def angle_calculator(x,y,z):
    sign = lambda a: copysign(1,a)
    u = 0.01
    pitch = np.arctan2(y,sign(z)*np.sqrt(np.power(z,2)+(u*np.power(x,2))))
    roll = np.arctan2((-x),(np.sqrt(np.power(y,2) + np.power(z,2))))
    yaw = np.arctan2(np.sqrt(np.power(x,2)+np.power(y,2)),z)
    return np.rad2deg(pitch),np.rad2deg(roll),np.rad2deg(yaw)

# initialise
x_angle = 0
y_angle = 0
z_angle = 0

x_angleth = 0
y_angleth = 0
z_angleth = 0


diffxth = 0
diffyth = 0
diffzth = 0

diffx = 0
diffy = 0
diffz = 0

spikex = 0
spikey = 0
spikez = 0

totalspike = 0
counter = 0
offline_spike = 0
offline = 0
# --------------------------------------- MAIN LOOP -------------------------------------------
while True:
    if ARMED_FLAG or offline_spike == 1:
        get_data_acc1(bus)
        get_data_acc2(bus)
        time.sleep(MEASURE_INTERVAL)

        # take reading
        if len(z_arr_18) > 15:
            diffx = x_arr_18[-1] - x_arr_19[-1]
            diffy = y_arr_18[-1] - y_arr_19[-1]
            diffz = z_arr_18[-1] - z_arr_19[-1]
            x_angle, y_angle, z_angle = angle_calculator(x_arr_19[-1], y_arr_19[-1], z_arr_19[-1])

            # checks if disconnected from internet and waits before sending spike event detection to app
            if offline_spike == 1:
                while offline == 1:
                    offline = 0
                    try:
                        urllib.request.urlopen("http://google.com")
                    except urllib.error.URLError as e:
                        offline_spike = 1
                        print('Still Offline')
                        offline = 1
                    time.sleep(3)
                    mqtt_thread.send_spike_message()
                    if offline == 0:
                        ARMED_FLAG = False
                        offline_spike = 0
                    print("offline spike")

            # Threshold detection checking for spike events
            if abs(diffx) > abs(diffxth)+1.6 or abs(diffx) < abs(diffxth) - 1.6:
                spikex = spikex + 1
            if abs(diffy) > abs(diffyth)+ 1.6 or abs(diffy) < abs(diffyth) - 1.6:
                spikey = spikey + 1
            if abs(diffz) > abs(diffzth)+ 1.6 or abs(diffz) < abs(diffzth) - 1.2:
                spikez = spikez + 1
            if (abs(x_angle) > abs(x_angleth) + 30 or abs(x_angle) < abs(x_angleth) - 30):
                print("spikex")
                spikex = spikex + 1
            if (abs(y_angle) > abs(y_angleth) + 30 or abs(y_angle) < abs(y_angleth) - 30):
                print("spikey")
                spikey = spikey + 1

            totalspike = spikez + spikey + spikex
            print(f" spiketotal - {totalspike}")
            print(f"counter -  {counter}")

            # spike event detected, notify to app
            if(totalspike > 7 ):
                offline_spike = 0
                try:
                    urllib.request.urlopen("http://google.com")
                except urllib.error.URLError as e:
                    offline_spike = 1
                    offline = 1
                    print('offline detected 1')

                led.color = (0,1,1)
                if offline == 0:
                    mqtt_thread.send_spike_message()
                    ARMED_FLAG = False
                totalspike = 0
                spikez = 0
                spikex = 0
                spikey = 0
                counter = 0

                diffxth = 0
                diffyth = 0
                diffzth = 0

                diffx = 0
                diffy = 0
                diffz = 0

                x_angle = 0
                y_angle = 0
                z_angle = 0

                x_angleth = 0
                y_angleth = 0
                z_angleth = 0

                x_arr_18 = [0]
                y_arr_18 = [0]
                z_arr_18 = [0]

                x_arr_19 = [0]
                y_arr_19 = [0]
                z_arr_19 = [0]
            # reset event detection cycle
            if(counter == 10):
                totalspike = 0
                spikez = 0
                spikex = 0
                spikey = 0
                counter = 0

            totalspike = spikez+spikey+spikex
        else:
            # establish stationary thresholds
            diffxth = x_arr_18[-1] - x_arr_19[-1]
            diffyth = y_arr_18[-1] - y_arr_19[-1]
            diffzth = z_arr_18[-1] - z_arr_19[-1]
            x_angleth, y_angleth, z_angleth = angle_calculator(x_arr_19[-1], y_arr_19[-1], z_arr_19[-1])

        print(f" x_angle - {x_angle}\n")
        print(f" y_angle - {y_angle}\n")
        print(f" z_angle - {z_angle}\n")
        print("########################")
        print(f" x_angleth - {x_angleth}\n")
        print(f" y_angleth - {y_angleth}\n")
        print(f" z_angleth - {z_angleth}\n")

        #print(f"Differential X data - {diffx}")
        #print(f"Differential Y data - {diffy}")
        #print(f"Differential Z data - {diffz}\n")
        #print(f"Differential X data - {diffxth}")
        #print(f"Differential Y data - {diffyth}")
        #print(f"Differential Z data - {diffzth}\n")
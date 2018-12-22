#!/usr/bin/env python
import paho.mqtt.publish as publish
import math
import time

MQTT_SERVER = "localhost"

x = 0
y = 0
z = 0
dx = math.pi / 360
dy = math.pi / 350
dz = math.pi / 330

while True:
    publish.single('x', str(x), hostname=MQTT_SERVER)
    publish.single('y', str(y), hostname=MQTT_SERVER)
    publish.single('z', str(z), hostname=MQTT_SERVER)
    x += dx
    y += dy
    z += dz
    time.sleep(0.01)


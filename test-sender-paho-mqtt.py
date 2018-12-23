#!/usr/bin/env python
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
import math
import time

MQTT_SERVER = "localhost"

x = 0
y = 0
z = 0
dx = math.pi / 360
dy = math.pi / 350
dz = math.pi / 330


client = mqtt.Client()
client.connect(MQTT_SERVER)
client.loop_start()

while True:
    client.publish('x', str(x))
    client.publish('y', str(y))
    client.publish('z', str(z))
    x += dx
    y += dy
    z += dz
    time.sleep(0.01)


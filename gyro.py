#!/usr/bin/python
import smbus
import math
import time
import paho.mqtt.client as mqtt

MQTT_SERVER = "192.168.178.65"

# Register
power_mgmt_1 = 0x6b
power_mgmt_2 = 0x6c
 
def read_byte(reg):
    return bus.read_byte_data(address, reg)
 
def read_word(reg):
    h = bus.read_byte_data(address, reg)
    l = bus.read_byte_data(address, reg+1)
    value = (h << 8) + l
    return value
 
def read_word_2c(reg):
    val = read_word(reg)
    if (val >= 0x8000):
        return -((65535 - val) + 1)
    else:
        return val
 
def dist(a,b):
    return math.sqrt((a*a)+(b*b))
 
def get_y_rotation(x,y,z):
    radians = math.atan2(x, dist(y,z))
    return radians
 
def get_x_rotation(x,y,z):
    radians = math.atan2(y, dist(x,z))
    return radians
 
bus = smbus.SMBus(1) # bus = smbus.SMBus(0) for Revision 1
address = 0x68       # via i2cdetect
 
# Initialize MPU-6050
bus.write_byte_data(address, power_mgmt_1, 0)

def get_rotations():
    gyro_xout = read_word_2c(0x43)
    gyro_yout = read_word_2c(0x45)
    gyro_zout = read_word_2c(0x47)

    accelleration_xout = read_word_2c(0x3b)
    accelleration_yout = read_word_2c(0x3d)
    accelleration_zout = read_word_2c(0x3f)
     
    accelleration_xout_scale = accelleration_xout / 16384.0
    accelleration_yout_scale = accelleration_yout / 16384.0
    accelleration_zout_scale = accelleration_zout / 16384.0

    rotation_x = get_x_rotation(accelleration_xout_scale, accelleration_yout_scale, accelleration_zout_scale)
    rotation_y = get_y_rotation(accelleration_xout_scale, accelleration_yout_scale, accelleration_zout_scale)
    return (rotation_x, rotation_y)


print("gyro")
print("--------")

gyro_xout = read_word_2c(0x43)
gyro_yout = read_word_2c(0x45)
gyro_zout = read_word_2c(0x47)

print("gyro_xout: ", ("%5d" % gyro_xout), " scale: ", (gyro_xout / 131.0))
print("gyro_yout: ", ("%5d" % gyro_yout), " scale: ", (gyro_yout / 131.0))
print("gyro_zout: ", ("%5d" % gyro_zout), " scale: ", (gyro_zout / 131.0))

print()
print("accellerationssensor")
print("---------------------")

accelleration_xout = read_word_2c(0x3b)
accelleration_yout = read_word_2c(0x3d)
accelleration_zout = read_word_2c(0x3f)
 
accelleration_xout_scale = accelleration_xout / 16384.0
accelleration_yout_scale = accelleration_yout / 16384.0
accelleration_zout_scale = accelleration_zout / 16384.0

print("accelleration_xout: ", ("%6d" % accelleration_xout), " scale: ", accelleration_xout_scale)
print("accelleration_yout: ", ("%6d" % accelleration_yout), " scale: ", accelleration_yout_scale)
print("accelleration_zout: ", ("%6d" % accelleration_zout), " scale: ", accelleration_zout_scale)

print("X Rotation: ", get_x_rotation(accelleration_xout_scale, accelleration_yout_scale, accelleration_zout_scale))
print("Y Rotation: ", get_y_rotation(accelleration_xout_scale, accelleration_yout_scale, accelleration_zout_scale))

client = mqtt.Client()
client.connect(MQTT_SERVER)

vx = vy = vz = 0
while True:
    try:
        (rotation_x, rotation_y) = get_rotations()
        print("Sending update: (%f, %f)" % (rotation_x, rotation_y))

        accelleration_xout = read_word_2c(0x3b)
        accelleration_yout = read_word_2c(0x3d)
        accelleration_zout = read_word_2c(0x3f)

        accelleration_xout_scale = accelleration_xout / 16384.0
        accelleration_yout_scale = accelleration_yout / 16384.0
        accelleration_zout_scale = accelleration_zout / 16384.0
        vx += accelleration_xout_scale
        vy += accelleration_yout_scale
        vz += accelleration_zout_scale
        print("V = (%f, %f, %f)" % (vx, vy, vz))
        client.publish('x', str(rotation_x))
        client.publish('y', str(rotation_y))
        client.publish('accelx', str(accelleration_xout_scale))
        client.publish('accely', str(accelleration_yout_scale))
        client.publish('accelz', str(accelleration_zout_scale))
    except IOError:
        time.sleep(0.1)

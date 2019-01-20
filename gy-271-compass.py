#!/usr/bin/python
import smbus
import math
import time
import paho.mqtt.client as mqtt

MQTT_SERVER = "192.168.178.65"


# Registers
register_a = 0
register_b = 0x01
register_mode = 0x02

x_axis_h = 0x03
y_axis_h = 0x05
z_axis_h = 0x07
declination = -0.00669


def init():
    # write to configuraiton to register A
    bus.write_byte_data(device_address, register_a, 0x70)
    # write to configuration register B for gain
    bus.write_byte_data(device_address, register_b, 0xa0)
    # write mode register to select mode
    bus.write_byte_data(device_address, register_mode, 0)
    
 
def read_word(reg):
    high = bus.read_byte_data(device_address, reg)
    low = bus.read_byte_data(device_address, reg+1)
    value = (high << 8) + low
    return value


def read_word_2c(reg):
    val = read_word(reg)
    if val >= 0x8000:
        return -((65535 - val) + 1)
    else:
        return val


def get_rotations():
    x = read_word_2c(x_axis_h)
    y = read_word_2c(y_axis_h)
    z = read_word_2c(z_axis_h)

    heading = math.atan2(y, x) + declination

    if heading > 2 * math.pi:
        heading -= 2 * math.pi

    if heading < 0:
        heading += 2 * math.pi

    print("Heading: %d degr. (raw: (%.2f, %.2f, %.2f)" % (math.degrees(heading), x, y, z))


if __name__ == "__main__":
    bus = smbus.SMBus(1)
    device_address = 0x0d       # via i2cdetect -y -1
    # Initialize GY0271
    init()

    while True:
        try:
            get_rotations()
            time.sleep(0.5)
        except IOError:
            time.sleep(0.5)

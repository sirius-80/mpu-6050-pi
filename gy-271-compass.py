#!/usr/bin/python
import smbus
import math
import time
import struct



# import paho.mqtt.client as mqtt
#
# MQTT_SERVER = "192.168.178.65"
#
#
# # Registers
# register_a = 0
# register_b = 0x01
# register_mode = 0x09
#
# x_axis_h = 0x00
# y_axis_h = 0x02
# z_axis_h = 0x04
# declination = -0.00669
#
# #Bit values for the STATUS register
# STATUS_DRDY = 1
# STATUS_OVL = 2
# STATUS_DOR = 4
#
# #Oversampling values for the CONFIG register
# MC5883L_CONFIG_OS512 = 0b00000000
# CONFIG_OS256 = 0b01000000
# CONFIG_OS128 = 0b10000000
# CONFIG_OS64  = 0b11000000
#
# #Range values for the CONFIG register
# CONFIG_2GAUSS = 0b00000000
# CONFIG_8GAUSS = 0b00010000
#
# #Rate values for the CONFIG register
# CONFIG_10HZ = 0b00000000
# CONFIG_50HZ = 0b00000100
# CONFIG_100HZ = 0b00001000
# CONFIG_200HZ = 0b00001100
#
# #Mode values for the CONFIG register
# CONFIG_STANDBY = 0b00000000
# CONFIG_CONT = 0b00000001
#
# def init():
#     # write to configuraiton to register A
#     bus.write_byte_data(device_address, register_a, 0x70)
#     # write to configuration register B for gain
#     bus.write_byte_data(device_address, register_b, 0xa0)
#     # write mode register to select mode
#     bus.write_byte_data(device_address, register_mode, 1)
#
#
# def read_word(reg):
#     high = bus.read_byte_data(device_address, reg)
#     low = bus.read_byte_data(device_address, reg+1)
#     value = (high << 8) + low
#     return value
#
#
# def read_word_2c(reg):
#     val = read_word(reg)
#     if val >= 0x8000:
#         return -((65535 - val) + 1)
#     else:
#         return val
#
#
# def get_rotations():
#     x = read_word_2c(x_axis_h)
#     y = read_word_2c(y_axis_h)
#     z = read_word_2c(z_axis_h)
#
#     heading = math.atan2(y, x) + declination
#
#     if heading > 2 * math.pi:
#         heading -= 2 * math.pi
#
#     if heading < 0:
#         heading += 2 * math.pi
#
#     print("Heading: %d degr. (raw: (%.2f, %.2f, %.2f)" % (math.degrees(heading), x, y, z))
#
#
# if __name__ == "__main__":
#     bus = smbus.SMBus(1)
#     device_address = 0x0d       # via i2cdetect -y -1
#     # Initialize GY0271
#     init()
#
#     while True:
#         try:
#             get_rotations()
#             time.sleep(0.5)
#         except IOError:
#             time.sleep(0.5)


class QMC5883:
    #Default I2C address
    ADDR = 0x0D

    #QMC5883 = Register = numbers
    X_LSB = 0
    X_MSB = 1
    Y_LSB = 2
    Y_MSB = 3
    Z_LSB = 4
    Z_MSB = 5
    STATUS = 6
    T_LSB = 7
    T_MSB = 8
    CONFIG = 9
    CONFIG2 = 10
    RESET = 11
    CHIP_ID = 13

    #Bit values for the STATUS register
    STATUS_DRDY = 1
    STATUS_OVL = 2
    STATUS_DOR = 4

    #Oversampling values for the CONFIG register
    MC5883L_CONFIG_OS512 = 0b00000000
    CONFIG_OS256 = 0b01000000
    CONFIG_OS128 = 0b10000000
    CONFIG_OS64  = 0b11000000

    #Range values for the CONFIG register
    CONFIG_2GAUSS = 0b00000000
    CONFIG_8GAUSS = 0b00010000

    #Rate values for the CONFIG register
    CONFIG_10HZ = 0b00000000
    CONFIG_50HZ = 0b00000100
    CONFIG_100HZ = 0b00001000
    CONFIG_200HZ = 0b00001100

    #Mode values for the CONFIG register
    CONFIG_STANDBY = 0b00000000
    CONFIG_CONT = 0b00000001

    #bus = smbus.SMBus(1)

    def reconfig(self):
        print("{0:b}".format(self.oversampling | self.range | self.rate | self.mode))
        self.bus.write_byte_data(QMC5883.ADDR, QMC5883.CONFIG, self.oversampling | self.range | self.rate | self.mode);

    def reset(self):
        self.bus.write_byte_data(QMC5883.ADDR, QMC5883.RESET, 0x01)
        time.sleep(0.1)
        self.reconfig()
        time.sleep(0.01)

    def __init__(self):
        self.bus = smbus.SMBus(1)
        self.oversampling = QMC5883.CONFIG_OS64
        self.range = QMC5883.CONFIG_2GAUSS
        self.rate = QMC5883.CONFIG_100HZ
        self.mode = QMC5883.CONFIG_CONT
        self.reset()

    def setOversampling(self, x):
        self.oversampling = x
        self.reconfig()

    def setRange(x):
        self.range = x
        self.reconfig()

    def setSamplingRate(self, x):
        self.rate = x
        self.reconfig()

    def ready(self):
        status = self.bus.read_byte_data(QMC5883.ADDR, QMC5883.STATUS)

        # prevent hanging up here.
        # Happens when reading less bytes then then all 3 axis and will end up in a loop.
        # So, return any data but avoid the loop.
        if (status == QMC5883.STATUS_DOR):
            print("fail")
            return QMC5883.STATUS_DRDY

        return status & QMC5883.STATUS_DRDY

    def readRaw(self):
        while (not self.ready()):
            pass

        # Python performs a wrong casting at read_i2c_block_data.
        # The filled buffer has to be onverted afterwards by mpdule Struct
        register = self.bus.read_i2c_block_data(QMC5883.ADDR, QMC5883.X_LSB, 9)

        # Convert the axis values to signed Short before returning
        x = struct.unpack('<h', bytes([register[0], register[1]]))[0]
        y = struct.unpack('<h', bytes([register[2], register[3]]))[0]
        z = struct.unpack('<h', bytes([register[4], register[5]]))[0]
        t = struct.unpack('<h', bytes([register[7], register[8]]))[0]

        return (x, y, z, t)


if __name__ == "__main__":
    compass = QMC5883()
    while True:
        try:
            x, y, z, t = compass.readRaw()
            print("x: %.2f, y: %.2f, z: %.2f, t: %.2f" % (x, y, z, t))
            time.sleep(0.5)
        except IOError:
            time.sleep(0.5)

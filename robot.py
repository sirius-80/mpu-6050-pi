#!/usr/bin/env python
import cmd

from apds9960.const import *
from apds9960 import APDS9960
import struct
import cwiid
import logging
import numpy
import RPi.GPIO as GPIO
import smbus
import time
import paho.mqtt.client as mqtt
import multiprocessing.queues
import multiprocessing.synchronize

import myrobot

MQTT_SERVER = "192.168.178.65"


#####
#
# TODO: Determine front-facing direction of the robot (orientation). This is required for the tracker to work
#       (otherwise it things it's always moving perpendicular to the y-axis!!)
#
#####


class GpioController(object):
    def __init__(self, cmd_queue):
        self.cmd_queue = cmd_queue
        GPIO.setmode(GPIO.BCM) # Use broadcom pin numbering
        GPIO.setwarnings(False)
        # GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Button to GPIO23
        # GPIO.setup(24, GPIO.OUT)  # LED to GPIO24

        self.GPIO_TRIGGER = 18
        self.GPIO_ECHO = 17
        self.pwm_left = None
        self.pwm_right = None

        self.init_ultrasound_module()
        self.motor_direction = -1 # Set to 1 or -1 depending on how the motors are placed (fwd or reversed)
        self.init_motor_controls()
        self.apds = self.init_apds9960()

    def _gesture_handler(self):
        directions = {
            APDS9960_DIR_NONE: None,
            APDS9960_DIR_LEFT: "left",
            APDS9960_DIR_RIGHT: "right",
            APDS9960_DIR_UP: "forward",
            APDS9960_DIR_DOWN: "backward",
            APDS9960_DIR_NEAR: None,
            APDS9960_DIR_FAR: None,
        }
        direction = directions[self.apds.readGesture()]
        if direction:
            logging.info("Received gesture: %s" % direction)
            self.cmd_queue.put(direction)

    def init_apds9960(self):
        port = 1
        bus = smbus.SMBus(port)
        apds = APDS9960(bus)
        GPIO.setup(4, GPIO.IN)
        GPIO.add_event_detect(4, GPIO.FALLING, callback=self._gesture_handler)
        apds.enableGestureSensor()
        return apds

    def init_ultrasound_module(self):
        # set GPIO Pins for ultra-sound TX module
        GPIO.setup(self.GPIO_TRIGGER, GPIO.OUT)
        GPIO.setup(self.GPIO_ECHO, GPIO.IN)

    def init_motor_controls(self):
        # set GPIO for PWM motor control
        GPIO.setup(6, GPIO.OUT)
        GPIO.setup(13, GPIO.OUT)
        GPIO.setup(19, GPIO.OUT)
        GPIO.setup(26, GPIO.OUT)
        self.pwm_left_fwd = GPIO.PWM(6, 100)
        self.pwm_left_bck = GPIO.PWM(13, 100)
        self.pwm_right_fwd = GPIO.PWM(19, 100)
        self.pwm_right_bck = GPIO.PWM(26, 100)
        self.pwm_left_fwd.start(0)
        self.pwm_left_bck.start(0)
        self.pwm_right_fwd.start(0)
        self.pwm_right_bck.start(0)

    def distance(self):
        """Measures and returns current distance in m."""
        # set Trigger to HIGH
        GPIO.output(self.GPIO_TRIGGER, True)

        # set Trigger after 0.01ms to LOW
        time.sleep(0.00001)
        GPIO.output(self.GPIO_TRIGGER, False)

        start_time = time.time()
        stop_time = time.time()

        # save StartTime
        while GPIO.input(self.GPIO_ECHO) == 0:
            start_time = time.time()

        # save time of arrival
        while GPIO.input(self.GPIO_ECHO) == 1:
            stop_time = time.time()

        # time difference between start and arrival
        time_elapsed = stop_time - start_time
        # multiply with the sonic speed (343.00 m/s)
        # and divide by 2, because there and back
        distance = (time_elapsed * 343.00) / 2

        return distance

    def left_wheel(self, speed):
        if speed * self.motor_direction > 0:
            self.pwm_left_bck.ChangeDutyCycle(0)
            self.pwm_left_fwd.ChangeDutyCycle(self.motor_direction * speed)
        else:
            self.pwm_left_fwd.ChangeDutyCycle(0)
            self.pwm_left_bck.ChangeDutyCycle(-self.motor_direction * speed)

    def right_wheel(self, speed):
        if speed * self.motor_direction > 0:
            self.pwm_right_bck.ChangeDutyCycle(0)
            self.pwm_right_fwd.ChangeDutyCycle(self.motor_direction * speed)
        else:
            self.pwm_right_fwd.ChangeDutyCycle(0)
            self.pwm_right_bck.ChangeDutyCycle(-self.motor_direction * speed)

    def close(self):
        self.pwm_left_fwd.stop()
        self.pwm_left_bck.stop()
        self.pwm_right_fwd.stop()
        self.pwm_right_bck.stop()
        GPIO.cleanup()


class WiimoteControl(object):
    def __init__(self):
        self.STICK_THRESHOLD = 1
        self.STICK_CENTER_POSITION = (127, 127)
        self.last_direction = (0, 0)
        self._connect()
        self.wiimote.rpt_mode = cwiid.RPT_NUNCHUK | cwiid.RPT_BTN
        self.wiimote.enable(cwiid.FLAG_MESG_IFC)
        self.wiimote.mesg_callback = self._wii_msg_callback
        self.wiimote.led = 9
        self.button_callback_functions = {}
        self.direction_callback_function = None
        # Nunchuk needs some time to start reporting
        time.sleep(.2)

    def on_button(self, button, function, *args, **kwargs):
        self.button_callback_functions[button] = (function, args, kwargs)

    def on_direction(self, func):
        """Provide function that takes direction tuple (left-right, fwd-backward) as input"""
        self.direction_callback_function = func

    def _connect(self):
        logging.warning('Press button 1 + 2 on your Wii Remote...')
        self.wiimote = None
        self._connected = False
        while not self.wiimote:
            try:
                self.wiimote = cwiid.Wiimote()
                self._connected = True
                logging.info('Wii Remote connected...')
                logging.info('Press the HOME button to disconnect the Wii and end the application')
                self.rumble()
            except RuntimeError:
                logging.warning("Timed out waiting for wii-remote, trying again...")
            except KeyboardInterrupt:
                logging.warning("Interrupted. Stopping.")

    def _wii_msg_callback(self, mesg_list, time):
        for mesg in mesg_list:
            if mesg[0] == cwiid.MESG_BTN:
                button = mesg[1]
                if button in self.button_callback_functions:
                    func = self.button_callback_functions[button][0]
                    args = self.button_callback_functions[button][1]
                    kwargs = self.button_callback_functions[button][2]
                    func(*args, **kwargs)
            if mesg[0] == cwiid.MESG_NUNCHUK:
                # {'acc': (76, 127, 139), 'buttons': 0, 'stick': (126, 127)}
                stick = mesg[1]['stick']
                direction = numpy.subtract(stick, self.STICK_CENTER_POSITION)
                change = numpy.subtract(self.last_direction, direction)
                if abs(change[0]) >= self.STICK_THRESHOLD or abs(change[1]) >= self.STICK_THRESHOLD:
                    normalized_direction = numpy.minimum((1.0, 1.0), numpy.divide(direction, (127.0, 100.0)))
                    if self.direction_callback_function:
                        logging.debug("calling direction callback with normalized direction %s", normalized_direction)
                        self.direction_callback_function(normalized_direction)
                self.last_direction = direction

    def connected(self):
        return self._connected

    def rumble(self, duration_seconds=0.1):
        self.wiimote.rumble = 1
        time.sleep(duration_seconds)
        self.wiimote.rumble = 0

    def close(self):
        if self._connected:
            self.rumble(0.5)
            self.wiimote.close()
        self._connected = False


def main():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s - %(message)s')
    queue = multiprocessing.queues.SimpleQueue()
    board_controller = GpioController(queue)
    location_tracker = myrobot.tracker.Tracker()
    #client = mqtt.Client()
    #client.connect(MQTT_SERVER)
    wii_controller = WiimoteControl()
    wii_controller.on_button(cwiid.BTN_HOME, wii_controller.close)

    def control_wheels(direction):
        (x, y) = direction
        left = 0
        right = 0
        EPSILON_MOTION = .1
        EPSILON_Y = .5
        if abs(y) > EPSILON_Y:
            d = numpy.sign(y)
        else:
            d = 1
        if numpy.linalg.norm(direction) > EPSILON_MOTION:
            if abs(y) < EPSILON_Y:
                # Turn in place
                left = -x
                right = x
            elif x > 0:
                # right
                left = abs(y) * d
                right = numpy.linalg.norm((x, y)) * d
            else:
                # left
                left = numpy.linalg.norm((x, y)) * d
                right = abs(y) * d

        left = 100 * left
        right = 100 * right

        logging.debug("wheels(%.1f, %.1f) => (%d, %d)", x, y, left, right)

        board_controller.left_wheel(left)
        board_controller.right_wheel(right)

    wii_controller.on_direction(control_wheels)

    directions = {
        APDS9960_DIR_NONE: None,
        APDS9960_DIR_LEFT: "left",
        APDS9960_DIR_RIGHT: "right",
        APDS9960_DIR_UP: "forward",
        APDS9960_DIR_DOWN: "backward",
        APDS9960_DIR_NEAR: None,
        APDS9960_DIR_FAR: None,
    }
    direction = None
    try:
        while wii_controller.connected():
            free_space = board_controller.distance()
            location = location_tracker.update_location()
            if self.apds.isGestureAvailable():
                direction = directions[apds.readGesture()]
            if location_tracker.distance >= 0.5:
                # Stop moving after certain time
                direction = None
                location_tracker.reset()
            logging.debug("At (%d,%d). Free distance: %f", location[0], location[1], free_space)
            #client.publish('location', "%d,%d" % (location[0], location[1]))
            #client.publish('free_space', str(free_space))
    except KeyboardInterrupt:
        logging.warning("Shutdown")
    finally:
        board_controller.close()
        wii_controller.close()


if __name__ == "__main__":
    main()

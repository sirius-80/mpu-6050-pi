#!/usr/bin/env python

import cwiid
import logging
import numpy
import RPi.GPIO as GPIO
import time
import concurrent.futures


class GpioController(object):
    def __init__(self):
        # GPIO Mode (BOARD / BCM)
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Button to GPIO23
        GPIO.setup(24, GPIO.OUT)  # LED to GPIO24

        self.blinking = None
        self.executor = None
        self.GPIO_TRIGGER = 18
        self.GPIO_ECHO = 17
        self.pwm_left = None
        self.pwm_right = None

        self.init_led_and_button()
        self.init_ultrasound_module()
        self.init_motor_controls()

    def init_led_and_button(self):
        self.blinking = False
        self.executor = concurrent.futures.ThreadPoolExecutor(4)
        GPIO.add_event_detect(23, GPIO.RISING)
        GPIO.add_event_callback(23, self.led_blinking_fast)
        GPIO.setmode(GPIO.BCM)

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

    def led_blinking_fast(self, channel):
        self.led_blinking(10)

    def led_blinking(self, frequency_hz=3):
        if self.blinking:
            task = self.blinking
            self.blinking = False
            task.result()

        def do_blink():
            while self.blinking:
                self._led(True)
                time.sleep(0.5/frequency_hz)
                self._led(False)
                time.sleep(0.5/frequency_hz)

        self.blinking = self.executor.submit(do_blink)

    def led(self, on_off):
        self.blinking = False
        self._led(on_off)

    def _led(self, on_off):
        """Turn led (connected to pin 24) <on_off>"""
        signal = on_off and GPIO.HIGH or GPIO.LOW
        GPIO.output(24, signal)
        logging.debug("LED %s", on_off and "on" or "off")

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
        if speed > 0:
            self.pwm_left_bck.ChangeDutyCycle(0)
            self.pwm_left_fwd.ChangeDutyCycle(speed)
        else:
            self.pwm_left_fwd.ChangeDutyCycle(0)
            self.pwm_left_bck.ChangeDutyCycle(-speed)

    def right_wheel(self, speed):
        if speed > 0:
            self.pwm_right_bck.ChangeDutyCycle(0)
            self.pwm_right_fwd.ChangeDutyCycle(speed)
        else:
            self.pwm_right_fwd.ChangeDutyCycle(0)
            self.pwm_right_bck.ChangeDutyCycle(-speed)

    def close(self):
        self.led(False)
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
        logging.warn('Press button 1 + 2 on your Wii Remote...')
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
                logging.warn("Timed out waiting for wii-remote, trying again...")
            except KeyboardInterrupt:
                logging.warn("Interrupted. Stopping.")

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
    wii_controller = WiimoteControl()
    board_controller = GpioController()

    wii_controller.on_button(cwiid.BTN_HOME, wii_controller.close)
    wii_controller.on_button(cwiid.BTN_PLUS, board_controller.led, True)
    wii_controller.on_button(cwiid.BTN_MINUS, board_controller.led, False)
    wii_controller.on_button(cwiid.BTN_A, board_controller.led_blinking)
    wii_controller.on_button(cwiid.BTN_1, board_controller.led_blinking, 1.0)
    wii_controller.on_button(cwiid.BTN_2, board_controller.led_blinking, 2.0)

    def wheels(direction):
        (x, y) = direction
        left = 0
        right = 0
        EPSILON = .1
        d = numpy.sign(y)
        if numpy.linalg.norm(direction) > EPSILON:
            if abs(y) < EPSILON:
                # Turn in place
                left = -x
                right = x
            elif x > 0:
                # right
                left = d * abs(y)
                right = d * numpy.linalg.norm((x, y))
            else:  # x > 0:
                # left
                left = d * numpy.linalg.norm((x, y))
                right = d * abs(y)

        left = 100 * left
        right = 100 * right

        logging.debug("wheels(%.1f, %.1f) => (%d, %d)", x, y, left, right)

        board_controller.left_wheel(left)
        board_controller.right_wheel(right)

    wii_controller.on_direction(wheels)

    try:
        while wii_controller.connected():
            time.sleep(.1)
            free_space = board_controller.distance()
            logging.debug("Distance: %f", free_space)
            if free_space < .1:
                board_controller.led_blinking(10)
            elif free_space < .2:
                board_controller.led_blinking(5)
            elif free_space < .3:
                board_controller.led_blinking(3)
            elif free_space < .5:
                board_controller.led_blinking(2)
            elif free_space < 1.0:
                board_controller.led_blinking(1)
            else:
                board_controller.led(False)

    except KeyboardInterrupt:
        logging.info("Shutdown")
    finally:
        board_controller.close()
        wii_controller.close()


if __name__ == "__main__":
    main()
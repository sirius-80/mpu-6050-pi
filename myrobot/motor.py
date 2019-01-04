import time
try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    import myrobot.gpiostub as GPIO


LEFT = "LEFT"
RIGHT = "RIGHT"
FORWARD = "FORWARD"
BACKWARD = "BACKWARD"


class Motor(object):
    def __init__(self):
        GPIO.setmode(GPIO.BCM)  # Use broadcom pin numbering
        GPIO.setwarnings(False)
        self.pwm_left = None
        self.pwm_right = None
        self.motor_direction = -1  # Set to 1 or -1 depending on how the motors are placed (fwd or reversed)
        self.pwm = self._init_motor_controls()

    def _init_motor_controls(self):
        # set GPIO for Pulse Width Modulated motor control
        GPIO.setup(6, GPIO.OUT)
        GPIO.setup(13, GPIO.OUT)
        GPIO.setup(19, GPIO.OUT)
        GPIO.setup(26, GPIO.OUT)
        pwm = {}
        pwm[LEFT] = {}
        pwm[LEFT][FORWARD] = GPIO.PWM(13, 100)
        pwm[LEFT][BACKWARD] = GPIO.PWM(6, 100)
        pwm[RIGHT] = {}
        pwm[RIGHT][FORWARD] = GPIO.PWM(26, 100)
        pwm[RIGHT][BACKWARD] = GPIO.PWM(19, 100)
        pwm[LEFT][FORWARD].start(0)
        pwm[LEFT][BACKWARD].start(0)
        pwm[RIGHT][FORWARD].start(0)
        pwm[RIGHT][BACKWARD].start(0)
        return pwm

    def turn_right(self):
        """Make a right turn of approximately 90 degrees."""
        self.pwm[LEFT][BACKWARD].ChangeDutyCycle(0)
        self.pwm[LEFT][FORWARD].ChangeDutyCycle(100)
        self.pwm[RIGHT][BACKWARD].ChangeDutyCycle(100)
        self.pwm[RIGHT][FORWARD].ChangeDutyCycle(0)
        time_left = 0.87
        while time_left > 0.01:
            start = time.monotonic()
            time.sleep(0.01)
            time_left -= time.monotonic() - start
        self.pwm[LEFT][FORWARD].ChangeDutyCycle(0)
        self.pwm[RIGHT][BACKWARD].ChangeDutyCycle(0)

    def turn_left(self):
        """Make a left turn of approximately 90 degrees."""
        self.pwm[LEFT][BACKWARD].ChangeDutyCycle(100)
        self.pwm[LEFT][FORWARD].ChangeDutyCycle(0)
        self.pwm[RIGHT][BACKWARD].ChangeDutyCycle(0)
        self.pwm[RIGHT][FORWARD].ChangeDutyCycle(100)
        time_left = 0.87
        while time_left > 0.01:
            start = time.monotonic()
            time.sleep(0.01)
            time_left -= time.monotonic() - start
        self.pwm[LEFT][BACKWARD].ChangeDutyCycle(0)
        self.pwm[RIGHT][FORWARD].ChangeDutyCycle(0)

    def forward(self, speed=100):
        """Drive forward at given speed. Speed must be an integer in the range [0..100]"""
        if speed < 0 or speed > 100:
            raise ValueError("Illegal speed (%d). Speed must be in range [0..100]!")
        self.pwm[LEFT][BACKWARD].ChangeDutyCycle(0)
        self.pwm[LEFT][FORWARD].ChangeDutyCycle(speed)
        self.pwm[RIGHT][BACKWARD].ChangeDutyCycle(0)
        self.pwm[RIGHT][FORWARD].ChangeDutyCycle(speed)

    def backward(self, speed=100):
        """Drive backward at given speed. Speed must be an integer in the range [0..100]"""
        if speed < 0 or speed > 100:
            raise ValueError("Illegal speed (%d). Speed must be in range [0..100]!")
        self.pwm[LEFT][BACKWARD].ChangeDutyCycle(speed)
        self.pwm[LEFT][FORWARD].ChangeDutyCycle(0)
        self.pwm[RIGHT][BACKWARD].ChangeDutyCycle(speed)
        self.pwm[RIGHT][FORWARD].ChangeDutyCycle(0)

    def stop(self):
        """Stop both wheels."""
        self.pwm[LEFT][BACKWARD].ChangeDutyCycle(0)
        self.pwm[LEFT][FORWARD].ChangeDutyCycle(0)
        self.pwm[RIGHT][BACKWARD].ChangeDutyCycle(0)
        self.pwm[RIGHT][FORWARD].ChangeDutyCycle(0)

    def left_wheel(self, speed):
        """Drive the left-wheel (independent of the right wheel) at given speed.
        Speed must be a value in the range [-100..100]. A negative speed results in backwards wheel rotation."""
        if speed > 0:
            self.pwm[LEFT][BACKWARD].ChangeDutyCycle(0)
            self.pwm[LEFT][FORWARD].ChangeDutyCycle(speed)
        else:
            self.pwm[LEFT][FORWARD].ChangeDutyCycle(0)
            self.pwm[LEFT][BACKWARD].ChangeDutyCycle(-speed)

    def right_wheel(self, speed):
        """Drive the right-wheel (independent of the right wheel) at given speed.
        Speed must be a value in the range [-100..100]. A negative speed results in backwards wheel rotation."""
        if speed > 0:
            self.pwm[RIGHT][BACKWARD].ChangeDutyCycle(0)
            self.pwm[RIGHT][FORWARD].ChangeDutyCycle(speed)
        else:
            self.pwm[RIGHT][FORWARD].ChangeDutyCycle(0)
            self.pwm[RIGHT][BACKWARD].ChangeDutyCycle(-speed)

    def close(self):
        """Stop motor-controls and cleanup GPIO module."""
        self.pwm[LEFT][FORWARD].stop()
        self.pwm[LEFT][BACKWARD].stop()
        self.pwm[RIGHT][FORWARD].stop()
        self.pwm[RIGHT][BACKWARD].stop()
        GPIO.cleanup()

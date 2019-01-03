import time

try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    import myrobot.gpiostub as GPIO


class Motor(object):
    def __init__(self):
        GPIO.setmode(GPIO.BCM) # Use broadcom pin numbering
        GPIO.setwarnings(False)

        self.pwm_left = None
        self.pwm_right = None

        self.motor_direction = -1 # Set to 1 or -1 depending on how the motors are placed (fwd or reversed)
        self._init_motor_controls()

    def _init_motor_controls(self):
        # set GPIO for PWM motor control
        GPIO.setup(6, GPIO.OUT)
        GPIO.setup(13, GPIO.OUT)
        GPIO.setup(19, GPIO.OUT)
        GPIO.setup(26, GPIO.OUT)
        self.pwm_left_fwd = GPIO.PWM(13, 100)
        self.pwm_left_bck = GPIO.PWM(6, 100)
        self.pwm_right_fwd = GPIO.PWM(26, 100)
        self.pwm_right_bck = GPIO.PWM(19, 100)
        self.pwm_left_fwd.start(0)
        self.pwm_left_bck.start(0)
        self.pwm_right_fwd.start(0)
        self.pwm_right_bck.start(0)

    def turn_right(self):
        self.pwm_left_bck.ChangeDutyCycle(0)
        self.pwm_left_fwd.ChangeDutyCycle(100)
        self.pwm_right_bck.ChangeDutyCycle(100)
        self.pwm_right_fwd.ChangeDutyCycle(0)
        time.sleep(0.85)
        self.pwm_left_fwd.ChangeDutyCycle(0)
        self.pwm_right_bck.ChangeDutyCycle(0)

    def turn_left(self):
        self.pwm_left_bck.ChangeDutyCycle(100)
        self.pwm_left_fwd.ChangeDutyCycle(0)
        self.pwm_right_bck.ChangeDutyCycle(0)
        self.pwm_right_fwd.ChangeDutyCycle(100)
        time.sleep(0.85)
        self.pwm_left_bck.ChangeDutyCycle(0)
        self.pwm_right_fwd.ChangeDutyCycle(0)

    def forward(self):
        self.pwm_left_bck.ChangeDutyCycle(0)
        self.pwm_left_fwd.ChangeDutyCycle(100)
        self.pwm_right_bck.ChangeDutyCycle(0)
        self.pwm_right_fwd.ChangeDutyCycle(100)

    def backward(self):
        self.pwm_left_bck.ChangeDutyCycle(100)
        self.pwm_left_fwd.ChangeDutyCycle(0)
        self.pwm_right_bck.ChangeDutyCycle(100)
        self.pwm_right_fwd.ChangeDutyCycle(0)

    def stop(self):
        self.pwm_left_bck.ChangeDutyCycle(0)
        self.pwm_left_fwd.ChangeDutyCycle(0)
        self.pwm_right_bck.ChangeDutyCycle(0)
        self.pwm_right_fwd.ChangeDutyCycle(0)

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


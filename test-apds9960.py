from apds9960.const import *
from apds9960 import APDS9960
import RPi.GPIO as GPIO
import smbus
import time

port = 1
bus = smbus.SMBus(port)

apds = APDS9960(bus)

def intH(channel):
    print("INTERRUPT")

GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN)

dirs = {
    APDS9960_DIR_NONE: "none",
    APDS9960_DIR_LEFT: "left",
    APDS9960_DIR_RIGHT: "right",
    APDS9960_DIR_UP: "up",
    APDS9960_DIR_DOWN: "down",
    APDS9960_DIR_NEAR: "near",
    APDS9960_DIR_FAR: "far",
}
try:
    # Interrupt-Event hinzufuegen, steigende Flanke
    GPIO.add_event_detect(4, GPIO.FALLING, callback = intH)

#    apds.setProximityIntLowThreshold(50)

    print("Gesture Test")
    print("============")
    apds.enableGestureSensor()
    while True:
        time.sleep(0.5)
        if apds.isGestureAvailable():
            motion = apds.readGesture()
            print("Gesture={}".format(dirs.get(motion, "unknown")))


finally:
    GPIO.cleanup()
    print "Bye"


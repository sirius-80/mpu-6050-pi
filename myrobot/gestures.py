import logging
import apds9960
import smbus
try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    import myrobot.gpiostub as GPIO


class GestureReceiver(object):
    """Initializes the apds9960 module and posts any gestures made to the provided queue.
    Supported gestures are: 'forward', 'backward', 'left' and 'right'."""
    def __init__(self, queue):
        self.queue = queue
        GPIO.setmode(GPIO.BCM) # Use broadcom pin numbering
        GPIO.setwarnings(False)
        port = 1
        bus = smbus.SMBus(port)
        self.apds = apds9960.APDS9960(bus)
        GPIO.setup(4, GPIO.IN)
        GPIO.add_event_detect(4, GPIO.FALLING, callback=self._gesture_handler)
        self.apds.enableGestureSensor()

    def _gesture_handler(self, channel):
        directions = {
            apds9960.const.APDS9960_DIR_NONE: None,
            apds9960.const.APDS9960_DIR_LEFT: "left",
            apds9960.const.APDS9960_DIR_RIGHT: "right",
            apds9960.const.APDS9960_DIR_UP: "forward",
            apds9960.const.APDS9960_DIR_DOWN: "backward",
            apds9960.const.APDS9960_DIR_NEAR: None,
            apds9960.const.APDS9960_DIR_FAR: None,
        }
        direction = directions[self.apds.readGesture()]
        if direction:
            logging.info("Received gesture: %s on channel %s" % (direction, str(channel)))
            self.queue.put(direction)

    def close(self):
        GPIO.cleanup()

BCM = "BCM"
BOARD = "BOARD"
PUD_UP = "PUD_UP"
PUD_DOWN = "PUD_DOWN"
IN = "IN"
OUT = "OUT"


def setwarnings(warnings):
    print("GPIO-stub: setwarnings(%s)" % (str(warnings)))


def setmode(mode):
    print("GPIO-stub: setmode(%s)" % (str(mode)))


def setup(pin, mode, pull_up_down=PUD_DOWN):
    print("GPIO-stub: setup(%s, %s, pull_up_down=%s)" % (str(pin), str(mode), str(pull_up_down)))


def add_event_detect(pin, rising_falling, callback=None):
    print("GPIO-stub: add_event_detect(%s, %s, callback=%s)" % (str(pin), str(rising_falling), str(callback)))


class PWM:
    def __init__(self, pin, frequency):
        print("GPIO-stub: PWN(%s, %s)" % (str(pin), str(frequency)))

    def ChangeDutyCycle(self, duty):
        pass

    def ChangeFrequency(self, frequency):
        pass

    def start(self, dutycycle):
        pass

def output(pin, output):
    print("GPIO-stub: output(%s, %s)" % (str(pin), str(output)))


def input(pin):
    print("GPIO-stub: input(%s)" % (str(pin)))


def cleanup():
    print("GPIO-stub: cleanup()")

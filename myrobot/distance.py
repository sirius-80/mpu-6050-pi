import threading
import time
import traceback
from myrobot.log import Log

try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    import myrobot.gpiostub as GPIO


class DistanceDevice(Log):
    def __init__(self, distance_callback, pubsub_client=None, update_frequency=2.0):
        super().__init__()
        self.distance_callback = distance_callback
        self.pubsub_client = pubsub_client
        self.update_frequency = update_frequency
        GPIO.setmode(GPIO.BCM)  # Use broadcom pin numbering
        GPIO.setwarnings(False)
        self.GPIO_TRIGGER = 18
        self.GPIO_ECHO = 17
        # set GPIO Pins for ultra-sound TX module
        GPIO.setup(self.GPIO_TRIGGER, GPIO.OUT)
        GPIO.setup(self.GPIO_ECHO, GPIO.IN)
        self.distance = None
        self.running = False
        self._thread = threading.Thread(target=self.run, name="DistanceDeviceThread")

    def start(self):
        self.running = True
        self._thread.start()

    def run(self):
        cycle_time = 1.0 / self.update_frequency
        while self.running:
            start = time.monotonic()

            self.distance = self.measure_distance()
            self.pubsub_client.send_free_space(self.distance)

            if self.distance_callback:
                try:
                    self.distance_callback(self.distance)
                except:
                    traceback.print_exc()

            # Determine next sleep period
            remaining_cycle_time = cycle_time - (time.monotonic() - start)
            if remaining_cycle_time > 0:
                time.sleep(remaining_cycle_time)

    def stop(self):
        self.running = False
        self._thread.join(timeout=5.0 / self.update_frequency)

    def get_distance(self):
        return self.distance

    def measure_distance(self):
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

    def close(self):
        """Stop distance measurements and cleanup GPIO module."""
        self.stop()
        GPIO.cleanup()

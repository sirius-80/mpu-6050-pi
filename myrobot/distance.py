import logging
import threading
import time
import traceback

try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    import myrobot.gpiostub as GPIO


class DistanceDevice:
    def __init__(self, update_frequency=2.0):
        GPIO.setmode(GPIO.BCM)  # Use broadcom pin numbering
        GPIO.setwarnings(False)
        self.GPIO_TRIGGER = 18
        self.GPIO_ECHO = 17
        # set GPIO Pins for ultra-sound TX module
        GPIO.setup(self.GPIO_TRIGGER, GPIO.OUT)
        GPIO.setup(self.GPIO_ECHO, GPIO.IN)
        self.distance = None
        self.running = False
        self.update_frequency = update_frequency
        self._thread = threading.Thread(target=self.run)
        self.min_distance_callable = (None, None)

    def start(self):
        self.running = True
        self._thread.start()

    def set_action_on_min_distance(self, callable, min_distance):
        """When measured distance falls below given min_distance, given callable is called."""
        self.min_distance_callable = (min_distance, callable)

    def run(self):
        cycle_time = 1.0 / self.update_frequency
        while self.running:
            start = time.monotonic()

            self.distance = self.get_distance()
            min_distance = self.min_distance_callable[0]
            if min_distance is not None and self.distance < min_distance:
                logging.info("Specified minimum distance (%.02f m) reached (%.02f m)." % (min_distance, self.distance))
                try:
                    self.min_distance_callable[1]()
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

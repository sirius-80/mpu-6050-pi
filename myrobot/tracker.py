import logging
import math
import struct
import threading


class Tracker:
    """Location tracker. Once started will update its location every second.
    """
    def __init__(self, pubsub_client=None):
        self.pubsub_client = pubsub_client
        self.location = [0.0, 0.0]
        self.mouse_fd = open("/dev/input/mice", "rb")
        self.scale = 0.0001958033
        self.start_location = self.location
        self.distance = 0.0
        self.running = False
        self._thread = threading.Thread(target=self._update_location)

    def start(self):
        """Start tracking the location."""
        self.running = True
        self._thread.start()

    def stop(self):
        """Stop tracking the location."""
        # self.scheduler.shutdown()
        self.running = False
        self._thread.join()

    def reset(self):
        """Resets distance. The start-location is set to the current location."""
        self.start_location = self.location
        self.distance = 0

    def get_distance(self):
        """Returns distance traveled  (m) since the last reset."""
        return self.distance

    def get_location(self):
        """Returns the current location as a tuple (x,y)."""
        return tuple(self.location)

    def _update_location(self):
        """Read-out mouse data to update the current location."""
        while self.running:
            buf = self.mouse_fd.read(3)
            dx, dy = [float(i) * self.scale for i in struct.unpack("bb", buf[1:])]
            self.location[0] += dx
            self.location[1] += dy
            self.distance += math.sqrt(dx*dx + dy*dy)

            self.pubsub_client.send_location(*self.location)
            logging.debug("Location update. Now at (%.02f, %.02f)" % self.location)

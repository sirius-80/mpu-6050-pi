import logging
import time
import queue
import threading
import myrobot.motor
import myrobot.tracker
import myrobot.gestures
import myrobot.distance


class Robot:
    """Creates a new robot. The robot takes gestures as commands, and uses an internal queue to process the commands
    into motor-commands (i.e. drive, turn)."""
    def __init__(self):
        self.command_queue = queue.Queue(1)
        self.motor = myrobot.motor.Motor()
        self.tracker = myrobot.tracker.Tracker()
        self.gestures = myrobot.gestures.GestureReceiver(self.command_queue)
        self.distance_device = myrobot.distance.DistanceDevice()
        self.running = False
        self._thread = threading.Thread(target=self._process_command_queue)

    def start(self):
        """Start all parts of the robot."""
        self.running = True
        self._thread.start()
        self.tracker.start()
        self.distance_device.start()

    def stop(self):
        self.running = False
        self._thread.join(timeout=5.0)
        self.tracker.stop()
        self.distance_device.stop()

    def _process_command_queue(self):
        while self.running:
            logging.info("Waiting for command...")
            command = self.command_queue.get()
            logging.info("Processing command: [%s]" % (command, ))
            if command == "forward":
                self.tracker.reset()
                self.motor.forward()
                while self.tracker.get_distance() < 0.5:
                    time.sleep(0.1)
                    logging.debug("Traveling forward: [%.2f / %.2f m.]" % (self.tracker.get_distance(), 0.5))
                self.motor.stop()
            elif command == "backward":
                self.tracker.reset()
                self.motor.backward()
                while self.tracker.get_distance() < 0.5:
                    time.sleep(0.1)
                    logging.debug("Traveling backward: [%.2f / %.2f m.]" % (self.tracker.get_distance(), 0.5))
                self.motor.stop()
            elif command == "left":
                self.motor.turn_left()
            elif command == "right":
                self.motor.turn_right()
        self.tracker.stop()
        self.motor.stop()
        self.motor.close()

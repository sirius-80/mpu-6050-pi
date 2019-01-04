import logging
import time
import queue
import threading
import myrobot.motor
import myrobot.tracker
import myrobot.gestures
import myrobot.distance


class Robot(threading.Thread):
    """Creates a new robot. The robot takes gestures as commands, and uses an internal queue to process the commands
    into motor-commands (i.e. drive, turn)."""
    def __init__(self):
        threading.Thread.__init__(self)
        self.command_queue = queue.Queue(1)
        self.motor = myrobot.motor.Motor()
        self.tracker = myrobot.tracker.Tracker()
        self.gestures = myrobot.gestures.GestureReceiver(self.command_queue)
        self.distance_device = myrobot.distance.DistanceDevice()
        self.running = False
        self.emergency = False
        self.distance_device.set_action_on_min_distance(self.emergency_break, 0.10)  # Emergency break at 0.10 m.

    def start(self):
        """Start all parts of the robot."""
        self.running = True
        self.tracker.start()
        self.distance_device.start()
        threading.Thread.start(self)

    def emergency_break(self):
        self.emergency = True

    def stop(self):
        self.running = False
        self.join(timeout=5.0)

    def run(self):
        while self.running:
            self.emergency = False
            logging.info("Waiting for command...")
            command = self.command_queue.get()
            logging.info("Processing command: [%s]" % (command, ))
            if command == "forward":
                self.tracker.reset()
                self.motor.forward()
                while not self.emergency and self.tracker.get_distance() < 0.5:
                    logging.debug("Traveling forward: [%.2f / %.2f m.]" % (self.tracker.get_distance(), 0.5))
                    time.sleep(0.1)
                self.motor.stop()
                logging.info("Traveled %.2f , forward.]" % (self.tracker.get_distance(), ))
            elif command == "backward":
                self.tracker.reset()
                self.motor.backward()
                while self.tracker.get_distance() < 0.5:
                    logging.debug("Traveling backward: [%.2f / %.2f m.]" % (self.tracker.get_distance(), 0.5))
                    time.sleep(0.1)
                self.motor.stop()
                logging.info("Traveled %.2f , backward.]" % (self.tracker.get_distance(), ))
            elif command == "left":
                self.motor.turn_left()
            elif command == "right":
                self.motor.turn_right()
        logging.info("Stopping all robot parts...")
        self.motor.stop()
        self.tracker.stop()
        self.distance_device.stop()

        self.motor.close()
        self.distance_device.close()

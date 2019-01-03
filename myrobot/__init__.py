import logging
import time
import queue
import threading
import myrobot.motor
import myrobot.tracker
import myrobot.gestures


class Robot:
    def __init__(self):
        self.command_queue = queue.Queue(1)
        self.motor = myrobot.motor.Motor()
        self.tracker = myrobot.tracker.Tracker()
        self.gestures = myrobot.gestures.GestureReceiver(self.command_queue)
        self.running = False

    def start(self):
        self.running = True
        thread = threading.Thread(target=self._process_queue)
        thread.start()

    def stop(self):
        self.running = False

    def _process_queue(self):
        while self.running:
            logging.info("Waiting for command...")
            command = self.command_queue.get()
            logging.info("Processing command: [%s]" % (command, ))
            if command == "forward":
                self.motor.forward()
                time.sleep(2)
                self.motor.stop()
            elif command == "backward":
                self.motor.backward()
                time.sleep(2)
                self.motor.stop()
            elif command == "left":
                self.motor.turn_left()
            elif command == "right":
                self.motor.turn_right()
        self.tracker.stop()
        self.motor.stop()

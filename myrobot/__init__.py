import time
import queue
import threading
import myrobot.motor
import myrobot.tracker
import myrobot.gestures
import myrobot.distance
import myrobot.pubsub
from myrobot.log import Log

BACKOFF = 'backoff'
COMMAND = 'command'


class DistanceEventListener:
    def distance_event(self, distance):
        pass


class Robot(threading.Thread, Log, DistanceEventListener):
    """Creates a new robot. The robot takes gestures as commands, and uses an internal queue to process the commands
    into motor-commands (i.e. drive, turn)."""
    def __init__(self):
        Log.__init__(self)
        threading.Thread.__init__(self, name="RobotThread")
        self.command_queue = queue.Queue(1)
        self.motor = myrobot.motor.Motor()
        pubsub = myrobot.pubsub.PubSubClient()
        self.tracker = myrobot.tracker.Tracker(pubsub)
        self.gestures = myrobot.gestures.GestureReceiver(self.command_queue)
        self.distance_device = myrobot.distance.DistanceDevice(self.distance_event, pubsub)
        self.running = False
        self.strategies = {COMMAND: CommandStrategy(self, self.command_queue),
                           BACKOFF: BackoffStrategy(self)}
        self.control_strategy = self.strategies[COMMAND]

    def start(self):
        """Start all parts of the robot."""
        self.running = True
        self.tracker.start()
        self.distance_device.start()
        threading.Thread.start(self)

    def distance_event(self, distance):
        if distance < 0.1:
            if self.control_strategy is not self.strategies[BACKOFF]:
                self.logger.warning("STRATEGY -> BACKOFF")
                self.control_strategy.interrupt()
                self.control_strategy = self.strategies[BACKOFF]
                self.control_strategy.proceed()
        else:
            if self.control_strategy is not self.strategies[COMMAND]:
                self.logger.warning("STRATEGY -> COMMAND")
                self.control_strategy.interrupt()
                self.control_strategy = self.strategies[COMMAND]
                self.control_strategy.proceed()

    def stop(self):
        self.running = False
        self.join(timeout=5.0)

    def run(self):
        while self.running:
            self.control_strategy.execute()
            self.motor.stop()
        self.logger.info("Stopping all robot parts...")
        self.motor.stop()
        self.tracker.stop()
        self.distance_device.stop()

        self.motor.close()
        self.distance_device.close()


class ControlStrategy(Log):
    def __init__(self, robot):
        super().__init__()
        self.robot = robot
        self.interrupted = False

    def execute(self):
        """Execute single pass of this strategy."""
        pass

    def interrupt(self):
        self.logger.info("%s interrupted!!!" % self.__class__)
        self.interrupted = True

    def proceed(self):
        self.interrupted = False


class BackoffStrategy(ControlStrategy):
    def __init__(self, robot):
        ControlStrategy.__init__(self, robot)

    def execute(self):
        self.logger.info("BackoffStrategy::execute()")
        ControlStrategy.execute(self)
        while not self.interrupted and self.robot.distance_device.get_distance() < 0.10:
            self.robot.motor.backward(100)
            time.sleep(0.1)
        self.robot.motor.stop()


class CommandStrategy(ControlStrategy):
    def __init__(self, robot, command_queue):
        ControlStrategy.__init__(self, robot)
        self.command_queue = command_queue

    def execute(self):
        self.logger.info("CommandStrategy::execute()")
        ControlStrategy.execute(self)
        self.logger.info("Waiting for command...")
        while self.command_queue.empty():
            time.sleep(0.1)
            if self.interrupted:
                return
        try:
            command = self.command_queue.get(timeout=0.1)
        except Empty:
            return

        self.logger.info("Processing command: [%s]" % (command, ))
        if command == "forward":
            self.robot.tracker.reset()
            self.robot.motor.forward()
            while not self.interrupted and self.robot.tracker.get_distance() < 0.5:
                self.logger.debug("Traveling forward: [%.2f / %.2f m.]" % (self.robot.tracker.get_distance(), 0.5))
                time.sleep(0.1)
            self.logger.info("Traveled %.2f , forward.]" % (self.robot.tracker.get_distance(), ))
        elif command == "backward":
            self.robot.tracker.reset()
            self.robot.motor.backward()
            while not self.interrupted and self.robot.tracker.get_distance() < 0.5:
                self.logger.debug("Traveling backward: [%.2f / %.2f m.]" % (self.robot.tracker.get_distance(), 0.5))
                time.sleep(0.1)
            self.logger.info("Traveled %.2f , backward.]" % (self.robot.tracker.get_distance(), ))
        elif command == "left":
            self.robot.motor.turn_left()
        elif command == "right":
            self.robot.motor.turn_right()
        self.robot.motor.stop()


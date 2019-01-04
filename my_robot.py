import myrobot
import logging


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s - %(message)s')
    try:
        robot = myrobot.Robot()
        robot.start()
        robot.join()
    except KeyboardInterrupt:
        logging.info("Stopping robot!")
        robot.stop()


if __name__ == "__main__":
    main()

import myrobot
import logging


def main():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s - %(message)s')
    try:
        robot = myrobot.Robot()
        robot.start()
    finally:
        robot.stop()


if __name__ == "__main__":
    main()

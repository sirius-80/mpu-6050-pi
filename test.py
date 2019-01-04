import random
import time
import statistics


def loop(frequency, duration=10):
    """Read-out mouse data to update the current location."""
    CYCLE_TIME = 1.0 / frequency
    last_start_time = time.monotonic()
    START = last_start_time
    end_time = last_start_time + duration
    jitter = []
    counter = 0
    while time.monotonic() < end_time:
        start = time.monotonic()
        print("Start: %f" % start)
        time.sleep(random.random() / frequency / 2.0)  # Pretend to do something
        next_tick = last_start_time + 2 * CYCLE_TIME
        jitter.append(abs(start - last_start_time - CYCLE_TIME))
        last_start_time = start
        # remaining_time = next_tick - time.monotonic()
        remaining_time = CYCLE_TIME - (time.monotonic() - start)
        print("  sleep: %f" % remaining_time)
        if remaining_time > 0:
            time.sleep(remaining_time)
        counter += 1
    END = time.monotonic()
    print("Iterated %d times in %f seconds. Mean cycle time: %f" % (counter, END-START, (END-START) / counter))
    print("Jitter: average: %f, std-dev: %f" % (statistics.mean(jitter[1:]), statistics.stdev(jitter[1:])), jitter[1:])



if __name__ == "__main__":
    loop(100)

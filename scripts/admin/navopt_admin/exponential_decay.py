import logging
import time

LOG = logging.getLogger(__name__)


def exponential_decay(time_limit):
    start_time = time.time()
    sleep_time = 0.1

    while time.time() - start_time < time_limit:
        yield

        time.sleep(sleep_time)
        sleep_time *= 2

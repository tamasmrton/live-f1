import logging
from time import sleep

import requests as re

log = logging.getLogger(__name__)


def get(endpoint: str, params: dict, retries: int = 3) -> re.Response:
    """
    Wraps over requests.get() method.
    Adds retriability and logging.
    """
    counter = 0
    while counter < retries:
        counter += 1
        log.info("GET %s (%s/%s)...", endpoint, counter, retries)
        response = re.get(url=endpoint, params=params)
        if response.status_code == 200 and response.json():
            return response
        log.warning("Unable to fetch data, retrying...")
        sleep(10)
    return response

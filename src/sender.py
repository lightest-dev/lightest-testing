import time
import logging
from models import Settings
import requests


class Sender:
    _max_tries: int
    _settings: Settings

    def __init__(self, settings: Settings):
        self._settings = settings

    def send_message(self, data: dict, endpoint: str):
        """Sends result to remote server

        Arguments:
            data {dict} -- json to send to remote
            endpoint {string} -- endpoint to send data to
        """
        logging.info(f'Data: {data}')
        tries = 0
        successful = False
        while not successful:
            try:
                if tries >= self._settings.max_try_time:
                    logging.error(f'Failed to send message to {endpoint}')
                    break
                r = requests.post(
                    self._settings.api_server + endpoint, json=data)
                successful = (r.status_code == 200)
                logging.info(f'Endpoint: {endpoint}. Successful: {successful}')
                if successful:
                    break
                time.sleep(5)
                tries += 5
            except:
                logging.error(f'Failing to send data to {endpoint}')
                time.sleep(5)
                tries += 5

    def notify_started(self):
        logging.info('Sending notification')
        message = {
            'ip': self._settings.ip,
        }
        self.send_message(message, 'new')

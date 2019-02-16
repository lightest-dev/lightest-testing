import asyncio
import logging
from models import Status, Settings
import requests
from hasher import get_server_hash


class Sender:
    _max_tries: int
    _settings: Settings

    def __init__(self, settings: Settings):
        self._settings = settings
        self._max_tries = 5

    async def send_message(self, data: dict, endpoint: str):
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
                if tries == self._max_tries:
                    logging.error(f'Failed to send message to {endpoint}')
                    break
                r = requests.post(
                    self._settings.api_server + endpoint, json=data)
                successful = (r.status_code == 200)
                logging.info(f'Endpoint: {endpoint}. Successful: {successful}')
                if successful:
                    break
                await asyncio.sleep(5)
                tries += 1
            except:
                logging.error(f'Failing to send data to {endpoint}')
                await asyncio.sleep(5)
                tries += 1

    async def send_status(self, status: Status):
        message = {
            'status': status.name
        }
        await self.send_message(message, 'status')

    async def notify_started(self):
        # wait for server to properly initialize
        await asyncio.sleep(20)
        logging.info('Sending notification')
        server_hash = get_server_hash()
        message = {
            'ip': self._settings.ip,
            'serverVersion': server_hash
        }
        await self.send_message(message, 'new')

    async def send_error(self, ex: Exception):
        data = {
            'errorMessage': str(ex)
        }
        await self.send_message(data, 'error')

import json
from command_provider import CommandProvider
from models.limits import Limits
from sender import Sender
from checker import CodeChecker
import logging
from models import Settings
import socket

if __name__ == "__main__":
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 1))  # connect() for UDP doesn't send packets
    local_ip_address = s.getsockname()[0]
    logging.basicConfig(level=logging.INFO)
    with open('settings.json') as f:
        data = json.load(f)
        logging.info(f'Config: {data}')
        settings = Settings.from_json(data)
    with open('languages.json') as f:
        data = json.load(f)
        provider = CommandProvider()
        provider.add_languages(*data)
    with open('limits.json') as f:
        data = json.load(f)
        logging.info(f'Limits: {data}')
        limits = Limits.from_json(data)
    logging.info(f'Local ip: {local_ip_address}')
    settings.ip = local_ip_address
    checker = CodeChecker(settings, limits, provider)
    sender = Sender(settings)

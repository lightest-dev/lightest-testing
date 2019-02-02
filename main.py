import asyncio
import json
from server import Server
import logging
from models.settings import Settings
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
    logging.info(f'Local ip: {local_ip_address}')
    settings.ip = local_ip_address
    current_server = Server(settings)
    asyncio.run(current_server.start())

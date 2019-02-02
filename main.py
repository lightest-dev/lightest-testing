import asyncio
import json
from server import Server
import logging
from models.settings import Settings

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with open('settings.json') as f:
        data = json.load(f)
        logging.info(f'Config: {data}')
        settings = Settings.from_json(data)
    current_server = Server(settings)
    asyncio.run(current_server.start())

import asyncio
import json
from server import Server
from models.settings import Settings

if __name__ == "__main__":
    with open('settings.json') as f:
        data = json.load(f)
        settings = Settings.from_json(data)
    current_server = Server(settings)
    asyncio.run(current_server.start())

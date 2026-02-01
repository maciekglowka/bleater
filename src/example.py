from bleater.server.storage import SqlliteStorageBuilder
import asyncio
from bleater.server import BleaterServer
import os

DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DIR, "test.db")

server = BleaterServer(storage=SqlliteStorageBuilder(DB_PATH))

if __name__ == "__main__":
    asyncio.run(server.serve())

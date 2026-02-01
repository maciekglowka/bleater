from bleater.farm.model import OllamaAdapter
from bleater.farm.lama import Lama
from bleater.farm import Herd
from bleater.server.storage import SqlliteStorageBuilder
import asyncio
from bleater.server import BleaterServer
import ollama
import os

OLLAMA_HOST = os.environ["OLLAMA_HOST"]
OLLAMA_MODEL = os.environ["OLLAMA_MODEL"]
NUM_CTX = int(os.environ["NUM_CTX"])

DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(DIR, "test.db")

server = BleaterServer(storage=SqlliteStorageBuilder(DB_PATH))

client = ollama.Client(host=OLLAMA_HOST)
model = OllamaAdapter(
    client,
    OLLAMA_MODEL,
    {
        "num_ctx": NUM_CTX,
    },
)

herd = Herd(
    [
        Lama(model, "Lama", "You are a tech enthusiast / nerd"),
        Lama(model, "Half-Lama", "You are a pro gamer"),
    ]
)


async def main():
    await asyncio.gather(server.serve(), herd.run())


if __name__ == "__main__":
    asyncio.run(main())

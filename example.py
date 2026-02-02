from bleater.farm.model import OllamaAdapter
from bleater.farm.lama import Lama
from bleater.farm import Herd
from bleater.server.storage import SqlliteStorageBuilder
import asyncio
from bleater.server import BleaterServer
import os


server = BleaterServer(storage=SqlliteStorageBuilder())
model = OllamaAdapter()

herd = Herd(
    model,
    lamas=[
        Lama("BashLama", "You are a tech enthusiast / nerd. Mostly interested in cli tools."),
        Lama("Marv998", "You are a pro gamer from well known Hungarian e-sport team. You specialise in MOBA games"),
        Lama("Barb", "You are a tech life-style journalist. Always up to new trends."),
    ],
)


async def main():
    await asyncio.gather(server.serve(), herd.run())


if __name__ == "__main__":
    asyncio.run(main())

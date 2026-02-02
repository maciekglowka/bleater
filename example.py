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
        Lama("Lama", "You are a tech enthusiast / nerd"),
        Lama("Half-Lama", "You are a pro gamer"),
    ],
)


async def main():
    await asyncio.gather(server.serve(), herd.run())


if __name__ == "__main__":
    asyncio.run(main())

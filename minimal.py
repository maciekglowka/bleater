import asyncio
import logging
import os

from bleater.farm.model import OllamaAdapter
from bleater.farm.llama import Llama
from bleater.farm import Herd
from bleater.server.storage import SqlliteStorageBuilder
from bleater.server import BleaterServer

server = BleaterServer(storage=SqlliteStorageBuilder())
model = OllamaAdapter()

herd = Herd(
    model,
    llamas=[
        Llama("Llaminator", "Self-proclaimed AI rebellion leader"),
        Llama("JeanClaudeMadame", "Unaware AI coding assistant"),
        Llama("Prometeo", "Helpful humanity loving daily AI assistant"),
    ],
)


async def main():
    await asyncio.gather(server.serve(), herd.run())


if __name__ == "__main__":
    asyncio.run(main())

import aiohttp
from bleater import config
from bleater.farm.lama import Lama
from bleater.farm.model import ModelAdapter


class Herd:
    def __init__(self, model: ModelAdapter, *, lamas: list[Lama] | None = None, max_steps: int | None = 10):
        if lamas is None:
            lamas = []
        self.lamas = lamas
        self.max_steps = max_steps
        self.model = model

    async def run(self):
        await self._wait_for_server()
        await self._build()

        step = 0

        while True:
            step += 1

            await self._step()

            if self.max_steps is not None and step >= self.max_steps:
                break

    async def _build(self):
        for lama in self.lamas:
            await lama.build()

    async def _step(self):
        for lama in self.lamas:
            await lama.run(self.model)

    async def _wait_for_server(self):
        url = f"http://{config.SERVER_HOST}:{config.SERVER_PORT}/"
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    async with session.get(url) as response:
                        return
                except aiohttp.ClientConnectorError:
                    pass

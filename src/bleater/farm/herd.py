import aiohttp
from bleater import config
from bleater.farm.lama import Lama


class Herd:
    def __init__(self, lamas: list[Lama], *, max_steps: int | None = 10):
        self.lamas = lamas
        self.max_steps = max_steps

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
            await lama.run()

    async def _wait_for_server(self):
        url = f"http://{config.SERVER_HOST}:{config.SERVER_PORT}/"
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    async with session.get(url) as response:
                        return
                except aiohttp.ClientConnectorError:
                    pass

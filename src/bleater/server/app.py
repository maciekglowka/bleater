from bleater import config
from bleater.server.storage import BaseStorageBuilder, get_storage
from fastapi import FastAPI
import uvicorn

from .api import router as api_router


class BleaterServer:
    def __init__(self, storage: BaseStorageBuilder):
        self.app = None
        self.storage = storage

    async def _build(self):
        app = FastAPI()
        app.dependency_overrides[get_storage] = await self.storage.build()

        app.include_router(api_router)

        @app.get("/")
        async def root():
            return {"message": "Hello"}

        self.app = app

    async def serve(self):
        await self._build()
        assert self.app is not None

        server_config = uvicorn.Config(self.app, port=config.SERVER_PORT, host=config.SERVER_BIND_ADDR)
        server = uvicorn.Server(server_config)
        try:
            await server.serve()
        finally:
            await self.storage.close()

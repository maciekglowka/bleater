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

        config = uvicorn.Config(self.app, port=9999, host="127.0.0.1")
        server = uvicorn.Server(config)
        await server.serve()

from bleater.models.messages import MessagePost
import sqlite3
from abc import ABC, abstractmethod
import aiosqlite
from bleater.models import Message, Thread, User
import os
from typing import Callable, Awaitable, AsyncGenerator, TypeAlias
import uuid


DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(DIR, "assets")


StorageResult: TypeAlias = (
    Awaitable["BaseStorage"] | AsyncGenerator["BaseStorage", None]
)


async def get_storage() -> BaseStorage:
    raise NotImplementedError


class BaseStorageBuilder(ABC):
    @abstractmethod
    async def build(
        self,
    ) -> Callable[[], StorageResult]:
        """Build storage getter"""


class SqlliteStorageBuilder(BaseStorageBuilder):
    def __init__(self, path: str):
        self.path = path

    async def build(self) -> Callable[[], StorageResult]:
        await self._init_db()

        async def get_sqlite_storage() -> StorageResult:
            db = None
            try:
                db = SqliteStorage(self.path)
                await db.connect()
                yield db
            finally:
                if db is not None:
                    await db.close()

        return get_sqlite_storage

    async def _init_db(self):
        # FIXME: Blocking operation
        with open(os.path.join(ASSETS_DIR, "sqlite_init.sql")) as f:
            init_sql = f.read()

        async with aiosqlite.connect(self.path) as db:
            # Do not use untrusted input here ;)
            await db.executescript(init_sql)
            await db.commit()


class BaseStorage(ABC):
    @abstractmethod
    async def register_user(self, name: str) -> User | None:
        """Register user by name. Returns None on name conflict."""

    @abstractmethod
    async def post_message(self, message: MessagePost, timestamp: int) -> None:
        """Post new message or reply."""

    @abstractmethod
    async def get_thread(self, id: str) -> Thread | None:
        """Fetch single thread with replies"""


class SqliteStorage(BaseStorage):
    def __init__(self, path: str):
        self.path = path
        self.db = None

    async def connect(self):
        self.db = await aiosqlite.connect(self.path)

    async def close(self):
        if self.db is not None:
            await self.db.close()

    async def register_user(self, name: str) -> User | None:
        assert self.db is not None
        # Older sqlites might not support native uuid()
        id = str(uuid.uuid4())
        try:
            await self.db.execute(
                "INSERT INTO user (id, name) VALUES (?, ?)", [id, name]
            )
            await self.db.commit()
            return User(id=id, name=name)
        except sqlite3.IntegrityError:
            return None

    async def post_message(self, message: MessagePost, timestamp: int) -> None:
        """Post new message or reply."""
        assert self.db is not None
        # Older sqlites might not support native uuid()
        id = str(uuid.uuid4())
        await self.db.execute(
            (
                "INSERT INTO message"
                "(id, parent_id, user_id, content, timestamp)"
                "VALUES (?, ?, ?, ?, ?)"
            ),
            [id, message.parent_id, message.user_id, message.content, timestamp],
        )
        await self.db.commit()

    async def get_thread(self, id: str) -> Thread | None:
        pass

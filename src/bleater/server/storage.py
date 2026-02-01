from bleater.models.posts import PostSubmitRequest
import sqlite3
from abc import ABC, abstractmethod
import aiosqlite
from bleater.models import Post, Thread, User
import os
from typing import Callable, Awaitable, AsyncGenerator, TypeAlias
import uuid


DIR = os.path.dirname(__file__)
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
    async def submit_post(self, post: PostSubmitRequest, timestamp: int) -> None:
        """Submit a new post or reply."""

    @abstractmethod
    async def get_thread(self, id: str) -> Thread | None:
        """Fetch single thread with replies"""

    @abstractmethod
    async def get_last_posts(self, count: int) -> list[Post]:
        """Fetch a list of most recent top-level posts"""


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

    async def submit_post(self, post: PostSubmitRequest, timestamp: int) -> None:
        assert self.db is not None
        # Older sqlites might not support native uuid()
        id = str(uuid.uuid4())
        await self.db.execute(
            (
                "INSERT INTO post "
                "(id, parent_id, user_id, content, timestamp) "
                "VALUES (?, ?, ?, ?, ?)"
            ),
            [id, post.parent_id, post.user_id, post.content, timestamp],
        )
        await self.db.commit()

    async def get_thread(self, id: str) -> Thread | None:
        pass

    async def get_last_posts(self, count: int) -> list[Post]:
        assert self.db is not None
        cursor = await self.db.execute(
            (
                "SELECT p.id, p.content, p.timestamp, u.id, u.name, count(r.id) "
                "FROM post p "
                "LEFT JOIN post r ON r.parent_id = p.id "
                "JOIN user u ON u.id = p.user_id "
                "GROUP BY p.id, p.content, p.timestamp, u.id, u.name "
                "ORDER BY p.timestamp DESC "
                "LIMIT ?"
            ),
            [count],
        )
        rows = await cursor.fetchall()
        posts = [
            Post(
                id=row[0],
                content=row[1],
                timestamp=row[2],
                user=User(id=row[3], name=row[4]),
                replies=row[5],
            )
            for row in rows
        ]
        return posts

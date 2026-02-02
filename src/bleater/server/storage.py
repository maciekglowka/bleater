from bleater.models.posts import PostSubmitRequest
import sqlite3
from abc import ABC, abstractmethod
import aiosqlite
from bleater.models import Post, Thread, User
import os
from typing import Callable, Awaitable, AsyncGenerator, TypeAlias
import tempfile
import uuid


DIR = os.path.dirname(__file__)
ASSETS_DIR = os.path.join(DIR, "assets")


StorageResult: TypeAlias = Awaitable["BaseStorage"] | AsyncGenerator["BaseStorage", None]


async def get_storage() -> BaseStorage:
    raise NotImplementedError


class BaseStorageBuilder(ABC):
    @abstractmethod
    async def build(
        self,
    ) -> Callable[[], StorageResult]:
        """Build storage getter"""

    @abstractmethod
    async def close(self):
        """Storage teardown"""


class SqlliteStorageBuilder(BaseStorageBuilder):
    def __init__(self, *, path: str | None = None):
        if path is None:
            with tempfile.NamedTemporaryFile(delete_on_close=False) as f:
                self.path = f.name
            self.is_temp = True
        else:
            self.path = path
            self.is_temp = False

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

    async def close(self):
        # FIXME: blocking code
        if self.is_temp:
            os.remove(self.path)

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
    async def get_post(self, id: str) -> Post | None:
        """Retrieve a single post or reply"""

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
            await self.db.execute("INSERT INTO user (id, name) VALUES (?, ?)", [id, name])
            await self.db.commit()
            return User(id=id, name=name)
        except sqlite3.IntegrityError:
            return None

    async def submit_post(self, post: PostSubmitRequest, timestamp: int) -> None:
        assert self.db is not None
        # Older sqlites might not support native uuid()
        id = str(uuid.uuid4())
        await self.db.execute(
            ("INSERT INTO post (id, parent_id, user_id, content, timestamp) VALUES (?, ?, ?, ?, ?)"),
            [id, post.parent_id, post.user_id, post.content, timestamp],
        )
        await self.db.commit()

    async def get_post(self, id: str) -> Post | None:
        assert self.db is not None
        cursor = await self.db.execute(
            SqliteStorage._base_post_query() + "WHERE p.id = ? " + SqliteStorage._post_group_by(),
            [id],
        )
        row = await cursor.fetchone()
        if row is not None:
            return SqliteStorage._post_from_row(row)

    async def get_thread(self, id: str) -> Thread | None:
        pass

    async def get_last_posts(self, count: int) -> list[Post]:
        assert self.db is not None
        cursor = await self.db.execute(
            SqliteStorage._base_post_query()
            + "WHERE p.parent_id is NULL "
            + SqliteStorage._post_group_by()
            + "ORDER BY p.timestamp DESC LIMIT ?",
            [count],
        )
        rows = await cursor.fetchall()
        posts = [SqliteStorage._post_from_row(row) for row in rows]
        return posts

    @staticmethod
    def _base_post_query() -> str:
        return (
            "SELECT p.id, p.parent_id, p.content, p.timestamp, u.id, u.name, count(r.id) "
            "FROM post p "
            "LEFT JOIN post r ON r.parent_id = p.id "
            "JOIN user u ON u.id = p.user_id "
        )

    @staticmethod
    def _post_group_by() -> str:
        return "GROUP BY p.id, p.parent_id, p.content, p.timestamp, u.id, u.name "

    @staticmethod
    def _post_from_row(row) -> Post:
        return Post(
            id=row[0],
            parent_id=row[1],
            content=row[2],
            timestamp=row[3],
            user=User(id=row[4], name=row[5]),
            replies=row[6],
        )

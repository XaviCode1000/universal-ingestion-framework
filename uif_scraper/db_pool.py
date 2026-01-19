import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import aiosqlite


class SQLitePool:
    def __init__(self, db_path: Path, max_size: int = 5, timeout: float = 5.0):
        self.db_path = db_path
        self.max_size = max_size
        self.timeout = timeout
        self._pool: asyncio.Queue[aiosqlite.Connection] = asyncio.Queue()
        self._all_connections: list[aiosqlite.Connection] = []
        self._initialized = False
        self._lock = asyncio.Lock()

    async def _create_connection(self) -> aiosqlite.Connection:
        conn = await aiosqlite.connect(self.db_path, timeout=self.timeout)
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA synchronous=NORMAL")
        await conn.execute("PRAGMA cache_size=-64000")
        await conn.execute(f"PRAGMA busy_timeout={int(self.timeout * 1000)}")
        return conn

    async def initialize(self) -> None:
        async with self._lock:
            if self._initialized:
                return
            for _ in range(self.max_size):
                conn = await self._create_connection()
                self._all_connections.append(conn)
                await self._pool.put(conn)
            self._initialized = True

    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        if not self._initialized:
            await self.initialize()

        conn = await self._pool.get()
        try:
            yield conn
        finally:
            await self._pool.put(conn)

    async def close_all(self) -> None:
        async with self._lock:
            while not self._pool.empty():
                await self._pool.get()

            for conn in self._all_connections:
                await conn.close()

            self._all_connections.clear()
            self._initialized = False

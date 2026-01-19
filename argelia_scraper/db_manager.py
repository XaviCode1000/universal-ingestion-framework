from typing import List, Optional
from argelia_scraper.db_pool import SQLitePool
from argelia_scraper.models import MigrationStatus


class StateManager:
    def __init__(self, pool: SQLitePool):
        self.pool = pool

    async def initialize(self) -> None:
        async with self.pool.acquire() as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS urls (
                    url TEXT PRIMARY KEY,
                    status TEXT NOT NULL DEFAULT 'pending',
                    type TEXT,
                    retries INTEGER DEFAULT 0,
                    last_error TEXT,
                    last_try TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_status_type ON urls(status, type)"
            )
            await db.commit()

    async def add_url(
        self, url: str, status: MigrationStatus, m_type: str = "webpage"
    ) -> None:
        async with self.pool.acquire() as db:
            await db.execute(
                "INSERT OR IGNORE INTO urls (url, status, type) VALUES (?, ?, ?)",
                (url, status.value, m_type),
            )
            await db.commit()

    async def add_urls_batch(
        self, urls: List[tuple[str, MigrationStatus, str]]
    ) -> None:
        if not urls:
            return
        async with self.pool.acquire() as db:
            await db.executemany(
                "INSERT OR IGNORE INTO urls (url, status, type) VALUES (?, ?, ?)",
                [(u, s.value, t) for u, s, t in urls],
            )
            await db.commit()

    async def update_status(
        self, url: str, status: MigrationStatus, error_msg: Optional[str] = None
    ) -> None:
        async with self.pool.acquire() as db:
            if error_msg:
                await db.execute(
                    "UPDATE urls SET status = ?, last_error = ?, last_try = CURRENT_TIMESTAMP WHERE url = ?",
                    (status.value, error_msg[:500], url),
                )
            else:
                await db.execute(
                    "UPDATE urls SET status = ?, last_error = NULL, last_try = CURRENT_TIMESTAMP WHERE url = ?",
                    (status.value, url),
                )
            await db.commit()

    async def increment_retry(self, url: str) -> int:
        async with self.pool.acquire() as db:
            await db.execute(
                "UPDATE urls SET retries = retries + 1, last_try = CURRENT_TIMESTAMP WHERE url = ?",
                (url,),
            )
            await db.commit()
            async with db.execute(
                "SELECT retries FROM urls WHERE url = ?", (url,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_pending_urls(
        self, m_type: str = "webpage", max_retries: int = 3
    ) -> List[str]:
        async with self.pool.acquire() as db:
            query = """
                SELECT url FROM urls 
                WHERE type = ? AND (
                    status = ? 
                    OR (status = ? AND retries < ?)
                )
            """
            async with db.execute(
                query,
                (
                    m_type,
                    MigrationStatus.PENDING.value,
                    MigrationStatus.FAILED.value,
                    max_retries,
                ),
            ) as cursor:
                rows = await cursor.fetchall()
                return [str(row[0]) for row in rows]

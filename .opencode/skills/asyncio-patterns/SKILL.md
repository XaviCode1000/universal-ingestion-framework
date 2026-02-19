---
name: asyncio-patterns
description: Asyncio patterns for UIF - TaskGroups, semaphores, and graceful shutdown
---

## Use this when

- Implementing concurrent web scraping
- Managing async database connections
- Building resilient async pipelines

## MANDATORY: TaskGroups (Python 3.11+)

Use TaskGroups instead of gather() for proper error handling:

```python
import asyncio


async def process_urls(urls: list[str]) -> list[str]:
    """Procesa URLs concurrentemente con TaskGroup."""
    results: list[str] = []

    async with asyncio.TaskGroup() as tg:
        for url in urls:
            tg.create_task(fetch_and_process(url, results))

    return results
```

## Semaphore for Rate Limiting

```python
import asyncio


class ConcurrentFetcher:
    def __init__(self, max_concurrent: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch(self, url: str) -> str:
        async with self.semaphore:
            return await self._do_fetch(url)
```

## aiosqlite with WAL Mode

```python
import aiosqlite


async def init_db(db_path: str) -> aiosqlite.Connection:
    """Inicializa SQLite con modo WAL."""
    db = await aiosqlite.connect(db_path)
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA synchronous=NORMAL")
    return db


async def insert_batch(db: aiosqlite.Connection, items: list[dict]) -> None:
    """Inserta batch de items."""
    async with db.executemany(
        "INSERT INTO pages (url, content) VALUES (?, ?)",
        [(i["url"], i["content"]) for i in items],
    ):
        pass
    await db.commit()
```

## Graceful Shutdown

```python
import asyncio
import signal


class Scraper:
    def __init__(self):
        self._shutdown = False

    async def run(self) -> None:
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._signal_handler)

        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self._worker())
        except* KeyboardInterrupt:
            pass
        finally:
            await self._cleanup()

    def _signal_handler(self) -> None:
        self._shutdown = True

    async def _cleanup(self) -> None:
        """Cierra conexiones y libera recursos."""
        pass
```

## Circuit Breaker Pattern

```python
import asyncio
from dataclasses import dataclass


@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    recovery_timeout: float = 60.0

    def __post_init__(self):
        self.failures = 0
        self.last_failure: float | None = None
        self._lock = asyncio.Lock()

    async def is_open(self) -> bool:
        async with self._lock:
            if self.failures < self.failure_threshold:
                return False
            if self.last_failure is None:
                return False
            elapsed = asyncio.get_event_loop().time() - self.last_failure
            return elapsed < self.recovery_timeout

    async def record_success(self) -> None:
        async with self._lock:
            self.failures = 0

    async def record_failure(self) -> None:
        async with self._lock:
            self.failures += 1
            self.last_failure = asyncio.get_event_loop().time()
```

## Timeout Pattern

```python
async def fetch_with_timeout(url: str, timeout: float = 30.0) -> str:
    """Fetch con timeout configurable."""
    async with asyncio.timeout(timeout):
        return await fetch(url)
```

import pytest
import asyncio
from pathlib import Path
from uif_scraper.db_pool import SQLitePool


@pytest.mark.asyncio
async def test_pool_concurrent_stress(tmp_path):
    db_path = tmp_path / "concurrent.db"
    pool = SQLitePool(db_path, max_size=5)
    await pool.initialize()

    async def worker(worker_id):
        async with pool.acquire() as conn:
            await conn.execute("INSERT INTO test (worker_id) VALUES (?)", (worker_id,))
            await conn.commit()
            await asyncio.sleep(0.01)

    async with pool.acquire() as conn:
        await conn.execute("CREATE TABLE test (worker_id INTEGER)")
        await conn.commit()

    tasks = [asyncio.create_task(worker(i)) for i in range(20)]
    await asyncio.gather(*tasks)

    async with pool.acquire() as conn:
        async with conn.execute("SELECT COUNT(*) FROM test") as cursor:
            row = await cursor.fetchone()
            assert row is not None
            assert row[0] == 20

    await pool.close_all()


@pytest.mark.asyncio
async def test_pool_acquire(tmp_path):
    db_path = tmp_path / "test.db"
    pool = SQLitePool(db_path, max_size=2)
    async with pool.acquire() as conn:
        await conn.execute("CREATE TABLE test (id INTEGER)")
        await conn.commit()

    async with pool.acquire() as conn:
        async with conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='test'"
        ) as cursor:
            row = await cursor.fetchone()
            assert row is not None

    await pool.close_all()

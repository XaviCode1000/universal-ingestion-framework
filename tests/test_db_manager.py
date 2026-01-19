import pytest
import os
from uif_scraper.db_pool import SQLitePool
from uif_scraper.db_manager import StateManager, MigrationStatus


@pytest.mark.asyncio
async def test_state_manager_init(tmp_path):
    db_path = tmp_path / "state.db"
    pool = SQLitePool(db_path)
    state = StateManager(pool)
    await state.initialize()

    async with pool.acquire() as db:
        async with db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='urls'"
        ) as cursor:
            assert await cursor.fetchone() is not None
    await pool.close_all()


@pytest.mark.asyncio
async def test_state_manager_add_update(tmp_path):
    db_path = tmp_path / "state.db"
    pool = SQLitePool(db_path)
    state = StateManager(pool)
    await state.initialize()

    url = "https://test.com"
    await state.add_url(url, MigrationStatus.PENDING)

    pending = await state.get_pending_urls()
    assert url in pending

    await state.update_status(url, MigrationStatus.COMPLETED)
    pending = await state.get_pending_urls()
    assert url not in pending

    new_retry = await state.increment_retry(url)
    assert new_retry == 1

    await pool.close_all()

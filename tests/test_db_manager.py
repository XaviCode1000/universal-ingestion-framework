
import pytest

from uif_scraper.db_manager import MigrationStatus, StateManager
from uif_scraper.db_pool import SQLitePool

# Valid test URLs from webscraper.io (designed for scraper testing)
TEST_URL = "https://webscraper.io/test-sites/e-commerce/static"


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
    # No iniciar batch processor para este test - usar actualizaciones inmediatas
    state = StateManager(pool)
    await state.initialize()

    await state.add_url(TEST_URL, MigrationStatus.PENDING)

    pending = await state.get_pending_urls()
    assert TEST_URL in pending

    # Usar immediate=True para evitar buffering
    await state.update_status(TEST_URL, MigrationStatus.COMPLETED, immediate=True)
    pending = await state.get_pending_urls()
    assert TEST_URL not in pending

    new_retry = await state.increment_retry(TEST_URL)
    assert new_retry == 1

    await pool.close_all()

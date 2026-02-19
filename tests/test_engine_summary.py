from unittest.mock import MagicMock

import pytest

from uif_scraper.config import ScraperConfig
from uif_scraper.db_manager import StateManager
from uif_scraper.db_pool import SQLitePool
from uif_scraper.engine import UIFMigrationEngine
from uif_scraper.navigation import NavigationService
from uif_scraper.reporter import ReporterService

# Valid test URLs from webscraper.io (designed for scraper testing)
TEST_URL = "https://webscraper.io/test-sites/e-commerce/static"


@pytest.mark.asyncio
async def test_engine_generate_summary(tmp_path):
    config = ScraperConfig(data_dir=tmp_path)
    db_path = tmp_path / "summary.db"
    pool = SQLitePool(db_path)
    state = StateManager(pool)
    await state.initialize()

    async with pool.acquire() as db:
        # Insertar con la nueva columna discovered_at (agregada en refactorización)
        await db.execute(
            "INSERT INTO urls (url, status, type, retries, last_error, discovered_at) VALUES ('u1', 'completed', 'webpage', 0, NULL, CURRENT_TIMESTAMP)"
        )
        await db.execute(
            "INSERT INTO urls (url, status, type, retries, last_error, discovered_at) VALUES ('u2', 'failed', 'webpage', 1, 'Network Error', CURRENT_TIMESTAMP)"
        )
        await db.commit()

    nav = NavigationService(TEST_URL)
    rep = ReporterService(MagicMock(), state)

    _ = UIFMigrationEngine(
        config=config,
        state=state,
        text_extractor=MagicMock(),
        metadata_extractor=MagicMock(),
        asset_extractor=MagicMock(),
        navigation_service=nav,
        reporter_service=rep,
    )

    await rep.generate_summary()
    await pool.close_all()

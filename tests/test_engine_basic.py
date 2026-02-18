import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from uif_scraper.config import ScraperConfig
from uif_scraper.db_manager import StateManager
from uif_scraper.db_pool import SQLitePool
from uif_scraper.engine import UIFMigrationEngine
from uif_scraper.extractors.asset_extractor import AssetExtractor
from uif_scraper.extractors.metadata_extractor import MetadataExtractor
from uif_scraper.extractors.text_extractor import TextExtractor
from uif_scraper.navigation import NavigationService
from uif_scraper.reporter import ReporterService

# Valid test URLs from webscraper.io (designed for scraper testing)
TEST_URL = "https://webscraper.io/test-sites/e-commerce/static"


@pytest.mark.asyncio
async def test_engine_simple_run(tmp_path):
    config = ScraperConfig(data_dir=tmp_path, default_workers=1)
    db_path = tmp_path / "test_engine.db"
    pool = SQLitePool(db_path)
    state = StateManager(pool)

    text_extractor = TextExtractor()
    metadata_extractor = MetadataExtractor()
    asset_extractor = AssetExtractor(tmp_path)

    nav = NavigationService(TEST_URL)
    rep = ReporterService(MagicMock(), state)

    engine = UIFMigrationEngine(
        config=config,
        state=state,
        text_extractor=text_extractor,
        metadata_extractor=metadata_extractor,
        asset_extractor=asset_extractor,
        navigation_service=nav,
        reporter_service=rep,
    )

    engine.setup = AsyncMock()
    await engine.url_queue.put(f"{TEST_URL}/page1")
    engine.process_page = AsyncMock()

    session = AsyncMock()
    task = asyncio.create_task(engine.page_worker(session))

    await engine.url_queue.join()
    task.cancel()

    engine.process_page.assert_called_once()
    await pool.close_all()

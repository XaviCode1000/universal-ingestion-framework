import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path
from uif_scraper.engine import UIFMigrationEngine
from uif_scraper.config import ScraperConfig
from uif_scraper.db_manager import StateManager
from uif_scraper.db_pool import SQLitePool
from uif_scraper.extractors.text_extractor import TextExtractor
from uif_scraper.extractors.metadata_extractor import MetadataExtractor
from uif_scraper.extractors.asset_extractor import AssetExtractor


@pytest.mark.asyncio
async def test_engine_simple_run(tmp_path):
    config = ScraperConfig(data_dir=tmp_path, default_workers=1)
    db_path = tmp_path / "test_engine.db"
    pool = SQLitePool(db_path)
    state = StateManager(pool)

    text_extractor = TextExtractor()
    metadata_extractor = MetadataExtractor()
    asset_extractor = AssetExtractor(tmp_path)

    engine = UIFMigrationEngine(
        config=config,
        state=state,
        text_extractor=text_extractor,
        metadata_extractor=metadata_extractor,
        asset_extractor=asset_extractor,
        base_url="https://test.com",
    )

    engine.setup = AsyncMock()
    await engine.url_queue.put("https://test.com/page1")
    engine.process_page = AsyncMock()

    session = AsyncMock()

    task = asyncio.create_task(engine.page_worker(session))

    await engine.url_queue.join()
    task.cancel()

    engine.process_page.assert_called_once()
    await pool.close_all()

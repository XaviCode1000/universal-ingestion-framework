import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from uif_scraper.engine import UIFMigrationEngine
from uif_scraper.config import ScraperConfig
from uif_scraper.db_manager import StateManager, MigrationStatus
from uif_scraper.db_pool import SQLitePool


@pytest.mark.asyncio
async def test_engine_setup_loads_state(tmp_path):
    config = ScraperConfig(data_dir=tmp_path)
    db_path = tmp_path / "test_setup.db"
    pool = SQLitePool(db_path)
    state = StateManager(pool)
    await state.initialize()
    await state.add_url("https://test.com/seen", MigrationStatus.COMPLETED)
    await state.add_url("https://test.com/pending", MigrationStatus.PENDING)

    engine = UIFMigrationEngine(
        config=config,
        state=state,
        text_extractor=MagicMock(),
        metadata_extractor=MagicMock(),
        asset_extractor=MagicMock(),
        base_url="https://test.com",
    )

    await engine.setup()

    assert "https://test.com/seen" in engine.seen_urls
    assert engine.pages_completed == 1
    assert engine.url_queue.qsize() == 1

    await pool.close_all()


@pytest.mark.asyncio
async def test_engine_download_asset(tmp_path):
    config = ScraperConfig(data_dir=tmp_path)
    pool = SQLitePool(tmp_path / "test_asset.db")
    state = StateManager(pool)
    await state.initialize()

    asset_extractor = AsyncMock()
    engine = UIFMigrationEngine(
        config=config,
        state=state,
        text_extractor=MagicMock(),
        metadata_extractor=MagicMock(),
        asset_extractor=asset_extractor,
        base_url="https://test.com",
    )

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.body = b"fake data"

    with patch(
        "scrapling.fetchers.AsyncFetcher.get", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = mock_resp
        await engine.download_asset("https://test.com/img.png")

        asset_extractor.extract.assert_called_once()
        assert engine.assets_completed == 1

    await pool.close_all()

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from uif_scraper.engine import UIFMigrationEngine, MigrationStatus
from uif_scraper.config import ScraperConfig
from uif_scraper.db_pool import SQLitePool
from uif_scraper.db_manager import StateManager


@pytest.mark.asyncio
async def test_engine_retry_logic(tmp_path):
    config = ScraperConfig(data_dir=tmp_path, max_retries=2)
    state = MagicMock()
    state.increment_retry = AsyncMock(side_effect=[1, 2])
    state.update_status = AsyncMock()

    engine = UIFMigrationEngine(
        config=config,
        state=state,
        text_extractor=MagicMock(),
        metadata_extractor=MagicMock(),
        asset_extractor=MagicMock(),
        base_url="https://test.com",
    )

    with patch(
        "scrapling.fetchers.AsyncFetcher.get", side_effect=Exception("Network fail")
    ):
        session = AsyncMock()
        await engine.process_page(session, "https://test.com")

        assert state.increment_retry.call_count == 1
        assert engine.url_queue.qsize() == 1


@pytest.mark.asyncio
async def test_engine_run_orchestration(tmp_path):
    config = ScraperConfig(data_dir=tmp_path, default_workers=2)
    pool = SQLitePool(tmp_path / "orch.db")
    state = StateManager(pool)
    await state.initialize()

    engine = UIFMigrationEngine(
        config=config,
        state=state,
        text_extractor=MagicMock(),
        metadata_extractor=MagicMock(),
        asset_extractor=MagicMock(),
        base_url="https://test.com",
    )

    engine.setup = AsyncMock()
    with patch("uif_scraper.engine.AsyncStealthySession") as mock_session:
        session_instance = AsyncMock()
        mock_session.return_value.__aenter__.return_value = session_instance

        await engine.run()
        engine.setup.assert_called_once()
    await pool.close_all()

from unittest.mock import AsyncMock, MagicMock, patch

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
async def test_engine_retry_logic(tmp_path):
    config = ScraperConfig(data_dir=tmp_path, max_retries=2)
    state = MagicMock()
    state.increment_retry = AsyncMock(side_effect=[1, 2])
    state.update_status = AsyncMock()

    nav = NavigationService(TEST_URL)
    rep = ReporterService(MagicMock(), state)

    engine = UIFMigrationEngine(
        config=config,
        state=state,
        text_extractor=MagicMock(),
        metadata_extractor=MagicMock(),
        asset_extractor=MagicMock(),
        navigation_service=nav,
        reporter_service=rep,
    )

    with patch(
        "scrapling.fetchers.AsyncFetcher.get", side_effect=Exception("Network fail")
    ):
        session = AsyncMock()
        await engine.process_page(session, TEST_URL)
        assert state.increment_retry.call_count == 1
        assert engine.url_queue.qsize() == 1


@pytest.mark.asyncio
async def test_engine_run_orchestration(tmp_path):
    config = ScraperConfig(data_dir=tmp_path, default_workers=2)
    pool = SQLitePool(tmp_path / "orch.db")
    state = StateManager(pool)
    await state.initialize()

    nav = NavigationService(TEST_URL)
    rep = ReporterService(MagicMock(), state)

    engine = UIFMigrationEngine(
        config=config,
        state=state,
        text_extractor=MagicMock(),
        metadata_extractor=MagicMock(),
        asset_extractor=MagicMock(),
        navigation_service=nav,
        reporter_service=rep,
    )

    engine.setup = AsyncMock()
    # Mock workers para evitar deadlock en colas vacías
    engine.page_worker = AsyncMock()
    engine.asset_worker = AsyncMock()

    with patch("uif_scraper.engine.AsyncStealthySession") as mock_session:
        session_instance = AsyncMock()
        mock_session.return_value.__aenter__.return_value = session_instance
        await engine.run()
        engine.setup.assert_called_once()
        # Verificar que se crearon los workers
        assert engine.page_worker.call_count == 2  # default_workers=2
    await pool.close_all()

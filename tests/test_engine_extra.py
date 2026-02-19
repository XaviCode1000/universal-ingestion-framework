from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from uif_scraper.config import ScraperConfig
from uif_scraper.core.engine_core import EngineCore
from uif_scraper.db_manager import MigrationStatus, StateManager
from uif_scraper.db_pool import SQLitePool
from uif_scraper.navigation import NavigationService
from uif_scraper.reporter import ReporterService

# Valid test URLs from webscraper.io (designed for scraper testing)
TEST_URL = "https://webscraper.io/test-sites/e-commerce/static"


@pytest.mark.asyncio
async def test_engine_setup_loads_state(tmp_path):
    config = ScraperConfig(data_dir=tmp_path)
    db_path = tmp_path / "test_setup.db"
    pool = SQLitePool(db_path)
    state = StateManager(pool)
    await state.initialize()
    await state.add_url(f"{TEST_URL}/seen", MigrationStatus.COMPLETED)
    await state.add_url(f"{TEST_URL}/pending", MigrationStatus.PENDING)

    nav = NavigationService(TEST_URL)
    rep = ReporterService(MagicMock(), state)

    core = EngineCore(
        config=config,
        state=state,
        text_extractor=MagicMock(),
        metadata_extractor=MagicMock(),
        asset_extractor=MagicMock(),
        navigation_service=nav,
        reporter_service=rep,
    )

    await core.setup()
    assert f"{TEST_URL}/seen" in core.seen_urls
    assert core.pages_completed == 1
    assert core.url_queue.qsize() == 1
    await pool.close_all()


@pytest.mark.asyncio
async def test_engine_download_asset(tmp_path):
    config = ScraperConfig(data_dir=tmp_path)
    pool = SQLitePool(tmp_path / "test_asset.db")
    state = StateManager(pool)
    await state.initialize()

    asset_extractor = AsyncMock()
    nav = NavigationService(TEST_URL)
    rep = ReporterService(MagicMock(), state)

    core = EngineCore(
        config=config,
        state=state,
        text_extractor=MagicMock(),
        metadata_extractor=MagicMock(),
        asset_extractor=asset_extractor,
        navigation_service=nav,
        reporter_service=rep,
    )

    # Mock aiohttp session and response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.read = AsyncMock(return_value=b"fake asset data")

    mock_session = AsyncMock()
    mock_session.get = MagicMock(return_value=AsyncMock())
    mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
    mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)

    with patch.object(
        core.http_cache, "get_session", new_callable=AsyncMock
    ) as mock_get_session:
        mock_get_session.return_value = mock_session
        await core._download_asset(f"{TEST_URL}/img.png")

        # Verify session.get was called with correct headers for hotlink protection
        mock_session.get.assert_called_once()
        call_args = mock_session.get.call_args
        assert call_args[0][0] == f"{TEST_URL}/img.png"
        assert "headers" in call_args.kwargs
        assert call_args.kwargs["headers"]["Referer"] == TEST_URL
        assert call_args.kwargs["headers"]["Origin"] == TEST_URL

        asset_extractor.extract.assert_called_once_with(
            b"fake asset data", f"{TEST_URL}/img.png"
        )
        assert core.assets_completed == 1

    await pool.close_all()

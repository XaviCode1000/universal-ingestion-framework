from unittest.mock import AsyncMock, MagicMock, patch

import asyncio
import pytest

from uif_scraper.config import ScraperConfig
from uif_scraper.core.engine_core import EngineCore
from uif_scraper.db_manager import StateManager
from uif_scraper.db_pool import SQLitePool
from uif_scraper.models import MigrationStatus, ScrapingScope
from uif_scraper.extractors.asset_extractor import AssetExtractor
from uif_scraper.extractors.metadata_extractor import MetadataExtractor
from uif_scraper.extractors.text_extractor import TextExtractor
from uif_scraper.navigation import NavigationService
from uif_scraper.reporter import ReporterService

# Valid test URLs from webscraper.io (designed for scraper testing)
TEST_URL = "https://webscraper.io/test-sites/e-commerce/static"


@pytest.mark.asyncio
async def test_engine_process_page_full(tmp_path):
    config = ScraperConfig(data_dir=tmp_path, default_workers=1)
    db_path = tmp_path / "test_full.db"
    pool = SQLitePool(db_path)
    state = StateManager(pool)
    await state.initialize()

    text_extractor = TextExtractor()
    metadata_extractor = MetadataExtractor()
    asset_extractor = AssetExtractor(tmp_path)

    # Use BROAD scope to allow all links within the domain
    nav = NavigationService(TEST_URL, scope=ScrapingScope.BROAD)
    rep = ReporterService(MagicMock(), state)

    core = EngineCore(
        config=config,
        state=state,
        text_extractor=text_extractor,
        metadata_extractor=metadata_extractor,
        asset_extractor=asset_extractor,
        navigation_service=nav,
        reporter_service=rep,
    )

    await state.add_url(TEST_URL, MigrationStatus.PENDING)
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.body = '<html><body><h1>Title</h1><p>Content</p><a href="/other">Link</a><img src="/img.png"></body></html>'
    mock_resp.raw_content = None
    # Mock css selector to return link nodes
    mock_resp.css = MagicMock(
        side_effect=lambda selector: (
            [MagicMock(__str__=lambda s: "/other")]
            if "href" in selector
            else [MagicMock(__str__=lambda s: "/img.png")]
        )
    )

    with patch(
        "scrapling.fetchers.AsyncFetcher.get", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = mock_resp
        session = AsyncMock()
        await core._process_page(session, TEST_URL)
        assert "https://webscraper.io/other" in core.seen_urls
        assert "https://webscraper.io/img.png" in core.seen_assets

        # Esperar que el batch processor flushee las actualizaciones de estado
        await asyncio.sleep(1.1)
        await state.stop_batch_processor()  # Forzar flush final

        async with pool.acquire() as db:
            async with db.execute(
                f"SELECT status FROM urls WHERE url='{TEST_URL}'"
            ) as cursor:
                row = await cursor.fetchone()
                assert row is not None
                assert row[0] == "completed"

    await pool.close_all()

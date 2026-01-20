import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path
from uif_scraper.engine import UIFMigrationEngine, MigrationStatus
from uif_scraper.config import ScraperConfig
from uif_scraper.db_manager import StateManager
from uif_scraper.db_pool import SQLitePool
from uif_scraper.extractors.text_extractor import TextExtractor
from uif_scraper.extractors.metadata_extractor import MetadataExtractor
from uif_scraper.extractors.asset_extractor import AssetExtractor
from uif_scraper.navigation import NavigationService
from uif_scraper.reporter import ReporterService


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

    nav = NavigationService("https://test.com")
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

    await state.add_url("https://test.com", MigrationStatus.PENDING)
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.body = '<html><body><h1>Title</h1><p>Content</p><a href="/other">Link</a><img src="/img.png"></body></html>'
    mock_resp.raw_content = None
    mock_resp.css = MagicMock(
        side_effect=lambda selector: ["/other" if "href" in selector else "/img.png"]
    )

    with patch(
        "scrapling.fetchers.AsyncFetcher.get", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = mock_resp
        session = AsyncMock()
        await engine.process_page(session, "https://test.com")
        assert "https://test.com/other" in engine.seen_urls
        assert "https://test.com/img.png" in engine.seen_assets

        async with pool.acquire() as db:
            async with db.execute(
                "SELECT status FROM urls WHERE url='https://test.com'"
            ) as cursor:
                row = await cursor.fetchone()
                assert row is not None
                assert row[0] == "completed"

    await pool.close_all()

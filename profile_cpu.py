"""Script to run profiling on the scraper."""

import asyncio
import cProfile
import pstats
from io import StringIO
from pathlib import Path

# Setup path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from uif_scraper.config import load_config_with_overrides
from uif_scraper.core.engine_core import EngineCore
from uif_scraper.db_manager import StateManager
from uif_scraper.db_pool import SQLitePool
from uif_scraper.extractors.asset_extractor import AssetExtractor
from uif_scraper.extractors.metadata_extractor import MetadataExtractor
from uif_scraper.extractors.text_extractor import TextExtractor
from uif_scraper.models import ScrapingScope
from uif_scraper.navigation import NavigationService
from uif_scraper.reporter import ReporterService
from uif_scraper.utils.url_utils import slugify
from urllib.parse import urlparse


async def run_scraping():
    """Run scraping mission."""
    url = "https://httpbin.org/links/20/0"
    workers = 2

    # Setup config
    config = load_config_with_overrides(None)
    config.default_workers = workers
    config.data_dir = Path.cwd() / "data"

    domain_slug = slugify(urlparse(url).netloc)
    project_data_dir = config.data_dir / domain_slug
    project_data_dir.mkdir(parents=True, exist_ok=True)

    db_path = project_data_dir / "state.db"
    pool = SQLitePool(
        db_path, max_size=config.db_pool_size, timeout=config.db_timeout_seconds
    )
    state = StateManager(
        pool,
        stats_cache_ttl=config.stats_cache_ttl_seconds,
        batch_interval=1.0,
        batch_size=100,
    )

    text_extractor = TextExtractor()
    metadata_extractor = MetadataExtractor(cache_size=1000)
    asset_extractor = AssetExtractor(project_data_dir)

    navigation_service = NavigationService(url, ScrapingScope("smart"))
    from rich.console import Console

    console = Console()
    reporter_service = ReporterService(console, state)

    # Create EngineCore
    core = EngineCore(
        config=config,
        state=state,
        text_extractor=text_extractor,
        metadata_extractor=metadata_extractor,
        asset_extractor=asset_extractor,
        navigation_service=navigation_service,
        reporter_service=reporter_service,
        extract_assets=False,
    )

    # Run engine
    try:
        await core.run()
    finally:
        await state.stop_batch_processor()
        await pool.close_all()


def main():
    """Run with profiling."""
    profiler = cProfile.Profile()
    profiler.enable()

    asyncio.run(run_scraping())

    profiler.disable()

    # Print stats
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
    ps.print_stats(30)
    print("\n=== TOP 30 BY CUMULATIVE TIME ===")
    print(s.getvalue())

    s2 = StringIO()
    ps2 = pstats.Stats(profiler, stream=s2).sort_stats("time")
    ps2.print_stats(20)
    print("\n=== TOP 20 BY TIME ===")
    print(s2.getvalue())

    # Save to file
    ps.dump_stats("profile_output.prof")
    print("\n✅ Profile saved to profile_output.prof")


if __name__ == "__main__":
    main()

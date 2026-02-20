"""Script to run memory profiling on the scraper using tracemalloc."""

import asyncio
import tracemalloc
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
from rich.console import Console


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
    """Run with memory profiling using tracemalloc."""
    # Start memory tracking
    tracemalloc.start()

    print("=== Starting Memory Profiling ===")
    snapshot_start = tracemalloc.take_snapshot()

    # Run the async code
    asyncio.run(run_scraping())

    # Get final snapshot
    snapshot_end = tracemalloc.take_snapshot()

    # Compare snapshots
    print("\n=== TOP 20 MEMORY ALLOCATIONS ===")
    top_stats = snapshot_end.compare_to(snapshot_start, "lineno")

    total_diff = 0
    for stat in top_stats[:20]:
        total_diff += stat.size_diff
        print(f"{stat.size_diff / 1024:.1f} KB {stat}")

    print(f"\nTotal memory growth: {total_diff / 1024:.1f} KB")

    # Show top allocations by size
    print("\n=== TOP 10 FILES BY MEMORY ===")
    top_stats = snapshot_end.statistics("filename")
    for stat in top_stats[:10]:
        print(f"{stat.size / 1024:.1f} KB {stat}")

    # Get current and peak
    current, peak = tracemalloc.get_traced_memory()
    print(f"\n=== MEMORY USAGE ===")
    print(f"Current: {current / 1024 / 1024:.2f} MB")
    print(f"Peak: {peak / 1024 / 1024:.2f} MB")

    tracemalloc.stop()

    # Save snapshot
    snapshot_end.dump("mem_profile.snap")
    print("\n✅ Memory profile saved to mem_profile.snap")


if __name__ == "__main__":
    main()

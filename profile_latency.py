"""Script to measure asyncio event loop latency and event system overhead."""

import asyncio
import time
import statistics
from pathlib import Path

# Setup path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from uif_scraper.config import load_config_with_overrides
from uif_scraper.core.engine_core import EngineCore, UICallback
from uif_scraper.core.types import EngineStats, ActivityEntry
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


class LatencyMonitor:
    """Monitor for detecting event loop blocking."""

    def __init__(self, threshold_ms: float = 50.0):
        self.threshold = threshold_ms / 1000.0  # Convert to seconds
        self._last_time = time.perf_counter()
        self._blocks: list[float] = []
        self._running = False

    async def monitor(self):
        """Monitor event loop latency."""
        self._running = True
        while self._running:
            await asyncio.sleep(0.001)  # Check every 1ms
            now = time.perf_counter()
            elapsed = now - self._last_time
            if elapsed > self.threshold:
                self._blocks.append(elapsed * 1000)  # Store in ms
            self._last_time = now

    def stop(self):
        """Stop monitoring."""
        self._running = False

    def get_stats(self) -> dict:
        """Get latency statistics."""
        if not self._blocks:
            return {"max_ms": 0, "avg_ms": 0, "count": 0}
        return {
            "max_ms": max(self._blocks),
            "avg_ms": statistics.mean(self._blocks),
            "count": len(self._blocks),
            "blocks": self._blocks,
        }


class ProfilingUICallback(UICallback):
    """UICallback that tracks event emission and latency."""

    def __init__(self):
        # Event counters
        self.progress_calls = 0
        self.activity_calls = 0
        self.mode_change_calls = 0
        self.circuit_change_calls = 0
        self.error_calls = 0
        self.state_change_calls = 0

        # Latency tracking
        self._emit_times: list[float] = []
        self._latencies: list[float] = []

        # Throttling tracking
        self.events_emitted = 0
        self.events_throttled = 0
        self._last_progress_time: float = 0.0
        self._last_activity_time: float = 0.0
        self.PROGRESS_THROTTLE_INTERVAL = 0.1  # 100ms
        self.ACTIVITY_THROTTLE_INTERVAL = 0.1  # 100ms

    def on_progress(self, stats: EngineStats) -> None:
        """Track progress events with throttling."""
        now = time.perf_counter()
        self.progress_calls += 1

        # Simulate throttling
        if now - self._last_progress_time >= self.PROGRESS_THROTTLE_INTERVAL:
            self._last_progress_time = now
            self.events_emitted += 1
            self._emit_times.append(now)
        else:
            self.events_throttled += 1

    def on_activity(self, entry: ActivityEntry) -> None:
        """Track activity events with throttling."""
        now = time.perf_counter()
        self.activity_calls += 1

        if now - self._last_activity_time >= self.ACTIVITY_THROTTLE_INTERVAL:
            self._last_activity_time = now
            self.events_emitted += 1
        else:
            self.events_throttled += 1

    def on_mode_change(self, browser_mode: bool) -> None:
        self.mode_change_calls += 1
        self.events_emitted += 1

    def on_circuit_change(self, state: str) -> None:
        self.circuit_change_calls += 1
        self.events_emitted += 1

    def on_error(self, url: str, error_type: str, message: str) -> None:
        self.error_calls += 1
        self.events_emitted += 1  # Errors are not throttled

    def on_state_change(
        self, state: str, mode: str, previous_state: str | None, reason: str | None
    ) -> None:
        self.state_change_calls += 1
        self.events_emitted += 1

    def get_stats(self) -> dict:
        """Get event statistics."""
        total_calls = (
            self.progress_calls
            + self.activity_calls
            + self.mode_change_calls
            + self.circuit_change_calls
            + self.error_calls
            + self.state_change_calls
        )

        throttle_percent = (
            (
                self.events_throttled
                / (self.events_emitted + self.events_throttled)
                * 100
            )
            if (self.events_emitted + self.events_throttled) > 0
            else 0
        )

        return {
            "total_calls": total_calls,
            "progress_calls": self.progress_calls,
            "activity_calls": self.activity_calls,
            "mode_change_calls": self.mode_change_calls,
            "circuit_change_calls": self.circuit_change_calls,
            "error_calls": self.error_calls,
            "state_change_calls": self.state_change_calls,
            "events_emitted": self.events_emitted,
            "events_throttled": self.events_throttled,
            "throttle_percent": throttle_percent,
        }


async def run_scraping_with_monitoring():
    """Run scraping mission with latency monitoring."""
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

    # Create profiling callback
    profiling_callback = ProfilingUICallback()

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

    # Use profiling callback instead of UI callback
    core.ui_callback = profiling_callback

    # Start latency monitor
    latency_monitor = LatencyMonitor(threshold_ms=10.0)
    monitor_task = asyncio.create_task(latency_monitor.monitor())

    # Run engine
    try:
        await core.run()
    finally:
        # Stop monitor
        latency_monitor.stop()
        await monitor_task

        await state.stop_batch_processor()
        await pool.close_all()

    # Print results
    print("\n" + "=" * 60)
    print("EVENT LOOP LATENCY REPORT")
    print("=" * 60)

    latency_stats = latency_monitor.get_stats()
    print(f"\nBlocks detected: {latency_stats['count']}")
    print(f"Max latency: {latency_stats['max_ms']:.2f} ms")
    print(f"Avg latency: {latency_stats['avg_ms']:.2f} ms")

    blocks = latency_stats.get("blocks", [])
    if blocks:
        # Show top 10 longest blocks
        sorted_blocks = sorted(blocks, reverse=True)[:10]
        print(f"\nTop 10 longest blocks (ms):")
        for i, block in enumerate(sorted_blocks, 1):
            print(f"  {i}. {block:.2f} ms")

    print("\n" + "=" * 60)
    print("EVENT SYSTEM REPORT")
    print("=" * 60)

    event_stats = profiling_callback.get_stats()
    print(f"\nTotal event calls: {event_stats['total_calls']}")
    print(f"  - Progress: {event_stats['progress_calls']}")
    print(f"  - Activity: {event_stats['activity_calls']}")
    print(f"  - Mode changes: {event_stats['mode_change_calls']}")
    print(f"  - Circuit changes: {event_stats['circuit_change_calls']}")
    print(f"  - Errors: {event_stats['error_calls']}")
    print(f"  - State changes: {event_stats['state_change_calls']}")

    print(f"\nEvents emitted to UI: {event_stats['events_emitted']}")
    print(f"Events throttled: {event_stats['events_throttled']}")
    print(f"Throttle rate: {event_stats['throttle_percent']:.1f}%")

    # Calculate throughput
    if latency_stats["count"] > 0:
        duration = latency_stats.get("duration", 3.5)  # Approximate
        print(f"\nThroughput: {event_stats['total_calls'] / duration:.1f} events/sec")


async def main():
    """Run with latency monitoring."""
    print("=== Starting Event Loop Latency Monitoring ===")
    await run_scraping_with_monitoring()


if __name__ == "__main__":
    asyncio.run(main())

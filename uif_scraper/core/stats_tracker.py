"""Stats tracking logic for UIF Engine.

Extracts statistical tracking from the main engine orchestrator.
"""

from __future__ import annotations

from uif_scraper.core.types import EngineStats


class StatsTracker:
    """Encapsulates engine statistics and progress tracking."""

    def __init__(self) -> None:
        self.pages_completed: int = 0
        self.assets_completed: int = 0
        self.pages_failed: int = 0
        self.assets_failed: int = 0
        self.error_count: int = 0

        self.pages_total_count: int = 0
        self.assets_total_count: int = 0

        self.seen_urls_count: int = 0
        self.seen_assets_count: int = 0

    def get_stats(self, queue_pending: int = 0) -> EngineStats:
        """Returns current engine statistics snapshot."""
        return EngineStats(
            pages_completed=self.pages_completed,
            pages_total=self.pages_total_count,
            assets_completed=self.assets_completed,
            assets_total=self.assets_total_count,
            pages_failed=self.pages_failed,
            assets_failed=self.assets_failed,
            seen_urls=self.seen_urls_count,
            seen_assets=self.seen_assets_count,
            error_count=self.error_count,
            queue_pending=queue_pending,
        )

    def record_page_success(self) -> None:
        self.pages_completed += 1

    def record_asset_success(self) -> None:
        self.assets_completed += 1

    def record_page_failure(self) -> None:
        self.pages_failed += 1
        self.error_count += 1

    def record_asset_failure(self) -> None:
        self.assets_failed += 1
        self.error_count += 1

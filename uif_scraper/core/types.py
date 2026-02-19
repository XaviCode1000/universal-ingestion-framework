"""Type definitions for UIF Migration Engine.

Pydantic models with frozen=True for immutability.
Reference: AGENTS.md - model_config = {"frozen": True} OBLIGATORIO
"""

from typing import Any

from pydantic import BaseModel, Field


class EngineStats(BaseModel):
    """Immutable snapshot of engine statistics.

    Used for UI updates and progress tracking.
    """

    model_config = {"frozen": True}

    pages_completed: int = 0
    pages_total: int = 0
    assets_completed: int = 0
    assets_total: int = 0
    seen_urls: int = 0
    seen_assets: int = 0
    error_count: int = 0
    queue_pending: int = 0

    @property
    def pages_per_second(self, elapsed_seconds: float = 1.0) -> float:
        """Calculate pages processed per second."""
        if elapsed_seconds <= 0:
            return 0.0
        return self.pages_completed / elapsed_seconds


class PageResult(BaseModel):
    """Result of processing a single page.

    Contains extracted data and discovered links.
    """

    model_config = {"frozen": True}

    url: str
    title: str
    content_md_path: str
    assets: list[str] = Field(default_factory=list)
    new_pages: list[str] = Field(default_factory=list)
    new_assets: list[str] = Field(default_factory=list)
    engine: str = "unknown"  # Which text extractor was used


class ActivityEntry(BaseModel):
    """Single activity log entry for UI display."""

    model_config = {"frozen": True}

    title: str
    engine: str
    timestamp: float  # Event loop time


class DashboardState(BaseModel):
    """Complete state snapshot for dashboard rendering.

    This is what gets sent to the UI on each update.
    """

    model_config = {"frozen": True}

    # Mission info
    base_url: str = ""
    scope: str = "smart"
    workers: int = 5
    mode: str = "stealth"  # "stealth" or "browser"

    # Progress
    stats: EngineStats = Field(default_factory=EngineStats)

    # Circuit breaker
    circuit_state: str = "closed"  # "closed", "open", "half-open"

    # Recent activity (last N entries)
    recent_activity: list[ActivityEntry] = Field(default_factory=list)

    # Timing
    elapsed_seconds: float = 0.0


class WorkerEvent(BaseModel):
    """Event emitted by workers for dashboard notification.

    Using events instead of direct UI coupling for clean separation.
    """

    model_config = {"frozen": True}

    event_type: str  # "page_completed", "asset_completed", "error", "mode_change"
    data: dict[str, Any] = Field(default_factory=dict)

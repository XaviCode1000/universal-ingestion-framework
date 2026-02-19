"""Textual UI adapter for EngineCore.

Implements UICallback to bridge EngineCore updates to Textual widgets.
"""

from typing import TYPE_CHECKING

from uif_scraper.core.engine_core import UICallback
from uif_scraper.core.types import ActivityEntry, EngineStats

if TYPE_CHECKING:
    from uif_scraper.tui.app import UIFDashboardApp


class TextualUICallback(UICallback):
    """Adapter that forwards EngineCore updates to Textual TUI.

    Uses message passing to update widgets from the background scraping task.
    """

    def __init__(self, app: "UIFDashboardApp") -> None:
        """Initialize with Textual app reference."""
        self._app = app
        self._last_circuit_state = "closed"

    def on_progress(self, stats: EngineStats) -> None:
        """Update progress bars and counts."""
        self._app.update_progress(
            pages_completed=stats.pages_completed,
            pages_total=stats.pages_total,
            assets_completed=stats.assets_completed,
            assets_total=stats.assets_total,
            seen_urls=stats.seen_urls,
            seen_assets=stats.seen_assets,
        )

    def on_activity(self, entry: ActivityEntry) -> None:
        """Add new activity to the list."""
        self._app.add_activity(entry.title, entry.engine)

    def on_mode_change(self, browser_mode: bool) -> None:
        """Update fetch mode indicator."""
        # Mode change is handled via status update in Textual
        self._update_status()

    def on_circuit_change(self, state: str) -> None:
        """Update circuit breaker indicator."""
        if state != self._last_circuit_state:
            self._last_circuit_state = state
            self._update_status()

    def _update_status(self) -> None:
        """Send full status update to TUI."""
        # The TUI app has a combined update_status method
        # We need to get current state from somewhere...
        # This is a design limitation - the callback doesn't have full state
        # For now, we rely on periodic polling in the engine
        pass

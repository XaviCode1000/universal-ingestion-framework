"""UIF Dashboard App - Main Textual Application.

This app controls the event loop and runs the scraping engine
as a background worker using Textual's worker system.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Callable, Coroutine

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.message import Message
from textual.widgets import Footer, Header
from textual.worker import Worker, WorkerState

from uif_scraper.tui.widgets.activity import ActivityPanel
from uif_scraper.tui.widgets.header import MissionHeader
from uif_scraper.tui.widgets.stats import StatsPanel
from uif_scraper.tui.widgets.status import SystemStatus

if TYPE_CHECKING:
    from textual.timer import Timer


class EngineStarted(Message):
    """Message sent when scraping engine starts."""

    def __init__(self, url: str, scope: str, workers: int) -> None:
        super().__init__()
        self.url = url
        self.scope = scope
        self.workers = workers


class EngineProgress(Message):
    """Message sent with progress updates."""

    def __init__(
        self,
        pages_completed: int,
        pages_total: int,
        assets_completed: int,
        assets_total: int,
        seen_urls: int,
        seen_assets: int,
    ) -> None:
        super().__init__()
        self.pages_completed = pages_completed
        self.pages_total = pages_total
        self.assets_completed = assets_completed
        self.assets_total = assets_total
        self.seen_urls = seen_urls
        self.seen_assets = seen_assets


class EngineActivity(Message):
    """Message sent when a new activity occurs."""

    def __init__(self, title: str, engine: str) -> None:
        super().__init__()
        self.title = title
        self.engine = engine


class EngineStatus(Message):
    """Message sent with system status updates."""

    def __init__(
        self,
        circuit_state: str,
        queue_pending: int,
        error_count: int,
        browser_mode: bool,
    ) -> None:
        super().__init__()
        self.circuit_state = circuit_state
        self.queue_pending = queue_pending
        self.error_count = error_count
        self.browser_mode = browser_mode


class UIFDashboardApp(App[None]):
    """Main TUI Dashboard for UIF Scraper.

    This app runs the scraping engine as a background worker and
    updates the UI through messages. Uses Textual's worker system
    for proper lifecycle management.
    """

    CSS_PATH = Path(__file__).parent / "styles" / "mocha.tcss"

    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("p", "toggle_pause", "Pause"),
        ("h", "show_help", "Help"),
    ]

    # Reactive state
    is_paused: bool = False

    def __init__(
        self,
        mission_url: str = "",
        scope: str = "smart",
        worker_count: int = 5,
        engine_factory: Callable[[], Coroutine[None, None, None]] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._mission_url = mission_url
        self._scope = scope
        self._worker_count = worker_count
        self._engine_factory = engine_factory
        self._update_timer: Timer | None = None

    def compose(self) -> ComposeResult:
        """Compose the main layout."""
        yield Header(show_clock=True)

        with Container(id="main-container"):
            # Mission Header
            yield MissionHeader(id="mission-header")

            # Main content area
            with Horizontal(id="content-area"):
                # Left: Stats
                yield StatsPanel(id="stats-panel")

                # Right: Activity
                yield ActivityPanel(id="activity-panel")

            # Bottom: System Status
            yield SystemStatus(id="system-status")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize on mount."""
        # Set up periodic update timer for elapsed time
        self._update_timer = self.set_interval(1.0, self._tick)

        # Initialize header with mission info
        header = self.query_one("#mission-header", MissionHeader)
        header.mission_url = self._mission_url
        header.mission_scope = self._scope
        header.worker_count = self._worker_count

        # Start engine as background worker if factory provided
        if self._engine_factory:
            self._run_engine_worker()
            self.post_message(
                EngineStarted(self._mission_url, self._scope, self._worker_count)
            )

    @work(exclusive=True, name="engine_worker")
    async def _run_engine_worker(self) -> None:
        """Run the scraping engine as a Textual worker.

        This method is decorated with @work to integrate with Textual's
        worker lifecycle management. When the engine completes, the
        on_worker_state_changed handler will exit the app.
        """
        if self._engine_factory:
            await self._engine_factory()

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Handle worker state changes.

        This is called when the engine worker changes state.
        When it reaches SUCCESS or ERROR, we exit the app.
        """
        from textual.worker import WorkerState

        # Only handle our engine worker
        if event.worker.name != "engine_worker":
            return

        if event.state == WorkerState.SUCCESS:
            self.notify(
                "Scraping completed successfully!", title="Done", severity="information"
            )
            self.call_later(self.exit)
        elif event.state == WorkerState.ERROR:
            self.notify(
                "Scraping failed with an error.", title="Error", severity="error"
            )
            self.call_later(self.exit)
        elif event.state == WorkerState.CANCELLED:
            # User cancelled - exit silently
            self.call_later(self.exit)

    def _tick(self) -> None:
        """Periodic update callback."""
        if not self.is_paused:
            stats = self.query_one("#stats-panel", StatsPanel)
            stats.tick()

    def action_toggle_pause(self) -> None:
        """Toggle pause state."""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.notify("Paused", title="Status", severity="warning")
        else:
            self.notify("Resumed", title="Status", severity="information")

    def action_show_help(self) -> None:
        """Show help screen."""
        self.notify(
            "Shortcuts: Ctrl+C=Quit, P=Pause",
            title="Help",
            severity="information",
        )

    # Message handlers

    def on_engine_started(self, event: EngineStarted) -> None:
        """Handle engine started message."""
        header = self.query_one("#mission-header", MissionHeader)
        header.mission_url = event.url
        header.mission_scope = event.scope
        header.worker_count = event.workers

    def on_engine_progress(self, event: EngineProgress) -> None:
        """Handle progress update message."""
        stats = self.query_one("#stats-panel", StatsPanel)
        stats.pages_completed = event.pages_completed
        stats.pages_total = event.pages_total
        stats.assets_completed = event.assets_completed
        stats.assets_total = event.assets_total
        stats.seen_urls = event.seen_urls
        stats.seen_assets = event.seen_assets

    def on_engine_activity(self, event: EngineActivity) -> None:
        """Handle activity message."""
        activity = self.query_one("#activity-panel", ActivityPanel)
        activity.add_activity(event.title, event.engine)

    def on_engine_status(self, event: EngineStatus) -> None:
        """Handle status update message."""
        status = self.query_one("#system-status", SystemStatus)
        status.circuit_state = event.circuit_state
        status.queue_pending = event.queue_pending
        status.error_count = event.error_count
        status.browser_mode = event.browser_mode

        # Also update header mode
        header = self.query_one("#mission-header", MissionHeader)
        header.engine_mode = "browser" if event.browser_mode else "stealth"

    # Public API for external updates (via messages)

    def update_progress(
        self,
        pages_completed: int,
        pages_total: int,
        assets_completed: int = 0,
        assets_total: int = 0,
        seen_urls: int = 0,
        seen_assets: int = 0,
    ) -> None:
        """Post a progress update message."""
        self.post_message(
            EngineProgress(
                pages_completed,
                pages_total,
                assets_completed,
                assets_total,
                seen_urls,
                seen_assets,
            )
        )

    def add_activity(self, title: str, engine: str = "unknown") -> None:
        """Post an activity message."""
        self.post_message(EngineActivity(title, engine))

    def update_status(
        self,
        circuit_state: str,
        queue_pending: int,
        error_count: int,
        browser_mode: bool,
    ) -> None:
        """Post a status update message."""
        self.post_message(
            EngineStatus(circuit_state, queue_pending, error_count, browser_mode)
        )

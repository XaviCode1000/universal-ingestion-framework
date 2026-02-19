"""Stats Panel Widget - Displays progress and metrics."""

from time import time

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import ProgressBar, Static


class StatsPanel(Vertical):
    """Panel displaying scraping progress and performance metrics."""

    DEFAULT_CSS = """
    StatsPanel {
        width: 1fr;
        height: auto;
        background: #313244;
        border: round #45475a;
        padding: 1;
        margin: 1;
    }

    StatsPanel .panel-title {
        color: #cba6f7;
        text-style: bold;
        margin-bottom: 1;
    }

    StatsPanel .progress-section {
        margin-bottom: 1;
        height: auto;
    }

    StatsPanel .progress-label {
        color: #bac2de;
        margin-bottom: 0;
    }

    StatsPanel .progress-stats {
        color: #cdd6f4;
        margin-top: 0;
        height: 1;
    }

    StatsPanel .metrics-grid {
        layout: grid;
        grid-size: 2;
        grid-columns: 1fr 1fr;
        margin-top: 1;
    }

    StatsPanel .metric-item {
        height: 2;
        margin: 0 1;
    }

    StatsPanel .metric-label {
        color: #a6adc8;
    }

    StatsPanel .metric-value {
        color: #b4befe;
        text-style: bold;
    }

    StatsPanel ProgressBar {
        margin-top: 0;
    }
    """

    # Reactive attributes
    pages_completed: reactive[int] = reactive(0)
    pages_total: reactive[int] = reactive(0)
    assets_completed: reactive[int] = reactive(0)
    assets_total: reactive[int] = reactive(0)
    start_time: reactive[float] = reactive(0.0)
    seen_urls: reactive[int] = reactive(0)
    seen_assets: reactive[int] = reactive(0)

    def __init__(
        self,
        pages_completed: int = 0,
        pages_total: int = 0,
        assets_completed: int = 0,
        assets_total: int = 0,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._pages_completed_init = pages_completed
        self._pages_total_init = pages_total
        self._assets_completed_init = assets_completed
        self._assets_total_init = assets_total

    def compose(self) -> ComposeResult:
        """Compose the stats panel."""
        yield Static("📊 PROGRESS", classes="panel-title")

        # Pages progress
        with Vertical(classes="progress-section"):
            yield Static("📄 Páginas", classes="progress-label")
            yield ProgressBar(total=self._pages_total_init, id="pages-progress")
            yield Static("", id="pages-stats", classes="progress-stats")

        # Assets progress
        with Vertical(classes="progress-section"):
            yield Static("🖼️  Assets", classes="progress-label")
            yield ProgressBar(total=self._assets_total_init, id="assets-progress")
            yield Static("", id="assets-stats", classes="progress-stats")

        # Metrics grid
        with Vertical(classes="metrics-grid"):
            with Vertical(classes="metric-item"):
                yield Static("⚡ Velocidad", classes="metric-label")
                yield Static("0.0 pages/s", id="speed-value", classes="metric-value")
            with Vertical(classes="metric-item"):
                yield Static("⏱️  Tiempo", classes="metric-label")
                yield Static("00:00:00", id="elapsed-value", classes="metric-value")
            with Vertical(classes="metric-item"):
                yield Static("🔗 URLs Vistas", classes="metric-label")
                yield Static("0", id="seen-urls-value", classes="metric-value")
            with Vertical(classes="metric-item"):
                yield Static("📦 Assets Vistos", classes="metric-label")
                yield Static("0", id="seen-assets-value", classes="metric-value")

    def _format_time(self, seconds: float) -> str:
        """Format seconds to HH:MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def _update_displays(self) -> None:
        """Update all display widgets."""
        # Update progress bars
        pages_progress = self.query_one("#pages-progress", ProgressBar)
        pages_progress.update(total=self.pages_total, progress=self.pages_completed)

        assets_progress = self.query_one("#assets-progress", ProgressBar)
        assets_progress.update(total=self.assets_total, progress=self.assets_completed)

        # Update stats text
        pages_pct = (
            (self.pages_completed / self.pages_total * 100)
            if self.pages_total > 0
            else 0
        )
        self.query_one("#pages-stats", Static).update(
            f"{self.pages_completed}/{self.pages_total} ({pages_pct:.1f}%)"
        )

        assets_pct = (
            (self.assets_completed / self.assets_total * 100)
            if self.assets_total > 0
            else 0
        )
        self.query_one("#assets-stats", Static).update(
            f"{self.assets_completed}/{self.assets_total} ({assets_pct:.1f}%)"
        )

        # Update metrics
        elapsed = time() - self.start_time if self.start_time > 0 else 0
        speed = self.pages_completed / elapsed if elapsed > 0 else 0

        self.query_one("#speed-value", Static).update(f"{speed:.2f} pages/s")
        self.query_one("#elapsed-value", Static).update(self._format_time(elapsed))
        self.query_one("#seen-urls-value", Static).update(str(self.seen_urls))
        self.query_one("#seen-assets-value", Static).update(str(self.seen_assets))

    def watch_pages_completed(self, old: int, new: int) -> None:  # noqa: ARG002
        """React to pages_completed changes."""
        self._update_displays()

    def watch_pages_total(self, old: int, new: int) -> None:  # noqa: ARG002
        """React to pages_total changes."""
        self._update_displays()

    def watch_assets_completed(self, old: int, new: int) -> None:  # noqa: ARG002
        """React to assets_completed changes."""
        self._update_displays()

    def watch_assets_total(self, old: int, new: int) -> None:  # noqa: ARG002
        """React to assets_total changes."""
        self._update_displays()

    def watch_seen_urls(self, old: int, new: int) -> None:  # noqa: ARG002
        """React to seen_urls changes."""
        self._update_displays()

    def watch_seen_assets(self, old: int, new: int) -> None:  # noqa: ARG002
        """React to seen_assets changes."""
        self._update_displays()

    def on_mount(self) -> None:
        """Initialize on mount."""
        if self.start_time == 0:
            self.start_time = time()
        self._update_displays()

    def tick(self) -> None:
        """Force update (called periodically for elapsed time)."""
        self._update_displays()

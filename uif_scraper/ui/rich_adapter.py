"""Rich UI adapter for EngineCore.

Implements UICallback to render dashboard using Rich library.
"""

import asyncio
from typing import Any

from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from uif_scraper.core.engine_core import EngineCore, UICallback
from uif_scraper.core.types import ActivityEntry


class RichDashboard:
    """Rich-based dashboard that renders EngineCore state.

    This class handles all Rich UI rendering, separating it from
    the scraping logic in EngineCore.

    Usage:
        dashboard = RichDashboard(core)
        with dashboard.live():
            await core.run()
    """

    def __init__(self, core: EngineCore) -> None:
        """Initialize dashboard with engine core reference."""
        self._core = core
        self._layout: Layout | None = None
        self._progress: Progress | None = None
        self._page_task: TaskID | None = None
        self._asset_task: TaskID | None = None
        self._start_time: float = 0
        self._live: Live | None = None

    def _create_layout(self) -> Layout:
        """Create the dashboard layout structure."""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
        )
        layout["body"].split_row(
            Layout(name="stats", ratio=1),
            Layout(name="activity", ratio=2),
        )
        return layout

    def _create_progress(self) -> Progress:
        """Create progress bars for pages and assets."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeElapsedColumn(),
            expand=True,
        )

    def _render_header(self) -> Panel:
        """Render header panel with mission info."""
        mode = "BROWSER" if self._core.use_browser_mode else "STEALTH"
        return Panel(
            f"🛸 [bold blue]MISIÓN:[/][white] {self._core.navigation.base_url} [/] | "
            f"[bold yellow]SCOPE:[/][white] {self._core.navigation.scope.value.upper()} [/] | "
            f"[bold cyan]WORKERS:[/][white] {self._core.config.default_workers} [/] | "
            f"[bold green]MODE:[/][white] {mode}",
            border_style="blue",
        )

    def _render_stats(self) -> Panel:
        """Render stats panel with progress and metrics."""
        # Progress bar
        if self._progress and self._page_task is not None:
            self._progress.update(
                self._page_task,
                completed=self._core.pages_completed,
                total=len(self._core.seen_urls) or 1,
            )
        if self._progress and self._asset_task is not None:
            self._progress.update(
                self._asset_task,
                completed=self._core.assets_completed,
                total=len(self._core.seen_assets) or 1,
            )

        # Metrics table
        elapsed = asyncio.get_event_loop().time() - self._start_time
        pages_per_sec = self._core.pages_completed / elapsed if elapsed > 0 else 0

        metrics = Table(box=None, expand=True)
        metrics.add_column("Métrica", style="dim")
        metrics.add_column("Valor", justify="right")
        metrics.add_row("Páginas/seg", f"{pages_per_sec:.2f}")
        metrics.add_row("Visto (URLs)", f"{len(self._core.seen_urls)}")
        metrics.add_row("Visto (Assets)", f"{len(self._core.seen_assets)}")

        # Combine progress and metrics in a simple table
        from rich.console import Group
        from rich.console import RenderableType

        content: RenderableType
        if self._progress:
            content = Group(self._progress, metrics)
        else:
            content = metrics

        return Panel(content, title="[bold]ESTADO ACTUAL[/]", border_style="cyan")

    def _render_activity(self) -> Panel:
        """Render activity panel with recent ingestas."""
        table = Table(box=None, expand=True)
        table.add_column("Título", ratio=3, style="bold white")
        table.add_column("Motor", ratio=1, justify="center")

        for entry in self._core.activity_log[-6:]:
            color = (
                "green"
                if entry["engine"] in ["trafilatura", "html-to-markdown"]
                else "yellow"
            )
            title = entry["title"]
            if len(title) > 45:
                title = title[:45] + ".."
            table.add_row(title, f"[{color}]{entry['engine']}[/]")

        return Panel(
            table,
            title="[bold green]ÚLTIMAS INGESTAS[/]",
            border_style="green",
        )

    def update(self) -> None:
        """Update the dashboard display."""
        if not self._layout:
            return

        self._layout["header"].update(self._render_header())
        self._layout["stats"].update(self._render_stats())
        self._layout["activity"].update(self._render_activity())

    def setup(self) -> None:
        """Initialize dashboard components."""
        self._start_time = asyncio.get_event_loop().time()
        self._layout = self._create_layout()
        self._progress = self._create_progress()

        # Add progress tasks
        self._page_task = self._progress.add_task(
            "[cyan]Páginas",
            total=len(self._core.seen_urls) or 1,
            completed=self._core.pages_completed,
        )
        self._asset_task = self._progress.add_task(
            "[magenta]Assets",
            total=len(self._core.seen_assets) or 1,
            completed=self._core.assets_completed,
        )

    def live(self) -> Live:
        """Get Live context manager for dashboard."""
        self._live = Live(
            self._layout,
            refresh_per_second=4,
            screen=False,
        )
        return self._live


class RichUICallback(UICallback):
    """Callback adapter that updates RichDashboard.

    Implements UICallback interface to receive updates from EngineCore.
    """

    def __init__(self, dashboard: RichDashboard) -> None:
        self._dashboard = dashboard

    def on_progress(self, stats: Any) -> None:
        """Update progress display."""
        self._dashboard.update()

    def on_activity(self, entry: ActivityEntry) -> None:
        """Add activity entry (dashboard pulls from core.activity_log)."""
        self._dashboard.update()

    def on_mode_change(self, browser_mode: bool) -> None:
        """Update mode indicator."""
        self._dashboard.update()

    def on_circuit_change(self, state: str) -> None:
        """Update circuit breaker indicator."""
        self._dashboard.update()

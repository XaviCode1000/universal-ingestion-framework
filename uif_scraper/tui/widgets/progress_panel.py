"""
LiveProgressPanel Widget - Panel de progreso con métricas y sparkline.

Este es el componente principal del dashboard. Muestra:
- Barras de progreso para páginas y assets
- Métricas de velocidad (actual, promedio, máxima)
- ETA con rango (optimista/pesimista)
- Sparkline de velocidad últimos 60s
"""

from collections import deque
from typing import TYPE_CHECKING, Any

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import ProgressBar, Static

from uif_scraper.tui.widgets.sparkline import Sparkline

if TYPE_CHECKING:
    from uif_scraper.tui.messages import ProgressUpdate, SpeedUpdate


class LiveProgressPanel(Vertical):
    """Panel de progreso con métricas y sparkline.

    Recibe actualizaciones vía reactive props y las muestra
    de forma eficiente con caching de referencias.
    """

    DEFAULT_CSS = """
    LiveProgressPanel {
        width: 1fr;
        height: 1fr;
        min-width: 30;
        min-height: 14;
        background: $surface0;
        border: round $surface1;
        padding: 1;
    }

    LiveProgressPanel .panel-title {
        color: $mauve;
        text-style: bold;
        margin-bottom: 1;
    }

    LiveProgressPanel .progress-section {
        margin-bottom: 1;
        height: auto;
    }

    LiveProgressPanel .progress-label {
        color: $subtext1;
        margin-bottom: 0;
    }

    LiveProgressPanel .progress-stats {
        color: $text;
        margin-top: 0;
        height: 1;
    }

    LiveProgressPanel .metrics-box {
        background: $surface1;
        padding: 1;
        margin-top: 1;
    }

    LiveProgressPanel .metric-row {
        height: 1;
    }

    LiveProgressPanel .metric-label {
        color: $subtext0;
    }

    LiveProgressPanel .metric-value {
        color: $lavender;
        text-style: bold;
    }

    LiveProgressPanel .eta-range {
        color: $yellow;
    }

    LiveProgressPanel .sparkline-container {
        margin-top: 1;
        height: 3;
    }

    LiveProgressPanel ProgressBar {
        margin-top: 0;
    }
    """

    # ═══════════════════════════════════════════════════════════════════════════
    # REACTIVE PROPS
    # ═══════════════════════════════════════════════════════════════════════════

    # Progreso
    pages_completed: reactive[int] = reactive(0, init=False)
    pages_total: reactive[int] = reactive(0, init=False)
    assets_completed: reactive[int] = reactive(0, init=False)
    assets_total: reactive[int] = reactive(0, init=False)
    urls_seen: reactive[int] = reactive(0, init=False)
    assets_seen: reactive[int] = reactive(0, init=False)

    # Velocidad
    speed_current: reactive[float] = reactive(0.0, init=False)
    speed_average: reactive[float] = reactive(0.0, init=False)
    speed_max: reactive[float] = reactive(0.0, init=False)

    # ETA con rango
    eta_seconds_best: reactive[int] = reactive(0, init=False)
    eta_seconds_worst: reactive[int] = reactive(0, init=False)

    # Historial para sparkline
    speed_history: reactive[list[float]] = reactive(list, init=False)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._update_pending: bool = False
        self._speed_buffer: deque[float] = deque(maxlen=60)

    def compose(self) -> ComposeResult:
        """Compone el layout del panel."""
        yield Static("📊 PROGRESS", classes="panel-title")

        # Sección de páginas
        with Vertical(classes="progress-section"):
            yield Static("📄 Páginas", classes="progress-label")
            yield ProgressBar(total=100, id="pages-progress")
            yield Static("", id="pages-stats", classes="progress-stats")

        # Sección de assets
        with Vertical(classes="progress-section"):
            yield Static("🖼️ Assets", classes="progress-label")
            yield ProgressBar(total=100, id="assets-progress")
            yield Static("", id="assets-stats", classes="progress-stats")

        # Caja de métricas
        with Vertical(classes="metrics-box"):
            yield Static("", id="speed-metric", classes="metric-row")
            yield Static("", id="eta-metric", classes="metric-row")
            yield Static("", id="urls-metric", classes="metric-row")
            yield Static("", id="assets-metric", classes="metric-row")

        # Sparkline
        with Vertical(classes="sparkline-container"):
            yield Sparkline(id="speed-sparkline", label="Speed", unit="p/s")

    def on_mount(self) -> None:
        """Cachea referencias a widgets en mount."""
        # Progress bars
        self._pages_progress = self.query_one("#pages-progress", ProgressBar)
        self._assets_progress = self.query_one("#assets-progress", ProgressBar)

        # Stats displays
        self._pages_stats = self.query_one("#pages-stats", Static)
        self._assets_stats = self.query_one("#assets-stats", Static)

        # Metrics
        self._speed_metric = self.query_one("#speed-metric", Static)
        self._eta_metric = self.query_one("#eta-metric", Static)
        self._urls_metric = self.query_one("#urls-metric", Static)
        self._assets_metric = self.query_one("#assets-metric", Static)

        # Sparkline
        self._sparkline = self.query_one("#speed-sparkline", Sparkline)

    def _schedule_update(self) -> None:
        """Programa un único update para el próximo tick."""
        if not self._update_pending:
            self._update_pending = True
            self.call_later(self._do_update)

    def _do_update(self) -> None:
        """Ejecuta el update real de todos los displays."""
        self._update_pending = False
        self._update_progress_bars()
        self._update_metrics()
        self._update_sparkline()

    def _update_progress_bars(self) -> None:
        """Actualiza las barras de progreso."""
        # Páginas
        self._pages_progress.update(
            total=self.pages_total,
            progress=self.pages_completed,
        )
        pages_pct = (
            (self.pages_completed / self.pages_total * 100)
            if self.pages_total > 0
            else 0
        )
        self._pages_stats.update(
            f"{self.pages_completed}/{self.pages_total} ({pages_pct:.0f}%)"
        )

        # Assets
        self._assets_progress.update(
            total=self.assets_total,
            progress=self.assets_completed,
        )
        assets_pct = (
            (self.assets_completed / self.assets_total * 100)
            if self.assets_total > 0
            else 0
        )
        self._assets_stats.update(
            f"{self.assets_completed}/{self.assets_total} ({assets_pct:.0f}%)"
        )

    def _update_metrics(self) -> None:
        """Actualiza las métricas de texto."""
        # Velocidad con comparación
        speed_trend = ""
        if self.speed_current > self.speed_average * 1.1:
            speed_trend = " [green]↑[/]"
        elif self.speed_current < self.speed_average * 0.9:
            speed_trend = " [red]↓[/]"

        self._speed_metric.update(
            f"⚡ [bold]{self.speed_current:.1f}[/] pages/s  "
            f"(avg: {self.speed_average:.1f}, max: {self.speed_max:.1f}){speed_trend}"
        )

        # ETA con rango
        if self.eta_seconds_best > 0:
            eta_best = self._format_time(self.eta_seconds_best)
            eta_worst = self._format_time(self.eta_seconds_worst)
            if self.eta_seconds_best != self.eta_seconds_worst:
                self._eta_metric.update(
                    f"⏱️ ETA: [yellow]{eta_best}[/] – [dim]{eta_worst}[/]"
                )
            else:
                self._eta_metric.update(f"⏱️ ETA: [yellow]{eta_best}[/]")
        else:
            self._eta_metric.update("⏱️ ETA: [dim]calculating...[/]")

        # URLs vistas
        self._urls_metric.update(f"🔗 URLs descubiertas: [bold]{self.urls_seen:,}[/]")

        # Assets vistos
        self._assets_metric.update(
            f"📦 Assets descubiertos: [bold]{self.assets_seen:,}[/]"
        )

    def _update_sparkline(self) -> None:
        """Actualiza el sparkline con el historial."""
        if self.speed_history:
            self._sparkline.values = self.speed_history
            self._sparkline.max_value = (
                max(self.speed_history) if self.speed_history else 1.0
            )

    def _format_time(self, seconds: int) -> str:
        """Formatea segundos a HH:MM:SS."""
        if seconds < 0:
            return "∞"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours:d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:d}:{secs:02d}"

    # ═══════════════════════════════════════════════════════════════════════════
    # WATCHERS - Todos usan el mismo scheduler
    # ═══════════════════════════════════════════════════════════════════════════

    def watch_pages_completed(self, old: int, new: int) -> None:
        self._schedule_update()

    def watch_pages_total(self, old: int, new: int) -> None:
        self._schedule_update()

    def watch_assets_completed(self, old: int, new: int) -> None:
        self._schedule_update()

    def watch_assets_total(self, old: int, new: int) -> None:
        self._schedule_update()

    def watch_urls_seen(self, old: int, new: int) -> None:
        self._schedule_update()

    def watch_assets_seen(self, old: int, new: int) -> None:
        self._schedule_update()

    def watch_speed_current(self, old: float, new: float) -> None:
        self._schedule_update()

    def watch_speed_average(self, old: float, new: float) -> None:
        self._schedule_update()

    def watch_speed_max(self, old: float, new: float) -> None:
        self._schedule_update()

    def watch_eta_seconds_best(self, old: int, new: int) -> None:
        self._schedule_update()

    def watch_eta_seconds_worst(self, old: int, new: int) -> None:
        self._schedule_update()

    def watch_speed_history(self, old: list[float], new: list[float]) -> None:
        self._schedule_update()

    # ═══════════════════════════════════════════════════════════════════════════
    # PUBLIC API - Helpers para actualización desde eventos
    # ═══════════════════════════════════════════════════════════════════════════

    def update_from_progress(self, event: "ProgressUpdate") -> None:
        """Actualiza desde un evento ProgressUpdate."""
        self.pages_completed = event.pages_completed
        self.pages_total = event.pages_total
        self.assets_completed = event.assets_completed
        self.assets_total = event.assets_total
        self.urls_seen = event.urls_seen
        self.assets_seen = event.assets_seen

    def update_from_speed(self, event: "SpeedUpdate") -> None:
        """Actualiza desde un evento SpeedUpdate."""
        self.speed_current = event.speed_current
        self.speed_average = event.speed_average
        self.speed_max = event.speed_max
        self.eta_seconds_best = event.eta_seconds_best
        self.eta_seconds_worst = event.eta_seconds_worst
        self.speed_history = event.speed_history

    def add_speed_sample(self, speed: float) -> None:
        """Agrega una muestra de velocidad al buffer."""
        self._speed_buffer.append(speed)
        self._sparkline.add_value(speed)


__all__ = ["LiveProgressPanel"]

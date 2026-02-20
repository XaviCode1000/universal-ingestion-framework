"""Dashboard Screen - Pantalla principal del TUI.

Layout:
┌────────────────────────────────────────────────────────────────────────┐
│ Header (clock + state)                                                 │
├────────────────────────────────────────────────────────────────────────┤
│ CurrentURLDisplay                                                      │
├────────────────────────────────────────────────────────────────────────┤
│ [Progress Panel]                          [Activity Feed]               │
├────────────────────────────────────────────────────────────────────────┤
│ SystemStatusBar                                                        │
└────────────────────────────────────────────────────────────────────────┘
"""

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Footer, Header

from uif_scraper.tui.widgets.activity_feed import ActivityFeed
from uif_scraper.tui.widgets.current_url import CurrentURLDisplay
from uif_scraper.tui.widgets.progress_panel import LiveProgressPanel
from uif_scraper.tui.widgets.status_bar import SystemStatusBar

if TYPE_CHECKING:
    from uif_scraper.tui.messages import (
        StateChange,
    )


class DashboardScreen(Screen[Message]):
    """Pantalla principal del dashboard.

    Muestra:
    - URL actual siendo procesada (prominente)
    - Panel de progreso con métricas y sparkline
    - Feed de actividad en tiempo real
    - Barra de estado del sistema
    """

    CSS_PATH = "../styles/mocha.tcss"

    def compose(self) -> ComposeResult:
        """Compone el layout del dashboard."""
        yield Header(show_clock=True)

        with Vertical(id="main-container"):
            # URL actual prominentemente
            with Vertical(id="current-url-container"):
                yield CurrentURLDisplay(id="current-url")

            # Contenido principal (dos columnas)
            with Horizontal(id="content-area"):
                yield LiveProgressPanel(id="progress-panel")
                yield ActivityFeed(id="activity-feed")

            # Barra de estado
            with Vertical(id="status-bar-container"):
                yield SystemStatusBar(id="status-bar")

        yield Footer()

    def on_mount(self) -> None:
        """Inicializa widgets en mount."""
        self._current_url = self.query_one("#current-url", CurrentURLDisplay)
        self._progress = self.query_one("#progress-panel", LiveProgressPanel)
        self._activity = self.query_one("#activity-feed", ActivityFeed)
        self._status = self.query_one("#status-bar", SystemStatusBar)
        self._header = self.query_one(Header)

        # Timer para actualizar timestamps del activity feed
        self.set_interval(1.0, self._tick)

    def _tick(self) -> None:
        """Actualización periódica para timestamps."""
        self._activity.tick()

    def update_from_event(self, event: "TUIEvent") -> None:
        """Actualiza widgets desde eventos.

        Args:
            event: Evento tipado del sistema de mensajes
        """
        from uif_scraper.tui.messages import (
            ActivityEvent,
            ProgressUpdate,
            SpeedUpdate,
            StateChange,
            SystemStatus,
        )

        match event:
            case ProgressUpdate():
                self._progress.update_from_progress(event)

            case SpeedUpdate():
                self._progress.update_from_speed(event)

            case ActivityEvent():
                self._activity.update_from_event(event)

            case SystemStatus():
                self._status.update_from_event(event)
                self._current_url.update_from_event(event)

            case StateChange():
                self._update_state(event)

    def _update_state(self, event: "StateChange") -> None:
        """Actualiza el estado del header y widgets."""
        state_colors = {
            "starting": "yellow",
            "running": "green",
            "paused": "yellow",
            "mission_complete": "green",  # Éxito!
            "finalizing": "cyan",  # Limpiando
            "stopping": "yellow",
            "stopped": "dim",
            "error": "red",
        }
        state_icons = {
            "starting": "⏳",
            "running": "🚀",
            "paused": "⏸",
            "mission_complete": "✅",
            "finalizing": "🔄",
            "stopping": "⏹",
            "stopped": "■",
            "error": "✗",
        }
        color = state_colors.get(event.state, "white")
        icon = state_icons.get(event.state, "●")
        mode_icon = "🌐" if event.mode == "browser" else "🥷"

        # Actualizar subtítulo de la app (el header muestra app.sub_title)
        if self.app:
            self.app.sub_title = (
                f"[{color}]{icon} {event.state.upper()}[/] | {mode_icon} {event.mode}"
            )

        # Actualizar el widget de URL según el estado
        self._current_url.update_from_state_change(event)

    def set_processing_url(self, url: str, worker_id: int, engine: str) -> None:
        """Setea la URL que se está procesando.

        Args:
            url: URL siendo procesada
            worker_id: ID del worker
            engine: Motor de extracción
        """
        self._current_url.set_processing(url, worker_id, engine)

    def set_idle(self) -> None:
        """Setea estado idle (sin URL activa)."""
        self._current_url.set_idle()

    def set_paused(self) -> None:
        """Setea estado pausado."""
        self._current_url.set_paused()

    def set_error(self, url: str, error_msg: str) -> None:
        """Setea estado de error.

        Args:
            url: URL que causó el error
            error_msg: Mensaje de error
        """
        self._current_url.set_error(url, error_msg)

    def clear_activity(self) -> None:
        """Limpia el feed de actividad."""
        self._activity.clear()


# Import para type hints
from uif_scraper.tui.messages import TUIEvent  # noqa: E402

__all__ = ["DashboardScreen"]

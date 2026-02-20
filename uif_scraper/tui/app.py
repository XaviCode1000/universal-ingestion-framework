"""UIF Dashboard App - Main Textual Application.

Arquitectura basada en Screens:
    EngineCore → TUICallback → Events → UIFDashboardApp → DashboardScreen → Widgets

La app maneja:
- Navegación entre pantallas (Dashboard, Queue, Errors, Config, Logs)
- Comunicación con EngineCore via callbacks
- Estado global (paused, running, etc.)
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Coroutine

from textual import work
from textual.app import App
from textual.worker import Worker

from uif_scraper.tui.messages import (
    ActivityEvent,
    ProgressUpdate,
    StateChange,
    SystemStatus,
    TUIEvent,
)
from uif_scraper.tui.screens import (
    ConfigScreen,
    DashboardScreen,
    ErrorScreen,
    LogsScreen,
    QueueScreen,
)

if TYPE_CHECKING:
    from textual.timer import Timer


class UIFDashboardApp(App[None]):
    """Main TUI Dashboard for UIF Scraper.

    Arquitectura basada en Screens con navegación via keybindings.
    El engine corre como background worker y emite eventos tipados.
    """

    TITLE = "🛸 UIF SCRAPER v3.0"
    SUB_TITLE = "● IDLE"

    CSS_PATH = Path(__file__).parent / "styles" / "mocha.tcss"

    BINDINGS = [
        # Globales
        ("ctrl+c", "quit", "Quit"),
        ("q", "quit", "Quit"),
        ("p", "toggle_pause", "Pause"),
        ("?", "show_help", "Help"),
        ("escape", "go_dashboard", "Dashboard"),
        # Navegación
        ("c", "push_screen('queue')", "Queue"),
        ("e", "push_screen('errors')", "Errors"),
        ("comma", "push_screen('config')", "Config"),
        ("l", "push_screen('logs')", "Logs"),
    ]

    SCREENS = {
        "dashboard": DashboardScreen,
        "queue": QueueScreen,
        "errors": ErrorScreen,
        "config": ConfigScreen,
        "logs": LogsScreen,
    }

    def __init__(
        self,
        mission_url: str = "",
        scope: str = "smart",
        worker_count: int = 5,
        engine_factory: Callable[[], Coroutine[None, None, None]] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._mission_url = mission_url
        self._scope = scope
        self._worker_count = worker_count
        self._engine_factory = engine_factory

        # Estado
        self._is_paused: bool = False
        self._is_running: bool = False
        self._engine_completed: bool = False
        self._update_timer: Timer | None = None

        # Queue para comandos al engine (pause, resume, etc.)
        self._command_handlers: dict[str, Callable] = {}

    def on_mount(self) -> None:
        """Inicializa la app en mount."""
        # Instalar pantalla principal
        self.push_screen("dashboard")

        # Timer para actualizaciones periódicas
        self._update_timer = self.set_interval(1.0, self._tick)

        # Iniciar engine si hay factory
        if self._engine_factory:
            self._run_engine_worker()

    def _tick(self) -> None:
        """Callback periódico para actualizaciones."""
        pass  # Las pantallas manejan sus propios timers

    # ═══════════════════════════════════════════════════════════════════════════
    # ENGINE WORKER
    # ═══════════════════════════════════════════════════════════════════════════

    @work(exclusive=True, name="engine_worker")
    async def _run_engine_worker(self) -> None:
        """Run the scraping engine as a Textual worker."""
        if self._engine_factory:
            try:
                self._is_running = True
                await self._engine_factory()
                self._engine_completed = True
            except Exception:
                raise
            finally:
                self._is_running = False
                self.call_later(self._safe_exit)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Handle worker state changes."""
        from textual.worker import WorkerState

        if event.worker.name != "engine_worker":
            return

        if event.state == WorkerState.SUCCESS:
            self.notify(
                "Scraping completed successfully!",
                title="Done",
                severity="information",
            )
            self.call_later(self.exit)
        elif event.state == WorkerState.ERROR:
            self.notify(
                "Scraping failed with an error.",
                title="Error",
                severity="error",
            )
            self.call_later(self.exit)
        elif event.state == WorkerState.CANCELLED:
            self.call_later(self.exit)

    def _safe_exit(self) -> None:
        """Safety exit handler."""
        if self._engine_completed:
            self.notify(
                "Scraping completed successfully!",
                title="Done",
                severity="information",
            )
        else:
            self.notify("Engine terminated.", title="Exit", severity="warning")
        self.exit()

    # ═══════════════════════════════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════════════════════════════

    def action_toggle_pause(self) -> None:
        """Toggle pause/resume."""
        self._is_paused = not self._is_paused

        if self._is_paused:
            self.SUB_TITLE = "● PAUSED"
            self.notify("Paused", title="Status", severity="warning")
        else:
            self.SUB_TITLE = "● RUNNING"
            self.notify("Resumed", title="Status", severity="information")

        # Notificar a handlers registrados
        if "pause" in self._command_handlers:
            self._command_handlers["pause"](self._is_paused)

    def action_go_dashboard(self) -> None:
        """Vuelve al dashboard desde cualquier pantalla."""
        if not isinstance(self.screen, DashboardScreen):
            self.pop_screen()

    def action_show_help(self) -> None:
        """Muestra ayuda."""
        self.notify(
            "Shortcuts: P=Pause, C=Queue, E=Errors, Q=Quit",
            title="Help",
            severity="information",
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # PUBLIC API - Para callbacks externos
    # ═══════════════════════════════════════════════════════════════════════════

    def handle_event(self, event: TUIEvent) -> None:
        """Maneja un evento del engine y lo propaga a la pantalla actual.

        Args:
            event: Evento tipado del sistema de mensajes
        """
        # Actualizar subtítulo global según estado
        if isinstance(event, StateChange):
            self._update_subtitle(event)

        # Propagar a la pantalla actual si es DashboardScreen
        if isinstance(self.screen, DashboardScreen):
            self.screen.update_from_event(event)

    def _update_subtitle(self, event: StateChange) -> None:
        """Actualiza el subtítulo de la app según el estado."""
        state_icons = {
            "starting": "⏳",
            "running": "▶",
            "paused": "⏸",
            "stopping": "⏹",
            "stopped": "■",
            "error": "✗",
        }
        icon = state_icons.get(event.state, "●")
        mode = "🌐" if event.mode == "browser" else "🥷"
        self.SUB_TITLE = f"{icon} {event.state.upper()} | {mode}"

    def register_command_handler(self, command: str, handler: Callable) -> None:
        """Registra un handler para un comando.

        Args:
            command: Nombre del comando (pause, resume, etc.)
            handler: Función a llamar cuando se ejecute el comando
        """
        self._command_handlers[command] = handler

    # ═══════════════════════════════════════════════════════════════════════════
    # LEGACY API - Compatibilidad con código existente
    # ═══════════════════════════════════════════════════════════════════════════

    def update_progress(
        self,
        pages_completed: int,
        pages_total: int,
        assets_completed: int = 0,
        assets_total: int = 0,
        seen_urls: int = 0,
        seen_assets: int = 0,
    ) -> None:
        """Post a progress update (legacy API)."""
        event = ProgressUpdate(
            pages_completed=pages_completed,
            pages_total=pages_total,
            assets_completed=assets_completed,
            assets_total=assets_total,
            urls_seen=seen_urls,
            assets_seen=seen_assets,
        )
        self.handle_event(event)

    def add_activity(self, title: str, engine: str = "unknown") -> None:
        """Post an activity message (legacy API)."""
        event = ActivityEvent(
            url="",
            title=title,
            engine=engine,
            status="success",
            elapsed_ms=0.0,
        )
        self.handle_event(event)

    def update_status(
        self,
        circuit_state: str,
        queue_pending: int,
        error_count: int,
        browser_mode: bool,
    ) -> None:
        """Post a status update (legacy API)."""
        from typing import Literal, cast

        # Cast a Literal para satisfacer el tipo
        circuit = cast(
            Literal["closed", "open", "half-open"],
            circuit_state
            if circuit_state in ("closed", "open", "half-open")
            else "closed",
        )
        event = SystemStatus(
            circuit_state=circuit,
            queue_pending=queue_pending,
            error_count=error_count,
            memory_mb=0,
            cpu_percent=0.0,
            current_url="",
            current_worker=0,
        )
        self.handle_event(event)


__all__ = ["UIFDashboardApp"]

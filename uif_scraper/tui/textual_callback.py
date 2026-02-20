"""Textual TUI callback adapter for EngineCore.

Implementa UICallback interface para conectar EngineCore con la TUI.
Usa los nuevos eventos tipados de messages.py.

Arquitectura:
    EngineCore → TextualUICallback → app.handle_event() → DashboardScreen → Widgets
"""

from time import time
from typing import TYPE_CHECKING, Literal, cast

from uif_scraper.core.engine_core import UICallback
from uif_scraper.core.types import ActivityEntry, EngineStats
from uif_scraper.tui.messages import (
    ActivityEvent,
    ProgressUpdate,
    SpeedUpdate,
    StateChange,
    SystemStatus,
)

if TYPE_CHECKING:
    from uif_scraper.tui.app import UIFDashboardApp


class TextualUICallback(UICallback):
    """Adapter que traduce callbacks de EngineCore a eventos tipados.

    NOTA: EngineCore corre en el mismo event loop que Textual (como worker).
    Por eso podemos llamar handle_event() directamente sin call_from_thread().

    Throttling:
    - Progress: throttled a 10 updates/segundo
    - Activity: throttled a 10 updates/segundo
    - Errors: SIN throttling (importante no perder info)
    """

    # Configuración de throttling
    PROGRESS_THROTTLE_INTERVAL = 0.1  # 100ms = 10 updates/s
    ACTIVITY_THROTTLE_INTERVAL = 0.1  # 100ms = 10 updates/s

    def __init__(self, app: "UIFDashboardApp") -> None:
        """Inicializar adapter con referencia al TUI app.

        Args:
            app: Instancia de UIFDashboardApp para enviar eventos.
        """
        self._app = app

        # Estado para throttling
        self._last_progress_time: float = 0.0
        self._last_activity_time: float = 0.0

        # Buffer para speed history (sparkline)
        self._speed_history: list[float] = []
        self._last_speed_time: float = 0.0

        # Estado del sistema
        self._circuit_state: str = "closed"
        self._queue_pending: int = 0
        self._error_count: int = 0
        self._browser_mode: bool = False
        self._current_url: str = ""
        self._current_worker: int = 0

    def on_progress(self, stats: EngineStats) -> None:
        """Notificar progreso al TUI con throttling.

        Args:
            stats: Snapshot de estadísticas del engine.
        """
        now = time()

        # Throttle: solo enviar si pasó suficiente tiempo
        if now - self._last_progress_time >= self.PROGRESS_THROTTLE_INTERVAL:
            self._last_progress_time = now

            # Crear evento de progreso
            event = ProgressUpdate(
                pages_completed=stats.pages_completed,
                pages_total=stats.pages_total,
                assets_completed=stats.assets_completed,
                assets_total=stats.assets_total,
                urls_seen=stats.seen_urls,
                assets_seen=stats.seen_assets,
            )
            self._app.handle_event(event)

            # Actualizar estado del sistema
            self._queue_pending = stats.queue_pending
            self._error_count = stats.error_count

    def on_activity(self, entry: ActivityEntry) -> None:
        """Notificar actividad reciente al TUI con throttling.

        Args:
            entry: Entrada de actividad con título y motor.
        """
        now = time()

        # Throttle: solo enviar si pasó suficiente tiempo
        if now - self._last_activity_time >= self.ACTIVITY_THROTTLE_INTERVAL:
            self._last_activity_time = now

            # Determinar status basado en contexto
            status: Literal["success", "warning", "error"] = "success"

            event = ActivityEvent(
                url="",  # No disponible en ActivityEntry
                title=entry.title,
                engine=entry.engine,
                status=status,
                elapsed_ms=0.0,
            )
            self._app.handle_event(event)

    def on_mode_change(self, browser_mode: bool) -> None:
        """Notificar cambio de modo (stealth ↔ browser).

        Args:
            browser_mode: True si cambió a modo navegador, False si es stealth.
        """
        self._browser_mode = browser_mode
        self._send_system_status()

    def on_circuit_change(self, state: str) -> None:
        """Notificar cambio de circuit breaker.

        Args:
            state: Estado del circuit breaker (closed, open, half-open).
        """
        self._circuit_state = state
        self._send_system_status()

    def update_current_url(self, url: str, worker_id: int) -> None:
        """Actualiza la URL siendo procesada actualmente.

        Args:
            url: URL siendo procesada
            worker_id: ID del worker
        """
        self._current_url = url
        self._current_worker = worker_id
        self._send_system_status()

    def update_speed(self, speed: float, elapsed: float) -> None:
        """Actualiza métricas de velocidad.

        Args:
            speed: Velocidad actual en pages/s
            elapsed: Tiempo transcurrido en segundos
        """
        now = time()

        # Agregar al historial (máximo 60 valores)
        self._speed_history.append(speed)
        if len(self._speed_history) > 60:
            self._speed_history = self._speed_history[-60:]

        # Enviar evento de velocidad cada segundo
        if now - self._last_speed_time >= 1.0:
            self._last_speed_time = now

            # Calcular métricas
            avg_speed = sum(self._speed_history) / len(self._speed_history)
            max_speed = max(self._speed_history) if self._speed_history else 0.0

            # Calcular ETA (estimación simple)
            # TODO: Implementar cálculo de ETA con rango

            event = SpeedUpdate(
                speed_current=speed,
                speed_average=avg_speed,
                speed_max=max_speed,
                eta_seconds_best=0,
                eta_seconds_worst=0,
                speed_history=list(self._speed_history),
            )
            self._app.handle_event(event)

    def notify_state_change(
        self,
        state: str,
        mode: str,
        previous_state: str | None = None,
        reason: str | None = None,
    ) -> None:
        """Notifica cambio de estado del engine.

        Args:
            state: Nuevo estado (starting, running, paused, stopping, stopped, error)
            mode: Modo actual (stealth, browser)
            previous_state: Estado anterior
            reason: Razón del cambio
        """
        # Validar y castear tipos
        valid_states = ("starting", "running", "paused", "stopping", "stopped", "error")
        valid_modes = ("stealth", "browser")

        state_literal = cast(
            Literal["starting", "running", "paused", "stopping", "stopped", "error"],
            state if state in valid_states else "running",
        )
        mode_literal = cast(
            Literal["stealth", "browser"],
            mode if mode in valid_modes else "stealth",
        )

        event = StateChange(
            state=state_literal,
            mode=mode_literal,
            previous_state=previous_state,
            reason=reason,
        )
        self._app.handle_event(event)

    def _send_system_status(self) -> None:
        """Envía el estado completo del sistema."""
        # Validar circuit_state
        valid_circuits = ("closed", "open", "half-open")
        circuit_literal = cast(
            Literal["closed", "open", "half-open"],
            self._circuit_state if self._circuit_state in valid_circuits else "closed",
        )

        event = SystemStatus(
            circuit_state=circuit_literal,
            queue_pending=self._queue_pending,
            error_count=self._error_count,
            memory_mb=0,  # TODO: Implementar
            cpu_percent=0.0,  # TODO: Implementar
            current_url=self._current_url,
            current_worker=self._current_worker,
        )
        self._app.handle_event(event)


__all__ = ["TextualUICallback"]

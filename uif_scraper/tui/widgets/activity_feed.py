"""
ActivityFeed Widget - Feed de actividad con buffer circular y throttling.

Muestra las últimas actividades del scraper con:
- Buffer circular de 100 items (no crece infinitamente)
- Throttling de 10 updates/segundo máximo
- Render eficiente con widgets pre-creados
- Timestamps relativos ("2s ago")
- Phase-specific coloring para Discovery/Extraction/Writing/RateLimit
"""

from collections import deque
from time import time
from typing import TYPE_CHECKING, Any, Literal, cast

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Static

if TYPE_CHECKING:
    from uif_scraper.tui.messages import (
        ActivityEvent,
        CircuitStateEvent,
        NetworkRetryEvent,
    )


# Phase-specific colors para diferenciación visual
PHASE_COLORS: dict[str, str] = {
    "discovery": "cyan",  # #89dceb - Encontrando nuevos links
    "extraction": "green",  # #a6e3a1 - Fetch & parse de página
    "writing": "magenta",  # #cba6f7 - Escribiendo a disco
    "rate_limit": "yellow",  # #f9e2af - Esperando throttling
    "retry": "orange",  # #fab387 - Reintento de red
    "circuit_open": "red",  # #f38ba8 - Circuit breaker abierto
    "circuit_half_open": "yellow",  # #f9e2af - Circuit breaker medio abierto
    "idle": "dim",  # Sin actividad
}

PHASE_ICONS: dict[str, str] = {
    "discovery": "🔍",
    "extraction": "⬇️",
    "writing": "💾",
    "rate_limit": "⏳",
    "retry": "🔄",
    "circuit_open": "🚫",
    "circuit_half_open": "🧪",
    "idle": "💤",
}


class ActivityFeed(Vertical):
    """Feed de actividad con buffer circular y throttling inteligente.

    Características:
    - Buffer circular de 100 items (memoria fija)
    - Máximo 10 actualizaciones/segundo (throttling)
    - 8 items visibles con scroll
    - Timestamps relativos actualizados
    - Phase-specific coloring para UX mejorada
    """

    # CSS movido a mocha.tcss para usar variables

    class ActivityAdded(Message):
        """Mensaje emitido cuando se agrega una actividad."""

        def __init__(self, url: str, title: str, engine: str, status: str) -> None:
            super().__init__()
            self.url = url
            self.title = title
            self.engine = engine
            self.status = status

    # ═══════════════════════════════════════════════════════════════════════════
    # CONFIGURACIÓN
    # ═══════════════════════════════════════════════════════════════════════════

    BUFFER_SIZE = 100  # Tamaño del buffer circular
    VISIBLE_ITEMS = 8  # Items visibles en pantalla
    MAX_UPDATES_PER_SECOND = 10  # Throttling

    # ═══════════════════════════════════════════════════════════════════════════
    # REACTIVE PROPS
    # ═══════════════════════════════════════════════════════════════════════════

    activities: reactive[list[dict[str, Any]]] = reactive(list, init=False)
    current_phase: reactive[str] = reactive("idle", init=False)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Buffer circular para memoria fija
        self._buffer: deque[dict[str, Any]] = deque(maxlen=self.BUFFER_SIZE)
        # Control de throttling
        self._last_update_time: float = 0.0
        self._pending_render: bool = False
        # Cache de timestamps para actualización
        self._timestamps: dict[int, float] = {}
        # Fase actual para coloración
        self._current_phase: Literal[
            "discovery",
            "extraction",
            "writing",
            "rate_limit",
            "retry",
            "circuit_open",
            "circuit_half_open",
            "idle",
        ] = "idle"

    def compose(self) -> ComposeResult:
        """Compone el layout del feed."""
        yield Static("🔄 ACTIVITY", classes="panel-title")
        with VerticalScroll(id="activity-scroll"):
            # Pre-crear widgets para render eficiente
            for i in range(self.VISIBLE_ITEMS):
                yield Static("", id=f"activity-{i}", classes="activity-line")

    def on_mount(self) -> None:
        """Cachea referencias a widgets."""
        self._widgets = [
            self.query_one(f"#activity-{i}", Static) for i in range(self.VISIBLE_ITEMS)
        ]

    def add_activity(
        self,
        url: str,
        title: str,
        engine: str = "unknown",
        status: str = "success",
        elapsed_ms: float = 0.0,
        size_bytes: int = 0,
        phase: Literal["discovery", "extraction", "writing", "rate_limit", "idle"]
        | None = None,
    ) -> None:
        """Agrega una actividad al feed con throttling.

        Args:
            url: URL procesada
            title: Título de la página
            engine: Motor de extracción usado
            status: success, warning, o error
            elapsed_ms: Tiempo de procesamiento en ms
            size_bytes: Tamaño del contenido en bytes
            phase: Fase actual del scraping (discovery/extraction/writing/rate_limit)
        """
        now = time()

        # Usar fase actual si no se específica
        current_phase = phase or self._current_phase

        # Agregar al buffer circular
        activity = {
            "url": url,
            "title": title[:50] + ("..." if len(title) > 50 else ""),
            "engine": engine,
            "status": status,
            "elapsed_ms": elapsed_ms,
            "size_bytes": size_bytes,
            "timestamp": now,
            "phase": current_phase,
        }
        self._buffer.appendleft(activity)

        # Throttling: solo renderizar si pasó suficiente tiempo
        time_since_last = now - self._last_update_time
        if time_since_last >= (1.0 / self.MAX_UPDATES_PER_SECOND):
            self._last_update_time = now
            self._render_visible()
            self.post_message(self.ActivityAdded(url, title, engine, status))
        else:
            self._pending_render = True

    def set_phase(
        self,
        phase: Literal[
            "discovery",
            "extraction",
            "writing",
            "rate_limit",
            "retry",
            "circuit_open",
            "circuit_half_open",
            "idle",
        ],
    ) -> None:
        """Establece la fase actual para coloración del feed.

        Args:
            phase: Fase actual del scraping
        """
        self._current_phase = phase
        self.current_phase = phase

    def _render_visible(self) -> None:
        """Renderiza los items visibles usando widgets cacheados."""
        for i, widget in enumerate(self._widgets):
            if i < len(self._buffer):
                activity = self._buffer[i]
                time_ago = self._format_time_ago(activity["timestamp"])
                engine = activity["engine"]
                title = activity["title"]
                status = activity["status"]

                # Phase-specific coloring para la fase actual
                phase = activity.get("phase", "idle")
                phase_color = PHASE_COLORS.get(phase, "dim")
                phase_icon = PHASE_ICONS.get(phase, "")

                # Color del engine según tipo (subordinado a fase)
                engine_colors = {
                    "trafilatura": "green",
                    "html-to-markdown": "green",
                    "readability": "yellow",
                    "beautifulsoup": "yellow",
                    "markitdown": "cyan",
                }
                engine_color = engine_colors.get(engine.lower(), "dim")

                # Indicador de estado
                status_icon = (
                    "✓" if status == "success" else "⚠" if status == "warning" else "✗"
                )

                # Formatear línea con phase icon
                if phase_icon:
                    content = (
                        f"{phase_icon} {status_icon} [bold]{title}[/]\n"
                        f"   [{phase_color}]{phase}[/] • [{engine_color}]{engine}[/] • {time_ago}"
                    )
                else:
                    content = (
                        f"{status_icon} [bold]{title}[/]\n"
                        f"   [{engine_color}]{engine}[/] • {time_ago}"
                    )
                widget.update(content)
                widget.display = True
            else:
                widget.display = False

    def _format_time_ago(self, timestamp: float) -> str:
        """Formatea timestamp a tiempo relativo."""
        elapsed = time() - timestamp
        if elapsed < 60:
            return f"{int(elapsed)}s ago"
        elif elapsed < 3600:
            return f"{int(elapsed / 60)}m ago"
        return f"{int(elapsed / 3600)}h ago"

    def tick(self) -> None:
        """Llamado periódicamente para actualizar timestamps y renders pendientes."""
        # Procesar render pendiente
        if self._pending_render:
            now = time()
            if now - self._last_update_time >= (1.0 / self.MAX_UPDATES_PER_SECOND):
                self._last_update_time = now
                self._pending_render = False

        # Siempre actualizar timestamps
        self._render_visible()

    def clear(self) -> None:
        """Limpia el feed."""
        self._buffer.clear()
        for widget in self._widgets:
            widget.display = False

    def get_count(self) -> int:
        """Retorna el número de actividades en el buffer."""
        return len(self._buffer)

    # ═══════════════════════════════════════════════════════════════════════════
    # PUBLIC API - Helper para actualizar desde eventos
    # ═══════════════════════════════════════════════════════════════════════════

    def update_from_event(self, event: "ActivityEvent") -> None:
        """Actualiza desde un evento ActivityEvent."""
        self.add_activity(
            url=event.url,
            title=event.title,
            engine=event.engine,
            status=event.status,
            elapsed_ms=event.elapsed_ms,
            size_bytes=event.size_bytes,
        )

    def update_from_retry_event(self, event: "NetworkRetryEvent") -> None:
        """Actualiza desde un evento NetworkRetryEvent."""
        self.add_retry_activity(
            url=event.url,
            attempt_number=event.attempt_number,
            wait_time=event.wait_time,
            reason=event.reason,
        )

    def update_from_circuit_event(self, event: "CircuitStateEvent") -> None:
        """Actualiza desde un evento CircuitStateEvent."""
        self.add_circuit_activity(
            domain=event.domain,
            old_state=event.old_state,
            new_state=event.new_state,
            failure_count=event.failure_count,
        )

    def set_phase_from_activity(self, activity_type: str) -> None:
        """Establece la fase basada en el tipo de actividad.

        Args:
            activity_type: Tipo de actividad (extract_links, download_asset, etc.)
        """
        phase_mapping: dict[str, str] = {
            "extract_links": "discovery",
            "download_asset": "writing",
            "process_page": "extraction",
            "throttle": "rate_limit",
        }
        raw_phase = phase_mapping.get(activity_type, "idle")
        phase = cast(
            Literal[
                "discovery",
                "extraction",
                "writing",
                "rate_limit",
                "retry",
                "circuit_open",
                "circuit_half_open",
                "idle",
            ],
            raw_phase,
        )
        self.set_phase(phase)

    # ═══════════════════════════════════════════════════════════════════════════════
    # NETWORK RESILIENCE EVENTS
    # ═══════════════════════════════════════════════════════════════════════════════

    def add_retry_activity(
        self,
        url: str,
        attempt_number: int,
        wait_time: float,
        reason: str,
    ) -> None:
        """Agrega una actividad de reintento al feed.

        Args:
            url: URL que se está reintentando
            attempt_number: Número de intento actual
            wait_time: Tiempo de espera antes del reintento
            reason: Razón del fallo original
        """
        now = time()

        activity = {
            "url": url,
            "title": f"Reintento {attempt_number} ({reason})",
            "engine": f"wait {wait_time:.1f}s",
            "status": "warning",
            "elapsed_ms": wait_time * 1000,
            "size_bytes": 0,
            "timestamp": now,
            "phase": "retry",
        }
        self._buffer.appendleft(activity)

        # Render inmediatamente para retries (no hay throttle aquí)
        self._render_visible()
        self.post_message(
            self.ActivityAdded(url, f"Reintento {attempt_number}", "network", "warning")
        )

    def add_circuit_activity(
        self,
        domain: str,
        old_state: str,
        new_state: str,
        failure_count: int,
    ) -> None:
        """Agrega una actividad de cambio de circuit breaker al feed.

        Args:
            domain: Dominio afectado
            old_state: Estado anterior
            new_state: Nuevo estado
            failure_count: Cantidad de fallos consecutivos
        """
        now = time()

        # Determinar fase según el nuevo estado
        if new_state == "open":
            phase = "circuit_open"
            title = f"Circuit ABIERTO: {domain}"
            status = "error"
        elif new_state == "half-open":
            phase = "circuit_half_open"
            title = f"Prueba {domain}"
            status = "warning"
        else:
            phase = "idle"
            title = f"Circuit CERRADO: {domain}"
            status = "success"

        activity = {
            "url": domain,
            "title": title,
            "engine": f"{failure_count} fallos",
            "status": status,
            "elapsed_ms": 0,
            "size_bytes": 0,
            "timestamp": now,
            "phase": phase,
        }
        self._buffer.appendleft(activity)

        # Render inmediatamente para cambios de circuit
        self._render_visible()
        self.post_message(self.ActivityAdded(domain, title, "circuit_breaker", status))


__all__ = ["ActivityFeed", "PHASE_COLORS", "PHASE_ICONS"]

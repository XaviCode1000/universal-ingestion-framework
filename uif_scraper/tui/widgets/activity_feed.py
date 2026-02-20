"""
ActivityFeed Widget - Feed de actividad con buffer circular y throttling.

Muestra las últimas actividades del scraper con:
- Buffer circular de 100 items (no crece infinitamente)
- Throttling de 10 updates/segundo máximo
- Render eficiente con widgets pre-creados
- Timestamps relativos ("2s ago")
"""

from collections import deque
from time import time
from typing import TYPE_CHECKING, Any

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Static

if TYPE_CHECKING:
    from uif_scraper.tui.messages import ActivityEvent


class ActivityFeed(Vertical):
    """Feed de actividad con buffer circular y throttling inteligente.

    Características:
    - Buffer circular de 100 items (memoria fija)
    - Máximo 10 actualizaciones/segundo (throttling)
    - 8 items visibles con scroll
    - Timestamps relativos actualizados
    """

    DEFAULT_CSS = """
    ActivityFeed {
        width: 1fr;
        height: 1fr;
        min-width: 35;
        min-height: 10;
        background: $surface0;
        border: round $surface1;
        padding: 1;
    }

    ActivityFeed .panel-title {
        color: $green;
        text-style: bold;
        margin-bottom: 1;
    }

    ActivityFeed VerticalScroll {
        height: 1fr;
    }

    ActivityFeed .activity-line {
        height: 2;
        padding: 0 1;
        margin-bottom: 1;
    }

    ActivityFeed .activity-line:nth-child(odd) {
        background: $surface1;
    }

    ActivityFeed .activity-title {
        color: $text;
        text-style: bold;
    }

    ActivityFeed .activity-meta {
        color: $subtext0;
    }

    ActivityFeed .engine-success {
        color: $green;
    }

    ActivityFeed .engine-warning {
        color: $yellow;
    }

    ActivityFeed .engine-error {
        color: $red;
    }

    ActivityFeed .empty-state {
        color: $subtext0;
        text-align: center;
        padding: 2;
    }
    """

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

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Buffer circular para memoria fija
        self._buffer: deque[dict[str, Any]] = deque(maxlen=self.BUFFER_SIZE)
        # Control de throttling
        self._last_update_time: float = 0.0
        self._pending_render: bool = False
        # Cache de timestamps para actualización
        self._timestamps: dict[int, float] = {}

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
    ) -> None:
        """Agrega una actividad al feed con throttling.

        Args:
            url: URL procesada
            title: Título de la página
            engine: Motor de extracción usado
            status: success, warning, o error
            elapsed_ms: Tiempo de procesamiento en ms
            size_bytes: Tamaño del contenido en bytes
        """
        now = time()

        # Agregar al buffer circular
        activity = {
            "url": url,
            "title": title[:50] + ("..." if len(title) > 50 else ""),
            "engine": engine,
            "status": status,
            "elapsed_ms": elapsed_ms,
            "size_bytes": size_bytes,
            "timestamp": now,
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

    def _render_visible(self) -> None:
        """Renderiza los items visibles usando widgets cacheados."""
        for i, widget in enumerate(self._widgets):
            if i < len(self._buffer):
                activity = self._buffer[i]
                time_ago = self._format_time_ago(activity["timestamp"])
                engine = activity["engine"]
                title = activity["title"]
                status = activity["status"]

                # Color del engine según tipo
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

                # Formatear línea
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


__all__ = ["ActivityFeed"]

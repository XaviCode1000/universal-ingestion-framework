"""
CurrentURLDisplay Widget - Muestra prominentemente la URL siendo procesada.

Este es el indicador más importante del dashboard. El usuario necesita
saber INMEDIATAMENTE qué está procesando el scraper en cada momento.
"""

from typing import TYPE_CHECKING, Any

from textual.reactive import reactive
from textual.widgets import Static

if TYPE_CHECKING:
    from uif_scraper.tui.messages import SystemStatus


class CurrentURLDisplay(Static):
    """Widget de alta visibilidad para la URL actual siendo procesada."""

    DEFAULT_CSS = """
    CurrentURLDisplay {
        width: 100%;
        height: 3;
        background: $surface1;
        padding: 0 1;
        margin: 0 1;
        border-left: thick $mauve;
        color: $text;
    }

    CurrentURLDisplay.processing {
        border-left: thick $blue;
        background: $surface1;
    }

    CurrentURLDisplay.idle {
        border-left: thick $subtext0;
        background: $surface0;
    }

    CurrentURLDisplay.error {
        border-left: thick $red;
        background: $surface0;
    }

    CurrentURLDisplay.paused {
        border-left: thick $yellow;
    }
    """

    # Reactive props con init=False para evitar watchers en __init__
    url: reactive[str] = reactive("", init=False)
    worker_id: reactive[int] = reactive(0, init=False)
    elapsed: reactive[float] = reactive(0.0, init=False)
    engine: reactive[str] = reactive("", init=False)
    status: reactive[str] = reactive(
        "idle", init=False
    )  # idle, processing, error, paused

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._update_pending: bool = False

    def _schedule_update(self) -> None:
        """Programa un único update para el próximo tick."""
        if not self._update_pending:
            self._update_pending = True
            self.call_later(self._do_update)

    def _do_update(self) -> None:
        """Ejecuta el update real."""
        self._update_pending = False

        # Actualizar clases CSS según estado
        self.remove_class("processing", "idle", "error", "paused")
        self.add_class(self.status)

        # Refresh del contenido
        self.refresh()

    # Watchers unificados
    def watch_url(self, old: str, new: str) -> None:
        self._schedule_update()

    def watch_worker_id(self, old: int, new: int) -> None:
        self._schedule_update()

    def watch_elapsed(self, old: float, new: float) -> None:
        self._schedule_update()

    def watch_engine(self, old: str, new: str) -> None:
        self._schedule_update()

    def watch_status(self, old: str, new: str) -> None:
        self._schedule_update()

    def render(self) -> str:
        """Renderiza el widget."""
        if not self.url:
            return "⏸  [dim italic]Esperando próxima URL...[/]"

        # Truncado inteligente: preservar inicio y fin de URL
        display_url = self._truncate_url(self.url, max_length=70)

        # Color del engine según tipo
        engine_colors = {
            "trafilatura": "green",
            "html-to-markdown": "green",
            "readability": "yellow",
            "beautifulsoup": "yellow",
            "markitdown": "cyan",
        }
        engine_color = engine_colors.get(self.engine.lower(), "dim")

        # Indicador de estado
        status_icons = {
            "idle": "⏸",
            "processing": "▶",
            "error": "✗",
            "paused": "⏸",
        }
        icon = status_icons.get(self.status, "●")

        return (
            f"{icon}  [bold]NOW:[/] [cyan]{display_url}[/]\n"
            f"   Worker #{self.worker_id} • "
            f"[{engine_color}]{self.engine or 'unknown'}[/] • "
            f"[yellow]{self.elapsed:.1f}s[/]"
        )

    @staticmethod
    def _truncate_url(url: str, max_length: int = 70) -> str:
        """Trunca URL preservando inicio y final."""
        if len(url) <= max_length:
            return url

        # Dividir en mitades con ellipsis
        half = (max_length - 3) // 2
        return f"{url[:half]}...{url[-half:]}"

    def update_from_event(self, event: "SystemStatus") -> None:
        """Helper para actualizar desde un SystemStatus event."""
        self.url = event.current_url
        self.worker_id = event.current_worker
        self.status = "processing" if event.current_url else "idle"

    def set_processing(self, url: str, worker_id: int, engine: str) -> None:
        """Helper para setear estado de procesamiento."""
        self.url = url
        self.worker_id = worker_id
        self.engine = engine
        self.elapsed = 0.0
        self.status = "processing"

    def set_idle(self) -> None:
        """Helper para setear estado idle."""
        self.url = ""
        self.status = "idle"

    def set_error(self, url: str, error_msg: str) -> None:
        """Helper para setear estado de error."""
        self.url = f"[ERROR] {url}"
        self.status = "error"

    def set_paused(self) -> None:
        """Helper para setear estado pausado."""
        self.status = "paused"


__all__ = ["CurrentURLDisplay"]

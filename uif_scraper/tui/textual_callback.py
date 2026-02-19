"""Textual TUI callback adapter for EngineCore.

Implements UICallback interface to bridge EngineCore events
to Textual's message passing system.
"""

from typing import TYPE_CHECKING

from uif_scraper.core.engine_core import UICallback
from uif_scraper.core.types import ActivityEntry, EngineStats

if TYPE_CHECKING:
    from uif_scraper.tui.app import UIFDashboardApp


class TextualUICallback(UICallback):
    """Adapter que traduce callbacks de EngineCore a Textual Messages.

    Usa call_from_thread() para thread-safe communication desde
    el worker de scraping hacia el main thread de Textual.
    """

    def __init__(self, app: "UIFDashboardApp") -> None:
        """Inicializar adapter con referencia al TUI app.

        Args:
            app: Instancia de UIFDashboardApp para enviar mensajes.
        """
        self._app = app

    def on_progress(self, stats: EngineStats) -> None:
        """Notificar progreso al TUI.

        Args:
            stats: Snapshot de estadísticas del engine.
        """
        from uif_scraper.tui.app import EngineProgress

        self._app.call_from_thread(
            self._app.post_message,
            EngineProgress(
                pages_completed=stats.pages_completed,
                pages_total=stats.pages_total,
                assets_completed=stats.assets_completed,
                assets_total=stats.assets_total,
                seen_urls=stats.seen_urls,
                seen_assets=stats.seen_assets,
            ),
        )

    def on_activity(self, entry: ActivityEntry) -> None:
        """Notificar actividad reciente al TUI.

        Args:
            entry: Entrada de actividad con título y motor.
        """
        from uif_scraper.tui.app import EngineActivity

        self._app.call_from_thread(
            self._app.post_message,
            EngineActivity(title=entry.title, engine=entry.engine),
        )

    def on_mode_change(self, browser_mode: bool) -> None:
        """Notificar cambio de modo (stealth ↔ browser).

        Args:
            browser_mode: True si cambió a modo navegador, False si es stealth.
        """
        from uif_scraper.tui.app import EngineStatus

        # Obtener estado actual para actualizar solo el modo
        self._app.call_from_thread(
            self._app.post_message,
            EngineStatus(
                circuit_state="unknown",  # No disponible en este contexto
                queue_pending=0,  # No disponible en este contexto
                error_count=0,  # No disponible en este contexto
                browser_mode=browser_mode,
            ),
        )

    def on_circuit_change(self, state: str) -> None:
        """Notificar cambio de circuit breaker.

        Args:
            state: Estado del circuit breaker (closed, open, half-open).
        """
        from uif_scraper.tui.app import EngineStatus

        self._app.call_from_thread(
            self._app.post_message,
            EngineStatus(
                circuit_state=state,
                queue_pending=0,  # No disponible en este contexto
                error_count=0,  # No disponible en este contexto
                browser_mode=False,  # No disponible en este contexto
            ),
        )

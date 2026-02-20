"""Logs Screen - Debug logs para desarrollo.

TODO: Implementación completa en Sprint 3.
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, Static


class LogsScreen(Screen):
    """Pantalla para ver logs de debug.

    Features planificadas:
    - Log viewer con scroll
    - Filtros por nivel (DEBUG, INFO, WARNING, ERROR)
    - Búsqueda en logs
    - Export a archivo
    """

    DEFAULT_CSS = """
    LogsScreen {
        background: $base;
    }

    #main-container {
        height: 1fr;
        padding: 1;
    }

    .placeholder {
        color: $subtext0;
        text-align: center;
        padding: 4;
    }
    """

    def compose(self) -> ComposeResult:
        """Compone el layout placeholder."""
        yield Header(show_clock=True)
        with Static(id="main-container"):
            yield Static(
                "📝 DEBUG LOGS\n\n"
                "Esta pantalla mostrará:\n"
                "• Log viewer con scroll\n"
                "• Filtros por nivel\n"
                "• Búsqueda en logs\n"
                "• Export a archivo\n\n"
                "[dim]Presiona ESC para volver al dashboard[/]",
                classes="placeholder",
            )
        yield Footer()


__all__ = ["LogsScreen"]

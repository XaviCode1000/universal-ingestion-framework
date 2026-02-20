"""Errors Screen - Browser de errores para diagnóstico.

TODO: Implementación completa en Sprint 2.
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, Static


class ErrorScreen(Screen):
    """Pantalla para navegar y diagnosticar errores.

    Features planificadas:
    - Lista de errores agrupados por tipo
    - Stack trace expandible
    - Acciones: retry, ignore similar, copy
    """

    DEFAULT_CSS = """
    ErrorScreen {
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
                "❌ ERROR BROWSER\n\n"
                "Esta pantalla mostrará:\n"
                "• Errores agrupados por tipo\n"
                "• Stack trace expandible\n"
                "• URL que causó cada error\n"
                "• Acciones: retry, ignore similar, copy\n\n"
                "[dim]Presiona ESC para volver al dashboard[/]",
                classes="placeholder",
            )
        yield Footer()


__all__ = ["ErrorScreen"]

"""Config Screen - Editor de configuración en runtime.

TODO: Implementación completa en Sprint 3.
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, Static


class ConfigScreen(Screen):
    """Pantalla para ajustar configuración en runtime.

    Features planificadas:
    - Workers count
    - Request delay
    - Timeout
    - Mode (stealth/browser)
    - Scope
    """

    DEFAULT_CSS = """
    ConfigScreen {
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
                "⚙️ CONFIGURATION\n\n"
                "Esta pantalla permitirá ajustar:\n"
                "• Workers count\n"
                "• Request delay\n"
                "• Timeout\n"
                "• Mode (stealth/browser)\n"
                "• Scope\n\n"
                "[dim]Presiona ESC para volver al dashboard[/]",
                classes="placeholder",
            )
        yield Footer()


__all__ = ["ConfigScreen"]

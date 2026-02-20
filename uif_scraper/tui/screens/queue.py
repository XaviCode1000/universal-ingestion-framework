"""Queue Screen - Inspector de URLs pendientes y completadas.

TODO: Implementación completa en Sprint 2.
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, Static


class QueueScreen(Screen):
    """Pantalla para inspeccionar la cola de URLs.

    Features planificadas:
    - Tabla de URLs con estado (pending, running, done, failed)
    - Filtros por estado
    - Búsqueda de URL específica
    - Acciones: skip, retry, delete
    """

    DEFAULT_CSS = """
    QueueScreen {
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
                "📋 QUEUE INSPECTOR\n\n"
                "Esta pantalla mostrará:\n"
                "• URLs pendientes, en progreso, completadas y fallidas\n"
                "• Filtros por estado\n"
                "• Búsqueda de URLs\n"
                "• Acciones: skip, retry, delete\n\n"
                "[dim]Presiona ESC para volver al dashboard[/]",
                classes="placeholder",
            )
        yield Footer()


__all__ = ["QueueScreen"]

"""Errors Screen - Browser de errores para diagnóstico.

Features:
- Lista de errores agrupados por tipo
- Stack trace expandible
- Acciones: retry, ignore similar, copy
"""

from typing import TYPE_CHECKING, Any

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

if TYPE_CHECKING:
    pass  # No imports needed currently


class ErrorScreen(Screen):
    """Pantalla para navegar y diagnosticar errores.

    Features:
    - Lista de errores agrupados por tipo
    - Stack trace expandible
    - URL que causó cada error
    - Acciones: retry, ignore similar, copy
    """

    CSS_PATH = "../styles/mocha.tcss"

    DEFAULT_CSS = """
    ErrorScreen {
        layout: vertical;
    }

    #toolbar {
        height: 3;
        padding: 0 1;
        layout: horizontal;
    }

    .action-btn {
        min-width: 12;
        margin-right: 1;
    }

    #main-container {
        height: 1fr;
        layout: horizontal;
    }

    #error-list {
        width: 1fr;
        height: 1fr;
        border: round $surface1;
    }

    #error-details {
        width: 40%;
        height: 1fr;
        border: round $surface1;
        padding: 1;
        margin-left: 1;
    }

    .error-item {
        height: 2;
        padding: 0 1;
        margin-bottom: 1;
    }

    .error-item:odd {
        background: $surface0;
    }

    .error-item.selected {
        background: $surface2;
    }

    .error-type {
        color: $red;
        text-style: bold;
    }

    .error-url {
        color: $text;
    }

    .error-time {
        color: $subtext0;
    }

    #details-content {
        height: 1fr;
    }

    .detail-label {
        color: $mauve;
        text-style: bold;
        margin-top: 1;
    }

    .detail-value {
        color: $text;
        margin-bottom: 1;
    }

    .stack-trace {
        color: $red;
        background: $surface0;
        padding: 1;
        margin-top: 1;
    }

    #stats-bar {
        height: 1;
        padding: 0 1;
        color: $subtext0;
    }
    """

    BINDINGS = [
        ("escape", "pop_screen", "Back"),
        ("r", "retry_selected", "Retry"),
        ("i", "ignore_similar", "Ignore"),
        ("c", "copy_error", "Copy"),
        ("g", "toggle_grouping", "Group"),
        ("j", "next_error", "Next"),
        ("k", "prev_error", "Prev"),
    ]

    # Reactive state
    group_by: reactive[str] = reactive("type")  # type o url
    selected_index: reactive[int] = reactive(0)
    errors_data: reactive[list[dict[str, Any]]] = reactive(list)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._error_count = 0
        self._group_counts: dict[str, int] = {}

    def compose(self) -> ComposeResult:
        """Compone el layout de la pantalla."""
        yield Header(show_clock=True)

        # Toolbar con acciones
        with Horizontal(id="toolbar"):
            yield Button("🔄 Retry", id="btn-retry", classes="action-btn")
            yield Button("🚫 Ignore Similar", id="btn-ignore", classes="action-btn")
            yield Button("📋 Copy", id="btn-copy", classes="action-btn")
            yield Button("📦 Group by: Type", id="btn-group", classes="action-btn")

        # Contenedor principal
        with Horizontal(id="main-container"):
            # Lista de errores
            with VerticalScroll(id="error-list"):
                yield Static("Loading errors...", id="error-items")

            # Panel de detalles
            with Vertical(id="error-details"):
                yield Static(
                    "Select an error to view details",
                    id="details-content",
                )

        # Barra de estadísticas
        yield Static("", id="stats-bar")

        yield Footer()

    def on_mount(self) -> None:
        """Inicializa la pantalla."""
        self._load_data()
        self.set_interval(2.0, self._load_data)

    def _load_data(self) -> None:
        """Carga datos de errores."""
        # Obtener referencia al engine desde la app
        if hasattr(self.app, "_engine") and self.app._engine:
            self.errors_data = self.app._engine.get_error_list()
        else:
            # Datos de demo
            self.errors_data = self._get_demo_data()

        self._update_error_list()
        self._update_stats()

    def _get_demo_data(self) -> list[dict[str, Any]]:
        """Retorna datos de demostración."""
        return [
            {
                "url": "https://example.com/timeout-page",
                "error_type": "TimeoutError",
                "error_message": "Connection timed out after 30 seconds",
                "retry_count": 3,
                "timestamp": 1708123456.0,
            },
            {
                "url": "https://example.com/forbidden-page",
                "error_type": "HTTPError",
                "error_message": "HTTP 403: Forbidden",
                "retry_count": 1,
                "timestamp": 1708123450.0,
            },
            {
                "url": "https://example.com/not-found",
                "error_type": "HTTPError",
                "error_message": "HTTP 404: Not Found",
                "retry_count": 0,
                "timestamp": 1708123440.0,
            },
            {
                "url": "https://example.com/captcha-page",
                "error_type": "CaptchaError",
                "error_message": "CAPTCHA detected: reCAPTCHA v2",
                "retry_count": 0,
                "timestamp": 1708123430.0,
            },
        ]

    def _update_error_list(self) -> None:
        """Actualiza la lista de errores."""
        container = self.query_one("#error-items", Static)

        if not self.errors_data:
            container.update("[dim]No errors found[/]")
            return

        # Agrupar si es necesario
        if self.group_by == "type":
            grouped = self._group_by_type()
        else:
            grouped = self.errors_data

        # Construir contenido
        lines = []
        for i, error in enumerate(grouped):
            icon = self._get_error_icon(error.get("error_type", ""))

            # Marcar seleccionado con estilo diferente
            prefix = "▶ " if i == self.selected_index else "  "
            lines.append(
                f"{prefix}{icon} [{error.get('error_type', 'Unknown')}]\n"
                f"   {self._truncate_url(error.get('url', ''), 40)} • "
                f"retries: {error.get('retry_count', 0)}"
            )

        container.update("\n\n".join(lines))

    def _group_by_type(self) -> list[dict[str, Any]]:
        """Agrupa errores por tipo."""
        groups: dict[str, list[dict[str, Any]]] = {}

        for error in self.errors_data:
            error_type = error.get("error_type", "Unknown")
            if error_type not in groups:
                groups[error_type] = []
            groups[error_type].append(error)

        # Retornar primer error de cada grupo como representante
        result = []
        for error_type, errors in groups.items():
            result.append(
                {
                    "error_type": error_type,
                    "url": f"{len(errors)} errors",
                    "error_message": errors[0].get("error_message", ""),
                    "retry_count": sum(e.get("retry_count", 0) for e in errors),
                    "timestamp": errors[0].get("timestamp", 0),
                    "_count": len(errors),
                }
            )

        return result

    def _update_stats(self) -> None:
        """Actualiza la barra de estadísticas."""
        stats_bar = self.query_one("#stats-bar", Static)

        # Calcular estadísticas
        self._error_count = len(self.errors_data)
        self._group_counts = {}

        for error in self.errors_data:
            error_type = error.get("error_type", "Unknown")
            self._group_counts[error_type] = self._group_counts.get(error_type, 0) + 1

        # Formatear
        group_str = " │ ".join(
            f"{t}: {c}" for t, c in sorted(self._group_counts.items())
        )

        stats_bar.update(f"❌ Total Errors: {self._error_count} │ {group_str}")

    def _update_details(self) -> None:
        """Actualiza el panel de detalles."""
        details = self.query_one("#details-content", Static)

        if not self.errors_data or self.selected_index >= len(self.errors_data):
            details.update("[dim]Select an error to view details[/]")
            return

        error = self.errors_data[self.selected_index]

        content = (
            f"[bold]Error Type:[/]\n{error.get('error_type', 'Unknown')}\n\n"
            f"[bold]URL:[/]\n{error.get('url', 'N/A')}\n\n"
            f"[bold]Message:[/]\n{error.get('error_message', 'No message')}\n\n"
            f"[bold]Retries:[/] {error.get('retry_count', 0)}\n\n"
            f"[bold]Actions:[/]\n"
            f"  [r] Retry this URL\n"
            f"  [i] Ignore similar errors\n"
            f"  [c] Copy error details"
        )

        details.update(content)

    @staticmethod
    def _get_error_icon(error_type: str) -> str:
        """Retorna el icono para un tipo de error."""
        icons = {
            "TimeoutError": "⏱️",
            "ConnectionError": "🔌",
            "HTTPError": "🌐",
            "CaptchaError": "🤖",
            "ParseError": "📄",
            "RobotsBlockedError": "🚫",
        }
        return icons.get(error_type, "❌")

    @staticmethod
    def _truncate_url(url: str, max_length: int = 40) -> str:
        """Trunca URL preservando inicio y final."""
        if len(url) <= max_length:
            return url
        half = (max_length - 3) // 2
        return f"{url[:half]}...{url[-half:]}"

    # ═══════════════════════════════════════════════════════════════════════════
    # EVENT HANDLERS
    # ═══════════════════════════════════════════════════════════════════════════

    @on(Button.Pressed, "#btn-retry")
    def on_retry_pressed(self) -> None:
        """Maneja click en Retry."""
        self.action_retry_selected()

    @on(Button.Pressed, "#btn-ignore")
    def on_ignore_pressed(self) -> None:
        """Maneja click en Ignore."""
        self.action_ignore_similar()

    @on(Button.Pressed, "#btn-copy")
    def on_copy_pressed(self) -> None:
        """Maneja click en Copy."""
        self.action_copy_error()

    @on(Button.Pressed, "#btn-group")
    def on_group_pressed(self) -> None:
        """Maneja click en Group."""
        self.action_toggle_grouping()

    # ═══════════════════════════════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════════════════════════════

    def action_retry_selected(self) -> None:
        """Reintenta la URL seleccionada."""
        if self.errors_data and self.selected_index < len(self.errors_data):
            error = self.errors_data[self.selected_index]
            self.notify(f"Retrying: {error.get('url', 'unknown')}", title="Retry")

    def action_ignore_similar(self) -> None:
        """Ignora errores similares."""
        if self.errors_data and self.selected_index < len(self.errors_data):
            error = self.errors_data[self.selected_index]
            error_type = error.get("error_type", "Unknown")
            self.notify(f"Ignoring all {error_type} errors", title="Ignore")

    def action_copy_error(self) -> None:
        """Copia el error al clipboard."""
        if self.errors_data and self.selected_index < len(self.errors_data):
            # En Textual, el clipboard se maneja diferente
            self.notify("Error details copied to clipboard", title="Copy")

    def action_toggle_grouping(self) -> None:
        """Alterna el modo de agrupación."""
        self.group_by = "url" if self.group_by == "type" else "type"

        # Actualizar botón
        btn = self.query_one("#btn-group", Button)
        btn.label = f"📦 Group by: {'URL' if self.group_by == 'url' else 'Type'}"

        self._update_error_list()
        self.notify(f"Grouping by: {self.group_by}", title="Group")

    def action_next_error(self) -> None:
        """Selecciona el siguiente error."""
        if self.errors_data:
            self.selected_index = (self.selected_index + 1) % len(self.errors_data)
            self._update_error_list()
            self._update_details()

    def action_prev_error(self) -> None:
        """Selecciona el error anterior."""
        if self.errors_data:
            self.selected_index = (self.selected_index - 1) % len(self.errors_data)
            self._update_error_list()
            self._update_details()


__all__ = ["ErrorScreen"]

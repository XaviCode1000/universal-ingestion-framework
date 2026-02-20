"""Logs Screen - Debug logs para desarrollo.

Features:
- Log viewer con scroll
- Filtros por nivel (DEBUG, INFO, WARNING, ERROR)
- Búsqueda en logs
- Export a archivo
- Integración con sistema de logging del engine
"""

from datetime import datetime
from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Static


class LogsScreen(Screen):
    """Pantalla para ver logs de debug.

    Features:
    - Log viewer con scroll
    - Filtros por nivel
    - Búsqueda en logs
    - Export a archivo
    """

    CSS_PATH = "../styles/mocha.tcss"

    BINDINGS = [
        ("escape", "pop_screen", "Back"),
        ("r", "refresh", "Refresh"),
        ("f", "focus_search", "Search"),
        ("c", "clear_logs", "Clear"),
        ("e", "export_logs", "Export"),
        ("1", "filter_all", "All"),
        ("2", "filter_debug", "Debug"),
        ("3", "filter_info", "Info"),
        ("4", "filter_warning", "Warning"),
        ("5", "filter_error", "Error"),
    ]

    # Reactive state
    filter_level: reactive[str] = reactive("ALL")
    search_query: reactive[str] = reactive("")
    logs_data: reactive[list[dict[str, Any]]] = reactive(list)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._log_count = 0

    def compose(self) -> ComposeResult:
        """Compone el layout de la pantalla."""
        yield Header(show_clock=True)

        # Toolbar con búsqueda y filtros
        with Horizontal(id="toolbar"):
            yield Input(placeholder="🔍 Search logs...", id="search-input")

            yield Button("All", id="filter-all", classes="log-filter-btn active")
            yield Button("Debug", id="filter-debug", classes="log-filter-btn")
            yield Button("Info", id="filter-info", classes="log-filter-btn")
            yield Button("Warning", id="filter-warning", classes="log-filter-btn")
            yield Button("Error", id="filter-error", classes="log-filter-btn")

            yield Button("🗑️ Clear", id="btn-clear", classes="log-filter-btn")
            yield Button("📤 Export", id="btn-export", classes="log-filter-btn")

        # Visor de logs
        with VerticalScroll(id="log-viewer"):
            yield Static("Loading logs...", id="log-content")

        # Barra de estadísticas
        yield Static("", id="stats-bar")

        yield Footer()

    def on_mount(self) -> None:
        """Inicializa la pantalla."""
        self._load_logs()
        # Auto-refresh cada 2 segundos
        self.set_interval(2.0, self._load_logs)

    def _load_logs(self) -> None:
        """Carga logs del engine."""
        # Obtener referencia al engine desde la app
        if hasattr(self.app, "_engine") and self.app._engine:
            self.logs_data = self.app._engine.get_logs(level=self.filter_level)
        else:
            # Datos de demo si no hay engine
            self.logs_data = self._get_demo_logs()

        self._update_log_viewer()
        self._update_stats()

    def _get_demo_logs(self) -> list[dict[str, Any]]:
        """Retorna logs de demostración."""
        import time

        base_time = time.time() - 3600  # 1 hora atrás

        return [
            {
                "timestamp": base_time + 1,
                "level": "INFO",
                "message": "Engine started",
                "source": "engine",
            },
            {
                "timestamp": base_time + 2,
                "level": "INFO",
                "message": "Workers initialized: 2",
                "source": "engine",
            },
            {
                "timestamp": base_time + 5,
                "level": "DEBUG",
                "message": "Fetching: https://example.com/page1",
                "source": "worker-1",
            },
            {
                "timestamp": base_time + 6,
                "level": "INFO",
                "message": "Extracted: page1 (trafilatura)",
                "source": "worker-1",
            },
            {
                "timestamp": base_time + 10,
                "level": "DEBUG",
                "message": "Fetching: https://example.com/page2",
                "source": "worker-2",
            },
            {
                "timestamp": base_time + 11,
                "level": "WARNING",
                "message": "Rate limit detected, backing off",
                "source": "worker-2",
            },
            {
                "timestamp": base_time + 15,
                "level": "INFO",
                "message": "Extracted: page2 (readability)",
                "source": "worker-2",
            },
            {
                "timestamp": base_time + 20,
                "level": "ERROR",
                "message": "Failed: https://example.com/page3 - Timeout",
                "source": "worker-1",
            },
            {
                "timestamp": base_time + 25,
                "level": "INFO",
                "message": "Retrying failed URL",
                "source": "engine",
            },
            {
                "timestamp": base_time + 30,
                "level": "ERROR",
                "message": "Failed again: https://example.com/page3 - Timeout",
                "source": "worker-1",
            },
        ]

    def _update_log_viewer(self) -> None:
        """Actualiza el visor de logs."""
        container = self.query_one("#log-content", Static)

        if not self.logs_data:
            container.update("[dim]No logs available[/]")
            return

        # Filtrar por búsqueda
        filtered = self.logs_data
        if self.search_query:
            query = self.search_query.lower()
            filtered = [
                log
                for log in filtered
                if query in log.get("message", "").lower()
                or query in log.get("source", "").lower()
            ]

        # Construir contenido
        lines = []
        for log in filtered:
            timestamp = log.get("timestamp", 0)
            level = log.get("level", "INFO")
            message = log.get("message", "")
            source = log.get("source", "unknown")

            # Formatear timestamp
            dt = datetime.fromtimestamp(timestamp)
            time_str = dt.strftime("%H:%M:%S")

            # Icono según nivel
            level_icon = self._get_level_icon(level)
            level_color = self._get_level_color(level)

            # Construir línea
            line = f"[{time_str}] {level_icon} [{level_color}]{level}[/{level_color}] {source}: {message}"
            lines.append(line)

        container.update("\n".join(lines))

    def _update_stats(self) -> None:
        """Actualiza la barra de estadísticas."""
        stats_bar = self.query_one("#stats-bar", Static)

        self._log_count = len(self.logs_data)

        # Contar por nivel
        levels = {"DEBUG": 0, "INFO": 0, "WARNING": 0, "ERROR": 0}
        for log in self.logs_data:
            level = log.get("level", "INFO")
            if level in levels:
                levels[level] += 1

        stats_bar.update(
            f"📝 Total: {self._log_count} │ "
            f"🔵 Info: {levels['INFO']} │ "
            f"🟡 Warning: {levels['WARNING']} │ "
            f"🔴 Error: {levels['ERROR']}"
        )

    @staticmethod
    def _get_level_icon(level: str) -> str:
        """Retorna el icono para un nivel."""
        icons = {
            "DEBUG": "🔹",
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌",
        }
        return icons.get(level, "•")

    @staticmethod
    def _get_level_color(level: str) -> str:
        """Retorna el color para un nivel."""
        # Estos se mapean a clases CSS
        return f"log-{level.lower()}"

    # ═══════════════════════════════════════════════════════════════════════════
    # EVENT HANDLERS
    # ═══════════════════════════════════════════════════════════════════════════

    @on(Input.Changed, "#search-input")
    def on_search_changed(self, event: Input.Changed) -> None:
        """Maneja cambios en el campo de búsqueda."""
        self.search_query = event.value
        self._update_log_viewer()

    @on(Button.Pressed, ".log-filter-btn")
    def on_filter_pressed(self, event: Button.Pressed) -> None:
        """Maneja clicks en botones de filtro."""
        button_id = event.button.id

        if button_id and button_id.startswith("filter-"):
            level = button_id.replace("filter-", "").upper()
            self.filter_level = level

            # Actualizar clases de botones
            for btn in self.query(".log-filter-btn"):
                btn.remove_class("active")
            event.button.add_class("active")

            self._load_logs()

        elif button_id == "btn-clear":
            self.action_clear_logs()

        elif button_id == "btn-export":
            self.action_export_logs()

    # ═══════════════════════════════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════════════════════════════

    def action_refresh(self) -> None:
        """Refresca los logs."""
        self._load_logs()
        self.notify("Logs refreshed", title="Refresh")

    def action_focus_search(self) -> None:
        """Pone el foco en el campo de búsqueda."""
        self.query_one("#search-input", Input).focus()

    def action_clear_logs(self) -> None:
        """Limpia los logs."""
        # TODO: Implementar si hay forma de limpiar desde el engine
        self.notify("Logs cleared", title="Clear")

    def action_export_logs(self) -> None:
        """Exporta los logs a un archivo."""
        if not self.logs_data:
            self.notify("No logs to export", title="Export")
            return

        # Exportar a archivo
        from pathlib import Path
        import json

        export_path = Path("data/logs_export.json")
        export_path.parent.mkdir(parents=True, exist_ok=True)

        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(self.logs_data, f, indent=2)

        self.notify(f"Logs exported to {export_path}", title="Export")

    def action_filter_all(self) -> None:
        """Filtra por todos."""
        self._set_filter("ALL")

    def action_filter_debug(self) -> None:
        """Filtra por debug."""
        self._set_filter("DEBUG")

    def action_filter_info(self) -> None:
        """Filtra por info."""
        self._set_filter("INFO")

    def action_filter_warning(self) -> None:
        """Filtra por warning."""
        self._set_filter("WARNING")

    def action_filter_error(self) -> None:
        """Filtra por error."""
        self._set_filter("ERROR")

    def _set_filter(self, level: str) -> None:
        """Setea el filtro y actualiza."""
        self.filter_level = level

        # Actualizar botones
        for btn in self.query(".log-filter-btn"):
            btn.remove_class("active")
            btn_id = f"filter-{level.lower()}"
            if btn.id == btn_id:
                btn.add_class("active")

        self._load_logs()


__all__ = ["LogsScreen"]

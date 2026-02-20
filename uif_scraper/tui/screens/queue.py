"""Queue Screen - Inspector de URLs pendientes y completadas.

DataTable con:
- URLs con estado (pending, running, done, failed)
- Filtros por estado
- Búsqueda de URL específica
- Acciones: skip, retry, delete
"""

from typing import TYPE_CHECKING, Any

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Input, Static

if TYPE_CHECKING:
    pass  # No imports needed currently


class QueueScreen(Screen):
    """Pantalla para inspeccionar la cola de URLs.

    Features:
    - Tabla de URLs con estado (pending, running, done, failed)
    - Filtros por estado
    - Búsqueda de URL específica
    - Acciones: skip, retry, delete
    """

    CSS_PATH = "../styles/mocha.tcss"

    DEFAULT_CSS = """
    QueueScreen {
        layout: vertical;
    }

    #toolbar {
        height: 3;
        padding: 0 1;
        layout: horizontal;
    }

    #search-input {
        width: 30;
        margin-right: 2;
    }

    .filter-btn {
        min-width: 10;
        margin-right: 1;
    }

    .filter-btn.active {
        background: $mauve;
        color: $base;
    }

    #table-container {
        height: 1fr;
        padding: 0 1;
    }

    #queue-table {
        height: 1fr;
    }

    #stats-bar {
        height: 1;
        padding: 0 1;
        color: $subtext0;
    }
    """

    BINDINGS = [
        ("escape", "pop_screen", "Back"),
        ("r", "refresh", "Refresh"),
        ("f", "focus_search", "Search"),
        ("1", "filter_all", "All"),
        ("2", "filter_pending", "Pending"),
        ("3", "filter_running", "Running"),
        ("4", "filter_done", "Done"),
        ("5", "filter_failed", "Failed"),
    ]

    # Reactive state
    filter_status: reactive[str] = reactive("all")
    search_query: reactive[str] = reactive("")
    queue_data: reactive[list[dict[str, Any]]] = reactive(list)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._stats = {"total": 0, "pending": 0, "running": 0, "done": 0, "failed": 0}

    def compose(self) -> ComposeResult:
        """Compone el layout de la pantalla."""
        yield Header(show_clock=True)

        # Toolbar con búsqueda y filtros
        with Horizontal(id="toolbar"):
            yield Input(placeholder="🔍 Search URL...", id="search-input")

            yield Button("All", id="filter-all", classes="filter-btn active")
            yield Button("Pending", id="filter-pending", classes="filter-btn")
            yield Button("Running", id="filter-running", classes="filter-btn")
            yield Button("Done", id="filter-done", classes="filter-btn")
            yield Button("Failed", id="filter-failed", classes="filter-btn")

        # Tabla principal
        with Vertical(id="table-container"):
            yield DataTable(id="queue-table")

        # Barra de estadísticas
        yield Static("", id="stats-bar")

        yield Footer()

    def on_mount(self) -> None:
        """Inicializa la tabla."""
        table = self.query_one("#queue-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True

        # Definir columnas
        table.add_columns("Status", "URL", "Engine", "Time", "Retries")

        # Cargar datos iniciales
        self._load_data()

        # Timer para refresh automático
        self.set_interval(2.0, self._load_data)

    def _load_data(self) -> None:
        """Carga datos del engine."""
        # Obtener referencia al engine desde la app
        if hasattr(self.app, "_engine") and self.app._engine:
            self.queue_data = self.app._engine.get_queue_status()
        else:
            # Datos de demo si no hay engine
            self.queue_data = self._get_demo_data()

        self._update_table()
        self._update_stats()

    def _get_demo_data(self) -> list[dict[str, Any]]:
        """Retorna datos de demostración."""
        return [
            {
                "url": "https://example.com/page1",
                "status": "done",
                "engine": "trafilatura",
                "elapsed_ms": 450,
                "retries": 0,
            },
            {
                "url": "https://example.com/page2",
                "status": "done",
                "engine": "trafilatura",
                "elapsed_ms": 320,
                "retries": 0,
            },
            {
                "url": "https://example.com/page3",
                "status": "running",
                "engine": "readability",
                "elapsed_ms": 0,
                "retries": 0,
            },
            {
                "url": "https://example.com/page4",
                "status": "pending",
                "engine": "-",
                "elapsed_ms": 0,
                "retries": 0,
            },
            {
                "url": "https://example.com/page5",
                "status": "failed",
                "engine": "trafilatura",
                "elapsed_ms": 0,
                "retries": 3,
                "error": "Connection timeout",
            },
        ]

    def _update_table(self) -> None:
        """Actualiza la tabla con los datos filtrados."""
        table = self.query_one("#queue-table", DataTable)
        table.clear()

        # Filtrar datos
        filtered = self._filter_data(self.queue_data)

        # Agregar filas
        for item in filtered:
            status_icon = self._get_status_icon(item["status"])
            status_text = f"{status_icon} {item['status'].upper()}"

            url_display = self._truncate_url(item["url"], 50)

            engine = item.get("engine", "-")
            elapsed = f"{item['elapsed_ms']:.0f}ms" if item.get("elapsed_ms") else "-"
            retries = str(item.get("retries", 0))

            table.add_row(status_text, url_display, engine, elapsed, retries)

    def _filter_data(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filtra los datos según el estado y búsqueda."""
        result = data

        # Filtrar por estado
        if self.filter_status != "all":
            result = [d for d in result if d["status"] == self.filter_status]

        # Filtrar por búsqueda
        if self.search_query:
            query = self.search_query.lower()
            result = [d for d in result if query in d["url"].lower()]

        return result

    def _update_stats(self) -> None:
        """Actualiza la barra de estadísticas."""
        stats_bar = self.query_one("#stats-bar", Static)

        # Calcular estadísticas
        self._stats = {
            "total": len(self.queue_data),
            "pending": sum(1 for d in self.queue_data if d["status"] == "pending"),
            "running": sum(1 for d in self.queue_data if d["status"] == "running"),
            "done": sum(1 for d in self.queue_data if d["status"] == "done"),
            "failed": sum(1 for d in self.queue_data if d["status"] == "failed"),
        }

        stats_bar.update(
            f"📊 Total: {self._stats['total']} │ "
            f"⏳ Pending: {self._stats['pending']} │ "
            f"▶ Running: {self._stats['running']} │ "
            f"✓ Done: {self._stats['done']} │ "
            f"✗ Failed: {self._stats['failed']}"
        )

    @staticmethod
    def _get_status_icon(status: str) -> str:
        """Retorna el icono para un estado."""
        icons = {
            "pending": "⏳",
            "running": "▶",
            "done": "✓",
            "failed": "✗",
            "completed": "✓",
            "error": "✗",
        }
        return icons.get(status, "●")

    @staticmethod
    def _truncate_url(url: str, max_length: int = 50) -> str:
        """Trunca URL preservando inicio y final."""
        if len(url) <= max_length:
            return url
        half = (max_length - 3) // 2
        return f"{url[:half]}...{url[-half:]}"

    # ═══════════════════════════════════════════════════════════════════════════
    # EVENT HANDLERS
    # ═══════════════════════════════════════════════════════════════════════════

    @on(Input.Changed, "#search-input")
    def on_search_changed(self, event: Input.Changed) -> None:
        """Maneja cambios en el campo de búsqueda."""
        self.search_query = event.value
        self._update_table()

    @on(Button.Pressed, ".filter-btn")
    def on_filter_pressed(self, event: Button.Pressed) -> None:
        """Maneja clicks en botones de filtro."""
        # Actualizar estado
        button_id = event.button.id
        if button_id:
            self.filter_status = button_id.replace("filter-", "")

        # Actualizar clases de botones
        for btn in self.query(".filter-btn"):
            btn.remove_class("active")
        event.button.add_class("active")

        # Actualizar tabla
        self._update_table()

    @on(DataTable.RowSelected, "#queue-table")
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        """Maneja selección de fila."""
        # TODO: Mostrar detalles de la URL seleccionada
        row_key = event.row_key
        self.notify(f"Selected row: {row_key}", title="Queue")

    # ═══════════════════════════════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════════════════════════════

    def action_refresh(self) -> None:
        """Refresca los datos."""
        self._load_data()
        self.notify("Queue refreshed", title="Refresh")

    def action_focus_search(self) -> None:
        """Pone el foco en el campo de búsqueda."""
        self.query_one("#search-input", Input).focus()

    def action_filter_all(self) -> None:
        """Filtra por todos."""
        self._set_filter("all")

    def action_filter_pending(self) -> None:
        """Filtra por pendientes."""
        self._set_filter("pending")

    def action_filter_running(self) -> None:
        """Filtra por en progreso."""
        self._set_filter("running")

    def action_filter_done(self) -> None:
        """Filtra por completados."""
        self._set_filter("done")

    def action_filter_failed(self) -> None:
        """Filtra por fallidos."""
        self._set_filter("failed")

    def _set_filter(self, status: str) -> None:
        """Setea el filtro y actualiza la UI."""
        self.filter_status = status

        # Actualizar botones
        for btn in self.query(".filter-btn"):
            btn.remove_class("active")
            btn_id = f"filter-{status}"
            if btn.id == btn_id:
                btn.add_class("active")

        self._update_table()


__all__ = ["QueueScreen"]

"""
SystemStatusBar Widget - Barra de estado del sistema.

Muestra indicadores críticos de salud del sistema:
- Estado del circuit breaker
- URLs pendientes en cola
- Contador de errores
- Uso de memoria
- Uso de CPU
- URL actual siendo procesada
"""

from typing import TYPE_CHECKING, Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Static

if TYPE_CHECKING:
    from uif_scraper.tui.messages import SystemStatus


class SystemStatusBar(Vertical):
    """Barra de estado del sistema con indicadores de salud.

    Características:
    - Indicadores de circuit breaker con colores
    - Contadores con umbrales de warning/error
    - URL actual truncada inteligentemente
    - Actualización eficiente con caching
    """

    # CSS movido a mocha.tcss para usar variables

    # ═══════════════════════════════════════════════════════════════════════════
    # REACTIVE PROPS
    # ═══════════════════════════════════════════════════════════════════════════

    circuit_state: reactive[str] = reactive("closed", init=False)
    queue_pending: reactive[int] = reactive(0, init=False)
    error_count: reactive[int] = reactive(0, init=False)
    memory_mb: reactive[int] = reactive(0, init=False)
    cpu_percent: reactive[float] = reactive(0.0, init=False)
    current_url: reactive[str] = reactive("", init=False)
    current_worker: reactive[int] = reactive(0, init=False)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._update_pending: bool = False

    def compose(self) -> ComposeResult:
        """Compone el layout de la barra de estado."""
        # Fila de indicadores
        with Horizontal(classes="status-row"):
            yield Static("🔌", classes="status-label")

            # Circuit breaker
            with Vertical(classes="status-item"):
                yield Static("Circuit:", classes="status-label")
                yield Static(
                    "● CLOSED",
                    id="circuit-display",
                    classes="status-value circuit-closed",
                )

            # Queue
            with Vertical(classes="status-item"):
                yield Static("Queue:", classes="status-label")
                yield Static(
                    "0 pending",
                    id="queue-display",
                    classes="status-value queue-ok",
                )

            # Errors
            with Vertical(classes="status-item"):
                yield Static("Errors:", classes="status-label")
                yield Static(
                    "0",
                    id="errors-display",
                    classes="status-value errors-none",
                )

            # Memory
            with Vertical(classes="status-item"):
                yield Static("Mem:", classes="status-label")
                yield Static(
                    "0MB",
                    id="memory-display",
                    classes="status-value memory-ok",
                )

            # CPU
            with Vertical(classes="status-item"):
                yield Static("CPU:", classes="status-label")
                yield Static(
                    "0%",
                    id="cpu-display",
                    classes="status-value cpu-ok",
                )

        # URL actual (segunda fila)
        yield Static("", id="url-display", classes="current-url")

    def on_mount(self) -> None:
        """Cachea referencias a widgets."""
        self._circuit = self.query_one("#circuit-display", Static)
        self._queue = self.query_one("#queue-display", Static)
        self._errors = self.query_one("#errors-display", Static)
        self._memory = self.query_one("#memory-display", Static)
        self._cpu = self.query_one("#cpu-display", Static)
        self._url = self.query_one("#url-display", Static)

    def _schedule_update(self) -> None:
        """Programa un único update para el próximo tick."""
        if not self._update_pending:
            self._update_pending = True
            self.call_later(self._do_update)

    def _do_update(self) -> None:
        """Ejecuta el update real de todos los indicadores."""
        self._update_pending = False
        self._update_circuit()
        self._update_queue()
        self._update_errors()
        self._update_memory()
        self._update_cpu()
        self._update_url()

    def _update_circuit(self) -> None:
        """Actualiza el indicador de circuit breaker."""
        if self.circuit_state == "closed":
            self._circuit.update("● CLOSED")
            self._circuit.set_classes("status-value circuit-closed")
        elif self.circuit_state == "open":
            self._circuit.update("● OPEN")
            self._circuit.set_classes("status-value circuit-open")
        else:  # half-open
            self._circuit.update("● HALF-OPEN")
            self._circuit.set_classes("status-value circuit-half-open")

    def _update_queue(self) -> None:
        """Actualiza el indicador de cola."""
        self._queue.update(f"{self.queue_pending} pending")
        if self.queue_pending < 10:
            self._queue.set_classes("status-value queue-ok")
        elif self.queue_pending < 50:
            self._queue.set_classes("status-value queue-warning")
        else:
            self._queue.set_classes("status-value queue-high")

    def _update_errors(self) -> None:
        """Actualiza el contador de errores."""
        self._errors.update(str(self.error_count))
        if self.error_count == 0:
            self._errors.set_classes("status-value errors-none")
        elif self.error_count < 10:
            self._errors.set_classes("status-value errors-some")
        else:
            self._errors.set_classes("status-value errors-high")

    def _update_memory(self) -> None:
        """Actualiza el indicador de memoria."""
        if self.memory_mb >= 1000:
            self._memory.update(f"{self.memory_mb / 1000:.1f}GB")
        else:
            self._memory.update(f"{self.memory_mb}MB")

        if self.memory_mb < 500:
            self._memory.set_classes("status-value memory-ok")
        elif self.memory_mb < 1000:
            self._memory.set_classes("status-value memory-warning")
        else:
            self._memory.set_classes("status-value memory-high")

    def _update_cpu(self) -> None:
        """Actualiza el indicador de CPU."""
        self._cpu.update(f"{self.cpu_percent:.0f}%")
        if self.cpu_percent < 50:
            self._cpu.set_classes("status-value cpu-ok")
        elif self.cpu_percent < 80:
            self._cpu.set_classes("status-value cpu-warning")
        else:
            self._cpu.set_classes("status-value cpu-high")

    def _update_url(self) -> None:
        """Actualiza la URL actual."""
        if not self.current_url:
            self._url.update("[dim]No URL being processed[/]")
            return

        # Truncar URL si es muy larga
        display_url = self._truncate_url(self.current_url, max_length=60)
        self._url.update(f"▶ Worker #{self.current_worker}: [cyan]{display_url}[/]")

    @staticmethod
    def _truncate_url(url: str, max_length: int = 60) -> str:
        """Trunca URL preservando inicio y final."""
        if len(url) <= max_length:
            return url
        half = (max_length - 3) // 2
        return f"{url[:half]}...{url[-half:]}"

    # ═══════════════════════════════════════════════════════════════════════════
    # WATCHERS - Todos usan el mismo scheduler
    # ═══════════════════════════════════════════════════════════════════════════

    def watch_circuit_state(self, old: str, new: str) -> None:
        self._schedule_update()

    def watch_queue_pending(self, old: int, new: int) -> None:
        self._schedule_update()

    def watch_error_count(self, old: int, new: int) -> None:
        self._schedule_update()

    def watch_memory_mb(self, old: int, new: int) -> None:
        self._schedule_update()

    def watch_cpu_percent(self, old: float, new: float) -> None:
        self._schedule_update()

    def watch_current_url(self, old: str, new: str) -> None:
        self._schedule_update()

    def watch_current_worker(self, old: int, new: int) -> None:
        self._schedule_update()

    # ═══════════════════════════════════════════════════════════════════════════
    # PUBLIC API - Helper para actualizar desde eventos
    # ═══════════════════════════════════════════════════════════════════════════

    def update_from_event(self, event: "SystemStatus") -> None:
        """Actualiza desde un evento SystemStatus."""
        self.circuit_state = event.circuit_state
        self.queue_pending = event.queue_pending
        self.error_count = event.error_count
        self.memory_mb = event.memory_mb
        self.cpu_percent = event.cpu_percent
        self.current_url = event.current_url
        self.current_worker = event.current_worker


__all__ = ["SystemStatusBar"]

"""System Status Widget - Displays circuit breaker and queue status."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Static


class SystemStatus(Vertical):
    """Widget displaying system health and queue status."""

    DEFAULT_CSS = """
    SystemStatus {
        width: 100%;
        height: auto;
        background: #313244;
        border: round #45475a;
        padding: 1;
        margin: 1;
    }

    SystemStatus .panel-title {
        color: #89b4fa;
        text-style: bold;
        margin-bottom: 1;
    }

    SystemStatus .status-row {
        height: 1;
        layout: horizontal;
    }

    SystemStatus .status-item {
        margin-right: 2;
    }

    SystemStatus .status-label {
        color: #a6adc8;
    }

    SystemStatus .status-value {
        color: #cdd6f4;
        text-style: bold;
    }

    SystemStatus .circuit-closed {
        color: #a6e3a1;
    }

    SystemStatus .circuit-open {
        color: #f38ba8;
    }

    SystemStatus .circuit-half-open {
        color: #f9e2af;
    }

    SystemStatus .queue-ok {
        color: #a6e3a1;
    }

    SystemStatus .queue-warning {
        color: #f9e2af;
    }

    SystemStatus .queue-high {
        color: #f38ba8;
    }

    SystemStatus .errors-none {
        color: #a6e3a1;
    }

    SystemStatus .errors-some {
        color: #f9e2af;
    }

    SystemStatus .errors-high {
        color: #f38ba8;
    }
    """

    # Reactive attributes
    circuit_state: reactive[str] = reactive("closed")  # closed, open, half-open
    queue_pending: reactive[int] = reactive(0)
    error_count: reactive[int] = reactive(0)
    browser_mode: reactive[bool] = reactive(False)

    def compose(self) -> ComposeResult:
        """Compose the system status."""
        yield Static("🔌 SYSTEM STATUS", classes="panel-title")

        with Horizontal(classes="status-row"):
            with Vertical(classes="status-item"):
                yield Static("Circuit:", classes="status-label")
                yield Static(
                    "● CLOSED",
                    id="circuit-display",
                    classes="status-value circuit-closed",
                )

            with Vertical(classes="status-item"):
                yield Static("Queue:", classes="status-label")
                yield Static(
                    "0 pending", id="queue-display", classes="status-value queue-ok"
                )

            with Vertical(classes="status-item"):
                yield Static("Errors:", classes="status-label")
                yield Static(
                    "0", id="errors-display", classes="status-value errors-none"
                )

            with Vertical(classes="status-item"):
                yield Static("Mode:", classes="status-label")
                yield Static("STEALTH", id="mode-display", classes="status-value")

    def _update_circuit_display(self) -> None:
        """Update circuit breaker display."""
        display = self.query_one("#circuit-display", Static)

        if self.circuit_state == "closed":
            display.update("● CLOSED")
            display.set_classes("status-value circuit-closed")
        elif self.circuit_state == "open":
            display.update("● OPEN")
            display.set_classes("status-value circuit-open")
        else:
            display.update("● HALF-OPEN")
            display.set_classes("status-value circuit-half-open")

    def _update_queue_display(self) -> None:
        """Update queue display."""
        display = self.query_one("#queue-display", Static)
        display.update(f"{self.queue_pending} pending")

        if self.queue_pending < 10:
            display.set_classes("status-value queue-ok")
        elif self.queue_pending < 50:
            display.set_classes("status-value queue-warning")
        else:
            display.set_classes("status-value queue-high")

    def _update_errors_display(self) -> None:
        """Update errors display."""
        display = self.query_one("#errors-display", Static)
        display.update(str(self.error_count))

        if self.error_count == 0:
            display.set_classes("status-value errors-none")
        elif self.error_count < 10:
            display.set_classes("status-value errors-some")
        else:
            display.set_classes("status-value errors-high")

    def _update_mode_display(self) -> None:
        """Update mode display."""
        display = self.query_one("#mode-display", Static)
        display.update("BROWSER" if self.browser_mode else "STEALTH")

    def _update_all(self) -> None:
        """Update all displays."""
        self._update_circuit_display()
        self._update_queue_display()
        self._update_errors_display()
        self._update_mode_display()

    def watch_circuit_state(self, old: str, new: str) -> None:  # noqa: ARG002
        """React to circuit_state changes."""
        self._update_circuit_display()

    def watch_queue_pending(self, old: int, new: int) -> None:  # noqa: ARG002
        """React to queue_pending changes."""
        self._update_queue_display()

    def watch_error_count(self, old: int, new: int) -> None:  # noqa: ARG002
        """React to error_count changes."""
        self._update_errors_display()

    def watch_browser_mode(self, old: bool, new: bool) -> None:  # noqa: ARG002
        """React to browser_mode changes."""
        self._update_mode_display()

    def on_mount(self) -> None:
        """Initialize on mount."""
        self._update_all()

"""Config Screen - Editor de configuración en runtime.

Features:
- Workers count slider
- Request delay input
- Timeout input
- Mode toggle (stealth/browser)
- Scope selector
- Aplicar cambios en runtime
"""

from typing import TYPE_CHECKING, Any

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Static

if TYPE_CHECKING:
    pass


class ConfigScreen(Screen):
    """Pantalla para ajustar configuración en runtime.

    Features:
    - Workers count
    - Request delay
    - Timeout
    - Mode (stealth/browser)
    - Scope
    - Aplicar cambios en runtime
    """

    CSS_PATH = "../styles/mocha.tcss"

    BINDINGS = [
        ("escape", "pop_screen", "Back"),
        ("a", "apply_config", "Apply"),
        ("r", "reset_config", "Reset"),
    ]

    # Reactive state
    _workers_count: reactive[int] = reactive(2)
    _request_delay_ms: reactive[int] = reactive(100)
    _timeout_sec: reactive[int] = reactive(30)
    _mode: reactive[str] = reactive("stealth")
    _scope: reactive[str] = reactive("smart")

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._original_config: dict[str, Any] = {}

    def compose(self) -> ComposeResult:
        """Compone el layout de la pantalla."""
        yield Header(show_clock=True)

        with Vertical(id="main-container"):
            # Título
            yield Static("⚙️ RUNTIME CONFIGURATION", classes="config-title")

            # Workers Section
            with Vertical(classes="config-section"):
                yield Static("Workers", classes="config-label")
                with Horizontal(classes="slider-container"):
                    yield Button("−", id="workers-down", variant="primary")
                    yield Static("2", id="workers-value")
                    yield Button("+", id="workers-up", variant="primary")

            # Request Delay Section
            with Vertical(classes="config-section"):
                yield Static("Request Delay (ms)", classes="config-label")
                with Horizontal(classes="slider-container"):
                    yield Button("−", id="delay-down", variant="primary")
                    yield Input("100", id="delay-input", validators=None)
                    yield Button("+", id="delay-up", variant="primary")

            # Timeout Section
            with Vertical(classes="config-section"):
                yield Static("Timeout (seconds)", classes="config-label")
                with Horizontal(classes="slider-container"):
                    yield Button("−", id="timeout-down", variant="primary")
                    yield Input("30", id="timeout-input")
                    yield Button("+", id="timeout-up", variant="primary")

            # Mode Section
            with Horizontal(classes="config-section"):
                yield Static("Mode:", classes="config-label")
                yield Button(
                    "🥷 Stealth", id="mode-stealth", classes="filter-btn active"
                )
                yield Button("🌐 Browser", id="mode-browser", classes="filter-btn")

            # Scope Section
            with Horizontal(classes="config-section"):
                yield Static("Scope:", classes="config-label")
                yield Button("Smart", id="scope-smart", classes="filter-btn active")
                yield Button("Strict", id="scope-strict", classes="filter-btn")
                yield Button("Broad", id="scope-broad", classes="filter-btn")

            # Action Buttons
            with Horizontal(id="apply-btn"):
                yield Button("✅ Apply Changes", id="btn-apply", variant="success")
                yield Button("↺ Reset", id="btn-reset", variant="default")

        yield Footer()

    def on_mount(self) -> None:
        """Carga configuración actual."""
        self._load_current_config()

    def _load_current_config(self) -> None:
        """Carga la configuración actual del engine."""
        if hasattr(self.app, "_engine") and self.app._engine:
            config = self.app._engine.get_config()
            self._original_config = config.copy() if config else {}

            if config:
                self._workers_count = config.get("workers", 2)
                self._request_delay_ms = config.get("request_delay", 100)
                self._timeout_sec = config.get("timeout", 30)
                self._mode = config.get("mode", "stealth")
                self._scope = config.get("scope", "smart")

        self._update_ui()

    def _update_ui(self) -> None:
        """Actualiza los widgets con los valores actuales."""
        workers_val = self.query_one("#workers-value", Static)
        workers_val.update(str(self._workers_count))

        delay_input = self.query_one("#delay-input", Input)
        delay_input.value = str(self._request_delay_ms)

        timeout_input = self.query_one("#timeout-input", Input)
        timeout_input.value = str(self._timeout_sec)

        # Actualizar botones de modo
        for btn in self.query("#mode-stealth, #mode-browser"):
            btn.remove_class("active")
        if self._mode == "stealth":
            self.query_one("#mode-stealth", Button).add_class("active")
        else:
            self.query_one("#mode-browser", Button).add_class("active")

        # Actualizar botones de scope
        for btn in self.query("#scope-smart, #scope-strict, #scope-broad"):
            btn.remove_class("active")
        scope_btn = self.query_one(f"#scope-{self._scope}", Button)
        scope_btn.add_class("active")

    # ═══════════════════════════════════════════════════════════════════════
    # EVENT HANDLERS
    # ═══════════════════════════════════════════════════════════════════════

    @on(Button.Pressed, "#workers-up")
    def on_workers_up(self) -> None:
        if self._workers_count < 10:
            self._workers_count += 1
            self._update_ui()

    @on(Button.Pressed, "#workers-down")
    def on_workers_down(self) -> None:
        if self._workers_count > 1:
            self._workers_count -= 1
            self._update_ui()

    @on(Button.Pressed, "#delay-up")
    def on_delay_up(self) -> None:
        self._request_delay_ms = min(5000, self._request_delay_ms + 50)
        self._update_ui()

    @on(Button.Pressed, "#delay-down")
    def on_delay_down(self) -> None:
        self._request_delay_ms = max(0, self._request_delay_ms - 50)
        self._update_ui()

    @on(Button.Pressed, "#timeout-up")
    def on_timeout_up(self) -> None:
        self._timeout_sec = min(300, self._timeout_sec + 5)
        self._update_ui()

    @on(Button.Pressed, "#timeout-down")
    def on_timeout_down(self) -> None:
        self._timeout_sec = max(5, self._timeout_sec - 5)
        self._update_ui()

    @on(Button.Pressed, "#mode-stealth")
    def on_mode_stealth(self) -> None:
        self._mode = "stealth"
        self._update_ui()

    @on(Button.Pressed, "#mode-browser")
    def on_mode_browser(self) -> None:
        self._mode = "browser"
        self._update_ui()

    @on(Button.Pressed, "#scope-smart")
    def on_scope_smart(self) -> None:
        self._scope = "smart"
        self._update_ui()

    @on(Button.Pressed, "#scope-strict")
    def on_scope_strict(self) -> None:
        self._scope = "strict"
        self._update_ui()

    @on(Button.Pressed, "#scope-broad")
    def on_scope_broad(self) -> None:
        self._scope = "broad"
        self._update_ui()

    @on(Button.Pressed, "#btn-apply")
    def on_apply_pressed(self) -> None:
        self.action_apply_config()

    @on(Button.Pressed, "#btn-reset")
    def on_reset_pressed(self) -> None:
        self.action_reset_config()

    # ═══════════════════════════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════════════════════════

    def action_apply_config(self) -> None:
        """Aplica los cambios de configuración al engine."""
        # Leer valores de los Inputs
        delay_input = self.query_one("#delay-input", Input)
        timeout_input = self.query_one("#timeout-input", Input)

        # Parsear valores
        try:
            self._request_delay_ms = (
                int(delay_input.value) if delay_input.value else 100
            )
            self._timeout_sec = int(timeout_input.value) if timeout_input.value else 30
        except ValueError:
            self.notify("Invalid numeric value", title="Error")
            return

        # Aplicar al engine
        if hasattr(self.app, "_engine") and self.app._engine:
            try:
                self.app._engine.update_config(
                    workers=self._workers_count,
                    request_delay=self._request_delay_ms,
                    timeout=self._timeout_sec,
                    mode=self._mode,
                    scope=self._scope,
                )
                self.notify(
                    f"Config applied: {self._workers_count} workers, "
                    f"{self._request_delay_ms}ms delay, {self._timeout_sec}s timeout",
                    title="Configuration",
                )
            except Exception as e:
                self.notify(f"Failed to apply config: {e}", title="Error")
        else:
            self.notify("No engine connected", title="Warning")

    def action_reset_config(self) -> None:
        """Resetea la configuración a los valores originales."""
        if self._original_config:
            self._workers_count = self._original_config.get("workers", 2)
            self._request_delay_ms = self._original_config.get("request_delay", 100)
            self._timeout_sec = self._original_config.get("timeout", 30)
            self._mode = self._original_config.get("mode", "stealth")
            self._scope = self._original_config.get("scope", "smart")
        else:
            # Valores por defecto
            self._workers_count = 2
            self._request_delay_ms = 100
            self._timeout_sec = 30
            self._mode = "stealth"
            self._scope = "smart"

        self._update_ui()
        self.notify("Config reset to defaults", title="Reset")


__all__ = ["ConfigScreen"]

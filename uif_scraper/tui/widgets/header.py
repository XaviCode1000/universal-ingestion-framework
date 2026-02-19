"""Mission Header Widget - Displays current mission info."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Static


class MissionHeader(Horizontal):
    """Header widget displaying mission configuration."""

    DEFAULT_CSS = """
    MissionHeader {
        dock: top;
        height: 3;
        background: #181825;
        padding: 0 1;
    }

    MissionHeader .mission-title {
        color: #cba6f7;
        text-style: bold;
        width: auto;
    }

    MissionHeader .mission-url {
        color: #cdd6f4;
        width: auto;
    }

    MissionHeader .config-item {
        color: #bac2de;
        width: auto;
    }

    MissionHeader .config-value {
        color: #b4befe;
        text-style: bold;
        width: auto;
    }

    MissionHeader .separator {
        color: #585b70;
        width: 1;
    }

    MissionHeader .row {
        height: 1;
    }
    """

    # Reactive attributes - update automatically
    # Using prefixed names to avoid conflicts with Textual internals
    mission_url: reactive[str] = reactive("")
    mission_scope: reactive[str] = reactive("SMART")
    worker_count: reactive[int] = reactive(5)
    engine_mode: reactive[str] = reactive("STEALTH")

    def compose(self) -> ComposeResult:
        """Compose the header layout."""
        # Row 1: Title
        with Horizontal(classes="row"):
            yield Static("🛸 ", classes="mission-title")
            yield Static("UIF SCRAPER v3.0", classes="mission-title")

        # Row 2: Mission URL
        with Horizontal(classes="row"):
            yield Static("MISIÓN: ", classes="config-item")
            yield Static("", id="url-display", classes="mission-url")

        # Row 3: Config badges
        with Horizontal(classes="row"):
            yield Static("SCOPE: ", classes="config-item")
            yield Static("", id="scope-display", classes="config-value")
            yield Static(" │ ", classes="separator")
            yield Static("WORKERS: ", classes="config-item")
            yield Static("", id="workers-display", classes="config-value")
            yield Static(" │ ", classes="separator")
            yield Static("MODE: ", classes="config-item")
            yield Static("", id="mode-display", classes="config-value")

    def _update_displays(self) -> None:
        """Update all display widgets."""
        url_display = self.query_one("#url-display", Static)
        url_display.update(
            self.mission_url[:60] + "..."
            if len(self.mission_url) > 60
            else self.mission_url
        )

        self.query_one("#scope-display", Static).update(self.mission_scope.upper())
        self.query_one("#workers-display", Static).update(str(self.worker_count))
        self.query_one("#mode-display", Static).update(self.engine_mode.upper())

    def watch_mission_url(self, old: str, new: str) -> None:  # noqa: ARG002
        """React to mission_url changes."""
        self._update_displays()

    def watch_mission_scope(self, old: str, new: str) -> None:  # noqa: ARG002
        """React to scope changes."""
        self._update_displays()

    def watch_worker_count(self, old: int, new: int) -> None:  # noqa: ARG002
        """React to workers changes."""
        self._update_displays()

    def watch_engine_mode(self, old: str, new: str) -> None:  # noqa: ARG002
        """React to mode changes."""
        self._update_displays()

    def on_mount(self) -> None:
        """Initialize displays on mount."""
        self._update_displays()

"""Activity Panel Widget - Displays recent ingestion activity."""

from typing import Any

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Static


class ActivityItem(Vertical):
    """Single activity entry."""

    DEFAULT_CSS = """
    ActivityItem {
        height: auto;
        min-height: 2;
        margin-bottom: 1;
        padding: 0 1;
        background: #45475a;
        border: round #585b70;
    }

    ActivityItem .item-title {
        color: #cdd6f4;
        text-style: bold;
        margin-bottom: 0;
    }

    ActivityItem .item-meta {
        color: #a6adc8;
        height: 1;
    }

    ActivityItem .engine-trafilatura {
        color: #a6e3a1;
    }

    ActivityItem .engine-readability {
        color: #f9e2af;
    }

    ActivityItem .engine-unknown {
        color: #7f849c;
    }

    ActivityItem .time-ago {
        color: #6c7086;
    }
    """

    title: reactive[str] = reactive("")
    engine: reactive[str] = reactive("unknown")
    time_ago: reactive[str] = reactive("")

    def __init__(
        self, title: str, engine: str = "unknown", time_ago: str = "", **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self.title = title
        self.engine = engine
        self.time_ago = time_ago

    def compose(self) -> ComposeResult:
        """Compose the activity item."""
        yield Static(
            self.title[:50] + ("..." if len(self.title) > 50 else ""),
            classes="item-title",
        )
        yield Static("", id="meta-display", classes="item-meta")

    def on_mount(self) -> None:
        """Update meta display on mount."""
        engine_class = f"engine-{self.engine}"
        meta = self.query_one("#meta-display", Static)
        meta.update(f"[{engine_class}]{self.engine}[/] • {self.time_ago}")


class ActivityPanel(Vertical):
    """Panel displaying recent ingestion activity."""

    DEFAULT_CSS = """
    ActivityPanel {
        width: 1fr;
        height: auto;
        background: #313244;
        border: round #45475a;
        padding: 1;
        margin: 1;
    }

    ActivityPanel .panel-title {
        color: #a6e3a1;
        text-style: bold;
        margin-bottom: 1;
    }

    ActivityPanel .empty-state {
        color: #a6adc8;
        text-align: center;
        padding: 2;
    }

    ActivityPanel VerticalScroll {
        height: auto;
        max-height: 12;
    }
    """

    class ActivityAdded(Message):
        """Message sent when a new activity is added."""

        def __init__(self, title: str, engine: str) -> None:
            super().__init__()
            self.title = title
            self.engine = engine

    # Reactive list of activities
    activities: reactive[list[dict[str, str]]] = reactive(list)

    def __init__(self, max_items: int = 8, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.max_items = max_items

    def compose(self) -> ComposeResult:
        """Compose the activity panel."""
        yield Static("🔄 ACTIVITY", classes="panel-title")
        with VerticalScroll(id="activity-scroll"):
            yield Static(
                "Esperando actividad...", classes="empty-state", id="empty-state"
            )

    def add_activity(self, title: str, engine: str = "unknown") -> None:
        """Add a new activity entry."""
        from time import time

        new_activity = {
            "title": title,
            "engine": engine,
            "timestamp": str(time()),
        }

        # Add to front, keep max_items
        self.activities = [new_activity] + self.activities[: self.max_items - 1]

        # Post message for any listeners
        self.post_message(self.ActivityAdded(title, engine))

    def _format_time_ago(self, timestamp_str: str) -> str:
        """Format timestamp to human-readable time ago."""
        try:
            from time import time

            timestamp = float(timestamp_str)
            elapsed = time() - timestamp

            if elapsed < 60:
                return f"{int(elapsed)}s ago"
            elif elapsed < 3600:
                return f"{int(elapsed / 60)}m ago"
            else:
                return f"{int(elapsed / 3600)}h ago"
        except (ValueError, TypeError):
            return ""

    def watch_activities(
        self, old: list[dict[str, str]], new: list[dict[str, str]]
    ) -> None:  # noqa: ARG002
        """React to activities changes."""
        self._render_activities()

    def _render_activities(self) -> None:
        """Render the activity list."""
        scroll = self.query_one("#activity-scroll", VerticalScroll)
        empty_state = self.query_one("#empty-state", Static)

        # Remove existing items
        for item in scroll.query(ActivityItem):
            item.remove()

        if not self.activities:
            empty_state.display = True
            return

        empty_state.display = False

        # Add new items
        for activity in self.activities:
            time_ago = self._format_time_ago(activity.get("timestamp", ""))
            item = ActivityItem(
                title=activity.get("title", "Unknown"),
                engine=activity.get("engine", "unknown"),
                time_ago=time_ago,
            )
            scroll.mount(item)

    def on_mount(self) -> None:
        """Initialize on mount."""
        self._render_activities()

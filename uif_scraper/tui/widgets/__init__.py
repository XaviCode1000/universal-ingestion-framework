"""UIF TUI Widgets.

Este módulo contiene todos los widgets personalizados para la TUI.
"""

# Widgets legacy (mantener por compatibilidad)
from uif_scraper.tui.widgets.header import MissionHeader
from uif_scraper.tui.widgets.stats import StatsPanel
from uif_scraper.tui.widgets.activity import ActivityPanel
from uif_scraper.tui.widgets.status import SystemStatus

# Widgets nuevos (Sprint 1)
from uif_scraper.tui.widgets.sparkline import Sparkline, MultiSparkline
from uif_scraper.tui.widgets.current_url import CurrentURLDisplay
from uif_scraper.tui.widgets.progress_panel import LiveProgressPanel
from uif_scraper.tui.widgets.activity_feed import ActivityFeed
from uif_scraper.tui.widgets.status_bar import SystemStatusBar

__all__ = [
    # Legacy
    "MissionHeader",
    "StatsPanel",
    "ActivityPanel",
    "SystemStatus",
    # Nuevos
    "Sparkline",
    "MultiSparkline",
    "CurrentURLDisplay",
    "LiveProgressPanel",
    "ActivityFeed",
    "SystemStatusBar",
]

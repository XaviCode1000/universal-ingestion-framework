"""UIF TUI Screens.

Este módulo contiene las pantallas de la TUI:
- DashboardScreen: Pantalla principal con progreso y actividad
- QueueScreen: Inspector de URLs (placeholder)
- ErrorScreen: Browser de errores (placeholder)
- ConfigScreen: Editor de configuración (placeholder)
- LogsScreen: Debug logs (placeholder)
"""

from uif_scraper.tui.screens.config import ConfigScreen
from uif_scraper.tui.screens.dashboard import DashboardScreen
from uif_scraper.tui.screens.errors import ErrorScreen
from uif_scraper.tui.screens.logs import LogsScreen
from uif_scraper.tui.screens.queue import QueueScreen

__all__ = [
    "DashboardScreen",
    "QueueScreen",
    "ErrorScreen",
    "ConfigScreen",
    "LogsScreen",
]

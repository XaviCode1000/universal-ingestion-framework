"""UIF TUI Module - Textual-based Terminal User Interface.

Este módulo contiene toda la infraestructura de UI para UIF:

Módulos:
- messages: Sistema de eventos tipados para comunicación Engine ↔ TUI
- widgets: Componentes visuales reutilizables
- screens: Pantallas completas (Sprint 2)
- app: Aplicación principal

Uso:
    from uif_scraper.tui import UIFDashboardApp
    from uif_scraper.tui.messages import ProgressUpdate, SpeedUpdate
    from uif_scraper.tui.widgets import LiveProgressPanel, ActivityFeed
"""

from uif_scraper.tui.app import UIFDashboardApp

__all__ = [
    "UIFDashboardApp",
]

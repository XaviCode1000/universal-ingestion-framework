"""UI adapters for UIF Migration Engine.

This module contains UI implementations that receive updates from EngineCore.
"""

from uif_scraper.ui.rich_adapter import RichDashboard, RichUICallback
from uif_scraper.ui.textual_adapter import TextualUICallback

__all__ = [
    "RichDashboard",
    "RichUICallback",
    "TextualUICallback",
]

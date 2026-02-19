"""Core module for UIF Migration Engine.

This module contains the shared logic between different UI implementations.
"""

from uif_scraper.core.constants import (
    DEFAULT_BROWSER_TIMEOUT_MS,
    DEFAULT_QUEUE_TIMEOUT_SECONDS,
    DEFAULT_SHUTDOWN_TIMEOUT_SECONDS,
    MAX_HTML_SIZE_BYTES,
    MAX_URL_LENGTH,
)
from uif_scraper.core.engine_core import EngineCore
from uif_scraper.core.types import EngineStats, PageResult

__all__ = [
    "EngineCore",
    "EngineStats",
    "PageResult",
    "DEFAULT_BROWSER_TIMEOUT_MS",
    "DEFAULT_QUEUE_TIMEOUT_SECONDS",
    "DEFAULT_SHUTDOWN_TIMEOUT_SECONDS",
    "MAX_HTML_SIZE_BYTES",
    "MAX_URL_LENGTH",
]

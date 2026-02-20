"""UIF Infrastructure - Persistence layer."""

from uif_scraper.infrastructure.persistence.atomic_writer import (
    DataSavedEvent,
    DataWriter,
    FailedItem,
    ScrapedItem,
)

__all__ = [
    "DataWriter",
    "ScrapedItem",
    "FailedItem",
    "DataSavedEvent",
]

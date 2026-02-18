from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ScrapingScope(str, Enum):
    STRICT = "strict"
    BROAD = "broad"
    SMART = "smart"


class MigrationStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    DISCOVERED = "discovered"


class WebPage(BaseModel):
    """Immutable schema for web page extraction results."""

    model_config = ConfigDict(frozen=True)

    url: str
    title: str = Field(default="Sin Título")
    content_md_path: str
    assets: list[str] = Field(default_factory=list)
    status: MigrationStatus = MigrationStatus.COMPLETED

from enum import Enum
from typing import List
from pydantic import BaseModel, Field


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
    url: str
    title: str = Field(default="Sin Título")
    content_md_path: str
    assets: List[str] = Field(default_factory=list)
    status: MigrationStatus = MigrationStatus.COMPLETED

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ScrapingScope(str, Enum):
    """Ámbitos de scraping para control de navegación."""

    STRICT = "strict"
    BROAD = "broad"
    SMART = "smart"


class MigrationStatus(str, Enum):
    """Estados del ciclo de vida de una URL."""

    PENDING = "pending"
    DISCOVERED = "discovered"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class WebPageInput(BaseModel):
    """Modelo de entrada para validación de datos de página web."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    url: str
    title: str = Field(default="Sin Título", min_length=1, max_length=500)
    content_md_path: str
    assets: list[str] = Field(default_factory=list)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        if not value.startswith(("http://", "https://")):
            msg = "URL inválida: debe comenzar con http:// o https://"
            raise ValueError(msg)
        return value

    @field_validator("content_md_path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        if not value.endswith(".md"):
            msg = "Path inválido: debe terminar en .md"
            raise ValueError(msg)
        return value


class WebPage(WebPageInput):
    """Modelo inmutable para resultados de extracción de páginas web.
    
    Extiende WebPageInput agregando metadata de sistema.
    """

    model_config = ConfigDict(frozen=True)

    status: MigrationStatus = MigrationStatus.COMPLETED
    extracted_at: datetime = Field(default_factory=datetime.now)
    error_message: str | None = Field(default=None, max_length=500)

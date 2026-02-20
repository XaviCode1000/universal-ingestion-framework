import os
from pathlib import Path
from typing import Any

import questionary
import yaml
from pydantic import BaseModel, Field, field_validator
from rich.console import Console

console = Console()


class ScraperConfig(BaseModel):
    """Scraper configuration.

    Deliberately NOT frozen: config values may be overridden
    from environment variables or CLI args after instantiation.
    """

    data_dir: Path = Field(default_factory=lambda: Path("data"))
    cache_dir: Path = Field(default_factory=lambda: Path("cache"))
    max_retries: int = 3
    timeout_seconds: int = 30
    request_delay: float = 1.0  # Fase 1: Rate Limiting
    default_workers: int = 5
    asset_workers: int = 8
    dns_overrides: dict[str, str] = Field(default_factory=dict)
    log_rotation_mb: int = 50
    log_level: str = "INFO"
    db_pool_size: int = 5
    db_timeout_seconds: float = 5.0
    stats_cache_ttl_seconds: float = 5.0

    @field_validator("data_dir", "cache_dir", mode="before")
    @classmethod
    def expand_paths(cls, v: Any) -> Path:
        if isinstance(v, (str, Path)):
            return Path(os.path.expandvars(os.path.expanduser(str(v))))
        return Path(v)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(self.model_dump(mode="json"), f, default_flow_style=False)

    @classmethod
    def load(cls, path: Path) -> "ScraperConfig":
        if not path.exists():
            return cls()
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls(**data)


def get_config_path(custom_path: Path | None = None) -> Path:
    if custom_path:
        return custom_path

    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        base_path = Path(xdg_config_home)
    else:
        base_path = Path.home() / ".config"

    paths = [
        base_path / "uif-scraper" / "config.yaml",
        Path.home() / ".config" / "uif-scraper" / "config.yaml",
        Path("/etc/uif-scraper/config.yaml"),
    ]

    for p in paths:
        if p.exists():
            return p

    return paths[0]


async def run_wizard() -> ScraperConfig:
    console.print("[bold yellow]🛸 CONFIGURACIÓN DE UIF SCRAPER v4.0[/]")

    data_dir = await questionary.text(
        "Directorio de datos (resultados):", default="data"
    ).ask_async()

    workers = await questionary.select(
        "Número de workers por defecto:", choices=["1", "5", "10", "20"], default="5"
    ).ask_async()

    log_level = await questionary.select(
        "Nivel de logging:",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
    ).ask_async()

    config = ScraperConfig(
        data_dir=Path(data_dir or "data"),
        default_workers=int(workers or 5),
        log_level=log_level or "INFO",
    )

    save_path = get_config_path()
    if await questionary.confirm(f"¿Guardar configuración en {save_path}?").ask_async():
        config.save(save_path)
        console.print(f"[green]✓ Configuración guardada en {save_path}[/]")

    return config


def load_config_with_overrides(custom_path: Path | None = None) -> ScraperConfig:
    config_path = get_config_path(custom_path)
    config = ScraperConfig.load(config_path)

    if "SCRAPER_DATA_DIR" in os.environ:
        config.data_dir = Path(os.environ["SCRAPER_DATA_DIR"])
    if "SCRAPER_MAX_WORKERS" in os.environ:
        config.default_workers = int(os.environ["SCRAPER_MAX_WORKERS"])

    return config

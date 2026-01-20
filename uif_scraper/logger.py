import sys
from pathlib import Path
from loguru import logger
from rich.logging import RichHandler


def setup_logger(data_dir: Path, rotation: int = 50, level: str = "INFO") -> None:
    logger.remove()

    logger.add(
        RichHandler(rich_tracebacks=True, markup=True, show_path=False),
        format="{message}",
        level="WARNING",
        enqueue=True,
    )

    log_path = data_dir / "logs" / "scraper_{time:YYYY-MM-DD}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_path,
        rotation=f"{rotation} MB",
        retention="10 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=level,
        enqueue=True,
        serialize=False,
    )

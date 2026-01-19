import sys
from pathlib import Path
from loguru import logger


def setup_logger(data_dir: Path, rotation: int = 50, level: str = "INFO") -> None:
    logger.remove()

    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level,
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

    # File output with rotation
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
        serialize=False,  # Change to True if you want JSON structured logs
    )

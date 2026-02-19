import logging
from pathlib import Path
from loguru import logger
from rich.logging import RichHandler


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno  # type: ignore[assignment]

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            if frame.f_back:
                frame = frame.f_back
                depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logger(data_dir: Path, rotation: int = 50, level: str = "INFO") -> None:
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    for noisy_logger in ["scrapling", "patchright", "httpx", "httpcore"]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

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

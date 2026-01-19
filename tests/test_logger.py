import pytest
from pathlib import Path
from uif_scraper.logger import setup_logger


def test_setup_logger(tmp_path):
    log_dir = tmp_path / "logs"
    setup_logger(tmp_path, rotation=10, level="DEBUG")

    from loguru import logger

    logger.info("Test log entry")

    assert log_dir.exists()

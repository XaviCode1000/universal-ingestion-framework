import os
from pathlib import Path
from uif_scraper.config import ScraperConfig


def test_config_default():
    config = ScraperConfig()
    assert config.max_retries == 3
    assert config.default_workers == 5


def test_config_save_load(tmp_path):
    config = ScraperConfig(default_workers=10)
    config_file = tmp_path / "config.yaml"
    config.save(config_file)

    loaded = ScraperConfig.load(config_file)
    assert loaded.default_workers == 10


def test_config_expand_paths():
    config = ScraperConfig(data_dir=Path("~/mydata"))
    assert config.data_dir == Path(os.path.expanduser("~/mydata"))


def test_config_env_overrides():
    os.environ["SCRAPER_DATA_DIR"] = "/tmp/env_data"
    os.environ["SCRAPER_MAX_WORKERS"] = "99"
    from uif_scraper.config import load_config_with_overrides

    config = load_config_with_overrides()
    assert str(config.data_dir) == "/tmp/env_data"
    assert config.default_workers == 99
    del os.environ["SCRAPER_DATA_DIR"]
    del os.environ["SCRAPER_MAX_WORKERS"]

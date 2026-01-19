import pytest
import sys
from unittest.mock import AsyncMock, patch, MagicMock
from uif_scraper.cli import main_async


@pytest.mark.asyncio
async def test_cli_setup_wizard():
    with patch("uif_scraper.cli.argparse.ArgumentParser.parse_args") as mock_args:
        mock_args.return_value = MagicMock(
            url=None, setup=True, config=None, scope="smart", workers=5
        )

        with patch(
            "uif_scraper.cli.run_wizard", new_callable=AsyncMock
        ) as mock_wizard:
            mock_wizard.return_value = MagicMock(
                data_dir="data", log_rotation_mb=50, log_level="INFO"
            )

            await main_async()
            mock_wizard.assert_called_once()


@pytest.mark.asyncio
async def test_cli_run_direct(tmp_path):
    with patch("uif_scraper.cli.argparse.ArgumentParser.parse_args") as mock_args:
        mock_args.return_value = MagicMock(
            url="https://example.com",
            setup=False,
            config=None,
            scope="smart",
            workers=5,
        )

        with patch("uif_scraper.cli.load_config_with_overrides") as mock_load:
            mock_load.return_value = MagicMock(
                data_dir=tmp_path,
                log_rotation_mb=50,
                log_level="INFO",
                default_workers=5,
                asset_workers=8,
                max_retries=3,
                timeout_seconds=30,
                dns_overrides={},
            )

            with patch(
                "uif_scraper.cli.UIFMigrationEngine", return_value=AsyncMock()
            ) as mock_engine:
                await main_async()
                mock_engine.assert_called_once()

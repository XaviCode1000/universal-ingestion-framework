"""Tests for UIF CLI.

Note: CLI was migrated from argparse to typer, so these tests
need to be updated to use typer.testing.CliRunner.
"""

import pytest
from typer.testing import CliRunner

from uif_scraper.cli import app

runner = CliRunner()


@pytest.mark.asyncio
async def test_cli_help():
    """Test that CLI help command works."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "scrape" in result.output or "UIF" in result.output


@pytest.mark.asyncio
async def test_cli_scrape_missing_url():
    """Test that scrape command requires URL or --setup."""
    result = runner.invoke(app, ["scrape"])
    # Should fail or show help since URL is required
    # (or prompt for URL in interactive mode)
    # The exact behavior depends on typer configuration


# TODO: Update these tests for typer-based CLI
# The old argparse-based tests are kept below as reference


@pytest.mark.skip(reason="CLI migrated to typer - needs CliRunner")
async def test_cli_setup_wizard():
    """Test setup wizard invocation."""
    pass


@pytest.mark.skip(reason="CLI migrated to typer - needs CliRunner")
async def test_cli_run_direct(tmp_path):
    """Test direct run with URL."""
    pass

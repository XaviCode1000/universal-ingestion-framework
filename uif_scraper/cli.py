"""UIF Scraper CLI with Typer and Textual TUI."""

import asyncio
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import questionary
import typer
from questionary import Choice
from rich.console import Console

from uif_scraper.config import load_config_with_overrides, run_wizard
from uif_scraper.core.engine_core import EngineCore
from uif_scraper.db_manager import StateManager
from uif_scraper.db_pool import SQLitePool
from uif_scraper.extractors.asset_extractor import AssetExtractor
from uif_scraper.extractors.metadata_extractor import MetadataExtractor
from uif_scraper.extractors.text_extractor import TextExtractor
from uif_scraper.logger import setup_logger
from uif_scraper.models import ScrapingScope
from uif_scraper.navigation import NavigationService
from uif_scraper.reporter import ReporterService
from uif_scraper.tui.textual_callback import TextualUICallback
from uif_scraper.utils.url_utils import slugify

# Catppuccin-themed console
console = Console()

app = typer.Typer(
    name="uif-scraper",
    help="🛸 Universal Ingestion Framework - Web scraping con TUI moderna",
    add_completion=True,
    rich_markup_mode="rich",
)


async def run_mission_wizard() -> dict[str, Any] | None:
    """Interactive mission wizard."""
    console.print("\n[bold magenta]🚀 ASISTENTE DE MISIÓN UIF[/]")

    url = await questionary.text("URL base del sitio:").ask_async()
    if not url:
        return None

    scope = await questionary.select(
        "Alcance del rastreo (Scope):",
        choices=[
            Choice(title="Smart (Subdirectorio o Dominio)", value="smart"),
            Choice(title="Strict (Solo ruta exacta)", value="strict"),
            Choice(title="Broad (Todo el dominio)", value="broad"),
        ],
        default="smart",
    ).ask_async()

    mode = await questionary.select(
        "Modo de extracción:",
        choices=[
            Choice(title="Solo Texto (Markdown optimizado)", value="text"),
            Choice(title="Texto + Assets (Imágenes, PDFs)", value="full"),
        ],
        default="full",
    ).ask_async()

    return {"url": url, "scope": scope, "mode": mode}


@app.command()
def scrape(
    url: str = typer.Argument(
        None,
        help="URL base del sitio a procesar",
    ),
    config_path: Path = typer.Option(
        None,
        "--config",
        "-c",
        help="Ruta al archivo de configuración",
        exists=False,
    ),
    scope: str = typer.Option(
        "smart",
        "--scope",
        "-s",
        help="Alcance del rastreo: smart, strict, broad",
    ),
    workers: int = typer.Option(
        None,
        "--workers",
        "-w",
        help="Número de workers concurrentes",
    ),
    only_text: bool = typer.Option(
        False,
        "--only-text",
        "-t",
        help="No descargar assets (solo texto)",
    ),
    output_dir: Path = typer.Option(
        None,
        "--output-dir",
        "-d",
        help="Directorio de salida para los datos",
    ),
    setup: bool = typer.Option(
        False,
        "--setup",
        help="Ejecutar wizard de configuración",
    ),
) -> None:
    """🛸 Ejecutar misión de scraping con TUI moderna."""
    asyncio.run(
        _run_async(
            url=url,
            config_path=config_path,
            scope=scope,
            workers=workers,
            only_text=only_text,
            output_dir=output_dir,
            setup=setup,
        )
    )


async def _run_async(
    url: str | None,
    config_path: Path | None,
    scope: str,
    workers: int | None,
    only_text: bool,
    output_dir: Path | None,
    setup: bool,
) -> None:
    """Async implementation of the scrape command."""
    from uif_scraper.tui.app import UIFDashboardApp

    mission_url = url
    mission_scope = scope
    mission_extract_assets = not only_text

    if setup:
        await run_wizard()
        return

    if not mission_url:
        wizard_data = await run_mission_wizard()
        if not wizard_data:
            console.print("[red]Operación cancelada.[/]")
            return
        mission_url = wizard_data["url"]
        mission_scope = wizard_data["scope"]
        mission_extract_assets = wizard_data["mode"] == "full"

    config = load_config_with_overrides(config_path)
    if workers:
        config.default_workers = workers

    if output_dir:
        config.data_dir = output_dir

    if not config.data_dir.is_absolute():
        config.data_dir = Path.cwd() / "data"

    setup_logger(config.data_dir, config.log_rotation_mb, config.log_level)

    domain_slug = slugify(urlparse(mission_url).netloc)
    project_data_dir = config.data_dir / domain_slug
    project_data_dir.mkdir(parents=True, exist_ok=True)

    db_path = project_data_dir / "state.db"
    pool = SQLitePool(
        db_path, max_size=config.db_pool_size, timeout=config.db_timeout_seconds
    )
    state = StateManager(
        pool,
        stats_cache_ttl=config.stats_cache_ttl_seconds,
        batch_interval=1.0,
        batch_size=100,
    )

    text_extractor = TextExtractor()
    metadata_extractor = MetadataExtractor(cache_size=1000)
    asset_extractor = AssetExtractor(project_data_dir)

    navigation_service = NavigationService(mission_url, ScrapingScope(mission_scope))
    reporter_service = ReporterService(console, state)

    # Create the TUI app first
    tui_app = UIFDashboardApp(
        mission_url=mission_url,
        scope=mission_scope,
        worker_count=config.default_workers,
    )

    # Create EngineCore directly with all dependencies
    core = EngineCore(
        config=config,
        state=state,
        text_extractor=text_extractor,
        metadata_extractor=metadata_extractor,
        asset_extractor=asset_extractor,
        navigation_service=navigation_service,
        reporter_service=reporter_service,
        extract_assets=mission_extract_assets,
    )

    # Set up UI callback for event-driven updates
    core.ui_callback = TextualUICallback(tui_app)

    # Pass core.run as the engine factory
    tui_app._engine_factory = core.run

    try:
        await state.start_batch_processor()
        # Run the TUI app asynchronously (we're already in an async context)
        # Textual handles Ctrl+C and worker lifecycle automatically via its worker system
        await tui_app.run_async()
    except asyncio.CancelledError:
        console.print("[yellow]⚠️  Operation cancelled by user[/]")
    finally:
        # CRITICAL: Ensure all pending writes complete before closing
        # This prevents data loss from buffered writes
        console.print("[dim]🔄 Finalizing pending writes...[/]")

        # Stop batch processor with explicit wait
        await state.stop_batch_processor()

        # Give time for any remaining file operations to complete
        await asyncio.sleep(0.5)

        # Close all database connections
        await pool.close_all()

        console.print("[dim]✅ Shutdown complete[/]")


@app.command()
def config() -> None:
    """⚙️  Abrir wizard de configuración."""
    asyncio.run(run_wizard())


@app.command()
def version() -> None:
    """📋 Mostrar versión."""
    console.print("[bold magenta]UIF Scraper[/] [cyan]v3.0.0[/]")
    console.print("[dim]Universal Ingestion Framework con Catppuccin Mocha theme[/]")


def main() -> None:
    """Entry point."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[red]✋ Interrupted by user[/]")


if __name__ == "__main__":
    main()

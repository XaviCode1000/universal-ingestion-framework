import argparse
import asyncio
import contextlib
import signal
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import questionary
from questionary import Choice
from rich.console import Console

from uif_scraper.config import load_config_with_overrides, run_wizard
from uif_scraper.db_manager import StateManager
from uif_scraper.db_pool import SQLitePool
from uif_scraper.engine import UIFMigrationEngine
from uif_scraper.extractors.asset_extractor import AssetExtractor
from uif_scraper.extractors.metadata_extractor import MetadataExtractor
from uif_scraper.extractors.text_extractor import TextExtractor
from uif_scraper.logger import setup_logger
from uif_scraper.models import ScrapingScope
from uif_scraper.navigation import NavigationService
from uif_scraper.reporter import ReporterService
from uif_scraper.utils.url_utils import slugify

console = Console()


def _setup_signal_handlers(shutdown_event: asyncio.Event) -> None:
    """Setup SIGTERM and SIGINT handlers for graceful shutdown.

    Uses asyncio's add_signal_handler on Unix for clean integration,
    falls back to signal.signal on Windows.
    """
    loop = asyncio.get_running_loop()

    try:
        # Unix/Linux/Mac: use the clean asyncio API
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, shutdown_event.set)
    except NotImplementedError:
        # Windows: fallback to sync API (cannot use add_signal_handler)
        # Note: signal_handler runs in the main thread, so we need to
        # schedule shutdown_event.set() in the event loop
        def signal_handler(signum: int, frame: Any) -> None:  # noqa: ARG001
            console.print(
                "\n[yellow]⚠️  Shutdown signal received. Finishing current tasks...[/]"
            )
            # Schedule in event loop since we're in signal context
            loop.call_soon_threadsafe(shutdown_event.set)

        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, signal_handler)


async def run_mission_wizard() -> dict[str, Any] | None:
    console.print("\n[bold yellow]🚀 ASISTENTE DE MISIÓN UIF[/]")

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


async def main_async() -> None:
    parser = argparse.ArgumentParser(description="UIF Scraper v3.0")
    parser.add_argument("url", nargs="?", help="URL base del sitio a procesar")
    parser.add_argument("--config", type=Path, help="Ruta al archivo de configuración")
    parser.add_argument(
        "--setup", action="store_true", help="Ejecutar wizard de configuración"
    )
    parser.add_argument(
        "--scope", choices=["smart", "strict", "broad"], default="smart"
    )
    parser.add_argument("--workers", type=int, help="Número de workers concurrentes")
    parser.add_argument("--only-text", action="store_true", help="No descargar assets")

    args = parser.parse_args()

    mission_url = args.url
    mission_scope = args.scope
    mission_extract_assets = not args.only_text

    if args.setup:
        await run_wizard()
        return

    if not mission_url:
        wizard_data = await run_mission_wizard()
        if not wizard_data:
            print("Operación cancelada.")
            return
        mission_url = wizard_data["url"]
        mission_scope = wizard_data["scope"]
        mission_extract_assets = wizard_data["mode"] == "full"

    config = load_config_with_overrides(args.config)
    if args.workers:
        config.default_workers = args.workers

    # Resolver data_dir relativo al directorio actual de ejecución si no es absoluto
    if not config.data_dir.is_absolute():
        config.data_dir = Path.cwd() / "data"

    setup_logger(config.data_dir, config.log_rotation_mb, config.log_level)

    domain_slug = slugify(urlparse(mission_url).netloc)
    project_data_dir = config.data_dir / domain_slug
    project_data_dir.mkdir(parents=True, exist_ok=True)

    db_path = project_data_dir / "state.db"
    pool = SQLitePool(
        db_path, 
        max_size=config.db_pool_size, 
        timeout=config.db_timeout_seconds
    )
    state = StateManager(
        pool,
        stats_cache_ttl=config.stats_cache_ttl_seconds,
        batch_interval=1.0,  # Flush cada 1 segundo
        batch_size=100,  # O cada 100 actualizaciones
    )

    text_extractor = TextExtractor()
    metadata_extractor = MetadataExtractor()
    asset_extractor = AssetExtractor(project_data_dir)

    navigation_service = NavigationService(mission_url, ScrapingScope(mission_scope))
    reporter_service = ReporterService(console, state)

    engine = UIFMigrationEngine(
        config=config,
        state=state,
        text_extractor=text_extractor,
        metadata_extractor=metadata_extractor,
        asset_extractor=asset_extractor,
        navigation_service=navigation_service,
        reporter_service=reporter_service,
        extract_assets=mission_extract_assets,
    )

    # Setup graceful shutdown
    shutdown_event = asyncio.Event()
    _setup_signal_handlers(shutdown_event)

    # Connect shutdown event to engine
    async def monitor_shutdown() -> None:
        await shutdown_event.wait()
        engine.request_shutdown()

    shutdown_monitor = asyncio.create_task(monitor_shutdown())

    try:
        # Iniciar batch processor para actualizaciones de estado
        await state.start_batch_processor()
        await engine.run()
    except asyncio.CancelledError:
        console.print("[yellow]⚠️  Operation cancelled by user[/]")
    finally:
        shutdown_monitor.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await shutdown_monitor
        # Detener batch processor y flushear pendientes
        await state.stop_batch_processor()
        await pool.close_all()


def main() -> None:
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        console.print("\n[red]✋ Interrupted by user[/]")


if __name__ == "__main__":
    main()

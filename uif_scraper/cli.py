import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import questionary
from rich.console import Console

from uif_scraper.config import load_config_with_overrides, run_wizard
from uif_scraper.db_manager import StateManager
from uif_scraper.db_pool import SQLitePool
from uif_scraper.engine import UIFMigrationEngine
from uif_scraper.extractors.text_extractor import TextExtractor
from uif_scraper.extractors.metadata_extractor import MetadataExtractor
from uif_scraper.extractors.asset_extractor import AssetExtractor
from uif_scraper.logger import setup_logger
from uif_scraper.models import ScrapingScope
from uif_scraper.utils.url_utils import slugify

console = Console()


async def run_mission_wizard() -> Optional[dict]:
    console.print("\n[bold yellow]🚀 ASISTENTE DE MISIÓN UIF[/]")

    url = await questionary.text("URL base del sitio:").ask_async()
    if not url:
        return None

    scope = await questionary.select(
        "Alcance del rastreo (Scope):",
        choices=[
            {"name": "Smart (Subdirectorio o Dominio)", "value": "smart"},
            {"name": "Strict (Solo ruta exacta)", "value": "strict"},
            {"name": "Broad (Todo el dominio)", "value": "broad"},
        ],
        default="smart",
    ).ask_async()

    mode = await questionary.select(
        "Modo de extracción:",
        choices=[
            {"name": "Solo Texto (Markdown optimizado)", "value": "text"},
            {"name": "Texto + Assets (Imágenes, PDFs)", "value": "full"},
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

    setup_logger(config.data_dir, config.log_rotation_mb, config.log_level)

    domain_slug = slugify(urlparse(mission_url).netloc)
    project_data_dir = config.data_dir / domain_slug
    project_data_dir.mkdir(parents=True, exist_ok=True)

    db_path = project_data_dir / "state.db"
    pool = SQLitePool(db_path, max_size=5)
    state = StateManager(pool)

    text_extractor = TextExtractor()
    metadata_extractor = MetadataExtractor()
    asset_extractor = AssetExtractor(project_data_dir)

    engine = UIFMigrationEngine(
        config=config,
        state=state,
        text_extractor=text_extractor,
        metadata_extractor=metadata_extractor,
        asset_extractor=asset_extractor,
        base_url=mission_url,
        scope=ScrapingScope(mission_scope),
        project_dir=project_data_dir,
        extract_assets=mission_extract_assets,
    )

    try:
        await engine.run()
    finally:
        await pool.close_all()


def main() -> None:
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

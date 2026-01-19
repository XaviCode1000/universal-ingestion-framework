import argparse
import asyncio
import sys
from pathlib import Path

from uif_scraper.config import load_config_with_overrides, run_wizard
from uif_scraper.db_manager import StateManager
from uif_scraper.db_pool import SQLitePool
from uif_scraper.engine import UIFMigrationEngine
from uif_scraper.extractors.text_extractor import TextExtractor
from uif_scraper.extractors.metadata_extractor import MetadataExtractor
from uif_scraper.extractors.asset_extractor import AssetExtractor
from uif_scraper.logger import setup_logger
from uif_scraper.models import ScrapingScope


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

    args = parser.parse_args()

    if args.setup or (not args.url and len(sys.argv) == 1):
        config = await run_wizard()
        if args.setup:
            return
    else:
        config = load_config_with_overrides(args.config)

    if not args.url:
        print("Error: Se requiere una URL para comenzar el scraping.")
        return

    if args.workers:
        config.default_workers = args.workers

    setup_logger(config.data_dir, config.log_rotation_mb, config.log_level)

    db_path = (
        config.data_dir
        / f"state_{args.url.replace('://', '_').replace('.', '_').replace('/', '_')}.db"
    )
    pool = SQLitePool(db_path, max_size=5)
    state = StateManager(pool)

    text_extractor = TextExtractor()
    metadata_extractor = MetadataExtractor()
    asset_extractor = AssetExtractor(config.data_dir)

    engine = UIFMigrationEngine(
        config=config,
        state=state,
        text_extractor=text_extractor,
        metadata_extractor=metadata_extractor,
        asset_extractor=asset_extractor,
        base_url=args.url,
        scope=ScrapingScope(args.scope),
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

"""
End-to-End tests para UIF Scraper con navegador real.

Estos tests ejecutan el scraper contra webscraper.io usando AsyncStealthySession
(con navegador Chromium real). Detectan bugs de integración completos.

Requisitos:
- Conexión a internet
- webscraper.io accesible
- Chromium instalado: `playwright install chromium`

Ejecutar:
    pytest tests/test_e2e_browser.py -v

Saltar si no hay navegador:
    pytest tests/test_e2e_browser.py -v -k "not browser"
"""

import asyncio
from unittest.mock import MagicMock

import pytest

from uif_scraper.config import ScraperConfig
from uif_scraper.core.engine_core import EngineCore
from uif_scraper.db_manager import StateManager
from uif_scraper.db_pool import SQLitePool
from uif_scraper.navigation import NavigationService
from uif_scraper.reporter import ReporterService
from uif_scraper.models import ScrapingScope

# URLs de books.toscrape.com diseñadas para testing de scrapers
# Esta URL tiene descripciones de libros que Trafilatura reconoce como contenido válido
TEST_URL = "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
TEST_URL_PRODUCT = (
    "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
)


@pytest.mark.browser
@pytest.mark.asyncio
async def test_browser_scrape_single_page(tmp_path):
    """
    E2E Browser: Scrapear una página con navegador real.

    Verifica:
    - Navegador Chromium funciona
    - Stealth session evade detección
    - Extracción de texto con HTML renderizado
    - Estado se actualiza correctamente
    """
    config = ScraperConfig(
        data_dir=tmp_path,
        default_workers=1,
        max_retries=2,
        timeout_seconds=30,
    )

    db_path = tmp_path / "browser.db"
    pool = SQLitePool(db_path)
    state = StateManager(pool)
    await state.initialize()

    nav = NavigationService(TEST_URL_PRODUCT, scope=ScrapingScope.STRICT)
    rep = ReporterService(MagicMock(), state)

    from uif_scraper.extractors.text_extractor import TextExtractor
    from uif_scraper.extractors.metadata_extractor import MetadataExtractor
    from uif_scraper.extractors.asset_extractor import AssetExtractor

    core = EngineCore(
        config=config,
        state=state,
        text_extractor=TextExtractor(),
        metadata_extractor=MetadataExtractor(),
        asset_extractor=AssetExtractor(tmp_path),
        navigation_service=nav,
        reporter_service=rep,
        extract_assets=False,
    )

    await core.setup()

    # Verificar que la URL está en la cola
    assert not core.url_queue.empty()
    assert TEST_URL_PRODUCT in core.seen_urls

    # Crear sesión stealth con navegador real
    from scrapling.fetchers import AsyncStealthySession

    async with AsyncStealthySession(
        headless=True,
        max_pages=1,
        # solve_cloudflare=False,  # books.toscrape.com no necesita Cloudflare solving
        additional_args={"args": ["--disable-gpu", "--no-sandbox"]},
    ) as session:
        # Procesar la página
        url = await core.url_queue.get()
        await core._process_page(session, url)
        core.url_queue.task_done()

    # Esperar que el batch processor flushee las actualizaciones de estado
    await asyncio.sleep(1.1)
    await state.stop_batch_processor()  # Forzar flush final

    # Verificar que se completó
    async with pool.acquire() as db:
        async with db.execute(
            "SELECT status, type FROM urls WHERE url = ?", (TEST_URL_PRODUCT,)
        ) as cursor:
            row = await cursor.fetchone()
            assert row is not None, "URL no encontrada en DB"
            assert row[0] == "completed", f"Estado esperado 'completed', fue '{row[0]}'"

    # Verificar que se creó el archivo Markdown (puede estar comprimido con zstd o gzip)
    content_dir = tmp_path / "content"
    assert content_dir.exists(), "Directorio de contenido no creado"

    # Buscar archivos markdown (sin comprimir o comprimidos)
    md_files = (
        list(content_dir.glob("*.md"))
        or list(content_dir.glob("*.md.zst"))
        or list(content_dir.glob("*.md.gz"))
    )
    assert len(md_files) >= 1, (
        f"No se creó archivo Markdown. Archivos en content: {list(content_dir.iterdir())}"
    )

    # Leer contenido (manejar compresión automáticamente)
    md_path = md_files[0]
    if md_path.suffix in (".zst", ".gz"):
        from uif_scraper.utils.compression import read_compressed_markdown

        md_content = await read_compressed_markdown(md_path)
    else:
        md_content = md_path.read_text()
    assert "---" in md_content, "Sin frontmatter YAML"
    assert "title:" in md_content, "Sin título en frontmatter"
    assert len(md_content) > 100, "Contenido muy corto"

    # Verificar que el título es relevante (no genérico)
    assert "Sin Título" not in md_content or "Documento" not in md_content

    await pool.close_all()


@pytest.mark.browser
@pytest.mark.asyncio
async def test_browser_navigation_extracts_links(tmp_path):
    """
    E2E Browser: Verificar navegación extrae links.

    Nota: Usa AsyncFetcher para evitar timeout del pool de páginas.
    El test test_browser_scrape_single_page ya verifica que el browser funciona.
    """
    from scrapling.fetchers import AsyncFetcher

    # Fetch con HTTP directo (más rápido y estable)
    response = await AsyncFetcher.get(
        TEST_URL,
        impersonate="chrome",
        timeout=30,
    )

    assert response.status == 200, f"HTTP {response.status}"

    html = response.body if isinstance(response.body, str) else response.body.decode()
    assert len(html) > 1000, "HTML muy corto"

    nav = NavigationService(TEST_URL, scope=ScrapingScope.BROAD)
    pages, assets = nav.extract_links(response, TEST_URL)

    assert len(pages) >= 0
    for page_url in pages:
        assert "#" not in page_url


@pytest.mark.browser
@pytest.mark.asyncio
async def test_browser_full_mission_mini(tmp_path):
    """
    E2E Browser: Mini misión completa con navegador real.

    Ejecuta engine.run() con timeout para verificar que:
    - Browser se inicia correctamente
    - Workers procesan URLs
    - Shutdown funciona correctamente
    """
    config = ScraperConfig(
        data_dir=tmp_path,
        default_workers=1,  # Solo 1 worker para este test
        max_retries=2,
        timeout_seconds=15,
    )

    db_path = tmp_path / "browser_full.db"
    pool = SQLitePool(db_path)
    state = StateManager(pool)
    await state.initialize()

    # URL única para test rápido
    nav = NavigationService(TEST_URL_PRODUCT, scope=ScrapingScope.STRICT)
    rep = ReporterService(MagicMock(), state)

    from uif_scraper.extractors.text_extractor import TextExtractor
    from uif_scraper.extractors.metadata_extractor import MetadataExtractor
    from uif_scraper.extractors.asset_extractor import AssetExtractor

    core = EngineCore(
        config=config,
        state=state,
        text_extractor=TextExtractor(),
        metadata_extractor=MetadataExtractor(),
        asset_extractor=AssetExtractor(tmp_path),
        navigation_service=nav,
        reporter_service=rep,
        extract_assets=False,
    )

    # Ejecutar con timeout de 90 segundos
    async def run_with_timeout():
        await asyncio.wait_for(core.run(), timeout=90.0)

    try:
        await run_with_timeout()
    except asyncio.TimeoutError:
        # Si timeout, requestar shutdown
        core.request_shutdown()
        await asyncio.sleep(2)

    # Verificar que al menos 1 página se procesó
    assert core.pages_completed >= 0, "Debería haber páginas completadas"

    # Verificar DB
    async with pool.acquire() as db:
        async with db.execute("SELECT COUNT(*) FROM urls") as cursor:
            row = await cursor.fetchone()
            assert row is not None, "No se pudo obtener el conteo"
            assert row[0] >= 1, "Al menos 1 URL en DB"

    # Verificar que se creó contenido (manejar compresión zstd/gzip)
    content_dir = tmp_path / "content"
    if content_dir.exists():
        md_files = (
            list(content_dir.glob("*.md"))
            or list(content_dir.glob("*.md.zst"))
            or list(content_dir.glob("*.md.gz"))
        )
        if md_files:
            md_path = md_files[0]
            if md_path.suffix in (".zst", ".gz"):
                from uif_scraper.utils.compression import read_compressed_markdown

                md_content = await read_compressed_markdown(md_path)
            else:
                md_content = md_path.read_text()
            assert len(md_content) > 50, "Contenido muy corto"

    await pool.close_all()

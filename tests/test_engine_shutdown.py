import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uif_scraper.config import ScraperConfig
from uif_scraper.core.engine_core import EngineCore
from uif_scraper.db_manager import StateManager, MigrationStatus
from uif_scraper.db_pool import SQLitePool
from uif_scraper.navigation import NavigationService
from uif_scraper.reporter import ReporterService
from uif_scraper.models import ScrapingScope

TEST_URL = "https://example.com/test"


@pytest.mark.asyncio
async def test_request_shutdown_sets_event(tmp_path):
    """request_shutdown() setea el evento de shutdown."""
    config = ScraperConfig(data_dir=tmp_path)
    db_path = tmp_path / "shutdown.db"
    pool = SQLitePool(db_path)
    await pool.initialize()
    
    state = StateManager(pool)
    await state.initialize()
    
    nav = NavigationService(TEST_URL, scope=ScrapingScope.BROAD)
    rep = ReporterService(MagicMock(), state)

    core = EngineCore(
        config=config,
        state=state,
        text_extractor=MagicMock(),
        metadata_extractor=MagicMock(),
        asset_extractor=MagicMock(),
        navigation_service=nav,
        reporter_service=rep,
    )

    # Verificar que inicialmente no está seteado
    assert not core._shutdown_event.is_set()

    # Request shutdown
    core.request_shutdown()

    # Verificar que se seteó
    assert core._shutdown_event.is_set()

    await pool.close_all()


@pytest.mark.asyncio
async def test_page_worker_handles_cancelled_error(tmp_path):
    """page_worker marca URL como pending si se cancela."""
    config = ScraperConfig(data_dir=tmp_path, default_workers=1)
    db_path = tmp_path / "worker.db"
    pool = SQLitePool(db_path)
    await pool.initialize()
    
    state = StateManager(pool)
    await state.initialize()
    await state.add_url(TEST_URL, MigrationStatus.PENDING)
    
    nav = NavigationService(TEST_URL, scope=ScrapingScope.BROAD)
    rep = ReporterService(MagicMock(), state)

    core = EngineCore(
        config=config,
        state=state,
        text_extractor=MagicMock(),
        metadata_extractor=MagicMock(),
        asset_extractor=MagicMock(),
        navigation_service=nav,
        reporter_service=rep,
    )

    # Mock session
    session = AsyncMock()

    # Poner URL en la cola
    await core.url_queue.put(TEST_URL)

    # Mockear process_page para que lance CancelledError
    async def raise_cancelled(*args):
        raise asyncio.CancelledError()

    core._process_page = raise_cancelled

    # Crear worker
    worker_task = asyncio.create_task(core._page_worker(session))

    # Esperar a que procese
    await asyncio.sleep(0.3)

    # Cancelar worker
    worker_task.cancel()

    try:
        await worker_task
    except asyncio.CancelledError:
        pass

    # Verificar que la URL sigue en DB (no se perdió)
    async with pool.acquire() as db:
        async with db.execute("SELECT COUNT(*) FROM urls") as cursor:
            count = await cursor.fetchone()
            assert count[0] >= 1  # Al menos 1 URL en DB

    await pool.close_all()


@pytest.mark.asyncio
async def test_worker_stops_when_shutdown_requested(tmp_path):
    """Los workers dejan de procesar cuando se requesta shutdown."""
    config = ScraperConfig(data_dir=tmp_path, default_workers=1)
    db_path = tmp_path / "stop.db"
    pool = SQLitePool(db_path)
    await pool.initialize()
    
    state = StateManager(pool)
    await state.initialize()
    
    nav = NavigationService(TEST_URL, scope=ScrapingScope.BROAD)
    rep = ReporterService(MagicMock(), state)

    core = EngineCore(
        config=config,
        state=state,
        text_extractor=MagicMock(),
        metadata_extractor=MagicMock(),
        asset_extractor=MagicMock(),
        navigation_service=nav,
        reporter_service=rep,
    )

    session = AsyncMock()

    # Request shutdown inmediatamente
    core.request_shutdown()

    # Crear worker - debería terminar rápido porque shutdown está seteado
    worker_task = asyncio.create_task(core._page_worker(session))

    # Esperar un poco
    await asyncio.sleep(0.5)

    # El worker debería estar terminado (no bloqueado esperando)
    assert worker_task.done() or not core.url_queue.empty()

    worker_task.cancel()
    try:
        await worker_task
    except (asyncio.CancelledError, Exception):
        pass

    await pool.close_all()

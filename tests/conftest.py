import pytest
import pytest_asyncio
from uif_scraper.config import ScraperConfig
from uif_scraper.db_pool import SQLitePool
from uif_scraper.db_manager import StateManager


@pytest_asyncio.fixture
async def db_pool(tmp_path):
    """Crear pool de conexiones SQLite para tests."""
    pool = SQLitePool(tmp_path / "test.db")
    await pool.initialize()
    yield pool
    await pool.close_all()


@pytest_asyncio.fixture
async def state(db_pool):
    """Crear StateManager inicializado para tests."""
    mgr = StateManager(db_pool)
    await mgr.initialize()
    return mgr


@pytest.fixture
def config(tmp_path):
    """Crear configuración base para tests."""
    return ScraperConfig(data_dir=tmp_path, default_workers=1)

import pytest
from uif_scraper.db_manager import MigrationStatus


@pytest.mark.asyncio
async def test_state_manager_batch_insert(state):
    """add_urls_batch inserta múltiples URLs eficientemente."""
    urls = [
        ("https://example.com/page1", MigrationStatus.PENDING, "webpage"),
        ("https://example.com/page2", MigrationStatus.PENDING, "webpage"),
        ("https://example.com/page3", MigrationStatus.PENDING, "webpage"),
        ("https://example.com/img.png", MigrationStatus.PENDING, "asset"),
    ]

    await state.add_urls_batch(urls)

    # Verificar que se insertaron
    pending = await state.get_pending_urls()
    assert "https://example.com/page1" in pending
    assert "https://example.com/page2" in pending
    assert "https://example.com/page3" in pending

    pending_assets = await state.get_pending_urls(m_type="asset")
    assert "https://example.com/img.png" in pending_assets


@pytest.mark.asyncio
async def test_state_manager_batch_insert_empty(state):
    """add_urls_batch con lista vacía no hace nada."""
    await state.add_urls_batch([])

    # No debería crashear y la DB debería estar vacía
    pending = await state.get_pending_urls()
    assert pending == []


@pytest.mark.asyncio
async def test_state_manager_batch_insert_ignores_duplicates(state):
    """add_urls_batch ignora URLs duplicadas (INSERT OR IGNORE)."""
    urls = [
        ("https://example.com/page1", MigrationStatus.PENDING, "webpage"),
        ("https://example.com/page1", MigrationStatus.PENDING, "webpage"),  # dup
        ("https://example.com/page1", MigrationStatus.PENDING, "webpage"),  # dup
    ]

    await state.add_urls_batch(urls)

    # Debería haber solo una entrada
    pending = await state.get_pending_urls()
    assert pending.count("https://example.com/page1") == 1

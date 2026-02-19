import pytest
from unittest.mock import MagicMock
from rich.console import Console
from io import StringIO
from uif_scraper.db_manager import StateManager, MigrationStatus
from uif_scraper.db_pool import SQLitePool
from uif_scraper.reporter import ReporterService


@pytest.mark.asyncio
async def test_summary_with_empty_db(tmp_path):
    """generate_summary con DB vacía no debería crashear."""
    db_path = tmp_path / "empty.db"
    pool = SQLitePool(db_path)
    await pool.initialize()
    
    state = StateManager(pool)
    await state.initialize()
    
    # Console con output a string para verificar
    output = StringIO()
    console = Console(file=output, width=80)
    
    reporter = ReporterService(console, state)
    await reporter.generate_summary()
    
    # Debería generar algo de output sin crashear
    result = output.getvalue()
    assert "INGESTIÓN FINALIZADA" in result
    
    await pool.close_all()


@pytest.mark.asyncio
async def test_summary_with_all_completed(tmp_path):
    """generate_summary con todos completados muestra éxito."""
    db_path = tmp_path / "completed.db"
    pool = SQLitePool(db_path)
    await pool.initialize()
    
    state = StateManager(pool)
    await state.initialize()
    
    # Agregar URLs completadas
    await state.add_url("https://example.com/page1", MigrationStatus.COMPLETED)
    await state.add_url("https://example.com/page2", MigrationStatus.COMPLETED)
    
    output = StringIO()
    console = Console(file=output, width=80)
    
    reporter = ReporterService(console, state)
    await reporter.generate_summary()
    
    result = output.getvalue()
    assert "Completada" in result or "completed" in result.lower()
    assert "2" in result  # Debería mostrar el count
    
    await pool.close_all()


@pytest.mark.asyncio
async def test_summary_with_failures(tmp_path):
    """generate_summary con fallos muestra diagnóstico de errores."""
    db_path = tmp_path / "failed.db"
    pool = SQLitePool(db_path)
    await pool.initialize()
    
    state = StateManager(pool)
    await state.initialize()
    
    # Agregar URLs fallidas con errores
    await state.add_url("https://example.com/page1", MigrationStatus.FAILED)
    await state.update_status("https://example.com/page1", MigrationStatus.FAILED, "Network Error", immediate=True)

    await state.add_url("https://example.com/page2", MigrationStatus.FAILED)
    await state.update_status("https://example.com/page2", MigrationStatus.FAILED, "Network Error", immediate=True)

    await state.add_url("https://example.com/page3", MigrationStatus.FAILED)
    await state.update_status("https://example.com/page3", MigrationStatus.FAILED, "Timeout", immediate=True)
    
    output = StringIO()
    console = Console(file=output, width=80)
    
    reporter = ReporterService(console, state)
    await reporter.generate_summary()
    
    result = output.getvalue()
    assert "Error" in result or "failed" in result.lower()
    assert "Network Error" in result
    assert "2" in result  # Debería mostrar count del error común
    
    await pool.close_all()

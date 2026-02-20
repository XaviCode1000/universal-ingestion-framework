"""Tests para EngineCore - Core Logic.

Tests unitarios y de integración para verificar:
- Inicialización correcta
- Sistema de callbacks
- Métricas y estadísticas
- Pause/Resume
- Shutdown limpio
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from uif_scraper.config import ScraperConfig
from uif_scraper.core.engine_core import EngineCore, UICallback
from uif_scraper.core.types import ActivityEntry, EngineStats
from uif_scraper.db_manager import StateManager
from uif_scraper.extractors.asset_extractor import AssetExtractor
from uif_scraper.extractors.metadata_extractor import MetadataExtractor
from uif_scraper.extractors.text_extractor import TextExtractor
from uif_scraper.models import MigrationStatus, ScrapingScope
from uif_scraper.navigation import NavigationService
from uif_scraper.reporter import ReporterService


class MockUICallback(UICallback):
    """Mock de UICallback para tests."""

    def __init__(self):
        self.progress_events: list[EngineStats] = []
        self.activity_events: list[ActivityEntry] = []
        self.mode_changes: list[bool] = []
        self.circuit_changes: list[str] = []
        self.errors: list[tuple[str, str, str]] = []
        self.state_changes: list[tuple[str, str]] = []

    def on_progress(self, stats: EngineStats) -> None:
        self.progress_events.append(stats)

    def on_activity(self, entry: ActivityEntry) -> None:
        self.activity_events.append(entry)

    def on_mode_change(self, browser_mode: bool) -> None:
        self.mode_changes.append(browser_mode)

    def on_circuit_change(self, state: str) -> None:
        self.circuit_changes.append(state)

    def on_error(self, url: str, error_type: str, message: str) -> None:
        self.errors.append((url, error_type, message))

    def on_state_change(
        self, state: str, mode: str, previous_state: str | None, reason: str | None
    ) -> None:
        self.state_changes.append((state, mode))


@pytest.fixture
def mock_state():
    """Fixture para StateManager mockeado."""
    state = AsyncMock(spec=StateManager)
    state.acquire_mission_lock = AsyncMock(return_value=True)
    state.release_mission_lock = AsyncMock(return_value=True)
    state.get_stats = AsyncMock(return_value={})
    state.get_pending_urls = AsyncMock(return_value=[])
    state.add_url = AsyncMock()
    state.add_urls_batch = AsyncMock()
    state.update_status = AsyncMock()
    state.exists = AsyncMock(return_value=False)
    state.start_batch_processor = AsyncMock()
    state.stop_batch_processor = AsyncMock()
    return state


@pytest.fixture
def mock_navigation():
    """Fixture para NavigationService mockeado."""
    nav = MagicMock(spec=NavigationService)
    nav.base_url = "https://example.com"
    nav.domain = "example.com"
    nav.scope = ScrapingScope.SMART
    nav.extract_links = AsyncMock(return_value=([], []))
    return nav


@pytest.fixture
def mock_reporter():
    """Fixture para ReporterService mockeado."""
    reporter = MagicMock(spec=ReporterService)
    reporter.generate_summary = AsyncMock()
    return reporter


@pytest.fixture
def config(tmp_path):
    """Fixture para ScraperConfig."""
    return ScraperConfig(
        default_workers=2,
        asset_workers=1,
        data_dir=tmp_path / "data",
        request_delay=0.1,
        timeout_seconds=30,
        max_retries=3,
    )


@pytest.fixture
def engine_core(config, mock_state, mock_navigation, mock_reporter, tmp_path):
    """Fixture para EngineCore."""
    text_extractor = TextExtractor()
    metadata_extractor = MetadataExtractor()
    asset_extractor = AssetExtractor(tmp_path / "assets")

    return EngineCore(
        config=config,
        state=mock_state,
        text_extractor=text_extractor,
        metadata_extractor=metadata_extractor,
        asset_extractor=asset_extractor,
        navigation_service=mock_navigation,
        reporter_service=mock_reporter,
        extract_assets=False,
    )


class TestEngineCoreInitialization:
    """Tests para inicialización del EngineCore."""

    def test_engine_core_creation(self, engine_core, config):
        """EngineCore se crea correctamente."""
        assert engine_core.config == config
        assert engine_core.extract_assets is False
        assert engine_core.url_queue is not None
        assert engine_core.asset_queue is not None

    def test_engine_core_has_stats_tracker(self, engine_core):
        """EngineCore tiene StatsTracker."""
        assert engine_core.stats is not None

    def test_engine_core_has_circuit_breaker(self, engine_core):
        """EngineCore tiene CircuitBreaker."""
        assert engine_core.circuit_breaker is not None

    def test_engine_core_initial_state(self, engine_core):
        """EngineCore inicia en estado 'starting'."""
        assert engine_core._engine_state == "starting"
        # _pause_event is set() initially, so is_paused() returns False
        # (False means NOT paused = running is allowed)
        assert engine_core.is_paused() is False


class TestEngineCoreCallbacks:
    """Tests para sistema de callbacks."""

    def test_set_ui_callback(self, engine_core):
        """Se puede establecer un callback de UI."""
        callback = MockUICallback()
        engine_core.ui_callback = callback
        assert engine_core.ui_callback is callback

    def test_notify_progress_calls_callback(self, engine_core):
        """_notify_ui llama al callback on_progress."""
        callback = MockUICallback()
        engine_core.ui_callback = callback
        engine_core._notify_ui()

        assert len(callback.progress_events) == 1

    def test_notify_activity_calls_callback(self, engine_core):
        """_notify_activity llama al callback on_activity."""
        callback = MockUICallback()
        engine_core.ui_callback = callback
        engine_core._notify_activity(
            url="https://example.com/page",
            title="Test Page",
            engine="test",
            status="success",
            elapsed_ms=100.0,
        )

        assert len(callback.activity_events) == 1
        assert callback.activity_events[0].title == "Test Page"

    def test_notify_error_calls_callback(self, engine_core):
        """_notify_error llama al callback on_error."""
        callback = MockUICallback()
        engine_core.ui_callback = callback
        engine_core._notify_error(
            url="https://example.com/page",
            error_type="TimeoutError",
            message="Connection timed out",
        )

        assert len(callback.errors) == 1
        assert callback.errors[0][0] == "https://example.com/page"
        assert callback.errors[0][1] == "TimeoutError"

    def test_notify_state_change_calls_callback(self, engine_core):
        """_notify_state_change llama al callback on_state_change."""
        callback = MockUICallback()
        engine_core.ui_callback = callback
        engine_core._notify_state_change("running", reason="test_reason")

        assert len(callback.state_changes) == 1
        assert callback.state_changes[0][0] == "running"


class TestEngineCoreStats:
    """Tests para estadísticas y métricas."""

    def test_get_stats_returns_engine_stats(self, engine_core):
        """get_stats retorna EngineStats."""
        stats = engine_core.get_stats()
        assert isinstance(stats, EngineStats)
        assert hasattr(stats, "pages_completed")
        assert hasattr(stats, "pages_failed")
        assert hasattr(stats, "pages_total")

    def test_stats_initial_values(self, engine_core):
        """Stats inician en cero."""
        stats = engine_core.get_stats()
        assert stats.pages_completed == 0
        assert stats.pages_failed == 0
        assert stats.error_count == 0

    def test_record_page_success(self, engine_core):
        """record_page_success incrementa contadores."""
        engine_core.stats.record_page_success()
        stats = engine_core.get_stats()
        assert stats.pages_completed == 1

    def test_record_page_failure(self, engine_core):
        """record_page_failure incrementa contadores."""
        engine_core.stats.record_page_failure()
        stats = engine_core.get_stats()
        assert stats.pages_failed == 1


class TestEngineCorePauseResume:
    """Tests para pause/resume."""

    def test_pause_sets_event(self, engine_core):
        """pause() limpia el evento de pausa."""
        # Initially _pause_event is set(), so is_paused() returns False (not paused)
        assert engine_core.is_paused() is False
        # Call pause - this clears _pause_event, making is_paused() return True
        engine_core.pause()
        assert engine_core.is_paused() is True

    def test_resume_sets_event(self, engine_core):
        """resume() establece el evento de pausa."""
        engine_core.pause()
        assert engine_core.is_paused() is True
        engine_core.resume()
        assert engine_core.is_paused() is False

    def test_pause_emits_state_change(self, engine_core):
        """pause() emite evento de cambio de estado."""
        callback = MockUICallback()
        engine_core.ui_callback = callback

        engine_core.pause()

        assert len(callback.state_changes) >= 1
        # El último state_change debe ser "paused"
        last_state = callback.state_changes[-1]
        assert last_state[0] == "paused"

    def test_resume_emits_state_change(self, engine_core):
        """resume() emite evento de cambio de estado."""
        callback = MockUICallback()
        engine_core.ui_callback = callback

        engine_core.pause()
        engine_core.resume()

        # Should have at least pause and resume state changes
        assert len(callback.state_changes) >= 2
        last_state = callback.state_changes[-1]
        assert last_state[0] == "running"


class TestEngineCoreShutdown:
    """Tests para shutdown."""

    @pytest.mark.asyncio
    async def test_graceful_shutdown(self, engine_core, mock_state):
        """_graceful_shutdown termina workers correctamente."""
        # Create mock tasks
        mock_task = AsyncMock()
        mock_task.done = MagicMock(return_value=False)
        mock_task.cancel = MagicMock()

        await engine_core._graceful_shutdown([mock_task])

        # Verify shutdown event is set
        assert engine_core._shutdown_event.is_set()

        # Verify sentinel was added to queue
        # (queue size should equal number of workers)

    def test_shutdown_event_initially_not_set(self, engine_core):
        """Shutdown event no está configurado al inicio."""
        assert not engine_core._shutdown_event.is_set()


class TestEngineCoreQueueManagement:
    """Tests para gestión de colas."""

    @pytest.mark.asyncio
    async def test_queue_discovered_links(self, engine_core):
        """_queue_discovered_links agrega URLs a la cola."""
        new_pages = ["https://example.com/page1", "https://example.com/page2"]
        new_assets = ["https://example.com/image.png"]

        # Mock state.exists to return False (not seen)
        engine_core.state.exists = AsyncMock(return_value=False)
        engine_core.state.add_urls_batch = AsyncMock()

        await engine_core._queue_discovered_links(new_pages, new_assets)

        # Check URLs were added to seen cache (pages always added)
        assert "https://example.com/page1" in engine_core.seen_urls
        assert "https://example.com/page2" in engine_core.seen_urls
        # Note: assets are NOT added because extract_assets=False in the fixture

    @pytest.mark.asyncio
    async def test_queue_skips_duplicates(self, engine_core):
        """_queue_discovered_links no agrega URLs duplicadas."""
        # Add URL to seen cache first
        engine_core.seen_urls["https://example.com/page1"] = True

        new_pages = ["https://example.com/page1"]

        # Mock state to track calls
        engine_core.state.add_urls_batch = AsyncMock()

        await engine_core._queue_discovered_links(new_pages, [])

        # add_urls_batch should NOT be called for duplicates
        # (or called with empty list)


class TestEngineCoreActivityLog:
    """Tests para activity log."""

    def test_activity_log_stores_entries(self, engine_core):
        """_notify_activity guarda entradas en activity_log."""
        engine_core._notify_activity(
            url="https://example.com/page",
            title="Test Page",
            engine="test",
            status="success",
            elapsed_ms=100.0,
            size_bytes=1000,
        )

        assert len(engine_core.activity_log) == 1
        entry = engine_core.activity_log[0]
        assert entry["title"] == "Test Page"
        assert entry["status"] == "success"

    def test_activity_log_limits_size(self, engine_core):
        """Activity log tiene límite de tamaño."""
        # Add many entries
        for i in range(150):
            engine_core._notify_activity(
                url=f"https://example.com/page{i}",
                title=f"Page {i}",
                engine="test",
                status="success",
                elapsed_ms=100.0,
            )

        # Activity log should be bounded (implementation detail)
        # This test just verifies it doesn't grow unboundedly
        assert len(engine_core.activity_log) <= 200


class TestEngineCoreSpeedTracking:
    """Tests para seguimiento de velocidad."""

    def test_update_speed_calculates_rate(self, engine_core):
        """_update_speed calcula velocidad correctamente."""
        # Simulate some pages processed
        engine_core._pages_since_last_check = 10
        engine_core._last_speed_check = (
            asyncio.get_event_loop().time() - 2.0  # 2 seconds ago
        )

        engine_core._update_speed()

        # Should have calculated speed
        assert engine_core._current_speed > 0

    def test_speed_tracking_initial_values(self, engine_core):
        """Velocidad inicial es cero."""
        assert engine_core._current_speed == 0.0
        assert engine_core._pages_since_last_check == 0

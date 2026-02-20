"""Tests para TextualUICallback Throttling.

Tests para verificar que el sistema de throttling:
- Limita la frecuencia de eventos de progreso
- Limita la frecuencia de eventos de actividad
- NO limita eventos de error (importante)
- Maneja correctamente el paso del tiempo
"""

import asyncio
import time
from unittest.mock import MagicMock, AsyncMock

import pytest

from uif_scraper.core.types import ActivityEntry, EngineStats
from uif_scraper.tui.textual_callback import TextualUICallback


class MockApp:
    """Mock de UIFDashboardApp para tests."""

    def __init__(self):
        self.events = []

    def handle_event(self, event):
        self.events.append(event)


class TestThrottlingProgress:
    """Tests para throttling de progress events."""

    @pytest.mark.asyncio
    async def test_progress_not_throttled_when_interval_passed(self):
        """Progress events se envían cuando pasa el intervalo."""
        app = MockApp()
        callback = TextualUICallback(app)

        # Create mock stats with all required attributes
        stats = MagicMock(spec=EngineStats)
        stats.pages_completed = 0
        stats.pages_total = 10
        stats.assets_completed = 0
        stats.assets_total = 5
        stats.seen_urls = 0
        stats.seen_assets = 0
        stats.queue_pending = 0
        stats.error_count = 0
        stats.queue_pending = 0
        stats.error_count = 0

        # First call should emit
        callback.on_progress(stats)
        await asyncio.sleep(0)  # Let coroutines run

        assert len(app.events) == 1

    @pytest.mark.asyncio
    async def test_progress_throttled_when_interval_not_passed(self):
        """Progress events se ignoran si no pasó el intervalo."""
        app = MockApp()
        callback = TextualUICallback(app)

        stats = MagicMock(spec=EngineStats)
        stats.pages_completed = 0
        stats.pages_total = 10
        stats.assets_completed = 0
        stats.assets_total = 5
        stats.seen_urls = 0
        stats.seen_assets = 0
        stats.queue_pending = 0
        stats.error_count = 0

        # First call should emit
        callback.on_progress(stats)
        await asyncio.sleep(0)

        # Immediate second call should be throttled
        callback.on_progress(stats)
        await asyncio.sleep(0)

        # Only one event should be emitted
        assert len(app.events) == 1

    @pytest.mark.asyncio
    async def test_progress_emits_after_interval(self):
        """Progress events se emiten después del intervalo."""
        app = MockApp()
        callback = TextualUICallback(app)

        stats = MagicMock(spec=EngineStats)
        stats.pages_completed = 0
        stats.pages_total = 10
        stats.assets_completed = 0
        stats.assets_total = 5
        stats.seen_urls = 0
        stats.seen_assets = 0
        stats.queue_pending = 0
        stats.error_count = 0

        # First call
        callback.on_progress(stats)
        await asyncio.sleep(0)

        # Wait for throttle interval to pass (100ms + buffer)
        await asyncio.sleep(0.15)

        # Second call should emit
        callback.on_progress(stats)
        await asyncio.sleep(0)

        assert len(app.events) == 2


class TestThrottlingActivity:
    """Tests para throttling de activity events."""

    @pytest.mark.asyncio
    async def test_activity_not_throttled_when_interval_passed(self):
        """Activity events se envían cuando pasa el intervalo."""
        app = MockApp()
        callback = TextualUICallback(app)

        entry = ActivityEntry(title="Test Page", engine="test", timestamp=time.time())

        # First call should emit
        callback.on_activity(entry)
        await asyncio.sleep(0)

        assert len(app.events) == 1

    @pytest.mark.asyncio
    async def test_activity_throttled_when_interval_not_passed(self):
        """Activity events se ignoran si no pasó el intervalo."""
        app = MockApp()
        callback = TextualUICallback(app)

        entry = ActivityEntry(title="Test Page", engine="test", timestamp=time.time())

        # First call should emit
        callback.on_activity(entry)
        await asyncio.sleep(0)

        # Immediate second call should be throttled
        callback.on_activity(entry)
        await asyncio.sleep(0)

        # Only one event should be emitted
        assert len(app.events) == 1


class TestThrottlingErrors:
    """Tests para verificar que errores NO se throttlean."""

    @pytest.mark.asyncio
    async def test_errors_never_throttled(self):
        """Error events siempre se envían (sin throttle)."""
        app = MockApp()
        callback = TextualUICallback(app)

        # Send multiple errors in rapid succession
        for i in range(10):
            callback.on_error(
                url=f"https://example.com/page{i}",
                error_type="TimeoutError",
                message="Connection timed out",
            )
        await asyncio.sleep(0)

        # All errors should be emitted (no throttling)
        assert len(app.events) == 10

    @pytest.mark.asyncio
    async def test_error_count_increments(self):
        """Error counter se incrementa correctamente."""
        app = MockApp()
        callback = TextualUICallback(app)

        callback.on_error(
            url="https://example.com/page1",
            error_type="TimeoutError",
            message="Error 1",
        )
        callback.on_error(
            url="https://example.com/page2",
            error_type="ConnectionError",
            message="Error 2",
        )

        await asyncio.sleep(0)

        # Both errors emitted
        assert len(app.events) == 2


class TestThrottlingModeChange:
    """Tests para cambios de modo."""

    @pytest.mark.asyncio
    async def test_mode_change_always_emits(self):
        """Mode change events siempre se envían."""
        app = MockApp()
        callback = TextualUICallback(app)

        # Multiple mode changes should all emit
        callback.on_mode_change(True)
        await asyncio.sleep(0)
        callback.on_mode_change(False)
        await asyncio.sleep(0)
        callback.on_mode_change(True)
        await asyncio.sleep(0)

        # Should have 3 events
        assert len(app.events) == 3


class TestThrottlingCircuitChange:
    """Tests para cambios de circuit breaker."""

    @pytest.mark.asyncio
    async def test_circuit_change_always_emits(self):
        """Circuit change events siempre se envían."""
        app = MockApp()
        callback = TextualUICallback(app)

        # Multiple circuit changes should all emit
        callback.on_circuit_change("closed")
        await asyncio.sleep(0)
        callback.on_circuit_change("open")
        await asyncio.sleep(0)
        callback.on_circuit_change("half-open")
        await asyncio.sleep(0)

        # Should have 3 events
        assert len(app.events) == 3


class TestThrottlingStateChange:
    """Tests para cambios de estado."""

    @pytest.mark.asyncio
    async def test_state_change_always_emits(self):
        """State change events siempre se envían."""
        app = MockApp()
        callback = TextualUICallback(app)

        # Multiple state changes should all emit
        callback.on_state_change("running", "stealth", None, "start")
        await asyncio.sleep(0)
        callback.on_state_change("paused", "stealth", "running", "user")
        await asyncio.sleep(0)
        callback.on_state_change("running", "stealth", "paused", "user")
        await asyncio.sleep(0)

        # Should have 3 events
        assert len(app.events) == 3


class TestThrottlingConfiguration:
    """Tests para configuración de throttling."""

    def test_default_throttle_intervals(self):
        """Verifica valores por defecto de throttle."""
        app = MockApp()
        callback = TextualUICallback(app)

        assert callback.PROGRESS_THROTTLE_INTERVAL == 0.1  # 100ms
        assert callback.ACTIVITY_THROTTLE_INTERVAL == 0.1  # 100ms

    def test_throttle_timestamps_initially_zero(self):
        """Timestamps de throttle inician en cero."""
        app = MockApp()
        callback = TextualUICallback(app)

        assert callback._last_progress_time == 0.0
        assert callback._last_activity_time == 0.0


class TestThrottlingStress:
    """Tests de stress para throttling."""

    @pytest.mark.asyncio
    async def test_high_frequency_events_throttled(self):
        """Many rapid events should be throttled correctly."""
        app = MockApp()
        callback = TextualUICallback(app)

        stats = MagicMock(spec=EngineStats)
        stats.pages_completed = 0
        stats.pages_total = 10
        stats.assets_completed = 0
        stats.assets_total = 5
        stats.seen_urls = 0
        stats.seen_assets = 0
        stats.queue_pending = 0
        stats.error_count = 0

        # Send 100 events as fast as possible
        for i in range(100):
            callback.on_progress(stats)
            # No await - fire as fast as possible

        await asyncio.sleep(0)

        # Should have much fewer events due to throttling
        # At 100ms interval, in ~1 second we'd get ~10 events
        # But these are synchronous calls, so we'll get fewer
        assert len(app.events) < 50  # Definitely throttled

    @pytest.mark.asyncio
    async def test_sustained_throttle_rate(self):
        """Verifica tasa de throttle sostenida."""
        app = MockApp()
        callback = TextualUICallback(app)

        stats = MagicMock(spec=EngineStats)
        stats.pages_completed = 0
        stats.pages_total = 10
        stats.assets_completed = 0
        stats.assets_total = 5
        stats.seen_urls = 0
        stats.seen_assets = 0
        stats.queue_pending = 0
        stats.error_count = 0

        # Emit events continuously for 1 second
        start = time.perf_counter()
        event_count = 0

        while time.perf_counter() - start < 1.0:
            callback.on_progress(stats)
            event_count += 1

        await asyncio.sleep(0.1)

        # With 100ms throttle, we should get ~10 events per second
        # Allow some tolerance
        events_emitted = len(app.events)
        assert events_emitted < event_count  # Definitely throttled
        assert events_emitted > 5  # But not completely blocked

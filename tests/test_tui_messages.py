"""Tests para el sistema de mensajes TUI.

Tests unitarios para verificar que todos los eventos son:
- Inmutables (frozen=True)
- Serializables correctamente
- Typing correcto
"""

import pytest
from pydantic import ValidationError

from uif_scraper.tui.messages import (
    ActivityEvent,
    Alert,
    EngineCommand,
    ErrorEvent,
    ProgressUpdate,
    SpeedUpdate,
    StateChange,
    SystemStatus,
    TUIEvent,
)


class TestTUIEvent:
    """Tests para la clase base TUIEvent."""

    def test_tuievent_is_frozen(self):
        """TUIEvent es inmutable - no se puede modificar después de crear."""
        event = TUIEvent()
        with pytest.raises(ValidationError):
            event.timestamp = "mutated"

    def test_tuievent_has_timestamp(self):
        """TUIEvent tiene timestamp por defecto."""
        event = TUIEvent()
        assert event.timestamp is not None


class TestProgressUpdate:
    """Tests para ProgressUpdate."""

    def test_progress_update_create(self):
        """Crear ProgressUpdate con valores válidos."""
        event = ProgressUpdate(
            pages_completed=10,
            pages_total=100,
            assets_completed=5,
            assets_total=50,
            urls_seen=100,
            assets_seen=50,
        )
        assert event.pages_completed == 10
        assert event.pages_total == 100
        # Verificar que podemos calcular el progreso
        progress = event.pages_completed / event.pages_total * 100
        assert progress == 10.0

    def test_progress_update_is_frozen(self):
        """ProgressUpdate es inmutable."""
        event = ProgressUpdate(
            pages_completed=10,
            pages_total=100,
            assets_completed=5,
            assets_total=50,
            urls_seen=100,
            assets_seen=50,
        )
        with pytest.raises(ValidationError):
            event.pages_completed = 20


class TestSpeedUpdate:
    """Tests para SpeedUpdate."""

    def test_speed_update_create(self):
        """Crear SpeedUpdate con valores válidos."""
        event = SpeedUpdate(
            speed_current=2.5,
            speed_average=2.0,
            speed_max=3.5,
            eta_seconds_best=40,
            eta_seconds_worst=60,
            speed_history=[2.0, 2.5, 3.0],
        )
        assert event.speed_current == 2.5
        assert event.speed_average == 2.0

    def test_speed_update_default_history(self):
        """SpeedUpdate tiene historial vacío por defecto."""
        event = SpeedUpdate(
            speed_current=2.5,
            speed_average=2.0,
            speed_max=3.5,
            eta_seconds_best=40,
            eta_seconds_worst=60,
        )
        assert event.speed_history == []

    def test_speed_update_is_frozen(self):
        """SpeedUpdate es inmutable."""
        event = SpeedUpdate(
            speed_current=2.5,
            speed_average=2.0,
            speed_max=3.5,
            eta_seconds_best=40,
            eta_seconds_worst=60,
        )
        with pytest.raises(ValidationError):
            event.speed_current = 5.0


class TestActivityEvent:
    """Tests para ActivityEvent."""

    def test_activity_event_success(self):
        """Crear ActivityEvent con status success."""
        event = ActivityEvent(
            url="https://example.com/page",
            title="Example Page",
            engine="trafilatura",
            status="success",
            elapsed_ms=450.0,
            size_bytes=12345,
        )
        assert event.status == "success"
        assert event.size_bytes == 12345

    def test_activity_event_warning(self):
        """Crear ActivityEvent con status warning."""
        event = ActivityEvent(
            url="https://example.com/page",
            title="Example Page",
            engine="readability",
            status="warning",
            elapsed_ms=1200.0,
            size_bytes=5000,
        )
        assert event.status == "warning"

    def test_activity_event_error(self):
        """Crear ActivityEvent con status error."""
        event = ActivityEvent(
            url="https://example.com/page",
            title="Example Page",
            engine="trafilatura",
            status="error",
            elapsed_ms=100.0,
            size_bytes=0,
        )
        assert event.status == "error"

    def test_activity_event_is_frozen(self):
        """ActivityEvent es inmutable."""
        event = ActivityEvent(
            url="https://example.com/page",
            title="Example Page",
            engine="trafilatura",
            status="success",
            elapsed_ms=450.0,
        )
        with pytest.raises(ValidationError):
            event.status = "error"


class TestErrorEvent:
    """Tests para ErrorEvent."""

    def test_error_event_create(self):
        """Crear ErrorEvent con valores válidos."""
        event = ErrorEvent(
            url="https://example.com/page",
            error_type="TimeoutError",
            error_message="Connection timed out",
            retry_count=2,
            is_fatal=False,
        )
        assert event.error_type == "TimeoutError"
        assert event.retry_count == 2

    def test_error_event_fatal(self):
        """Crear ErrorEvent fatal."""
        event = ErrorEvent(
            url="https://example.com/page",
            error_type="CaptchaError",
            error_message="CAPTCHA detected",
            is_fatal=True,
        )
        assert event.is_fatal is True

    def test_error_event_with_stack_trace(self):
        """Crear ErrorEvent con stack trace."""
        event = ErrorEvent(
            url="https://example.com/page",
            error_type="ValueError",
            error_message="Invalid value",
            stack_trace="Traceback (most recent call last):\n  ...",
        )
        assert event.stack_trace is not None

    def test_error_event_is_frozen(self):
        """ErrorEvent es inmutable."""
        event = ErrorEvent(
            url="https://example.com/page",
            error_type="TimeoutError",
            error_message="Connection timed out",
        )
        with pytest.raises(ValidationError):
            event.retry_count = 5


class TestSystemStatus:
    """Tests para SystemStatus."""

    def test_system_status_create(self):
        """Crear SystemStatus con valores válidos."""
        event = SystemStatus(
            circuit_state="closed",
            queue_pending=10,
            error_count=2,
            memory_mb=128,
            cpu_percent=25.5,
            current_url="https://example.com/page",
            current_worker=1,
        )
        assert event.circuit_state == "closed"
        assert event.queue_pending == 10

    def test_system_status_circuit_open(self):
        """Crear SystemStatus con circuit breaker open."""
        event = SystemStatus(
            circuit_state="open",
            queue_pending=50,
            error_count=10,
            memory_mb=512,
            cpu_percent=80.0,
            current_url="https://example.com/page",
            current_worker=2,
        )
        assert event.circuit_state == "open"

    def test_system_status_is_frozen(self):
        """SystemStatus es inmutable."""
        event = SystemStatus(
            circuit_state="closed",
            queue_pending=10,
            error_count=2,
            memory_mb=128,
            cpu_percent=25.5,
            current_url="https://example.com/page",
            current_worker=1,
        )
        with pytest.raises(ValidationError):
            event.error_count = 100


class TestStateChange:
    """Tests para StateChange."""

    def test_state_change_running(self):
        """Crear StateChange de inicio."""
        event = StateChange(
            state="running",
            mode="stealth",
            previous_state="starting",
            reason="user_request",
        )
        assert event.state == "running"
        assert event.mode == "stealth"

    def test_state_change_paused(self):
        """Crear StateChange de pausa."""
        event = StateChange(
            state="paused",
            mode="browser",
            previous_state="running",
            reason="user_request",
        )
        assert event.state == "paused"

    def test_state_change_minimal(self):
        """Crear StateChange con valores mínimos."""
        event = StateChange(
            state="running",
            mode="stealth",
        )
        assert event.previous_state is None
        assert event.reason is None

    def test_state_change_is_frozen(self):
        """StateChange es inmutable."""
        event = StateChange(
            state="running",
            mode="stealth",
        )
        with pytest.raises(ValidationError):
            event.state = "stopped"


class TestAlert:
    """Tests para Alert."""

    def test_alert_info(self):
        """Crear Alert de información."""
        event = Alert(
            level="info",
            title="Process Started",
            message="Scraping started",
            source="engine",
        )
        assert event.level == "info"

    def test_alert_warning(self):
        """Crear Alert de advertencia."""
        event = Alert(
            level="warning",
            title="Rate Limited",
            message="Too many requests, backing off",
            source="rate_limiter",
        )
        assert event.level == "warning"

    def test_alert_critical(self):
        """Crear Alert crítico con acción requerida."""
        event = Alert(
            level="critical",
            title="Circuit Breaker Open",
            message="Too many errors, stopping",
            source="circuit_breaker",
            action_required=True,
            suggested_action="Check network connection",
        )
        assert event.action_required is True

    def test_alert_is_frozen(self):
        """Alert es inmutable."""
        event = Alert(
            level="info",
            title="Test",
            message="Test message",
            source="test",
        )
        with pytest.raises(ValidationError):
            event.level = "error"


class TestEngineCommand:
    """Tests para EngineCommand."""

    def test_engine_command_pause(self):
        """Crear comando de pause."""
        cmd = EngineCommand(
            command="pause",
            payload={},
        )
        assert cmd.command == "pause"

    def test_engine_command_resume(self):
        """Crear comando de resume."""
        cmd = EngineCommand(
            command="resume",
            payload={},
        )
        assert cmd.command == "resume"

    def test_engine_command_with_payload(self):
        """Crear comando con payload."""
        cmd = EngineCommand(
            command="set_workers",
            payload={"workers": 5},
        )
        assert cmd.command == "set_workers"
        assert cmd.payload["workers"] == 5

    def test_engine_command_set_mode(self):
        """Crear comando de set_mode."""
        cmd = EngineCommand(
            command="set_mode",
            payload={"mode": "browser"},
        )
        assert cmd.payload["mode"] == "browser"

    def test_engine_command_is_frozen(self):
        """EngineCommand es inmutable."""
        cmd = EngineCommand(
            command="pause",
            payload={},
        )
        with pytest.raises(ValidationError):
            cmd.command = "resume"

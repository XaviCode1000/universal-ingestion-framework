"""
TUI Message System - Eventos tipados para comunicación Engine ↔ TUI.

Arquitectura:
    EngineCore emite eventos → Queue → TUICallback → post_message → Widgets

Todos los modelos son inmutables (frozen=True) para thread-safety.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class TUIEvent(BaseModel):
    """Base inmutable para todos los eventos de la UI."""

    model_config = {"frozen": True}
    timestamp: datetime = Field(default_factory=datetime.now)


# ═══════════════════════════════════════════════════════════════════════════════
# CANAL: PROGRESS (100ms interval)
# ═══════════════════════════════════════════════════════════════════════════════


class ProgressUpdate(TUIEvent):
    """Actualización de progreso para barras y contadores."""

    pages_completed: int
    pages_total: int
    assets_completed: int
    assets_total: int
    urls_seen: int
    assets_seen: int


# ═══════════════════════════════════════════════════════════════════════════════
# CANAL: SPEED (1s interval)
# ═══════════════════════════════════════════════════════════════════════════════


class SpeedUpdate(TUIEvent):
    """Métricas de velocidad para sparkline y ETA."""

    speed_current: float  # pages/s actual
    speed_average: float  # promedio desde inicio
    speed_max: float  # máximo alcanzado
    eta_seconds_best: int  # ETA optimista
    eta_seconds_worst: int  # ETA pesimista
    speed_history: list[float] = Field(default_factory=list)  # últimos 60 valores


# ═══════════════════════════════════════════════════════════════════════════════
# CANAL: ACTIVITY (evento, throttled 10/s)
# ═══════════════════════════════════════════════════════════════════════════════


class ActivityEvent(TUIEvent):
    """Notificación de página procesada para el feed."""

    url: str
    title: str
    engine: str  # trafilatura, html-to-markdown, readability, etc.
    status: Literal["success", "warning", "error"]
    elapsed_ms: float
    size_bytes: int = 0


class NetworkRetryEvent(TUIEvent):
    """Evento de reintento de red.

    Se emite cuando una petición falla y se reintenta automáticamente.
    Útil para debugging de problemas de conectividad.
    """

    url: str
    attempt_number: int
    wait_time: float  # segundos de espera antes del reintento
    reason: str  # TimeoutError, ConnectionError, HTTP 429, etc.


class CircuitStateEvent(TUIEvent):
    """Evento de cambio de estado del Circuit Breaker por dominio.

    Se emite cuando el circuit breaker cambia de estado (closed → open → half-open).
    """

    domain: str
    old_state: Literal["closed", "open", "half-open"]
    new_state: Literal["closed", "open", "half-open"]
    failure_count: int  # cantidad de fallos que motivaron el cambio


# ═══════════════════════════════════════════════════════════════════════════════
# CANAL: ERRORS (evento, NO throttled)
# ═══════════════════════════════════════════════════════════════════════════════


class ErrorEvent(TUIEvent):
    """Error que requiere atención del usuario."""

    url: str
    error_type: str  # TimeoutError, ConnectionError, etc.
    error_message: str
    stack_trace: str | None = None
    retry_count: int = 0
    is_fatal: bool = False


# ═══════════════════════════════════════════════════════════════════════════════
# CANAL: SYSTEM (500ms interval)
# ═══════════════════════════════════════════════════════════════════════════════


class SystemStatus(TUIEvent):
    """Estado del sistema para la barra de estado."""

    circuit_state: Literal["closed", "open", "half-open"]
    queue_pending: int
    error_count: int
    memory_mb: int
    cpu_percent: float
    current_url: str
    current_worker: int


# ═══════════════════════════════════════════════════════════════════════════════
# CANAL: STATE (evento)
# ═══════════════════════════════════════════════════════════════════════════════


class StateChange(TUIEvent):
    """Cambio de estado del engine."""

    state: Literal[
        "starting",
        "running",
        "paused",
        "mission_complete",
        "finalizing",
        "stopping",
        "stopped",
        "error",
    ]
    mode: Literal["stealth", "browser"]
    previous_state: str | None = None
    reason: str | None = (
        None  # Por qué cambió (user_request, error, completed, queue_exhausted)
    )


# ═══════════════════════════════════════════════════════════════════════════════
# ALERTAS (evento, NO throttled)
# ═══════════════════════════════════════════════════════════════════════════════


class Alert(TUIEvent):
    """Alerta para sistema de notificaciones (toast/banner/modal)."""

    level: Literal["info", "warning", "error", "critical"]
    title: str
    message: str
    source: str  # circuit_breaker, rate_limiter, captcha_detector, etc.
    action_required: bool = False
    suggested_action: str | None = None


# ═══════════════════════════════════════════════════════════════════════════════
# COMANDOS (TUI → Engine)
# ═══════════════════════════════════════════════════════════════════════════════


class EngineCommand(BaseModel):
    """Comando de la TUI hacia el Engine."""

    model_config = {"frozen": True}

    command: Literal[
        "pause",
        "resume",
        "stop",
        "skip_current",
        "retry_failed",
        "set_workers",
        "set_mode",
    ]
    payload: dict[str, Any] = Field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = [
    "TUIEvent",
    "ProgressUpdate",
    "SpeedUpdate",
    "ActivityEvent",
    "NetworkRetryEvent",
    "CircuitStateEvent",
    "ErrorEvent",
    "SystemStatus",
    "StateChange",
    "Alert",
    "EngineCommand",
]

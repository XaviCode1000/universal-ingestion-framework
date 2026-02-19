"""Centralized constants for UIF Migration Engine.

Eliminates magic numbers and strings throughout the codebase.
Reference: AGENTS.md best practices - Separar configuración de lógica.
"""

# ============================================================================
# TIMEOUTS
# ============================================================================

# Browser mode fetch timeout (ms) - usado cuando AsyncFetcher falla con 403/429
DEFAULT_BROWSER_TIMEOUT_MS: int = 45000  # 45 segundos

# Queue get timeout (seconds) - tiempo máximo esperando por un item en la cola
DEFAULT_QUEUE_TIMEOUT_SECONDS: float = 1.0

# Shutdown wait timeout (seconds) - tiempo para confirmar cancelación de workers
DEFAULT_SHUTDOWN_TIMEOUT_SECONDS: float = 5.0

# Minimum shutdown timeout when tasks are pending
MIN_SHUTDOWN_TIMEOUT_SECONDS: float = 30.0

# ============================================================================
# SIZE LIMITS
# ============================================================================

# Maximum HTML size to process (bytes) - prevenir OOM con páginas gigantes
MAX_HTML_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB

# Maximum URL length - límite razonable para evitar issues de storage
MAX_URL_LENGTH: int = 2048

# ============================================================================
# RETRY & BACKOFF
# ============================================================================

# Maximum backoff time for circuit breaker (seconds)
MAX_CIRCUIT_BREAKER_BACKOFF_SECONDS: float = 30.0

# ============================================================================
# UI UPDATE FREQUENCY
# ============================================================================

# Dashboard refresh rate (Hz)
DASHBOARD_REFRESH_RATE: int = 4  # 4 updates per second

# Dashboard update interval (seconds)
DASHBOARD_UPDATE_INTERVAL: float = 0.25

# ============================================================================
# HTTP SESSION
# ============================================================================

# HTTP cache max connections per host
HTTP_MAX_CONNECTIONS_PER_HOST: int = 10

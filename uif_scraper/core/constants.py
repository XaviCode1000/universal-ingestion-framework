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

# ============================================================================
# V4.0 RESILIENCE & SCALE CONSTANTS
# ============================================================================

# Memory management
SEEN_URLS_CACHE_MAXSIZE: int = 100000
SEEN_ASSETS_CACHE_MAXSIZE: int = 100000
SEEN_CACHE_TTL_SECONDS: int = 3600

# DB Batching
DEFAULT_DB_BATCH_SIZE: int = 100
DEFAULT_DB_BATCH_INTERVAL: float = 1.0
DB_PAGINATION_LIMIT: int = 1000

# Robots.txt
ROBOTS_CACHE_MAXSIZE: int = 100
ROBOTS_CACHE_TTL_SECONDS: int = 3600
ROBOTS_FETCH_TIMEOUT: int = 10

# CAPTCHA Detection
CAPTCHA_CONFIDENCE_THRESHOLD: float = 0.8

# Adaptive Rate Limiting Jitter
DEFAULT_JITTER_MAX: float = 0.5

# Paths
DEFAULT_DATA_DIR: str = "data"
LOGS_DIR: str = "logs"
RAW_DIR: str = "raw"
PROCESSED_DIR: str = "processed"

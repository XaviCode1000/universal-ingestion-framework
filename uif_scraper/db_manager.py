from __future__ import annotations

import time
from urllib.parse import urlparse

from uif_scraper.db_pool import SQLitePool
from uif_scraper.models import MigrationStatus


class StateManager:
    """Gestión de estado de URLs con SQLite y pool de conexiones.
    
    Incluye caché de estadísticas para reducir presión en la DB.
    """

    def __init__(self, pool: SQLitePool, stats_cache_ttl: float = 5.0):
        self.pool = pool
        self._stats_cache: dict[str, int] | None = None
        self._stats_cached_at: float = 0
        self._stats_cache_ttl = stats_cache_ttl

    async def initialize(self) -> None:
        """Inicializa la tabla de URLs con índices optimizados."""
        async with self.pool.acquire() as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS urls (
                    url TEXT PRIMARY KEY,
                    status TEXT NOT NULL DEFAULT 'pending',
                    type TEXT,
                    retries INTEGER DEFAULT 0,
                    last_error TEXT,
                    last_try TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            # Índices para queries comunes
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_status_type ON urls(status, type)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_retries ON urls(retries)"
            )
            # Índices para queries temporales
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_discovered_at ON urls(discovered_at)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_last_try ON urls(last_try)"
            )
            # Índice compuesto para queries frecuentes
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_status_type_retries ON urls(status, type, retries)"
            )
            await db.commit()

    async def add_url(
        self, url: str, status: MigrationStatus, m_type: str = "webpage"
    ) -> None:
        """Agrega una URL individual a la base de datos con validación temprana.
        
        Args:
            url: URL a agregar
            status: Estado inicial
            m_type: Tipo de recurso ("webpage" o "asset")
        
        Raises:
            ValueError: Si la URL tiene formato inválido o es demasiado larga.
        """
        # Validación temprana de URL
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid URL format: {url}")
        if len(url) > 2048:  # Límite práctico de URL
            raise ValueError(f"URL too long: {len(url)} chars")
        
        async with self.pool.acquire() as db:
            await db.execute(
                "INSERT OR IGNORE INTO urls (url, status, type) VALUES (?, ?, ?)",
                (url, status.value, m_type),
            )
            await db.commit()

    async def add_urls_batch(
        self, urls: list[tuple[str, MigrationStatus, str]], batch_size: int = 500
    ) -> None:
        """Inserción batch eficiente para múltiples URLs con tamaño óptimo.
        
        Args:
            urls: Lista de tuplas (url, status, type)
            batch_size: Tamaño máximo de cada batch para evitar locks largos.
        
        Nota:
            Los batches más grandes pueden causar locks prolongados en SQLite.
            El valor por defecto (500) balancea performance y concurrencia.
        """
        if not urls:
            return
        
        # Validación temprana de todas las URLs antes de insertar
        for url, _, _ in urls:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError(f"Invalid URL format: {url}")
            if len(url) > 2048:
                raise ValueError(f"URL too long: {len(url)} chars")
        
        # Procesar en batches más pequeños para evitar locks largos
        for i in range(0, len(urls), batch_size):
            batch = urls[i : i + batch_size]
            async with self.pool.acquire() as db:
                await db.executemany(
                    "INSERT OR IGNORE INTO urls (url, status, type) VALUES (?, ?, ?)",
                    [(u, s.value, t) for u, s, t in batch],
                )
                await db.commit()

    async def update_status(
        self, url: str, status: MigrationStatus, error_msg: str | None = None
    ) -> None:
        """Actualiza el estado de una URL con truncado seguro de errores."""
        async with self.pool.acquire() as db:
            if error_msg:
                # Truncar errores a 500 chars (AGENTS.md requirement)
                await db.execute(
                    "UPDATE urls SET status = ?, last_error = ?, last_try = CURRENT_TIMESTAMP WHERE url = ?",
                    (status.value, error_msg[:500], url),
                )
            else:
                await db.execute(
                    "UPDATE urls SET status = ?, last_error = NULL, last_try = CURRENT_TIMESTAMP WHERE url = ?",
                    (status.value, url),
                )
            await db.commit()

    async def increment_retry(self, url: str) -> int:
        """Incrementa contador de reintentos y retorna el nuevo valor."""
        async with self.pool.acquire() as db:
            await db.execute(
                "UPDATE urls SET retries = retries + 1, last_try = CURRENT_TIMESTAMP WHERE url = ?",
                (url,),
            )
            await db.commit()
            async with db.execute(
                "SELECT retries FROM urls WHERE url = ?", (url,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_pending_urls(
        self, m_type: str = "webpage", max_retries: int = 3
    ) -> list[str]:
        """Obtiene URLs pendientes o fallidas con reintentos disponibles."""
        async with self.pool.acquire() as db:
            query = """
                SELECT url FROM urls
                WHERE type = ? AND (
                    status = ?
                    OR (status = ? AND retries < ?)
                )
            """
            async with db.execute(
                query,
                (
                    m_type,
                    MigrationStatus.PENDING.value,
                    MigrationStatus.FAILED.value,
                    max_retries,
                ),
            ) as cursor:
                rows = await cursor.fetchall()
                return [str(row[0]) for row in rows]

    async def get_stats(self, force_refresh: bool = False) -> dict[str, int]:
        """Obtiene estadísticas de estado con caché TTL.
        
        Args:
            force_refresh: Si True, invalida el caché y consulta la DB.
        
        Returns:
            Diccionario con conteo por estado: {"completed": 100, "pending": 50, ...}
        """
        now = time.time()
        
        # Usar caché si es válido y no se fuerza refresh
        if (
            not force_refresh
            and self._stats_cache is not None
            and (now - self._stats_cached_at) < self._stats_cache_ttl
        ):
            return self._stats_cache
        
        async with self.pool.acquire() as db:
            query = """
                SELECT status, COUNT(*) as count
                FROM urls
                GROUP BY status
            """
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                self._stats_cache = {str(row[0]): int(row[1]) for row in rows}
                self._stats_cached_at = now
                return self._stats_cache

    def invalidate_stats_cache(self) -> None:
        """Invalida el caché de estadísticas cuando hay cambios significativos."""
        self._stats_cache = None
        self._stats_cached_at = 0

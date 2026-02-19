from __future__ import annotations

import asyncio
import time
from urllib.parse import urlparse

from uif_scraper.db_pool import SQLitePool
from uif_scraper.models import MigrationStatus


class StateManager:
    """Gestión de estado de URLs con SQLite y pool de conexiones.
    
    Incluye:
    - Caché de estadísticas con TTL para reducir presión en DB
    - Buffer de actualizaciones para batch processing
    - Validación temprana de URLs
    """

    def __init__(
        self,
        pool: SQLitePool,
        stats_cache_ttl: float = 5.0,
        batch_interval: float = 1.0,
        batch_size: int = 100,
    ):
        self.pool = pool
        self._stats_cache: dict[str, int] | None = None
        self._stats_cached_at: float = 0
        self._stats_cache_ttl = stats_cache_ttl
        
        # Batch update buffers para reducir commits individuales
        self._status_buffer: list[tuple[str, str, str | None]] = []
        self._buffer_lock = asyncio.Lock()
        self._batch_interval = batch_interval
        self._batch_size = batch_size
        self._batch_task: asyncio.Task[None] | None = None
        self._flush_lock = asyncio.Lock()

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

    async def _start_batch_processor(self) -> None:
        """Inicia procesador batch en background para flush periódico."""
        
        async def process_batches() -> None:
            while True:
                await asyncio.sleep(self._batch_interval)
                await self._flush_status_buffer()
        
        self._batch_task = asyncio.create_task(process_batches())

    async def _flush_status_buffer(self) -> None:
        """Flushea buffer de actualizaciones en batch para reducir commits."""
        async with self._flush_lock:
            async with self._buffer_lock:
                if not self._status_buffer:
                    return
                
                batch = self._status_buffer.copy()
                self._status_buffer.clear()
            
            if batch:
                async with self.pool.acquire() as db:
                    await db.executemany(
                        """UPDATE urls 
                           SET status = ?, last_error = ?, last_try = CURRENT_TIMESTAMP 
                           WHERE url = ?""",
                        [(status, url, error) for status, url, error in batch],
                    )
                    await db.commit()

    async def start_batch_processor(self) -> None:
        """Inicia el procesador batch explícitamente.
        
        Nota: El batch processor NO se inicia automáticamente en __init__.
        Debe llamarse a este método explícitamente cuando se desea usar
        buffering batch.
        """
        if self._batch_task is None:
            await self._start_batch_processor()

    async def stop_batch_processor(self) -> None:
        """Detiene el procesador batch y flushea pendientes."""
        if self._batch_task:
            self._batch_task.cancel()
            try:
                await self._batch_task
            except asyncio.CancelledError:
                pass
            self._batch_task = None
        
        # Flush final
        await self._flush_status_buffer()

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
        self,
        url: str,
        status: MigrationStatus,
        error_msg: str | None = None,
        immediate: bool = False,
    ) -> None:
        """Actualiza estado de URL con buffering batch opcional.
        
        Args:
            url: URL a actualizar
            status: Nuevo estado
            error_msg: Mensaje de error (opcional, se trunca a 500 chars)
            immediate: Si True, actualiza inmediatamente (para errores críticos)
        
        Nota:
            Por defecto (immediate=False), las actualizaciones se bufferizan
            y se flushean cada batch_interval segundos o cuando se alcanza
            batch_size actualizaciones.
        """
        if immediate:
            # Actualización inmediata para casos críticos
            async with self.pool.acquire() as db:
                if error_msg:
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
        else:
            # Buffer para batch processing - orden: (status, error_msg, url)
            async with self._buffer_lock:
                self._status_buffer.append(
                    (status.value, url, error_msg[:500] if error_msg else None)
                )
            
            # Flush inmediato si buffer supera threshold
            if len(self._status_buffer) >= self._batch_size:
                await self._flush_status_buffer()

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

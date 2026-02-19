"""Gestión de sesiones HTTP con connection pooling optimizado."""

from __future__ import annotations

import logging
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)


class HTTPSessionCache:
    """Caché de sesiones HTTP reutilizables con connection pooling.
    
    Proporciona:
    - Connection pooling con límites configurables
    - DNS caching para reducir resolución
    - Keep-alive para reutilizar conexiones
    - Timeouts configurables por operación
    - Cleanup automático de conexiones cerradas
    
    Uso:
        cache = HTTPSessionCache()
        session = await cache.get_session()
        async with session.get(url) as response:
            content = await response.read()
        
        # Al finalizar:
        await cache.close()
    """

    def __init__(
        self,
        max_pool_size: int = 100,
        max_connections_per_host: int = 20,
        timeout_total: float = 30.0,
        timeout_connect: float = 10.0,
        timeout_read: float = 20.0,
    ):
        """Inicializa caché de sesiones HTTP.
        
        Args:
            max_pool_size: Límite total de conexiones simultáneas
            max_connections_per_host: Límite de conexiones por dominio
            timeout_total: Timeout máximo total en segundos
            timeout_connect: Timeout para establecimiento de conexión
            timeout_read: Timeout para lectura de respuesta
        """
        self._session: Optional[aiohttp.ClientSession] = None
        self._max_pool_size = max_pool_size
        self._max_per_host = max_connections_per_host
        self._timeout_total = timeout_total
        self._timeout_connect = timeout_connect
        self._timeout_read = timeout_read
        self._connector: Optional[aiohttp.TCPConnector] = None

    def _create_connector(self) -> aiohttp.TCPConnector:
        """Configura connection pooling optimizado."""
        return aiohttp.TCPConnector(
            limit=self._max_pool_size,  # Total conexiones simultáneas
            limit_per_host=self._max_per_host,  # Por dominio
            ttl_dns_cache=300,  # DNS cache 5 min
            use_dns_cache=True,
            enable_cleanup_closed=True,  # Limpia conexiones cerradas
            force_close=False,  # Reutiliza conexiones
            keepalive_timeout=30,  # Keep-alive 30s
            ssl=False,  # Opcional: deshabilitar SSL verify para scraping
        )

    async def get_session(self) -> aiohttp.ClientSession:
        """Obtiene o crea una sesión HTTP reutilizable.
        
        Returns:
            aiohttp.ClientSession configurada con pooling
        """
        if self._session is None or self._session.closed:
            self._connector = self._create_connector()
            self._session = aiohttp.ClientSession(
                connector=self._connector,
                timeout=aiohttp.ClientTimeout(
                    total=self._timeout_total,
                    connect=self._timeout_connect,
                    sock_read=self._timeout_read,
                    sock_connect=self._timeout_connect,
                ),
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;"
                    "q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Cache-Control": "max-age=0",
                },
                raise_for_status=False,
            )
            logger.debug(
                "Created new HTTP session with pool_size=%d, per_host=%d",
                self._max_pool_size,
                self._max_per_host,
            )
        
        return self._session

    async def close(self) -> None:
        """Cierra la sesión y libera conexiones."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("HTTP session closed")
        
        if self._connector and not self._connector.closed:
            await self._connector.close()
            logger.debug("HTTP connector closed")
        
        self._session = None
        self._connector = None

    @property
    def is_active(self) -> bool:
        """Verifica si la sesión está activa."""
        return self._session is not None and not self._session.closed

"""Motor de cumplimiento legal para robots.txt."""

from __future__ import annotations

import asyncio
from urllib.robotparser import RobotFileParser

from cachetools import TTLCache
from loguru import logger

from uif_scraper.utils.http_session import HTTPSessionCache


class RobotsChecker:
    """Validador de cumplimiento de directivas robots.txt.

    Mantiene un caché de parsers por dominio para evitar peticiones redundantes.
    """

    def __init__(self, session_cache: HTTPSessionCache) -> None:
        """Inicializa el verificador de robots.

        Args:
            session_cache: Caché de sesiones HTTP para obtener el robots.txt
        """
        self.session_cache = session_cache
        # Caché de parsers con TTL de 1 hora
        self._parsers: TTLCache[str, RobotFileParser] = TTLCache(maxsize=100, ttl=3600)
        self._lock = asyncio.Lock()

    async def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        """Verifica si una URL puede ser rastreada según robots.txt.

        Args:
            url: URL a verificar
            user_agent: User-agent para la verificación

        Returns:
            True si el rastreo está permitido o si no se pudo obtener el robots.txt
        """
        from urllib.parse import urlparse

        parsed_url = urlparse(url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        robots_url = f"{domain}/robots.txt"

        async with self._lock:
            if domain not in self._parsers:
                parser = RobotFileParser()
                try:
                    session = await self.session_cache.get_session()
                    async with session.get(robots_url, timeout=10) as response:
                        if response.status == 200:
                            content = await response.text()
                            parser.parse(content.splitlines())
                        elif response.status in (401, 403):
                            # Si es 401/403, asumimos que no se permite nada
                            parser.disallow_all = True
                        else:
                            # Otros errores (404, etc.) suelen implicar que se permite todo
                            parser.allow_all = True
                except Exception as e:
                    logger.warning(
                        f"Error cargando robots.txt para {domain}: {str(e)[:100]}"
                    )
                    # En caso de error, permitimos por defecto para no bloquear si el sitio está caído
                    parser.allow_all = True

                self._parsers[domain] = parser

        parser = self._parsers[domain]
        # RobotFileParser.can_fetch es síncrono y rápido una vez parseado
        return bool(parser.can_fetch(user_agent, url))

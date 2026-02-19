from __future__ import annotations

import hashlib
from functools import lru_cache
from typing import Any
from urllib.parse import urlparse

import trafilatura
from selectolax.parser import HTMLParser

from uif_scraper.extractors.base import IExtractor


class MetadataExtractor(IExtractor):
    """Extractor de metadata con caché LRU para contenido repetido.

    Usa functools.lru_cache que es:
    - Thread-safe por defecto
    - Más rápido que implementación custom
    - Incluye cache_info() para monitoring
    - maxsize configurable para controlar memoria
    """

    def __init__(self, cache_size: int = 1000):
        """Inicializa extractor con caché LRU.

        Args:
            cache_size: Máximo de entradas en caché (1000 por defecto).
                       Cada entrada ~1KB, total ~1MB de memoria.
        """
        self._cache_size = cache_size
        # Configurar caché dinámicamente
        self._extract_metadata_cached = lru_cache(maxsize=cache_size)(
            self._extract_metadata_pure
        )

    def _extract_metadata_pure(
        self, content_hash: str, content: str, url: str
    ) -> dict[str, Any]:
        """Extracción pura de metadata (sin efectos secundarios).

        Args:
            content_hash: Hash del contenido para caché
            content: HTML crudo
            url: URL de origen

        Returns:
            Diccionario con metadata extraída
        """
        tree = HTMLParser(content)
        domain = urlparse(url).netloc

        og_title = tree.css_first('meta[property="og:title"]')
        title_tag = tree.css_first("title")
        h1 = tree.css_first("h1")

        title: str = "Documento"
        detected_title: str | None = None

        if og_title and og_title.attributes.get("content"):
            detected_title = og_title.attributes.get("content")
        elif title_tag:
            detected_title = title_tag.text(strip=True)
        elif h1:
            detected_title = h1.text(strip=True)

        if detected_title:
            title = str(detected_title).split("|")[0].split(" - ")[0].strip()

        try:
            traf_metadata = trafilatura.extract_metadata(content)
        except Exception:
            traf_metadata = None

        return {
            "url": url,
            "title": title,
            "author": getattr(traf_metadata, "author", "Desconocido")
            if traf_metadata
            else "Desconocido",
            "date": getattr(traf_metadata, "date", "N/A") if traf_metadata else "N/A",
            "sitename": getattr(traf_metadata, "sitename", domain)
            if traf_metadata
            else domain,
            "ingestion_engine": "UIF v3.0",
        }

    async def extract(self, content: Any, url: str) -> dict[str, Any]:
        """Extrae metadata con caché LRU automático.

        El caché usa hash del contenido para detectar duplicados,
        permitiendo reutilizar resultados para URLs diferentes con
        el mismo HTML.

        Args:
            content: HTML crudo
            url: URL de origen

        Returns:
            Diccionario con metadata extraída
        """
        if not content or not isinstance(content, str):
            return {}

        # Hash del contenido para caché (primeros 10KB son suficientes)
        content_hash = hashlib.md5(content[:10000].encode()).hexdigest()

        # Extraer con caché
        result = self._extract_metadata_cached(content_hash, content, url)

        return result

    def get_cache_info(self) -> dict[str, Any]:
        """Obtiene estadísticas de caché para monitoring.

        Returns:
            Diccionario con hits, misses, tamaño actual y máximo.
        """
        info = self._extract_metadata_cached.cache_info()
        return {
            "hits": info.hits,
            "misses": info.misses,
            "maxsize": info.maxsize if info.maxsize is not None else 0,
            "currsize": info.currsize,
            "hit_rate_percent": round(
                (info.hits / (info.hits + info.misses) * 100)
                if (info.hits + info.misses) > 0
                else 0,
                2,
            ),
        }

    def clear_cache(self) -> None:
        """Limpia completamente la caché de metadata."""
        self._extract_metadata_cached.cache_clear()

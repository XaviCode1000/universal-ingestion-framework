from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from typing import Any
from urllib.parse import urlparse

import trafilatura
from pydantic import BaseModel, Field
from selectolax.parser import HTMLParser

from uif_scraper.extractors.base import IExtractor


class DocumentHeader(BaseModel):
    """Header extraído del documento para TOC."""

    model_config = {"frozen": True}

    level: int = Field(ge=1, le=6)
    text: str
    id: str | None = None


class ExtendedMetadata(BaseModel):
    """Metadata completa del documento para RAG optimizado."""

    model_config = {"frozen": True}

    # Metadata básica (existente)
    url: str
    title: str = "Documento"
    author: str = "Desconocido"
    date: str = "N/A"
    sitename: str
    ingestion_engine: str = "UIF v3.0"

    # Metadata expandida (nueva)
    description: str | None = None
    keywords: list[str] = Field(default_factory=list)

    # Open Graph
    og_title: str | None = None
    og_description: str | None = None
    og_image: str | None = None
    og_type: str | None = None

    # Twitter Cards
    twitter_card: str | None = None
    twitter_site: str | None = None
    twitter_title: str | None = None

    # Structured Data
    json_ld: dict[str, Any] | None = None

    # Estructura del documento (para Fase B)
    headers: list[DocumentHeader] = Field(default_factory=list)


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
        """Extracción completa de metadata con soporte OG, Twitter, JSON-LD.

        Args:
            content_hash: Hash del contenido para caché
            content: HTML crudo
            url: URL de origen

        Returns:
            Diccionario con metadata completa extraída
        """
        tree = HTMLParser(content)
        domain = urlparse(url).netloc

        # === HELPERS ===
        def get_meta(prop_type: str, name: str) -> str | None:
            """Extrae valor de meta tag por property o name."""
            tag = tree.css_first(f'meta[{prop_type}="{name}"]')
            return tag.attributes.get("content") if tag else None

        # === OPEN GRAPH ===
        og_title = get_meta("property", "og:title")
        og_description = get_meta("property", "og:description")
        og_image = get_meta("property", "og:image")
        og_type = get_meta("property", "og:type")

        # === TWITTER CARDS ===
        twitter_card = get_meta("name", "twitter:card")
        twitter_site = get_meta("name", "twitter:site")
        twitter_title = get_meta("name", "twitter:title")

        # === META TAGS ESTÁNDAR ===
        meta_description = get_meta("name", "description")
        meta_keywords = get_meta("name", "keywords") or ""
        keywords = [k.strip() for k in meta_keywords.split(",") if k.strip()]

        # === JSON-LD (Structured Data) ===
        json_ld: dict[str, Any] | None = None
        json_ld_tag = tree.css_first('script[type="application/ld+json"]')
        if json_ld_tag:
            try:
                json_ld = json.loads(json_ld_tag.text())
            except (json.JSONDecodeError, ValueError):
                json_ld = None

        # === TITLE (fallback chain) ===
        title_tag = tree.css_first("title")
        h1 = tree.css_first("h1")

        title: str = "Documento"
        detected_title: str | None = None

        # Prioridad: OG > title tag > H1
        if og_title:
            detected_title = og_title
        elif title_tag:
            detected_title = title_tag.text(strip=True)
        elif h1:
            detected_title = h1.text(strip=True)

        if detected_title:
            title = str(detected_title).split("|")[0].split(" - ")[0].strip()

        # === TRAFILATURA METADATA (fallback) ===
        try:
            traf_metadata = trafilatura.extract_metadata(content)
        except Exception:
            traf_metadata = None

        # Author: meta tag > trafilatura
        author = get_meta("name", "author")
        if not author:
            author = (
                getattr(traf_metadata, "author", "Desconocido")
                if traf_metadata
                else "Desconocido"
            )

        # Date: JSON-LD > trafilatura
        date = "N/A"
        if json_ld and isinstance(json_ld, dict):
            date = json_ld.get("datePublished") or json_ld.get("dateCreated") or "N/A"
        if date == "N/A" and traf_metadata:
            date = getattr(traf_metadata, "date", "N/A") or "N/A"

        # Sitename: OG > trafilatura > domain
        sitename = get_meta("property", "og:site_name")
        if not sitename:
            sitename = (
                getattr(traf_metadata, "sitename", domain) if traf_metadata else domain
            )

        # === HEADERS H1-H6 (para TOC - Fase B) ===
        headers: list[DocumentHeader] = []
        for level in range(1, 7):
            for h in tree.css(f"h{level}"):
                header_text = h.text(strip=True)
                if header_text:  # Solo agregar si tiene texto
                    headers.append(
                        DocumentHeader(
                            level=level,
                            text=header_text,
                            id=h.attributes.get("id"),
                        )
                    )

        # === CONSTRUIR RESPONSE ===
        metadata = ExtendedMetadata(
            url=url,
            title=title,
            author=author,
            date=date,
            sitename=sitename,
            description=meta_description,
            keywords=keywords,
            og_title=og_title,
            og_description=og_description,
            og_image=og_image,
            og_type=og_type,
            twitter_card=twitter_card,
            twitter_site=twitter_site,
            twitter_title=twitter_title,
            json_ld=json_ld,
            headers=headers,
        )

        return metadata.model_dump()

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

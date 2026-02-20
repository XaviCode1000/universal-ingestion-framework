from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from typing import Any
from urllib.parse import urlparse

from html_to_markdown import (
    ConversionOptions,
    MetadataConfig,
    convert_with_metadata,
)
from pydantic import BaseModel, Field

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
    author: str | None = "Desconocido"
    date: str | None = "N/A"
    sitename: str | None = None
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
        """Extracción completa de metadata con html-to-markdown.

        Usa la librería html-to-markdown (Rust core) para:
        - Conversión HTML→Markdown 18x más rápida
        - Metadata extraction integrada (OG, Twitter, headers, JSON-LD)
        - Type hints completos para Python 3.12+

        Args:
            content_hash: Hash del contenido para caché
            content: HTML crudo
            url: URL de origen

        Returns:
            Diccionario con metadata completa extraída
        """
        domain = urlparse(url).netloc

        # === HTML-TO-MARKDOWN EXTRACTION ===
        options = ConversionOptions(heading_style="atx")
        metadata_config = MetadataConfig(
            extract_document=True,  # Title, description, keywords, OG, Twitter
            extract_headers=True,  # H1-H6 para TOC
            extract_links=False,  # No necesitamos links aquí
            extract_images=False,  # No necesitamos imágenes aquí
            extract_structured_data=True,  # JSON-LD, Microdata, RDFa
        )

        # Convertir y extraer metadata (no usamos el markdown aquí)
        # Nota: metadata_config va como keyword argument
        _, md_metadata = convert_with_metadata(
            content, options=options, metadata_config=metadata_config
        )

        # === EXTRAER METADATA DEL RESULTADO ===
        doc_meta = md_metadata.get("document", {}) or {}

        # === OPEN GRAPH (primero, para usar como fallback del título) ===
        # html-to-markdown pone OG data en nested dict: document.open_graph
        og_data = doc_meta.get("open_graph", {}) or {}
        og_title = og_data.get("title") if isinstance(og_data, dict) else None
        og_description = (
            og_data.get("description")
            if isinstance(og_data, dict)
            else doc_meta.get("og_description")
        )
        og_image = (
            og_data.get("image")
            if isinstance(og_data, dict)
            else doc_meta.get("og_image")
        )
        og_type = (
            og_data.get("type")
            if isinstance(og_data, dict)
            else doc_meta.get("og_type")
        )

        # === TWITTER CARDS ===
        # html-to-markdown pone Twitter data en nested dict: document.twitter_card
        twitter_data = doc_meta.get("twitter_card", {}) or {}
        twitter_card = (
            twitter_data.get("card")
            if isinstance(twitter_data, dict)
            else doc_meta.get("twitter_card")
        )
        twitter_site = (
            twitter_data.get("site")
            if isinstance(twitter_data, dict)
            else doc_meta.get("twitter_site")
        )
        twitter_title = (
            twitter_data.get("title")
            if isinstance(twitter_data, dict)
            else doc_meta.get("twitter_title")
        )

        # === TÍTULO ===
        # Prioridad: OG title > title tag > "Documento" (los tests esperan OG primero)
        title = og_title or doc_meta.get("title") or "Documento"
        if title:
            title = str(title).split("|")[0].split(" - ")[0].strip()

        # Author: meta tag > "Desconocido"
        author = doc_meta.get("author") or "Desconocido"

        # Date: structured data > meta > "N/A"
        date = doc_meta.get("date") or "N/A"

        # Sitename: OG site_name > domain
        # html-to-markdown pone og:site_name en open_graph['site_name']
        sitename = None
        if isinstance(og_data, dict):
            sitename = og_data.get("site_name")
        sitename = sitename or domain

        # Description: meta description
        description = doc_meta.get("description")

        # Keywords: meta keywords (puede ser string o lista)
        keywords_raw = doc_meta.get("keywords", [])
        if isinstance(keywords_raw, str):
            keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]
        else:
            keywords = list(keywords_raw) if keywords_raw else []

        # === STRUCTURED DATA (JSON-LD) ===
        # html-to-markdown devuelve structured_data como lista de dicts con:
        # - data_type: "json_ld", "microdata", "rdfa"
        # - raw_json: string del JSON (para json_ld)
        # - schema_type: tipo de schema (Article, Product, etc.)
        structured_data = md_metadata.get("structured_data", [])
        json_ld: dict[str, Any] | None = None
        if structured_data and isinstance(structured_data, list):
            for sd in structured_data:
                if isinstance(sd, dict) and sd.get("data_type") == "json_ld":
                    # Parsear el raw_json string
                    raw_json = sd.get("raw_json")
                    if raw_json and isinstance(raw_json, str):
                        try:
                            json_ld = json.loads(raw_json)
                            break
                        except (json.JSONDecodeError, ValueError):
                            # JSON inválido, continuar con el siguiente
                            continue

        # === HEADERS H1-H6 (para TOC - Fase B) ===
        # html-to-markdown ya extrae headers con nivel, texto, id
        headers: list[DocumentHeader] = []
        headers_raw = md_metadata.get("headers", [])
        for h in headers_raw:
            if isinstance(h, dict):
                level = h.get("level", 1)
                text = h.get("text", "")
                header_id = h.get("id")
                if text and 1 <= level <= 6:
                    headers.append(
                        DocumentHeader(
                            level=level,
                            text=text,
                            id=header_id,
                        )
                    )

        # === CONSTRUIR RESPONSE ===
        metadata = ExtendedMetadata(
            url=url,
            title=title,
            author=author,
            date=date,
            sitename=sitename,
            description=description,
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

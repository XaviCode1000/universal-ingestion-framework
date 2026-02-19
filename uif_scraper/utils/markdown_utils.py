"""Markdown processing utilities for RAG-optimized output.

This module provides utilities for enhancing markdown output:
- TOC (Table of Contents) generation from headers
- Relative URL resolution for clickable links

Reference: AGENTS.md - Single Responsibility Principle
"""

from __future__ import annotations

import re
from typing import Any

from uif_scraper.extractors.metadata_extractor import DocumentHeader


def generate_toc(
    headers: list[DocumentHeader],
    max_level: int = 3,
    title: str = "Tabla de Contenidos",
) -> str:
    """Genera TOC (Table of Contents) en markdown desde headers extraídos.

    Args:
        headers: Lista de DocumentHeader con level, text, id
        max_level: Nivel máximo de header a incluir (1-6, default 3)
        title: Título de la sección TOC

    Returns:
        String markdown con TOC formateado

    Example:
        >>> headers = [
        ...     DocumentHeader(level=1, text="Intro", id="intro"),
        ...     DocumentHeader(level=2, text="Setup", id="setup"),
        ... ]
        >>> print(generate_toc(headers))
        ## Tabla de Contenidos

        - [Intro](#intro)
          - [Setup](#setup)
    """
    if not headers:
        return ""

    # Filtrar headers por nivel máximo
    filtered_headers = [h for h in headers if 1 <= h.level <= max_level]

    if not filtered_headers:
        return ""

    toc_lines = [f"## {title}\n"]

    for header in filtered_headers:
        # Indentación basada en nivel (level 1 = 0 indent, level 2 = 2 spaces, etc.)
        indent = "  " * (header.level - 1)

        # Generar anchor: usar id si existe, si no generar desde texto
        anchor = header.id or _slugify_anchor(header.text)

        toc_lines.append(f"{indent}- [{header.text}](#{anchor})")

    return "\n".join(toc_lines) + "\n"


def _slugify_anchor(text: str) -> str:
    """Convierte texto a anchor válido para markdown.

    Args:
        text: Texto del header

    Returns:
        Anchor slug (lowercase, sin espacios ni caracteres especiales)
    """
    # Lowercase
    slug = text.lower()
    # Reemplazar espacios con guiones
    slug = re.sub(r"\s+", "-", slug)
    # Remover caracteres no alfanuméricos (excepto guiones)
    slug = re.sub(r"[^a-z0-9\-]", "", slug)
    # Remover guiones múltiples
    slug = re.sub(r"-+", "-", slug)
    # Remover guiones al inicio/final
    slug = slug.strip("-")
    return slug or "section"


def resolve_relative_links(markdown: str, base_url: str) -> str:
    """Convierte links relativos a absolutos en contenido markdown.

    Preserva:
    - Links absolutos (http://, https://)
    - Anchors (#section)
    - Emails (mailto:)
    - Imágenes
    - Links inline y reference-style

    Args:
        markdown: Contenido markdown con links posiblemente relativos
        base_url: URL base para resolver links relativos

    Returns:
        Markdown con links absolutos

    Example:
        >>> md = "[docs](/docs) and [home](../index.html)"
        >>> resolve_relative_links(md, "https://example.com/guides/intro/")
        '[docs](https://example.com/docs) and [home](https://example.com/index.html)'
    """
    if not markdown or not base_url:
        return markdown

    # Pattern para links inline: [text](url)
    # Captura: group(1)=text, group(2)=url
    inline_link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"

    def replace_inline_link(match: re.Match[str]) -> str:
        text = match.group(1)
        url = match.group(2)

        # Skip si ya es absoluto o especial
        if _is_special_url(url):
            return match.group(0)

        # Resolver URL relativa
        absolute_url = _resolve_url(base_url, url)
        return f"[{text}]({absolute_url})"

    # Pattern para imágenes: ![alt](url)
    image_pattern = r"!\[([^\]]*)\]\(([^)]+)\)"

    def replace_image_link(match: re.Match[str]) -> str:
        alt = match.group(1)
        url = match.group(2)

        if _is_special_url(url):
            return match.group(0)

        absolute_url = _resolve_url(base_url, url)
        return f"![{alt}]({absolute_url})"

    # Procesar imágenes primero (para no confundir con links)
    result = re.sub(image_pattern, replace_image_link, markdown)
    # Luego procesar links
    result = re.sub(inline_link_pattern, replace_inline_link, result)

    return result


def _is_special_url(url: str) -> bool:
    """Determina si una URL no debe ser procesada.

    Args:
        url: URL a verificar

    Returns:
        True si es URL especial (absoluta, anchor, mailto, etc.)
    """
    if not url:
        return True

    url_stripped = url.strip()

    # Links absolutos
    if url_stripped.startswith(("http://", "https://")):
        return True

    # Anchors
    if url_stripped.startswith("#"):
        return True

    # Email
    if url_stripped.startswith("mailto:"):
        return True

    # Teléfono
    if url_stripped.startswith("tel:"):
        return True

    # Data URIs
    if url_stripped.startswith("data:"):
        return True

    # JavaScript (no debería existir pero por seguridad)
    if url_stripped.startswith("javascript:"):
        return True

    return False


def _resolve_url(base_url: str, relative_url: str) -> str:
    """Resuelve URL relativa contra base URL.

    Args:
        base_url: URL base (debe ser absoluta)
        relative_url: URL relativa a resolver

    Returns:
        URL absoluta
    """
    # Normalizar base_url (remover trailing slash para consistencia)
    base = base_url.rstrip("/")

    # Si relative_url empieza con /, es root-relative
    if relative_url.startswith("/"):
        # Extraer scheme + domain
        from urllib.parse import urlparse

        parsed = urlparse(base)
        return f"{parsed.scheme}://{parsed.netloc}{relative_url}"

    # Para paths relativos normales, usar lógica simple
    # (urljoin de urllib.parse tiene edge cases indeseados)

    # Separar path del base
    if "/" in base:
        base_path = base.rsplit("/", 1)[0]
    else:
        base_path = base

    # Manejar ../
    path = relative_url
    while path.startswith("../"):
        # Subir un nivel en base_path
        if "/" in base_path:
            base_path = base_path.rsplit("/", 1)[0]
        path = path[3:]  # Remover "../"

    # Manejar ./
    path = path.removeprefix("./")

    # Construir URL final
    if path:
        return f"{base_path}/{path}"
    return base_path


def enhance_markdown_for_rag(
    markdown: str,
    metadata: dict[str, Any],
    base_url: str,
    toc_max_level: int = 3,
    include_toc: bool = True,
) -> str:
    """Pipeline completo de enhancement de markdown para RAG.

    Aplica:
    1. Generación de TOC (si hay headers y include_toc=True)
    2. Resolución de links relativos

    Args:
        markdown: Contenido markdown original
        metadata: Metadata del documento (debe incluir 'headers')
        base_url: URL base para resolver links
        toc_max_level: Nivel máximo de headers en TOC
        include_toc: Si incluir TOC al inicio

    Returns:
        Markdown enhanced para RAG
    """
    if not markdown:
        return markdown

    result = markdown

    # 1. Resolver links relativos
    result = resolve_relative_links(result, base_url)

    # 2. Agregar TOC si hay headers
    if include_toc and "headers" in metadata:
        headers_data = metadata["headers"]
        if headers_data:
            # Convertir dicts a DocumentHeader si es necesario
            headers = [
                DocumentHeader(**h) if isinstance(h, dict) else h for h in headers_data
            ]
            toc = generate_toc(headers, max_level=toc_max_level)
            if toc:
                # Insertar TOC después del primer párrafo si existe
                # o al inicio si no hay párrafos claros
                lines = result.split("\n")
                insert_pos = 0

                # Buscar dónde insertar (después del primer bloque de texto)
                for i, line in enumerate(lines):
                    if line.strip() and not line.startswith("#"):
                        insert_pos = i
                        break

                lines.insert(insert_pos, "\n" + toc + "\n")
                result = "\n".join(lines)

    return result

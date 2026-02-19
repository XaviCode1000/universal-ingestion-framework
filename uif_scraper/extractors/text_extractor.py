import io
import time
from typing import Any

import trafilatura
from loguru import logger
from markitdown import MarkItDown

from uif_scraper.extractors.base import IExtractor
from uif_scraper.utils.text_utils import clean_text


class TextExtractor(IExtractor):
    """Extractor de texto con fallback automático y métricas de performance."""

    def __init__(self) -> None:
        self.md_converter = MarkItDown()

    async def extract(self, content: Any, url: str) -> dict[str, Any]:
        """Extrae texto como markdown usando trafilatura con fallback a MarkItDown.
        
        Args:
            content: HTML crudo a procesar
            url: URL de origen para logging y debugging
        
        Returns:
            Diccionario con markdown extraído y motor utilizado.
        """
        # Defensive: ensure content is valid string
        if not content or not isinstance(content, str):
            logger.debug("Empty or invalid content for %s", url)
            return {"markdown": "", "engine": "none"}

        extracted_md: str | None = None
        engine = "trafilatura"
        error_context: dict[str, Any] = {}

        try:
            start_time = time.perf_counter()
            extracted_md = trafilatura.extract(
                content,
                include_tables=True,
                include_comments=False,
                output_format="markdown",
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            # Log métrica de performance para debugging
            if elapsed_ms > 1000:  # Más de 1 segundo es lento
                logger.warning(
                    "Trafilatura slow extraction",
                    extra={
                        "url": url,
                        "elapsed_ms": elapsed_ms,
                        "content_length": len(content),
                    },
                )
        except Exception as e:
            error_context = {
                "url": url,
                "error": str(e),
                "error_type": type(e).__name__,
                "content_length": len(content),
                "content_preview": content[:200] if len(content) > 200 else content,
            }
            logger.warning("Trafilatura extraction failed", extra=error_context)
            extracted_md = None

        # Fallback to MarkItDown if trafilatura result is insufficient
        if not extracted_md or len(extracted_md) < 250:
            try:
                html_stream = io.BytesIO(content.encode("utf-8"))
                conversion_result = self.md_converter.convert_stream(
                    html_stream, extension=".html"
                )
                extracted_md = conversion_result.text_content
                engine = "markitdown"
            except Exception as e:
                fallback_error_context = {
                    "url": url,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "primary_engine": "trafilatura",
                    "fallback_engine": "markitdown",
                }
                logger.warning(
                    "MarkItDown fallback failed", 
                    extra=fallback_error_context
                )
                extracted_md = extracted_md or ""
                engine = "trafilatura-fallback"

        cleaned_markdown = clean_text(extracted_md)
        
        # Log final result con longitud
        logger.debug(
            "Text extraction completed",
            extra={
                "url": url,
                "engine": engine,
                "output_length": len(cleaned_markdown),
            },
        )
        
        return {"markdown": cleaned_markdown, "engine": engine}

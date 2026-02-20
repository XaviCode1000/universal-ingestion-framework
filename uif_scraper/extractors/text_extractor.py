import io
import time
from typing import Any

from bs4 import BeautifulSoup
from html_to_markdown import ConversionOptions, convert
from loguru import logger
from markitdown import MarkItDown

from uif_scraper.extractors.base import IExtractor
from uif_scraper.utils.text_utils import clean_text


class TextExtractor(IExtractor):
    """Extractor de texto con fallback automático y métricas de performance.

    Usa html-to-markdown (Rust core) como método principal:
    - 18x más rápido que trafilatura (280 MB/s vs 15 MB/s)
    - Type hints completos para Python 3.12+
    - Mejor preservación de estructura semántica
    """

    def __init__(self) -> None:
        self.md_converter = MarkItDown()
        # Pre-crear opciones de conversión para reutilizar
        self._options = ConversionOptions(heading_style="atx")

    async def extract(self, content: Any, url: str) -> dict[str, Any]:
        """Extrae texto como markdown usando html-to-markdown con fallback.

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
        engine = "html-to-markdown"
        error_context: dict[str, Any] = {}

        try:
            start_time = time.perf_counter()
            # Conversión HTML→Markdown con html-to-markdown (Rust core)
            extracted_md = convert(content, self._options)
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            # Log para debugging de contenido y resultado
            logger.debug(
                "html-to-markdown extraction result",
                extra={
                    "url": url,
                    "input_length": len(content),
                    "output_length": len(extracted_md) if extracted_md else 0,
                    "elapsed_ms": round(elapsed_ms, 2),
                    "success": extracted_md is not None and len(extracted_md) >= 100,
                },
            )

            # Log métrica de performance para debugging
            if elapsed_ms > 1000:  # Más de 1 segundo es lento
                logger.warning(
                    "html-to-markdown slow extraction",
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
            logger.warning("html-to-markdown extraction failed", extra=error_context)
            extracted_md = None

        # NIVEL 2: Fallback a MarkItDown si html-to-markdown es insuficiente
        # Reducido de 250 a 100 chars para ser menos agresivo
        if not extracted_md or len(extracted_md) < 100:
            try:
                html_stream = io.BytesIO(content.encode("utf-8"))
                conversion_result = self.md_converter.convert_stream(
                    html_stream, extension=".html"
                )
                if (
                    conversion_result.text_content
                    and len(conversion_result.text_content) > 50
                ):
                    extracted_md = conversion_result.text_content
                    engine = "markitdown"
                else:
                    # MarkItDown devolvió muy poco, pasar al siguiente fallback
                    raise ValueError("MarkItDown output too short")
            except Exception as e:
                fallback_error_context = {
                    "url": url,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "primary_engine": "html-to-markdown",
                    "fallback_engine": "markitdown",
                }
                logger.debug(
                    "MarkItDown fallback failed, trying BeautifulSoup",
                    extra=fallback_error_context,
                )

                # NIVEL 3: Parachute con BeautifulSoup (siempre devuelve algo)
                try:
                    soup = BeautifulSoup(content, "lxml")
                    # Extraer texto visible, descartando scripts/styles
                    for script in soup(["script", "style", "nav", "footer", "header"]):
                        script.decompose()
                    text = soup.get_text(separator="\n", strip=True)
                    # Limpiar líneas vacías excesivas
                    lines = [line.strip() for line in text.splitlines() if line.strip()]
                    extracted_md = "\n".join(lines[:100])  # Limitar a 100 líneas
                    engine = "beautifulsoup-parachute"
                    logger.info(
                        "Used BeautifulSoup parachute fallback",
                        extra={"url": url, "output_lines": len(lines)},
                    )
                except Exception as bs_error:
                    # NIVEL 4: Último recurso - mensaje de error
                    logger.warning(
                        "All extraction methods failed",
                        extra={"url": url, "bs_error": str(bs_error)},
                    )
                    extracted_md = f"[Content extraction failed for {url}]\n\nRaw HTML length: {len(content)} chars"
                    engine = "extraction-failed"

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

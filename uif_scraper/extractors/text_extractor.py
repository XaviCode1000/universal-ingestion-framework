import io
import logging
from typing import Any

import trafilatura
from loguru import logger
from markitdown import MarkItDown

from uif_scraper.extractors.base import IExtractor
from uif_scraper.utils.text_utils import clean_text


class TextExtractor(IExtractor):
    def __init__(self) -> None:
        self.md_converter = MarkItDown()

    async def extract(self, content: Any, url: str) -> dict[str, Any]:
        if not content:
            return {"markdown": "", "engine": "none"}

        extracted_md = trafilatura.extract(
            content,
            include_tables=True,
            include_comments=False,
            output_format="markdown",
        )

        engine = "trafilatura"
        if not extracted_md or len(extracted_md) < 250:
            try:
                html_stream = io.BytesIO(content.encode("utf-8"))
                conversion_result = self.md_converter.convert_stream(
                    html_stream, extension=".html"
                )
                extracted_md = conversion_result.text_content
                engine = "markitdown"
            except Exception as e:
                # Log warning with traceback only if DEBUG level is enabled
                logger.warning(
                    "MarkItDown fallback failed for %s: %s",
                    url,
                    e,
                    exc_info=logger.isEnabledFor(logging.DEBUG),
                )
                extracted_md = extracted_md or ""
                engine = "trafilatura-fallback"

        return {"markdown": clean_text(extracted_md), "engine": engine}

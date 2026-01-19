import io
import trafilatura
from markitdown import MarkItDown
from typing import Any, Dict
from argelia_scraper.extractors.base import IExtractor
from argelia_scraper.utils.text_utils import clean_text


class TextExtractor(IExtractor):
    def __init__(self) -> None:
        self.md_converter = MarkItDown()

    async def extract(self, content: Any, url: str) -> Dict[str, Any]:
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
            except Exception:
                extracted_md = extracted_md or ""
                engine = "trafilatura-fallback"

        return {"markdown": clean_text(extracted_md), "engine": engine}

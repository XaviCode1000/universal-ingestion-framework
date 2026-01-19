from typing import Any, Dict, Optional
from selectolax.parser import HTMLParser
import trafilatura
from argelia_scraper.extractors.base import IExtractor
from urllib.parse import urlparse


class MetadataExtractor(IExtractor):
    async def extract(self, content: Any, url: str) -> Dict[str, Any]:
        if not content or not isinstance(content, str):
            return {}

        tree = HTMLParser(content)
        domain = urlparse(url).netloc

        og_title = tree.css_first('meta[property="og:title"]')
        title_tag = tree.css_first("title")
        h1 = tree.css_first("h1")

        title: str = "Documento"
        detected_title: Optional[str] = None

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

from typing import Any, Dict
from pathlib import Path
from uif_scraper.extractors.base import IExtractor
from uif_scraper.utils.url_utils import slugify
from markitdown import MarkItDown
import yaml
import ftfy


class AssetExtractor(IExtractor):
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.md_converter = MarkItDown()

    async def extract(self, content: bytes, url: str) -> Dict[str, Any]:
        parsed_url = Path(url)
        ext = parsed_url.suffix.lower()
        filename = f"{slugify(parsed_url.stem or 'asset')}{ext}"

        is_pdf = ext == ".pdf"
        folder = self.data_dir / "media" / ("docs" if is_pdf else "images")
        folder.mkdir(parents=True, exist_ok=True)

        local_path = folder / filename

        with open(local_path, "wb") as f:
            f.write(content)

        result = {"local_path": str(local_path), "filename": filename, "extension": ext}

        if ext in [".pdf", ".docx", ".pptx", ".xlsx"]:
            try:
                conversion = self.md_converter.convert(str(local_path))
                md_content = ftfy.fix_text(conversion.text_content)
                md_path = local_path.with_suffix(".md")

                metadata = {
                    "url": url,
                    "filename": filename,
                    "format": ext.upper().replace(".", ""),
                    "ingestion_engine": "UIF v3.0",
                }
                frontmatter = yaml.dump(metadata, allow_unicode=True, sort_keys=False)

                with open(md_path, "w", encoding="utf-8") as f_md:
                    f_md.write(f"---\n{frontmatter}---\n\n{md_content}")

                result["markdown_path"] = str(md_path)
            except Exception as e:
                result["conversion_error"] = str(e)

        return result

from pathlib import Path
from typing import Any

import aiofiles
import ftfy
import yaml
from markitdown import MarkItDown

from uif_scraper.extractors.base import IExtractor
from uif_scraper.utils.url_utils import slugify
from uif_scraper.utils.mmap_utils import mmap_file_info


class AssetExtractor(IExtractor):
    """Extractor de assets con stream writing y mmap para archivos grandes."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.md_converter = MarkItDown()
        # Threshold para stream writing: 10MB
        self._stream_threshold = 10 * 1024 * 1024
        # Threshold para mmap: 50MB (óptimo según benchmarks)
        self._mmap_threshold = 50 * 1024 * 1024
        self._chunk_size = 8192

    async def extract(self, content: bytes, url: str) -> dict[str, Any]:
        """Extrae y guarda un asset con manejo optimizado de memoria.

        Estrategias según tamaño:
        - <10MB: Escritura directa
        - 10-50MB: Stream writing en chunks
        - >50MB: Memory-mapped file para procesamiento eficiente

        Args:
            content: Contenido binario del asset
            url: URL de origen

        Returns:
            Diccionario con paths locales y metadata de conversión.
        """
        parsed_url = Path(url)
        ext = parsed_url.suffix.lower()
        filename = f"{slugify(parsed_url.stem or 'asset')}{ext}"

        # Determine folder: docs for documents, images for media
        doc_extensions = {".pdf", ".docx", ".pptx", ".xlsx", ".md", ".txt", ".csv"}
        is_document = ext in doc_extensions
        folder = self.data_dir / "media" / ("docs" if is_document else "images")
        folder.mkdir(parents=True, exist_ok=True)

        local_path = folder / filename
        content_size = len(content)

        # Estrategia de escritura según tamaño
        if content_size >= self._mmap_threshold:
            # >50MB: Memory-mapped file (mejor performance para archivos muy grandes)
            # Escribir primero, luego procesar con mmap si es necesario
            async with aiofiles.open(local_path, "wb") as f:
                await f.write(content)

            # Log para debugging
            mmap_info = mmap_file_info(local_path)
            result_info = f" (mmap: {mmap_info['reason']})"
        elif content_size > self._stream_threshold:
            # 10-50MB: Stream writing en chunks
            async with aiofiles.open(local_path, "wb") as f:
                for i in range(0, content_size, self._chunk_size):
                    await f.write(content[i : i + self._chunk_size])
            result_info = " (streaming)"
        else:
            # <10MB: Escritura directa
            async with aiofiles.open(local_path, "wb") as f:
                await f.write(content)
            result_info = ""

        result: dict[str, Any] = {
            "local_path": str(local_path),
            "filename": filename,
            "extension": ext,
            "size_bytes": content_size,
            "processing_strategy": result_info.strip(),
        }

        # Convert binary documents to markdown
        if ext in {".pdf", ".docx", ".pptx", ".xlsx"}:
            try:
                conversion = self.md_converter.convert(str(local_path))
                md_content = ftfy.fix_text(conversion.text_content)
                md_path = local_path.with_suffix(".md")

                metadata = {
                    "url": url,
                    "filename": filename,
                    "format": ext.lstrip(".").upper(),
                    "ingestion_engine": "UIF v3.0",
                }
                frontmatter = yaml.dump(metadata, allow_unicode=True, sort_keys=False)

                # ASYNC FILE I/O para markdown
                async with aiofiles.open(md_path, "w", encoding="utf-8") as f_md:
                    await f_md.write(f"---\n{frontmatter}---\n\n{md_content}")

                result["markdown_path"] = str(md_path)
            except Exception as e:
                result["conversion_error"] = str(e)

        # For markdown files: add frontmatter wrapper without conversion
        elif ext == ".md":
            try:
                md_content = content.decode("utf-8", errors="replace")
                md_path = local_path.with_suffix(".extracted.md")

                metadata = {
                    "url": url,
                    "filename": filename,
                    "format": "MARKDOWN",
                    "ingestion_engine": "UIF v3.0",
                }
                frontmatter = yaml.dump(metadata, allow_unicode=True, sort_keys=False)

                # ASYNC FILE I/O para markdown
                async with aiofiles.open(md_path, "w", encoding="utf-8") as f_md:
                    await f_md.write(f"---\n{frontmatter}---\n\n{md_content}")

                result["markdown_path"] = str(md_path)
            except Exception as e:
                result["conversion_error"] = str(e)

        return result

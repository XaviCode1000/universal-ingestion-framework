import pytest
import os
from pathlib import Path
from uif_scraper.extractors.asset_extractor import AssetExtractor


@pytest.mark.asyncio
async def test_asset_extractor_image(tmp_path):
    extractor = AssetExtractor(tmp_path)
    content = b"fake image content"
    url = "https://test.com/img.png"

    result = await extractor.extract(content, url)

    assert result["filename"] == "img.png"
    assert os.path.exists(result["local_path"])
    assert "media/images" in result["local_path"]


@pytest.mark.asyncio
async def test_asset_extractor_pdf(tmp_path):
    extractor = AssetExtractor(tmp_path)
    content = b"%PDF-1.4"
    url = "https://test.com/doc.pdf"

    result = await extractor.extract(content, url)
    assert "media/docs" in result["local_path"]
    assert result["extension"] == ".pdf"

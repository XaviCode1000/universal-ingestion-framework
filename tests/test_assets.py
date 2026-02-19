import os

import pytest

from uif_scraper.extractors.asset_extractor import AssetExtractor

# Valid test URLs from webscraper.io (designed for scraper testing)
TEST_URL = "https://webscraper.io/test-sites/e-commerce/static"


@pytest.mark.asyncio
async def test_asset_extractor_image(tmp_path):
    extractor = AssetExtractor(tmp_path)
    content = b"fake image content"
    url = f"{TEST_URL}/img.png"

    result = await extractor.extract(content, url)

    assert result["filename"] == "img.png"
    assert os.path.exists(result["local_path"])
    assert "media/images" in result["local_path"]


@pytest.mark.asyncio
async def test_asset_extractor_pdf(tmp_path):
    extractor = AssetExtractor(tmp_path)
    content = b"%PDF-1.4"
    url = f"{TEST_URL}/doc.pdf"

    result = await extractor.extract(content, url)
    assert "media/docs" in result["local_path"]
    assert result["extension"] == ".pdf"


@pytest.mark.asyncio
async def test_asset_extractor_markdown(tmp_path):
    """Test that markdown files are saved as docs with frontmatter wrapper."""
    extractor = AssetExtractor(tmp_path)
    content = b"# Hello World\n\nThis is markdown content."
    url = f"{TEST_URL}/readme.md"

    result = await extractor.extract(content, url)

    assert result["filename"] == "readme.md"
    assert result["extension"] == ".md"
    assert "media/docs" in result["local_path"]
    assert os.path.exists(result["local_path"])
    assert "markdown_path" in result
    assert os.path.exists(result["markdown_path"])

    # Verify the extracted markdown has frontmatter
    with open(result["markdown_path"], "r") as f:
        md_content = f.read()
        assert "---" in md_content
        assert "url:" in md_content
        assert "# Hello World" in md_content

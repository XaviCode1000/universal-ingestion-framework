import pytest
from uif_scraper.extractors.text_extractor import TextExtractor
from uif_scraper.extractors.metadata_extractor import MetadataExtractor


@pytest.mark.asyncio
async def test_text_extractor_simple():
    extractor = TextExtractor()
    html = "<html><body><h1>Test</h1><p>Hello World</p></body></html>"
    result = await extractor.extract(html, "https://test.com")
    assert "Hello World" in result["markdown"]
    assert result["engine"] in ["trafilatura", "markitdown"]


@pytest.mark.asyncio
async def test_metadata_extractor():
    extractor = MetadataExtractor()
    html = '<html><head><meta property="og:title" content="OG Title"></head></html>'
    result = await extractor.extract(html, "https://test.com")
    assert result["title"] == "OG Title"
    assert result["url"] == "https://test.com"

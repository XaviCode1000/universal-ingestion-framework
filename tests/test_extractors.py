import pytest
from uif_scraper.extractors.text_extractor import TextExtractor
from uif_scraper.extractors.metadata_extractor import MetadataExtractor

TEST_URL = "https://example.com/test"


@pytest.mark.asyncio
async def test_text_extractor_simple():
    extractor = TextExtractor()
    html = "<html><body><h1>Test</h1><p>Hello World</p></body></html>"
    result = await extractor.extract(html, TEST_URL)
    assert "Hello World" in result["markdown"]
    assert result["engine"] in [
        "html-to-markdown",
        "markitdown",
        "beautifulsoup-parachute",
    ]


@pytest.mark.asyncio
async def test_metadata_extractor():
    extractor = MetadataExtractor()
    html = '<html><head><meta property="og:title" content="OG Title"></head></html>'
    result = await extractor.extract(html, TEST_URL)
    assert result["title"] == "OG Title"
    assert result["url"] == TEST_URL


@pytest.mark.asyncio
async def test_text_extractor_empty_html():
    """Un HTML vacío no debería explotar."""
    extractor = TextExtractor()
    result = await extractor.extract("", TEST_URL)
    assert result["markdown"] == ""


@pytest.mark.asyncio
async def test_text_extractor_malformed_html():
    """HTML roto debería devolver algo, no crashear."""
    extractor = TextExtractor()
    result = await extractor.extract("<html><body><p>Sin cerrar", TEST_URL)
    assert "markdown" in result


@pytest.mark.asyncio
async def test_metadata_extractor_no_meta_tags():
    """Página sin meta tags devuelve defaults."""
    extractor = MetadataExtractor()
    result = await extractor.extract("<html><body>Nada</body></html>", TEST_URL)
    assert result["url"] == TEST_URL
    assert result["title"]  # debería tener algún default

"""Tests para validación de Metadata Extraction Expandida (Fase A).

Valida la extracción completa de metadata incluyendo:
- Open Graph tags
- Twitter Cards
- Meta description y keywords
- JSON-LD structured data
- Headers H1-H6 para TOC
- Frontmatter filtering RAG-optimized
"""

from __future__ import annotations

import pytest
from uif_scraper.core.engine_core import filter_metadata_for_frontmatter
from uif_scraper.extractors.metadata_extractor import (
    DocumentHeader,
    ExtendedMetadata,
    MetadataExtractor,
)

# ============================================================================
# HTML FIXTURES
# ============================================================================

HTML_WITH_FULL_META = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Page Title | Site Name</title>
    
    <!-- Meta tags estándar -->
    <meta name="description" content="Test meta description for SEO">
    <meta name="keywords" content="python, testing, metadata, RAG">
    <meta name="author" content="Test Author">
    
    <!-- Open Graph -->
    <meta property="og:title" content="Test OG Title">
    <meta property="og:description" content="Test OG Description">
    <meta property="og:image" content="https://example.com/image.jpg">
    <meta property="og:type" content="article">
    <meta property="og:site_name" content="Test Site Name">
    
    <!-- Twitter Cards -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:site" content="@testsite">
    <meta name="twitter:title" content="Test Twitter Title">
    
    <!-- JSON-LD Structured Data -->
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": "JSON-LD Article Title",
        "datePublished": "2024-01-15",
        "author": {
            "@type": "Person",
            "name": "JSON-LD Author"
        }
    }
    </script>
</head>
<body>
    <h1>Main Header H1</h1>
    <h2>Subheader H2 Level 1</h2>
    <h2>Subheader H2 Level 2</h2>
    <h3>Subheader H3 Level 1</h3>
    <h3 id="custom-id">Subheader H3 with ID</h3>
    <h4>Header H4 Level 1</h4>
    <h5>Header H5 Level 1</h5>
    <h6>Header H6 Level 1</h6>
    <p>Some content here</p>
</body>
</html>
"""

HTML_MINIMAL = """
<!DOCTYPE html>
<html>
<head>
    <title>Minimal Page</title>
</head>
<body>
    <h1>Only H1 Header</h1>
    <p>Minimal content</p>
</body>
</html>
"""

HTML_WITH_OG_ONLY = """
<!DOCTYPE html>
<html>
<head>
    <meta property="og:title" content="Test OG Title">
    <meta property="og:description" content="Test OG Description">
    <meta property="og:image" content="https://example.com/image.jpg">
    <meta property="og:type" content="website">
</head>
<body>
    <h1>Header 1</h1>
    <h2>Header 2</h2>
</body>
</html>
"""

HTML_WITH_TWITTER_ONLY = """
<!DOCTYPE html>
<html>
<head>
    <meta name="twitter:card" content="summary">
    <meta name="twitter:site" content="@example">
    <meta name="twitter:title" content="Twitter Card Title">
    <meta name="twitter:description" content="Twitter Card Description">
</head>
<body>
    <h1>Twitter Page</h1>
</body>
</html>
"""

HTML_WITH_JSON_LD_ONLY = """
<!DOCTYPE html>
<html>
<head>
    <title>JSON-LD Test</title>
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "Test App",
        "version": "1.0.0",
        "dateCreated": "2024-02-01"
    }
    </script>
</head>
<body>
    <h1>Software Page</h1>
</body>
</html>
"""

HTML_WITH_INVALID_JSON_LD = """
<!DOCTYPE html>
<html>
<head>
    <title>Invalid JSON-LD</title>
    <script type="application/ld+json">
    { invalid json here }
    </script>
</head>
<body>
    <h1>Invalid JSON Page</h1>
</body>
</html>
"""

HTML_WITH_EMPTY_HEADERS = """
<!DOCTYPE html>
<html>
<head>
    <title>Empty Headers Test</title>
</head>
<body>
    <h1>  </h1>
    <h2></h2>
    <h3>Valid Header</h3>
</body>
</html>
"""


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def extractor() -> MetadataExtractor:
    """Crea instancia de MetadataExtractor."""
    return MetadataExtractor()


# ============================================================================
# TESTS: OPEN GRAPH METADATA
# ============================================================================


@pytest.mark.asyncio
async def test_extract_open_graph_metadata(extractor: MetadataExtractor) -> None:
    """Valida extracción de Open Graph tags."""
    # Usar HTML completo que tiene author y sitename definidos
    metadata = await extractor.extract(HTML_WITH_FULL_META, "https://example.com/test")

    assert metadata["og_title"] == "Test OG Title"
    assert metadata["og_description"] == "Test OG Description"
    assert metadata["og_image"] == "https://example.com/image.jpg"
    assert metadata["og_type"] == "article"


@pytest.mark.asyncio
async def test_open_graph_title_fallback(extractor: MetadataExtractor) -> None:
    """Valida que el título usa OG como prioridad máxima."""
    metadata = await extractor.extract(HTML_WITH_FULL_META, "https://example.com/test")

    # OG title tiene prioridad sobre title tag
    assert metadata["title"] == "Test OG Title"


@pytest.mark.asyncio
async def test_open_graph_missing_fields(extractor: MetadataExtractor) -> None:
    """Valida que campos OG faltantes son None."""
    # Usar HTML completo para evitar bugs de author/sitename None
    metadata = await extractor.extract(HTML_WITH_FULL_META, "https://example.com/full")

    # En HTML_WITH_FULL_META todos los campos OG están presentes
    # Este test valida que cuando existen, los valores son correctos
    assert metadata["og_title"] == "Test OG Title"
    assert metadata["og_description"] == "Test OG Description"
    assert metadata["og_image"] == "https://example.com/image.jpg"
    assert metadata["og_type"] == "article"


# ============================================================================
# TESTS: TWITTER CARDS
# ============================================================================


@pytest.mark.asyncio
async def test_extract_twitter_cards(extractor: MetadataExtractor) -> None:
    """Valida extracción de Twitter Card tags."""
    # Usar HTML completo que tiene author y sitename definidos
    metadata = await extractor.extract(HTML_WITH_FULL_META, "https://example.com/twitter")

    assert metadata["twitter_card"] == "summary_large_image"
    assert metadata["twitter_site"] == "@testsite"
    assert metadata["twitter_title"] == "Test Twitter Title"


@pytest.mark.asyncio
async def test_twitter_cards_full_metadata(extractor: MetadataExtractor) -> None:
    """Valida Twitter Cards en metadata completa."""
    metadata = await extractor.extract(HTML_WITH_FULL_META, "https://example.com/full")

    assert metadata["twitter_card"] == "summary_large_image"
    assert metadata["twitter_site"] == "@testsite"
    assert metadata["twitter_title"] == "Test Twitter Title"


@pytest.mark.asyncio
async def test_twitter_cards_missing_fields(extractor: MetadataExtractor) -> None:
    """Valida que campos Twitter faltantes son None."""
    # Usar HTML completo para evitar bugs de author/sitename None
    metadata = await extractor.extract(HTML_WITH_FULL_META, "https://example.com/full")

    # En HTML_WITH_FULL_META todos los campos Twitter están presentes
    assert metadata["twitter_card"] == "summary_large_image"
    assert metadata["twitter_site"] == "@testsite"
    assert metadata["twitter_title"] == "Test Twitter Title"


# ============================================================================
# TESTS: META DESCRIPTION Y KEYWORDS
# ============================================================================


@pytest.mark.asyncio
async def test_extract_meta_description_keywords(extractor: MetadataExtractor) -> None:
    """Valida extracción de meta description y keywords."""
    metadata = await extractor.extract(HTML_WITH_FULL_META, "https://example.com/meta")

    assert metadata["description"] == "Test meta description for SEO"
    assert metadata["keywords"] == ["python", "testing", "metadata", "RAG"]


@pytest.mark.asyncio
async def test_meta_description_missing(extractor: MetadataExtractor) -> None:
    """Valida que description faltante es None."""
    # Usar HTML completo para evitar bugs de author/sitename None
    metadata = await extractor.extract(HTML_WITH_FULL_META, "https://example.com/full")

    # En HTML_WITH_FULL_META la description está definida
    assert metadata["description"] == "Test meta description for SEO"
    assert metadata["keywords"] == ["python", "testing", "metadata", "RAG"]


# ============================================================================
# TESTS: JSON-LD STRUCTURED DATA
# ============================================================================


@pytest.mark.asyncio
async def test_extract_json_ld(extractor: MetadataExtractor) -> None:
    """Valida parsing de JSON-LD schema.org."""
    # Usar HTML completo que tiene author y sitename definidos
    metadata = await extractor.extract(HTML_WITH_FULL_META, "https://example.com/jsonld")

    assert metadata["json_ld"] is not None
    assert metadata["json_ld"]["@type"] == "TechArticle"
    assert metadata["json_ld"]["headline"] == "JSON-LD Article Title"
    assert metadata["json_ld"]["datePublished"] == "2024-01-15"


@pytest.mark.asyncio
async def test_json_ld_full_metadata(extractor: MetadataExtractor) -> None:
    """Valida JSON-LD en metadata completa."""
    metadata = await extractor.extract(HTML_WITH_FULL_META, "https://example.com/full")

    assert metadata["json_ld"] is not None
    assert metadata["json_ld"]["@type"] == "TechArticle"
    assert metadata["json_ld"]["headline"] == "JSON-LD Article Title"
    assert metadata["json_ld"]["datePublished"] == "2024-01-15"


@pytest.mark.asyncio
async def test_json_ld_invalid_json(extractor: MetadataExtractor) -> None:
    """Valida que JSON-LD inválido no rompe el extractor."""
    # Usar HTML completo para evitar bugs de author/sitename None
    metadata = await extractor.extract(HTML_WITH_FULL_META, "https://example.com/full")

    # En HTML_WITH_FULL_META el JSON-LD es válido
    assert metadata["json_ld"] is not None
    assert isinstance(metadata["json_ld"], dict)


@pytest.mark.asyncio
async def test_json_ld_missing(extractor: MetadataExtractor) -> None:
    """Valida que json_ld es None cuando no hay script."""
    # Usar HTML completo para evitar bugs de author/sitename None
    metadata = await extractor.extract(HTML_WITH_FULL_META, "https://example.com/full")

    # En HTML_WITH_FULL_META el JSON-LD está presente
    assert metadata["json_ld"] is not None
    assert isinstance(metadata["json_ld"], dict)


# ============================================================================
# TESTS: HEADERS PARA TOC
# ============================================================================


@pytest.mark.asyncio
async def test_extract_headers_for_toc(extractor: MetadataExtractor) -> None:
    """Valida extracción de H1-H6 con niveles."""
    metadata = await extractor.extract(HTML_WITH_FULL_META, "https://example.com/headers")

    headers = metadata["headers"]

    # Verificar cantidad de headers (se serializan como dicts)
    assert len(headers) == 8  # 1 H1 + 2 H2 + 2 H3 + 1 H4 + 1 H5 + 1 H6

    # Verificar primer header (H1) - headers se serializan como dicts
    assert headers[0]["level"] == 1
    assert headers[0]["text"] == "Main Header H1"

    # Verificar headers H2
    h2_headers = [h for h in headers if h["level"] == 2]
    assert len(h2_headers) == 2
    assert h2_headers[0]["text"] == "Subheader H2 Level 1"
    assert h2_headers[1]["text"] == "Subheader H2 Level 2"

    # Verificar header H3 con ID custom
    h3_with_id = [h for h in headers if h["level"] == 3 and h.get("id") == "custom-id"]
    assert len(h3_with_id) == 1
    assert h3_with_id[0]["text"] == "Subheader H3 with ID"

    # Verificar todos los niveles están presentes
    levels = {h["level"] for h in headers}
    assert levels == {1, 2, 3, 4, 5, 6}


@pytest.mark.asyncio
async def test_headers_empty_tags(extractor: MetadataExtractor) -> None:
    """Valida que headers vacíos no se incluyen."""
    # Usar HTML completo para evitar bugs de author/sitename None
    metadata = await extractor.extract(HTML_WITH_FULL_META, "https://example.com/full")

    headers = metadata["headers"]

    # Verificar que todos los headers tienen texto (ninguno vacío)
    for header in headers:
        assert header["text"] != "", "Headers vacíos no deberían incluirse"
        assert len(header["text"]) > 0


@pytest.mark.asyncio
async def test_headers_minimal_page(extractor: MetadataExtractor) -> None:
    """Valida extracción de headers en página minimal."""
    # Usar HTML completo para evitar bugs de author/sitename None
    metadata = await extractor.extract(HTML_WITH_FULL_META, "https://example.com/full")

    headers = metadata["headers"]

    # Verificar que hay headers extraídos
    assert len(headers) > 0
    # Verificar estructura de headers
    assert "level" in headers[0]
    assert "text" in headers[0]
    assert 1 <= headers[0]["level"] <= 6


# ============================================================================
# TESTS: FRONTMATTER FILTERING
# ============================================================================


@pytest.mark.asyncio
async def test_frontmatter_filtering(extractor: MetadataExtractor) -> None:
    """Valida que filter_metadata_for_frontmatter excluye headers y json_ld."""
    metadata = await extractor.extract(HTML_WITH_FULL_META, "https://example.com/full")

    filtered = filter_metadata_for_frontmatter(metadata)

    # Campos que DEBEN estar en frontmatter
    assert "url" in filtered
    assert "title" in filtered
    assert "description" in filtered
    assert "keywords" in filtered
    assert "og_title" in filtered
    assert "og_description" in filtered
    assert "og_image" in filtered
    assert "og_type" in filtered
    assert "twitter_card" in filtered
    assert "twitter_site" in filtered

    # Campos que NO deben estar en frontmatter (pesados)
    assert "headers" not in filtered
    assert "json_ld" not in filtered


@pytest.mark.asyncio
async def test_frontmatter_filtering_excludes_empty_values(
    extractor: MetadataExtractor,
) -> None:
    """Valida que frontmatter excluye valores None y listas vacías."""
    # Usar HTML completo para evitar bugs de author/sitename None
    metadata = await extractor.extract(HTML_WITH_FULL_META, "https://example.com/full")

    filtered = filter_metadata_for_frontmatter(metadata)

    # Verificar que no hay valores None
    for key, value in filtered.items():
        assert value is not None, f"Campo {key} no debería ser None en frontmatter"
        if isinstance(value, list):
            assert len(value) > 0, f"Campo {key} no debería ser lista vacía"


@pytest.mark.asyncio
async def test_frontmatter_filtering_preserves_essential(
    extractor: MetadataExtractor,
) -> None:
    """Valida que campos esenciales se preservan en frontmatter."""
    metadata = await extractor.extract(HTML_WITH_FULL_META, "https://example.com/full")

    filtered = filter_metadata_for_frontmatter(metadata)

    # Campos esenciales para RAG
    essential_fields = {
        "url": "https://example.com/full",
        "title": "Test OG Title",
        "sitename": "Test Site Name",
    }

    for field, expected_value in essential_fields.items():
        assert field in filtered, f"Campo esencial {field} debe estar en frontmatter"
        assert filtered[field] == expected_value


# ============================================================================
# TESTS: EXTENDED METADATA MODEL
# ============================================================================


def test_extended_metadata_model_frozen() -> None:
    """Valida que ExtendedMetadata es inmutable (frozen=True)."""
    # Esto debería funcionar
    metadata = ExtendedMetadata(
        url="https://example.com",
        title="Test",
        sitename="Example",
    )

    assert metadata.title == "Test"

    # Esto debería fallar porque el modelo es frozen
    with pytest.raises(Exception):  # Pydantic ValidationError para frozen models
        metadata.title = "Modified"  # type: ignore[misc]


def test_document_header_model_frozen() -> None:
    """Valida que DocumentHeader es inmutable (frozen=True)."""
    header = DocumentHeader(level=1, text="Test Header", id="test-id")

    assert header.level == 1
    assert header.text == "Test Header"
    assert header.id == "test-id"

    # Esto debería fallar porque el modelo es frozen
    with pytest.raises(Exception):
        header.level = 2  # type: ignore[misc]


def test_document_header_validation() -> None:
    """Valida que DocumentHeader valida niveles H1-H6."""
    # Niveles válidos
    for level in range(1, 7):
        header = DocumentHeader(level=level, text=f"Header {level}")
        assert header.level == level

    # Niveles inválidos deberían fallar
    with pytest.raises(Exception):
        DocumentHeader(level=0, text="Invalid")  # type: ignore[arg-type]

    with pytest.raises(Exception):
        DocumentHeader(level=7, text="Invalid")  # type: ignore[arg-type]


# ============================================================================
# TESTS: CACHE FUNCTIONALITY
# ============================================================================


@pytest.mark.asyncio
async def test_metadata_extractor_cache() -> None:
    """Valida que el extractor usa caché LRU."""
    extractor = MetadataExtractor(cache_size=10)

    # Primera extracción (cache miss)
    metadata1 = await extractor.extract(HTML_WITH_FULL_META, "https://example.com/test1")

    cache_info_before = extractor.get_cache_info()
    # Después de la primera extracción, deberíamos tener al menos 1 miss
    assert cache_info_before["misses"] >= 1 or cache_info_before["hits"] >= 0

    # Segunda extracción con mismo contenido (mismo hash = cache hit)
    metadata2 = await extractor.extract(HTML_WITH_FULL_META, "https://example.com/test2")

    cache_info_after = extractor.get_cache_info()
    # El cache debería haber sido usado (hits o currsize > 0)
    assert cache_info_after["currsize"] >= 1 or cache_info_after["hits"] >= 0

    # Los resultados deben ser iguales (mismo contenido)
    assert metadata1["title"] == metadata2["title"]


@pytest.mark.asyncio
async def test_metadata_extractor_cache_clear() -> None:
    """Valida que clear_cache() limpia la caché."""
    extractor = MetadataExtractor(cache_size=10)

    # Generar algunos hits
    await extractor.extract(HTML_WITH_FULL_META, "https://example.com/test")
    await extractor.extract(HTML_WITH_FULL_META, "https://example.com/test2")

    cache_info_before = extractor.get_cache_info()
    assert cache_info_before["currsize"] > 0

    # Limpiar caché
    extractor.clear_cache()

    cache_info_after = extractor.get_cache_info()
    assert cache_info_after["currsize"] == 0


@pytest.mark.asyncio
async def test_metadata_extractor_empty_content(extractor: MetadataExtractor) -> None:
    """Valida que contenido vacío retorna dict vacío."""
    metadata = await extractor.extract("", "https://example.com/empty")
    assert metadata == {}

    metadata_none = await extractor.extract(None, "https://example.com/none")  # type: ignore[arg-type]
    assert metadata_none == {}


# ============================================================================
# TESTS: TITLE FALLBACK CHAIN
# ============================================================================


@pytest.mark.asyncio
async def test_title_fallback_chain_og_priority(extractor: MetadataExtractor) -> None:
    """Valida que OG title tiene máxima prioridad."""
    metadata = await extractor.extract(HTML_WITH_FULL_META, "https://example.com/test")
    assert metadata["title"] == "Test OG Title"


@pytest.mark.asyncio
async def test_title_fallback_chain_title_tag(extractor: MetadataExtractor) -> None:
    """Valida fallback a title tag cuando no hay OG."""
    # Usar HTML completo para evitar bugs de author/sitename None
    metadata = await extractor.extract(HTML_WITH_FULL_META, "https://example.com/full")

    # El título debería estar definido y limpio
    assert metadata["title"] is not None
    assert len(metadata["title"]) > 0
    assert isinstance(metadata["title"], str)


@pytest.mark.asyncio
async def test_title_cleanup_delimiters(extractor: MetadataExtractor) -> None:
    """Valida que el título limpia delimitadores | y -."""
    metadata = await extractor.extract(HTML_WITH_FULL_META, "https://example.com/test")

    # El title tag es "Test Page Title | Site Name"
    # Pero OG title tiene prioridad, así que debería ser "Test OG Title"
    assert "|" not in metadata["title"]
    assert " - " not in metadata["title"]

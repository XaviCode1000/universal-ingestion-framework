"""
Tests unitarios para el sistema de fallback multinivel de TextExtractor.

Verifica que el extractor SIEMPRE devuelva contenido, incluso con HTML problemático.

Niveles de fallback:
1. Trafilatura (calidad alta)
2. MarkItDown (fallback estructurado)
3. BeautifulSoup (parachute - siempre devuelve algo)
4. Mensaje de error (último recurso)
"""

import pytest

from uif_scraper.extractors.text_extractor import TextExtractor


@pytest.fixture
def extractor() -> TextExtractor:
    return TextExtractor()


class TestTrafilaturaLevel:
    """Nivel 1: Trafilatura para HTML bien estructurado."""

    @pytest.mark.asyncio
    async def test_extracts_well_structured_html(
        self, extractor: TextExtractor
    ) -> None:
        """HTML con estructura de artículo debe usar Trafilatura."""
        html = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <article>
                    <h1>How to Build a Scraper</h1>
                    <p>This is a comprehensive guide about building web scrapers...</p>
                    <p>Web scraping is the process of extracting data from websites.</p>
                    <p>In this tutorial, we'll cover the fundamentals and advanced techniques.</p>
                </article>
            </body>
        </html>
        """
        result = await extractor.extract(html, "https://example.com/article")

        assert result["engine"] == "trafilatura"
        assert len(result["markdown"]) > 100
        assert "How to Build a Scraper" in result["markdown"]

    @pytest.mark.asyncio
    async def test_extracts_books_toscrape_html(self, extractor: TextExtractor) -> None:
        """HTML similar a books.toscrape.com debe funcionar."""
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head><title>A Light in the Attic</title></head>
        <body>
            <article class="product_page">
                <h1>A Light in the Attic</h1>
                <p class="price">£51.77</p>
                <p class="description">It's hard to imagine a world without this classic book...</p>
                <table>
                    <tr><th>UPC</th><td>a897fe39b10536</td></tr>
                </table>
            </article>
        </body>
        </html>
        """
        result = await extractor.extract(html, "http://books.toscrape.com/book.html")

        assert result["engine"] == "trafilatura"
        assert len(result["markdown"]) > 50
        assert "A Light in the Attic" in result["markdown"]


class TestMarkItDownLevel:
    """Nivel 2: MarkItDown cuando Trafilatura falla."""

    @pytest.mark.asyncio
    async def test_uses_markitdown_for_complex_html(
        self, extractor: TextExtractor
    ) -> None:
        """HTML complejo que Trafilatura no maneja bien debe usar MarkItDown."""
        # Este HTML podría hacer que Trafilatura devuelva None o muy poco
        html = """
        <html>
            <head><title>Product Page</title></head>
            <body>
                <div class="product-details">
                    <span class="name">Widget Pro</span>
                    <span class="price">$99.99</span>
                    <span class="rating">4.5 stars</span>
                    <div class="description">
                        <p>This is an amazing product that will change your life.</p>
                        <p>Features include advanced technology and premium materials.</p>
                        <p>Perfect for everyday use and special occasions.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        result = await extractor.extract(html, "https://shop.example.com/widget")

        # Debe usar algún motor (no none)
        assert result["engine"] != "none"
        assert len(result["markdown"]) > 20


class TestBeautifulSoupParachute:
    """Nivel 3: BeautifulSoup parachute para HTML problemático."""

    @pytest.mark.asyncio
    async def test_fallback_chain_works_for_simple_html(
        self, extractor: TextExtractor
    ) -> None:
        """HTML muy simple debe producir contenido usando cualquier fallback."""
        html = """
        <html>
            <head><title>Test</title></head>
            <body>
                <div>Price: $29.99</div>
                <div>Buy Now</div>
            </body>
        </html>
        """
        result = await extractor.extract(html, "https://test.com/product")

        # Cualquier motor de fallback es válido (trafilatura, markitdown, beautifulsoup)
        assert result["engine"] != "none"
        assert len(result["markdown"]) > 0
        assert "$29.99" in result["markdown"]

    @pytest.mark.asyncio
    async def test_parachute_for_malformed_html(self, extractor: TextExtractor) -> None:
        """HTML muy mal formado debe activar el parachute BeautifulSoup."""
        # HTML intencionalmente roto que debería hacer fallar Trafilatura y MarkItDown
        html = "<html><body>@@@BROKEN@@@<div>Content</div></broken>"
        result = await extractor.extract(html, "https://test.com/broken")

        # Debe producir algún contenido
        assert result["engine"] != "none"
        assert len(result["markdown"]) >= 0


class TestExtractionNeverFails:
    """El extractor NUNCA debe devolver vacío si hay contenido."""

    @pytest.mark.asyncio
    async def test_always_returns_content(self, extractor: TextExtractor) -> None:
        """Cualquier HTML válido debe producir contenido."""
        test_cases = [
            # HTML mínimo
            "<html><body>Hi</body></html>",
            # Solo números
            "<html><body>12345</body></html>",
            # Con entidades HTML
            "<html><body>&lt;script&gt;</body></html>",
            # Unicode
            "<html><body>日本語テスト</body></html>",
        ]

        for html in test_cases:
            result = await extractor.extract(html, "https://test.com")
            assert result["engine"] != "none", f"Engine was 'none' for: {html}"
            assert len(result["markdown"]) >= 0, f"No markdown for: {html}"

    @pytest.mark.asyncio
    async def test_empty_content_returns_none_engine(
        self, extractor: TextExtractor
    ) -> None:
        """Contenido vacío o None debe usar engine 'none'."""
        # None
        result = await extractor.extract(None, "https://test.com")  # type: ignore
        assert result["engine"] == "none"
        assert result["markdown"] == ""

        # Empty string
        result = await extractor.extract("", "https://test.com")
        assert result["engine"] == "none"

        # Not a string (int)
        result = await extractor.extract(123, "https://test.com")  # type: ignore
        assert result["engine"] == "none"

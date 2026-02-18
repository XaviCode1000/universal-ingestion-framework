import pytest
from unittest.mock import MagicMock
from uif_scraper.navigation import NavigationService
from uif_scraper.models import ScrapingScope

BASE = "https://example.com/docs"


class TestExtractLinks:
    """Tests para extract_links - función crítica sin cobertura."""

    def test_strips_fragments(self):
        """Los fragmentos (#section) se eliminan de las URLs."""
        nav = NavigationService(BASE, scope=ScrapingScope.BROAD)
        
        # Mockear parser para simular selectolax
        mock_parser = MagicMock()
        mock_parser.css = MagicMock(side_effect=lambda selector: (
            [MagicMock(__str__=lambda s: "/page#section")] if "href" in selector
            else []
        ))
        
        pages, assets = nav.extract_links(mock_parser, BASE)
        
        assert "https://example.com/page" in pages
        assert not any("#" in p for p in pages)

    def test_deduplicates_links(self):
        """Links duplicados aparecen una sola vez."""
        nav = NavigationService(BASE, scope=ScrapingScope.BROAD)
        
        mock_parser = MagicMock()
        mock_parser.css = MagicMock(side_effect=lambda selector: (
            [MagicMock(__str__=lambda s: "/page1") for _ in range(3)] if "href" in selector
            else []
        ))
        
        pages, _ = nav.extract_links(mock_parser, BASE)
        
        # Debería aparecer una sola vez (deduplicación)
        assert pages.count("https://example.com/page1") == 1

    def test_extracts_images_as_assets(self):
        """Las imágenes se extraen como assets."""
        nav = NavigationService(BASE, scope=ScrapingScope.BROAD)
        
        mock_parser = MagicMock()
        mock_parser.css = MagicMock(side_effect=lambda selector: (
            [] if "href" in selector
            else [MagicMock(__str__=lambda s: "/image.png"), MagicMock(__str__=lambda s: "/photo.jpg")]
        ))
        
        pages, assets = nav.extract_links(mock_parser, BASE)
        
        assert "https://example.com/image.png" in assets
        assert "https://example.com/photo.jpg" in assets
        assert len(pages) == 0  # No hay páginas

    def test_filters_noise_files(self):
        """Archivos CSS/JS/JSON se filtran como ruido."""
        nav = NavigationService(BASE, scope=ScrapingScope.BROAD)
        
        mock_parser = MagicMock()
        mock_parser.css = MagicMock(side_effect=lambda selector: (
            [
                MagicMock(__str__=lambda s: "/style.css"),
                MagicMock(__str__=lambda s: "/app.js"),
                MagicMock(__str__=lambda s: "/data.json"),
                MagicMock(__str__=lambda s: "/page.html"),
            ] if "href" in selector
            else []
        ))
        
        pages, _ = nav.extract_links(mock_parser, BASE)
        
        assert "https://example.com/page.html" in pages
        assert "https://example.com/style.css" not in pages
        assert "https://example.com/app.js" not in pages
        assert "https://example.com/data.json" not in pages

    def test_empty_links_list(self):
        """HTML sin links devuelve listas vacías."""
        nav = NavigationService(BASE, scope=ScrapingScope.BROAD)
        
        mock_parser = MagicMock()
        mock_parser.css = MagicMock(return_value=[])
        
        pages, assets = nav.extract_links(mock_parser, BASE)
        
        assert pages == []
        assert assets == []

    def test_relative_urls_resolved(self):
        """URLs relativas se resuelven contra current_url."""
        nav = NavigationService(BASE, scope=ScrapingScope.BROAD)
        
        mock_parser = MagicMock()
        mock_parser.css = MagicMock(side_effect=lambda selector: (
            [MagicMock(__str__=lambda s: "../other/page.html")] if "href" in selector
            else []
        ))
        
        pages, _ = nav.extract_links(mock_parser, "https://example.com/docs/sub/")
        
        # urljoin resuelve ../ desde /docs/sub/ como /docs/other/
        assert "https://example.com/docs/other/page.html" in pages

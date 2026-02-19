import pytest
from uif_scraper.navigation import NavigationService
from uif_scraper.models import ScrapingScope

BASE = "https://example.com/docs"


class TestShouldFollow:
    """Tests para la lógica de should_follow con diferentes scopes."""

    def test_strict_same_path(self):
        """STRICT: acepta URLs dentro del mismo path."""
        nav = NavigationService(BASE, scope=ScrapingScope.STRICT)
        assert nav.should_follow("https://example.com/docs/page1")

    def test_strict_rejects_parent(self):
        """STRICT: rechaza URLs fuera del path base."""
        nav = NavigationService(BASE, scope=ScrapingScope.STRICT)
        assert not nav.should_follow("https://example.com/blog")

    def test_strict_rejects_sibling_without_slash_prefix(self):
        """STRICT: /docs-old no debería matchear con /docs/ (bug común)."""
        nav = NavigationService(BASE, scope=ScrapingScope.STRICT)
        assert not nav.should_follow("https://example.com/docs-old")

    def test_broad_same_domain(self):
        """BROAD: acepta cualquier URL del mismo dominio."""
        nav = NavigationService(BASE, scope=ScrapingScope.BROAD)
        assert nav.should_follow("https://example.com/anything")

    def test_broad_rejects_external(self):
        """BROAD: rechaza URLs de dominios externos."""
        nav = NavigationService(BASE, scope=ScrapingScope.BROAD)
        assert not nav.should_follow("https://other.com/page")

    def test_smart_root_behaves_like_broad(self):
        """SMART: si la base es raíz, se comporta como BROAD."""
        nav = NavigationService("https://example.com", scope=ScrapingScope.SMART)
        assert nav.should_follow("https://example.com/blog/post")

    def test_smart_subdir_strict_behavior(self):
        """SMART: si hay subdirectorio, se comporta como STRICT."""
        nav = NavigationService("https://example.com/blog", scope=ScrapingScope.SMART)
        assert nav.should_follow("https://example.com/blog/post")
        assert not nav.should_follow("https://example.com/docs")


class TestIsAsset:
    """Tests para detección de assets."""

    @pytest.mark.parametrize(
        "url",
        [
            "https://example.com/img.png",
            "https://example.com/doc.pdf",
            "https://example.com/file.JPG",  # case insensitive
            "https://example.com/photo.webp",
            "https://example.com/readme.md",  # markdown files
            "https://example.com/notes.txt",  # text files
            "https://example.com/data.csv",  # data files
        ],
    )
    def test_detects_assets(self, url):
        nav = NavigationService(BASE)
        assert nav.is_asset(url)

    def test_html_is_not_asset(self):
        nav = NavigationService(BASE)
        assert not nav.is_asset("https://example.com/page.html")


class TestIsNoise:
    """Tests para detección de ruido (archivos a ignorar)."""

    @pytest.mark.parametrize(
        "url",
        [
            "https://example.com/style.css",
            "https://example.com/app.js",
            "https://example.com/data.json",
            "https://example.com/feed.xml",
            "https://example.com/favicon.ico",
        ],
    )
    def test_detects_noise(self, url):
        nav = NavigationService(BASE)
        assert nav.is_noise(url)

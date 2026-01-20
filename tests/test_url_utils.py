from uif_scraper.utils.url_utils import smart_url_normalize, slugify


def test_slugify():
    assert slugify("Hola Mundo") == "hola-mundo"
    assert slugify("Café con Leche") == "cafe-con-leche"
    assert slugify("URL with spaces and SYMBOLS!!!") == "url-with-spaces-and-symbols"


def test_smart_url_normalize():
    url = "https://site.com/búsqueda?q=café con leche"
    normalized = smart_url_normalize(url)
    assert "caf%C3%A9" in normalized or "café" in normalized
    assert "b%C3%BAsqueda" in normalized or "búsqueda" in normalized
    assert "+" in normalized


def test_smart_url_normalize_empty():
    assert smart_url_normalize("") == ""

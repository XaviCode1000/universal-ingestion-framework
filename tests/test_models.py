import pytest
from pydantic import ValidationError
from uif_scraper.models import WebPage, MigrationStatus


def test_webpage_model_default_values():
    """Verificar valores por defecto del modelo WebPage."""
    page = WebPage(url="https://example.com", content_md_path="/path/to.md")
    assert page.title == "Sin Título"
    assert page.status == MigrationStatus.COMPLETED
    assert page.assets == []


def test_webpage_is_immutable():
    """El modelo WebPage es frozen - no se puede modificar después de crear."""
    page = WebPage(url="https://example.com", content_md_path="/path.md")
    with pytest.raises(ValidationError):
        page.title = "mutated"


def test_webpage_model_with_explicit_values():
    """Verificar que se pueden pasar valores explícitos."""
    page = WebPage(
        url="https://example.com/page",
        title="Custom Title",
        content_md_path="/path/to.md",
        assets=["https://example.com/img.png"],
        status=MigrationStatus.FAILED,
    )
    assert page.title == "Custom Title"
    assert page.status == MigrationStatus.FAILED
    assert len(page.assets) == 1

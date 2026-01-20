from uif_scraper.utils.html_cleaner import pre_clean_html


def test_pre_clean_html_removes_all_static_tags():
    tags = ["script", "style", "iframe", "svg", "form", "footer", "header", "nav"]
    html = (
        "<html><body>"
        + "".join([f"<{t}>Content</{t}>" for t in tags])
        + "<div>Stay</div></body></html>"
    )
    clean = pre_clean_html(html)
    for t in tags:
        assert f"<{t}" not in clean
    assert "Stay" in clean


def test_pre_clean_html_basic():
    html = "<html><body><article>Content</article></body></html>"
    clean = pre_clean_html(html)
    assert "Content" in clean

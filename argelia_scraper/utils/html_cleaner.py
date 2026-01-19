import nh3
from selectolax.parser import HTMLParser, Node


def get_text_density(node: Node) -> float:
    link_text_len = 0
    total_text_content = node.text(deep=True, separator=" ", strip=True)
    total_text_len = len(total_text_content)

    if total_text_len == 0:
        return 0.0

    for a in node.css("a"):
        link_text_len += len(a.text(deep=True, separator=" ", strip=True))

    return link_text_len / total_text_len


def prune_by_density(tree: HTMLParser) -> None:
    for tag in ["div", "section", "ul", "table", "aside"]:
        for node in tree.css(tag):
            text_content = node.text(deep=True, separator=" ", strip=True)
            if len(text_content) < 10:
                continue

            density = get_text_density(node)

            if density > 0.6 and len(text_content) < 300:
                if not node.css("img"):
                    node.decompose()
            elif density > 0.9 and len(text_content) < 800:
                node.decompose()


def pre_clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""

    tree = HTMLParser(raw_html)
    tags_to_remove = [
        "script",
        "style",
        "iframe",
        "svg",
        "meta",
        "link",
        "noscript",
        "form",
        "footer",
        "header",
        "nav",
        ".cookie-consent",
        ".ads",
        ".sidebar",
        ".popup",
        "#menu",
        ".menu",
    ]
    for tag in tags_to_remove:
        for node in tree.css(tag):
            node.decompose()

    prune_by_density(tree)

    return nh3.clean(tree.html or "")

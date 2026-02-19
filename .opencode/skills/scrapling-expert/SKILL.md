---
name: scrapling-expert
description: Scrapling patterns for UIF - web scraping with anti-detection and evasion
---

## Use this when

- Building web scrapers with anti-detection
- Handling JavaScript-rendered pages
- Evading WAF protections (Cloudflare, Akamai)

## MANDATORY: Chrome Impersonation

Always use `impersonate="chrome"`:

```python
from scrapling import Fetcher


fetcher = Fetcher(
    impersonate="chrome",
    follow_redirects=True,
    timeout=30,
)

response = fetcher.fetch("https://example.com")
```

## Anti-Detection Configuration

```python
from scrapling import Fetcher


fetcher = Fetcher(
    impersonate="chrome",
    headers={
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
    },
    disable_webdriver=True,
    stealth=True,
)
```

## Retry with Exponential Backoff

```python
import asyncio
import random


async def fetch_with_retry(
    fetcher: Fetcher,
    url: str,
    max_retries: int = 3,
    base_delay: float = 1.0,
) -> str:
    """Fetch con reintento exponencial y jitter."""
    for attempt in range(max_retries):
        try:
            response = await asyncio.to_thread(fetcher.fetch, url)
            if response.status == 200:
                return response.content
        except Exception:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2**attempt) + random.uniform(0, 1)
            await asyncio.sleep(delay)
    raise RuntimeError("Max retries exceeded")
```

## HTML Parsing with Selectolax

```python
from selectolax.lexbor import LexborHTMLParser


def extract_links(html: str, base_url: str) -> list[str]:
    """Extrae links del HTML."""
    parser = LexborHTMLParser(html)
    links = []
    for node in parser.css("a[href]"):
        href = node.attributes.get("href", "")
        if href.startswith("http"):
            links.append(href)
    return links
```

## HTML to Markdown (MarkItDown)

```python
from markitdown import MarkItDown


def html_to_markdown(html: str, url: str) -> str:
    """Convierte HTML a Markdown para LLM/RAG."""
    converter = MarkItDown()
    result = converter.convert(html, url=url)
    return result.text_content
```

## Handling JavaScript Pages

```python
from scrapling import Fetcher


fetcher = Fetcher(
    impersonate="chrome",
    headless=True,
    auto_match=True,
    network_idle=True,
    wait_for="body",
)

response = fetcher.fetch("https://spa-example.com")
```

## Common Patterns

### Extract structured data
```python
from selectolax.lexbor import LexborHTMLParser


def extract_article(html: str) -> dict[str, str]:
    parser = LexborHTMLParser(html)
    return {
        "title": parser.css_first("h1").text() if parser.css_first("h1") else "",
        "content": parser.css_first("article").text() if parser.css_first("article") else "",
        "date": parser.css_first("time").attributes.get("datetime", ""),
    }
```

### Handle pagination
```python
def get_next_page(html: str, base_url: str) -> str | None:
    parser = LexborHTMLParser(html)
    next_link = parser.css_first('a[rel="next"], a.next, a[aria-label="Next"]')
    if next_link:
        href = next_link.attributes.get("href", "")
        if href.startswith("/"):
            return f"{base_url.rstrip('/')}{href}"
        return href
    return None
```

## Error Handling

```python
from scrapling import Fetcher


async def safe_fetch(fetcher: Fetcher, url: str) -> dict:
    """Fetch con manejo de errores completo."""
    try:
        response = await asyncio.to_thread(fetcher.fetch, url)
        return {
            "url": url,
            "status": response.status,
            "content": response.content,
            "success": response.status == 200,
        }
    except Exception as e:
        return {
            "url": url,
            "status": 0,
            "error": str(e)[:500],
            "success": False,
        }
```

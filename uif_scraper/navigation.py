from typing import Any, Protocol
from urllib.parse import urljoin, urlparse

from uif_scraper.models import ScrapingScope


class HTMLParserLike(Protocol):
    """Protocolo para parsers HTML con método css()."""

    def css(self, selector: str) -> Any:
        """Selecciona elementos del DOM usando CSS selectors."""
        ...


class NavigationService:
    """Servicio de navegación y control de scope para web scraping."""

    def __init__(self, base_url: str, scope: ScrapingScope = ScrapingScope.SMART):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.scope = scope

    def is_asset(self, url: str) -> bool:
        asset_extensions = [
            ".pdf",
            ".jpg",
            ".png",
            ".jpeg",
            ".gif",
            ".svg",
            ".webp",
            ".md",  # Markdown files are assets, not webpages
            ".txt",  # Text files
            ".csv",  # Data files
        ]
        return any(url.lower().endswith(ext) for ext in asset_extensions)

    def is_noise(self, url: str) -> bool:
        noise_extensions = [".css", ".js", ".json", ".xml", ".ico"]
        return any(url.lower().endswith(ext) for ext in noise_extensions)

    def should_follow(self, full_url: str) -> bool:
        parsed_link = urlparse(full_url)
        # 1. Validación de dominio (External Leak Protection)
        if parsed_link.netloc != self.domain:
            return False

        # 2. Broad Scope: Todo el dominio está permitido
        if self.scope == ScrapingScope.BROAD:
            return True

        # 3. Strict Scope: Solo subrutas exactas de la semilla
        # Usa removeprefix para verificar pertenencia de forma segura
        if self.scope == ScrapingScope.STRICT:
            return full_url == self.base_url or full_url.removeprefix(
                self.base_url
            ).startswith("/")

        # 4. Smart Scope: Lógica de subdirectorio inteligente
        # Si la semilla es raíz (ej: domain.com/), se comporta como Broad.
        # Si tiene subdirectorio (ej: domain.com/blog), se comporta como Strict.
        base_path = urlparse(self.base_url).path
        path_parts = [p for p in base_path.strip("/").split("/") if p]
        if not path_parts:
            return True  # Es raíz del dominio

        return full_url == self.base_url or full_url.removeprefix(
            self.base_url
        ).startswith("/")

    def extract_links(
        self, html_parser: HTMLParserLike, current_url: str
    ) -> tuple[list[str], list[str]]:
        """Extrae links y assets de una página HTML.

        Args:
            html_parser: Parser HTML con método css() (selectolax, scrapling, etc.)
            current_url: URL actual para resolver links relativos.

        Returns:
            Tupla (nuevas_paginas, nuevos_assets) sin duplicados.
        """
        links = [str(node) for node in html_parser.css("a::attr(href)")]
        images = [str(node) for node in html_parser.css("img::attr(src)")]

        new_pages: list[str] = []
        new_assets: list[str] = []

        for link in links + images:
            if not link:
                continue
            full_url = urljoin(current_url, str(link)).split("#")[0]

            if self.is_asset(full_url):
                if self.should_follow(full_url):
                    new_assets.append(full_url)
            elif not self.is_noise(full_url):
                if self.should_follow(full_url):
                    new_pages.append(full_url)

        return list(set(new_pages)), list(set(new_assets))

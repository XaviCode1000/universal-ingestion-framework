from urllib.parse import urljoin, urlparse
from typing import List, Any
from uif_scraper.models import ScrapingScope


class NavigationService:
    def __init__(self, base_url: str, scope: ScrapingScope = ScrapingScope.SMART):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.scope = scope

    def is_asset(self, url: str) -> bool:
        asset_extensions = [".pdf", ".jpg", ".png", ".jpeg", ".gif", ".svg", ".webp"]
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

        # 3. Normalización de base_url para comparaciones de prefijo
        # Aseguramos que termine en / si tiene path para evitar emparejamientos parciales (ej: /docs vs /docs-old)
        base_path = urlparse(self.base_url).path
        normalized_base = (
            self.base_url
            if base_path.endswith("/") or not base_path
            else f"{self.base_url}/"
        )

        # 4. Strict Scope: Solo subrutas exactas de la semilla
        if self.scope == ScrapingScope.STRICT:
            return full_url.startswith(normalized_base) or full_url == self.base_url

        # 5. Smart Scope: Lógica de subdirectorio inteligente
        # Si la semilla es una raíz (ej: domain.com/), se comporta como Broad.
        # Si tiene subdirectorio (ej: domain.com/blog), se comporta como Strict.
        path_parts = [p for p in base_path.strip("/").split("/") if p]
        if not path_parts:
            return True  # Es raíz del dominio

        return full_url.startswith(normalized_base) or full_url == self.base_url

    def extract_links(
        self, html_parser: Any, current_url: str
    ) -> tuple[List[str], List[str]]:
        links = [str(node) for node in html_parser.css("a::attr(href)")]
        images = [str(node) for node in html_parser.css("img::attr(src)")]

        new_pages: List[str] = []
        new_assets: List[str] = []

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

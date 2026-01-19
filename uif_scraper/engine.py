import asyncio
import json
from typing import Optional, Set
from urllib.parse import urljoin, urlparse

import aiofiles
from loguru import logger
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID
from scrapling.fetchers import AsyncFetcher, AsyncStealthySession

from uif_scraper.config import ScraperConfig
from uif_scraper.db_manager import StateManager
from uif_scraper.models import MigrationStatus, ScrapingScope, WebPage
from uif_scraper.extractors.text_extractor import TextExtractor
from uif_scraper.extractors.metadata_extractor import MetadataExtractor
from uif_scraper.extractors.asset_extractor import AssetExtractor
from uif_scraper.utils.url_utils import smart_url_normalize, slugify
from uif_scraper.utils.html_cleaner import pre_clean_html

from uif_scraper.utils.circuit_breaker import CircuitBreaker

console = Console()


class UIFMigrationEngine:
    def __init__(
        self,
        config: ScraperConfig,
        state: StateManager,
        text_extractor: TextExtractor,
        metadata_extractor: MetadataExtractor,
        asset_extractor: AssetExtractor,
        base_url: str,
        scope: ScrapingScope = ScrapingScope.SMART,
        circuit_breaker: Optional[CircuitBreaker] = None,
    ):
        self.config = config
        self.state = state
        self.text_extractor = text_extractor
        self.metadata_extractor = metadata_extractor
        self.asset_extractor = asset_extractor
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.scope = scope
        self.circuit_breaker = circuit_breaker or CircuitBreaker()

        self.url_queue: asyncio.Queue[str] = asyncio.Queue()
        self.asset_queue: asyncio.Queue[str] = asyncio.Queue()

        self.seen_urls: Set[str] = set()
        self.seen_assets: Set[str] = set()

        self.pages_completed = 0
        self.assets_completed = 0

        self.semaphore = asyncio.Semaphore(config.default_workers)
        self.report_lock = asyncio.Lock()

        self.progress: Optional[Progress] = None

        self.page_task: Optional[TaskID] = None
        self.asset_task: Optional[TaskID] = None
        self.use_browser_mode = False

    async def log_event(self, data: WebPage) -> None:
        report_path = self.config.data_dir / "migration_audit.jsonl"
        async with self.report_lock:
            async with aiofiles.open(report_path, "a", encoding="utf-8") as f:
                await f.write(json.dumps(data.model_dump(mode="json")) + "\n")

    async def setup(self) -> None:
        await self.state.initialize()

        async with self.state.pool.acquire() as db:
            async with db.execute("SELECT url, type, status FROM urls") as cursor:
                async for row in cursor:
                    url, m_type, status = row
                    if m_type == "asset":
                        self.seen_assets.add(url)
                        if status == MigrationStatus.COMPLETED.value:
                            self.assets_completed += 1
                    else:
                        self.seen_urls.add(url)
                        if status == MigrationStatus.COMPLETED.value:
                            self.pages_completed += 1

        pending = await self.state.get_pending_urls(max_retries=self.config.max_retries)
        if not pending and not self.seen_urls:
            await self.state.add_url(self.base_url, MigrationStatus.PENDING)
            self.seen_urls.add(self.base_url)
            pending = [self.base_url]

        for url in pending:
            await self.url_queue.put(url)

        pending_assets = await self.state.get_pending_urls(
            m_type="asset", max_retries=self.config.max_retries
        )
        for asset in pending_assets:
            await self.asset_queue.put(asset)

    async def download_asset(self, asset_url: str) -> None:
        async with self.semaphore:
            try:
                response = await AsyncFetcher.get(
                    asset_url, impersonate="chrome", timeout=self.config.timeout_seconds
                )
                if response.status == 200:
                    content = (
                        response.body
                        if isinstance(response.body, bytes)
                        else response.body.encode()
                    )
                    await self.asset_extractor.extract(content, asset_url)
                    await self.state.update_status(asset_url, MigrationStatus.COMPLETED)
                    self.assets_completed += 1
                    if self.progress and self.asset_task:
                        self.progress.update(
                            self.asset_task, completed=self.assets_completed
                        )
                else:
                    raise Exception(f"HTTP {response.status}")
            except Exception as e:
                await self.state.update_status(
                    asset_url, MigrationStatus.FAILED, str(e)
                )

    async def process_page(self, session: AsyncStealthySession, url: str) -> None:
        if not self.circuit_breaker.should_allow(self.domain):
            logger.warning(f"Circuit broken. Skipping {url}")
            await self.url_queue.put(url)
            await asyncio.sleep(1)
            return

        try:
            encoded_url = smart_url_normalize(url)

            page = None
            if self.use_browser_mode:
                page = await session.fetch(encoded_url, timeout=45000)
            else:
                resp = await AsyncFetcher.get(
                    encoded_url,
                    impersonate="chrome",
                    timeout=self.config.timeout_seconds,
                    headers={"Referer": self.base_url, "Origin": self.base_url},
                )

                if resp.status == 500:
                    await self.state.update_status(
                        url, MigrationStatus.FAILED, "Server Side Error (500)"
                    )
                    return

                if resp.status in [403, 401, 429]:
                    self.use_browser_mode = True
                    page = await session.fetch(encoded_url, timeout=45000)
                elif resp.status == 200:
                    page = resp
                else:
                    raise Exception(f"HTTP {resp.status}")

            if not page:
                raise Exception("Empty content")

            self.circuit_breaker.record_success(self.domain)

            raw_html = getattr(page, "raw_content", "") or getattr(page, "body", "")

            if not isinstance(raw_html, str):
                raw_html = raw_html.decode("utf-8", errors="replace")

            clean_html = pre_clean_html(raw_html)

            metadata_task = asyncio.create_task(
                self.metadata_extractor.extract(raw_html, url)
            )
            text_task = asyncio.create_task(
                self.text_extractor.extract(clean_html, url)
            )

            metadata = await metadata_task
            text_data = await text_task

            path_slug = slugify(
                url.replace(self.base_url, "").replace(".php", "") or "index"
            )
            md_path = self.config.data_dir / "content" / f"{path_slug}.md"
            md_path.parent.mkdir(parents=True, exist_ok=True)

            import yaml

            frontmatter = yaml.dump(metadata, allow_unicode=True, sort_keys=False)
            async with aiofiles.open(md_path, "w", encoding="utf-8") as f:
                await f.write(f"---\n{frontmatter}---\n\n{text_data['markdown']}")

            new_assets = []
            new_pages = []

            links = [str(node) for node in page.css("a::attr(href)")]
            images = [str(node) for node in page.css("img::attr(src)")]

            for link in links + images:
                if not link:
                    continue
                full_url = urljoin(url, str(link)).split("#")[0]
                parsed_link = urlparse(full_url)

                if parsed_link.netloc != self.domain:
                    continue

                is_asset = any(
                    full_url.lower().endswith(ext)
                    for ext in [
                        ".pdf",
                        ".jpg",
                        ".png",
                        ".jpeg",
                        ".gif",
                        ".svg",
                        ".webp",
                    ]
                )

                should_follow = False
                if is_asset:
                    should_follow = True
                elif self.scope == ScrapingScope.BROAD:
                    should_follow = True
                elif self.scope == ScrapingScope.STRICT:
                    if full_url.startswith(self.base_url):
                        should_follow = True
                elif self.scope == ScrapingScope.SMART:
                    path_parts = urlparse(self.base_url).path.strip("/").split("/")
                    path_depth = len([p for p in path_parts if p])
                    if path_depth >= 1:
                        if full_url.startswith(self.base_url):
                            should_follow = True
                    else:
                        should_follow = True

                if not should_follow:
                    continue

                if is_asset:
                    if full_url not in self.seen_assets:
                        self.seen_assets.add(full_url)
                        new_assets.append(full_url)
                else:
                    if not any(
                        full_url.lower().endswith(x)
                        for x in [".css", ".js", ".json", ".xml", ".ico"]
                    ):
                        if full_url not in self.seen_urls:
                            self.seen_urls.add(full_url)
                            new_pages.append(full_url)

            assets_to_add = [
                (asset, MigrationStatus.PENDING, "asset") for asset in new_assets
            ]
            pages_to_add = [
                (p_url, MigrationStatus.PENDING, "webpage") for p_url in new_pages
            ]

            await self.state.add_urls_batch(assets_to_add + pages_to_add)

            for asset in new_assets:
                await self.asset_queue.put(asset)

            for p_url in new_pages:
                await self.url_queue.put(p_url)

            await self.state.update_status(url, MigrationStatus.COMPLETED)
            self.pages_completed += 1

            if self.progress:
                if self.page_task:
                    self.progress.update(
                        self.page_task,
                        completed=self.pages_completed,
                        total=len(self.seen_urls),
                    )
                if self.asset_task:
                    self.progress.update(self.asset_task, total=len(self.seen_assets))

            await self.log_event(
                WebPage(
                    url=url,
                    title=metadata["title"],
                    content_md_path=str(md_path),
                    assets=new_assets,
                )
            )

        except Exception as e:
            self.circuit_breaker.record_failure(self.domain)
            current_retries = await self.state.increment_retry(url)
            logger.warning(
                f"Retry {current_retries}/{self.config.max_retries} for {url}: {e}"
            )
            if current_retries < self.config.max_retries:
                backoff = 2**current_retries
                await asyncio.sleep(float(backoff))
                await self.url_queue.put(url)
            else:
                await self.state.update_status(url, MigrationStatus.FAILED, str(e))

    async def page_worker(self, session: AsyncStealthySession) -> None:
        while True:
            url = await self.url_queue.get()
            try:
                async with self.semaphore:
                    await self.process_page(session, url)
            finally:
                self.url_queue.task_done()

    async def asset_worker(self) -> None:
        while True:
            url = await self.asset_queue.get()
            try:
                await self.download_asset(url)
            finally:
                self.asset_queue.task_done()

    async def generate_summary(self) -> None:
        import polars as pl

        console.print("\n[bold cyan]📊 Reporte Final de Migración[/]")

        async with self.state.pool.acquire() as db:
            cursor = await db.execute(
                "SELECT status, COUNT(*) as count FROM urls GROUP BY status"
            )
            rows = await cursor.fetchall()

            if rows:
                schema_gen = {"status": pl.String, "count": pl.Int64}
                df = pl.DataFrame(rows, schema=schema_gen, orient="row")
                console.print(df.sort("count", descending=True))
            else:
                console.print("[dim]No hay datos.[/dim]")

            console.print("\n[bold red]⚠️ Fallos Críticos (Top 5):[/]")
            cursor_fail = await db.execute(
                "SELECT COALESCE(last_error, 'Unknown') as error, COUNT(*) as count FROM urls WHERE status='failed' GROUP BY last_error ORDER BY count DESC LIMIT 5"
            )
            rows_fail = await cursor_fail.fetchall()

            if rows_fail:
                schema_fail = {"error": pl.String, "count": pl.Int64}
                console.print(pl.DataFrame(rows_fail, schema=schema_fail, orient="row"))
            else:
                console.print("[green]¡Cero fallos![/green]")

    async def run(self) -> None:
        await self.setup()

        dns_args = []
        if self.config.dns_overrides:
            rules = ", ".join(
                [
                    f"MAP {domain} {ip}"
                    for domain, ip in self.config.dns_overrides.items()
                ]
            )
            dns_args.append(f"--host-resolver-rules={rules}")

        additional_args = {"args": dns_args + ["--disable-gpu", "--no-sandbox"]}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            console=console,
        ) as progress:
            self.progress = progress
            self.page_task = progress.add_task(
                "[cyan]Páginas",
                total=len(self.seen_urls),
                completed=self.pages_completed,
            )
            self.asset_task = progress.add_task(
                "[magenta]Assets",
                total=len(self.seen_assets),
                completed=self.assets_completed,
            )

            async with AsyncStealthySession(
                headless=True,
                max_pages=self.config.default_workers,
                solve_cloudflare=True,
                additional_args=additional_args,
            ) as session:
                page_workers = [
                    asyncio.create_task(self.page_worker(session))
                    for _ in range(self.config.default_workers)
                ]
                asset_workers = [
                    asyncio.create_task(self.asset_worker())
                    for _ in range(self.config.asset_workers)
                ]

                await self.url_queue.join()
                await self.asset_queue.join()

                for w in page_workers + asset_workers:
                    w.cancel()

        await self.generate_summary()

import asyncio
import json
from pathlib import Path
from typing import Any

import aiofiles
import yaml
from loguru import logger
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from scrapling.fetchers import AsyncFetcher, AsyncStealthySession

from uif_scraper.config import ScraperConfig
from uif_scraper.db_manager import StateManager
from uif_scraper.extractors.asset_extractor import AssetExtractor
from uif_scraper.extractors.metadata_extractor import MetadataExtractor
from uif_scraper.extractors.text_extractor import TextExtractor
from uif_scraper.models import MigrationStatus, WebPage
from uif_scraper.navigation import NavigationService
from uif_scraper.reporter import ReporterService
from uif_scraper.utils.circuit_breaker import CircuitBreaker
from uif_scraper.utils.compression import write_compressed_markdown
from uif_scraper.utils.html_cleaner import pre_clean_html
from uif_scraper.utils.http_session import HTTPSessionCache
from uif_scraper.utils.url_utils import slugify, smart_url_normalize


class UIFMigrationEngine:
    def __init__(
        self,
        config: ScraperConfig,
        state: StateManager,
        text_extractor: TextExtractor,
        metadata_extractor: MetadataExtractor,
        asset_extractor: AssetExtractor,
        navigation_service: NavigationService,
        reporter_service: ReporterService,
        extract_assets: bool = True,
    ) -> None:
        self.config = config
        self.state = state
        self.text_extractor = text_extractor
        self.metadata_extractor = metadata_extractor
        self.asset_extractor = asset_extractor
        self.navigation = navigation_service
        self.reporter = reporter_service

        self.extract_assets = extract_assets
        self.circuit_breaker = CircuitBreaker()
        self.http_cache = HTTPSessionCache(
            max_pool_size=config.asset_workers * 2,
            max_connections_per_host=10,
            timeout_total=config.timeout_seconds,
        )

        self.url_queue: asyncio.Queue[str] = asyncio.Queue()
        self.asset_queue: asyncio.Queue[str] = asyncio.Queue()

        self.seen_urls: set[str] = set()
        self.seen_assets: set[str] = set()

        self.pages_completed = 0
        self.assets_completed = 0

        self.semaphore = asyncio.Semaphore(config.default_workers)
        self.report_lock = asyncio.Lock()

        self.progress: Progress | None = None
        self.page_task: TaskID | None = None
        self.asset_task: TaskID | None = None
        self.use_browser_mode = False
        self.activity_log: list[dict[str, Any]] = []
        self.start_time = asyncio.get_event_loop().time()
        self._shutdown_event = asyncio.Event()
        self._page_workers: list[asyncio.Task[None]] = []
        self._asset_workers: list[asyncio.Task[None]] = []

    def create_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
        )
        layout["body"].split_row(
            Layout(name="stats", ratio=1),
            Layout(name="activity", ratio=2),
        )
        return layout

    def update_layout(self, layout: Layout) -> None:
        # Header
        layout["header"].update(
            Panel(
                f"🛸 [bold blue]MISIÓN:[/][white] {self.navigation.base_url} [/] | "
                f"[bold yellow]SCOPE:[/][white] {self.navigation.scope.value.upper()} [/] | "
                f"[bold cyan]WORKERS:[/][white] {self.config.default_workers} [/] | "
                f"[bold green]MODE:[/][white] {'BROWSER' if self.use_browser_mode else 'STEALTH'}",
                border_style="blue",
            )
        )

        # Stats Panel
        stats_table = Table.grid(expand=True)
        stats_table.add_row(self.progress) if self.progress else None

        elapsed = asyncio.get_event_loop().time() - self.start_time
        pages_per_sec = self.pages_completed / elapsed if elapsed > 0 else 0

        summary_table = Table(box=None, expand=True)
        summary_table.add_column("Métrica", style="dim")
        summary_table.add_column("Valor", justify="right")
        summary_table.add_row("Páginas/seg", f"{pages_per_sec:.2f}")
        summary_table.add_row("Visto (URLs)", f"{len(self.seen_urls)}")
        summary_table.add_row("Visto (Assets)", f"{len(self.seen_assets)}")

        layout["stats"].update(
            Panel(
                Layout(stats_table), title="[bold]ESTADO ACTUAL[/]", border_style="cyan"
            )
        )

        # Activity Panel
        activity_table = Table(box=None, expand=True)
        activity_table.add_column("Título", ratio=3, style="bold white")
        activity_table.add_column("Motor", ratio=1, justify="center")

        for entry in self.activity_log[-6:]:
            color = "green" if entry["engine"] == "trafilatura" else "yellow"
            title = (
                (entry["title"][:45] + "..")
                if len(entry["title"]) > 45
                else entry["title"]
            )
            activity_table.add_row(title, f"[{color}]{entry['engine']}[/]")

        layout["activity"].update(
            Panel(
                activity_table,
                title="[bold green]ÚLTIMAS INGESTAS[/]",
                border_style="green",
            )
        )

    async def log_event(self, data: WebPage, engine: str = "unknown") -> None:
        report_path = self.asset_extractor.data_dir / "migration_audit.jsonl"

        # Actualizar log visual interno
        self.activity_log.append(
            {
                "title": data.title,
                "engine": engine,
                "time": asyncio.get_event_loop().time(),
            }
        )

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
            await self.state.add_url(self.navigation.base_url, MigrationStatus.PENDING)
            self.seen_urls.add(self.navigation.base_url)
            pending = [self.navigation.base_url]

        for url in pending:
            await self.url_queue.put(url)

        pending_assets = await self.state.get_pending_urls(
            m_type="asset", max_retries=self.config.max_retries
        )
        for asset in pending_assets:
            await self.asset_queue.put(asset)

    async def download_asset(self, asset_url: str) -> None:
        """Descarga asset usando sesión HTTP reutilizable con connection pooling."""
        async with self.semaphore:
            try:
                # Usar sesión HTTP reutilizable en lugar de crear nueva conexión
                session = await self.http_cache.get_session()
                async with session.get(asset_url) as response:
                    if response.status == 200:
                        content = await response.read()
                        await self.asset_extractor.extract(content, asset_url)
                        await self.state.update_status(
                            asset_url, MigrationStatus.COMPLETED
                        )
                        self.assets_completed += 1
                        if self.progress and self.asset_task:
                            self.progress.update(
                                self.asset_task, completed=self.assets_completed
                            )
                    else:
                        raise Exception(f"HTTP {response.status}")
            except Exception as e:
                await self.state.update_status(asset_url, MigrationStatus.FAILED, str(e))

    async def process_page(self, session: AsyncStealthySession, url: str) -> None:
        if not self.circuit_breaker.should_allow(self.navigation.domain):
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
                    headers={
                        "Referer": self.navigation.base_url,
                        "Origin": self.navigation.base_url,
                    },
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

            self.circuit_breaker.record_success(self.navigation.domain)
            raw_html = getattr(page, "raw_content", "") or getattr(page, "body", "")
            if not isinstance(raw_html, str):
                raw_html = raw_html.decode("utf-8", errors="replace")

            clean_html = pre_clean_html(raw_html)
            
            # Concurrencia estructurada con TaskGroup (Python 3.11+)
            # Permite cancelación automática si una tarea falla
            async with asyncio.TaskGroup() as tg:
                metadata_task = tg.create_task(
                    self.metadata_extractor.extract(raw_html, url)
                )
                text_task = tg.create_task(
                    self.text_extractor.extract(clean_html, url)
                )
            
            metadata = metadata_task.result()
            text_data = text_task.result()

            # Construcción robusta del path (Python 3.9+ best practice)
            # 1. removeprefix es más seguro que replace (solo quita del inicio)
            rel_path = url.removeprefix(self.navigation.base_url)
            # 2. Path.stem extrae el nombre sin extensión automáticamente
            raw_slug = Path(rel_path).stem or "index"
            # 3. Slugify sanitiza para nombre de archivo seguro
            path_slug = slugify(raw_slug)
            # 4. with_suffix maneja la extensión correctamente
            md_path = (
                self.asset_extractor.data_dir / "content" / path_slug
            ).with_suffix(".md")
            md_path.parent.mkdir(parents=True, exist_ok=True)

            frontmatter = yaml.dump(metadata, allow_unicode=True, sort_keys=False)
            markdown_content = f"---\n{frontmatter}---\n\n{text_data['markdown']}"
            
            # Guardar con compresión Zstandard (ahorra 30-40% de espacio)
            md_path = await write_compressed_markdown(
                self.asset_extractor.data_dir / "content" / path_slug,
                markdown_content,
                compression="zstd",  # Mejor balance velocidad/ratio
                compression_level=3,  # Nivel óptimo para uso general
            )
            md_path.parent.mkdir(parents=True, exist_ok=True)

            new_pages, new_assets = self.navigation.extract_links(page, url)

            new_assets_filtered = [
                a
                for a in new_assets
                if a not in self.seen_assets and self.extract_assets
            ]
            new_pages_filtered = [p for p in new_pages if p not in self.seen_urls]

            for a in new_assets_filtered:
                self.seen_assets.add(a)
            for p in new_pages_filtered:
                self.seen_urls.add(p)

            assets_to_add = [
                (a, MigrationStatus.PENDING, "asset") for a in new_assets_filtered
            ]
            pages_to_add = [
                (p, MigrationStatus.PENDING, "webpage") for p in new_pages_filtered
            ]
            await self.state.add_urls_batch(assets_to_add + pages_to_add)

            for a in new_assets_filtered:
                await self.asset_queue.put(a)
            for p in new_pages_filtered:
                await self.url_queue.put(p)

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
                    assets=new_assets_filtered,
                ),
                engine=text_data["engine"],
            )

        except Exception as e:
            self.circuit_breaker.record_failure(self.navigation.domain)
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
        """Worker de páginas con early exit para circuit breaker."""
        while not self._shutdown_event.is_set():
            try:
                url = await asyncio.wait_for(self.url_queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            # EARLY EXIT: Verificar circuit breaker ANTES de adquirir semaphore
            # Evita trabajo innecesario cuando el circuito está abierto
            if not self.circuit_breaker.should_allow(self.navigation.domain):
                logger.warning(
                    f"Circuit breaker open for {self.navigation.domain}, requeuing {url}"
                )
                await self.url_queue.put(url)
                # Backoff exponencial basado en fallos
                failures = self.circuit_breaker.failures.get(self.navigation.domain, 0)
                await asyncio.sleep(min(2**failures, 30))  # Max 30s
                self.url_queue.task_done()
                continue

            try:
                async with self.semaphore:
                    # Doble verificación después de adquirir semaphore
                    if not self.circuit_breaker.should_allow(self.navigation.domain):
                        await self.url_queue.put(url)
                        self.url_queue.task_done()
                        continue
                    await self.process_page(session, url)
            except asyncio.CancelledError:
                logger.warning(
                    "Worker cancelled processing %s, marking as pending", url
                )
                await self.state.update_status(
                    url, MigrationStatus.PENDING, immediate=True
                )
                raise
            except Exception as e:
                logger.error("Error processing %s: %s", url, e)
            finally:
                self.url_queue.task_done()

    async def asset_worker(self) -> None:
        while not self._shutdown_event.is_set():
            try:
                url = await asyncio.wait_for(self.asset_queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            try:
                await self.download_asset(url)
            except asyncio.CancelledError:
                logger.warning(
                    "Asset worker cancelled downloading %s, marking as pending", url
                )
                await self.state.update_status(url, MigrationStatus.PENDING)
                raise
            except Exception as e:
                logger.error("Error downloading %s: %s", url, e)
            finally:
                # Always mark task as done
                self.asset_queue.task_done()

    def request_shutdown(self) -> None:
        """Signal graceful shutdown. Workers will stop accepting new tasks."""
        self._shutdown_event.set()
        logger.info("Shutdown requested. Workers will finish current tasks...")

    async def run(self) -> None:
        """Ejecuta el scraping con métricas de performance y shutdown adaptativo."""
        await self.setup()
        
        # Log de configuración inicial para debugging
        logger.info(
            "Starting scraping mission",
            extra={
                "url": self.navigation.base_url,
                "scope": self.navigation.scope.value,
                "workers": self.config.default_workers,
                "asset_workers": self.config.asset_workers,
                "timeout_seconds": self.config.timeout_seconds,
            },
        )
        
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

        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeElapsedColumn(),
            expand=True,
        )

        self.page_task = self.progress.add_task(
            "[cyan]Páginas",
            total=len(self.seen_urls),
            completed=self.pages_completed,
        )
        self.asset_task = self.progress.add_task(
            "[magenta]Assets",
            total=len(self.seen_assets),
            completed=self.assets_completed,
        )

        dashboard = self.create_layout()

        with Live(dashboard, refresh_per_second=4, screen=False):
            async with AsyncStealthySession(
                headless=True,
                max_pages=self.config.default_workers,
                solve_cloudflare=True,
                additional_args=additional_args,
            ) as session:
                self._page_workers = [
                    asyncio.create_task(self.page_worker(session))
                    for _ in range(self.config.default_workers)
                ]
                self._asset_workers = []
                if self.extract_assets:
                    self._asset_workers = [
                        asyncio.create_task(self.asset_worker())
                        for _ in range(self.config.asset_workers)
                    ]

                all_workers = self._page_workers + self._asset_workers

                try:
                    while not self._shutdown_event.is_set():
                        self.update_layout(dashboard)

                        # Check if all work is done
                        if (
                            self.url_queue.empty()
                            and self.asset_queue.empty()
                            and all(w.done() for w in all_workers)
                        ):
                            break

                        await asyncio.sleep(0.25)

                    # Graceful shutdown: wait for queues to drain
                    if not self._shutdown_event.is_set():
                        logger.info("Work completed. Draining queues...")

                    await self.url_queue.join()
                    if self.extract_assets:
                        await self.asset_queue.join()

                except* Exception as exc_group:
                    # Manejo estructurado de excepciones múltiples (Python 3.11+)
                    for exc in exc_group.exceptions:
                        logger.error(f"Error en worker: {exc}")
                        self.circuit_breaker.record_failure(self.navigation.domain)
                    raise

                finally:
                    # Signal workers to stop
                    self._shutdown_event.set()
                    
                    # Timeout adaptativo basado en tareas pendientes
                    pending_urls = self.url_queue.qsize()
                    pending_assets = self.asset_queue.qsize()
                    total_pending = pending_urls + pending_assets
                    
                    if total_pending > 0:
                        # 2 segundos por tarea pendiente, mínimo 30s
                        per_worker_timeout = max(30.0, total_pending * 2.0)
                        logger.info(
                            f"Waiting for {total_pending} pending tasks with {per_worker_timeout}s timeout"
                        )
                    else:
                        per_worker_timeout = 30.0

                    # Wait for workers to finish with adaptive timeout
                    if all_workers:
                        done, pending = await asyncio.wait(
                            all_workers,
                            timeout=per_worker_timeout,
                            return_when=asyncio.ALL_COMPLETED,
                        )

                        # Cancel solo los que realmente están pendientes
                        if pending:
                            for w in pending:
                                logger.warning(
                                    f"Worker {w.get_name()} did not finish in time, cancelling"
                                )
                                w.cancel()

                            # Esperar confirmación de cancelación
                            await asyncio.wait(pending, timeout=5.0)

        await self.reporter.generate_summary()
        
        # Cerrar sesión HTTP para liberar conexiones
        await self.http_cache.close()

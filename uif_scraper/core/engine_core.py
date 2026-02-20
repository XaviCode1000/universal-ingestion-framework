"""Core engine logic for UIF Migration Engine.

This module contains the complete scraping business logic.
UI implementations subscribe via UICallback interface.

Reference: AGENTS.md - SRP (Single Responsibility Principle)
"""

import asyncio
import enum
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

import aiohttp
import yaml
from cachetools import TTLCache
from loguru import logger
from scrapling.fetchers import AsyncFetcher, AsyncStealthySession

from uif_scraper.config import ScraperConfig
from uif_scraper.core.constants import (
    DEFAULT_BROWSER_TIMEOUT_MS,
    DEFAULT_QUEUE_TIMEOUT_SECONDS,
    HTTP_MAX_CONNECTIONS_PER_HOST,
    MIN_SHUTDOWN_TIMEOUT_SECONDS,
)
from uif_scraper.core.types import ActivityEntry, DashboardState, EngineStats
from uif_scraper.db_manager import StateManager
from uif_scraper.extractors.asset_extractor import AssetExtractor
from uif_scraper.extractors.metadata_extractor import MetadataExtractor
from uif_scraper.extractors.text_extractor import TextExtractor
from uif_scraper.models import MigrationStatus
from uif_scraper.navigation import NavigationService
from uif_scraper.reporter import ReporterService
from uif_scraper.utils.captcha_detector import CaptchaDetector
from uif_scraper.utils.circuit_breaker import CircuitBreaker
from uif_scraper.utils.compression import write_compressed_markdown
from uif_scraper.utils.html_cleaner import pre_clean_html
from uif_scraper.utils.http_session import HTTPSessionCache
from uif_scraper.utils.markdown_utils import enhance_markdown_for_rag
from uif_scraper.utils.robots_checker import RobotsChecker
from uif_scraper.utils.url_utils import slugify, smart_url_normalize


# ============================================================================
# FRONTMATTER FILTERING (RAG-optimized)
# ============================================================================

# Campos que van al YAML frontmatter (RAG-friendly)
FRONTMATTER_FIELDS: set[str] = {
    "url",
    "title",
    "author",
    "date",
    "sitename",
    "description",
    "keywords",
    "og_title",
    "og_description",
    "og_image",
    "og_type",
    "twitter_card",
    "twitter_site",
    "ingestion_engine",
}


def filter_metadata_for_frontmatter(metadata: dict[str, Any]) -> dict[str, Any]:
    """Filtra metadata para incluir solo campos relevantes en YAML frontmatter.

    Excluye campos pesados como headers (TOC) y json_ld (structured data)
    que inflan el frontmatter sin aportar valor al filtering RAG.

    Args:
        metadata: Metadata completa del documento

    Returns:
        Metadata filtrada para YAML frontmatter
    """
    filtered = {k: v for k, v in metadata.items() if k in FRONTMATTER_FIELDS}
    # Solo incluir campos con valores no-vacíos
    return {k: v for k, v in filtered.items() if v is not None and v != []}


class _Sentinel(enum.Enum):
    """Sentinel value for signaling workers to stop.

    Using Enum is the recommended pattern for mypy compatibility.
    Reference: https://stackoverflow.com/questions/57959664/handling-conditional-logic-sentinel-value-with-mypy
    """

    STOP = object()


# Sentinel instance to signal workers to stop
_STOP_SENTINEL = _Sentinel.STOP

# Type alias for queue items - URL string or stop sentinel
QueueItem = str | _Sentinel

if TYPE_CHECKING:
    pass


class UICallback(ABC):
    """Abstract interface for UI updates.

    Implement this in your UI class (Rich, Textual, etc.)
    to receive updates from the engine core.
    """

    @abstractmethod
    def on_progress(self, stats: EngineStats) -> None:
        """Called when progress updates are available."""
        ...

    @abstractmethod
    def on_activity(self, entry: ActivityEntry) -> None:
        """Called when a new activity occurs."""
        ...

    @abstractmethod
    def on_mode_change(self, browser_mode: bool) -> None:
        """Called when fetch mode changes (stealth -> browser)."""
        ...

    @abstractmethod
    def on_circuit_change(self, state: str) -> None:
        """Called when circuit breaker state changes."""
        ...


class EngineCore:
    """Core scraping engine - UI-agnostic business logic.

    This class contains all the scraping logic. UI implementations should:
    1. Create EngineCore with dependencies
    2. Set ui_callback for event-driven updates
    3. Call run() to start scraping

    Example:
        core = EngineCore(config, state, extractors, ...)
        core.ui_callback = MyUICallback()
        await core.run()
    """

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
        # Configuration
        self.config = config
        self.extract_assets = extract_assets

        # Dependencies
        self.state = state
        self.text_extractor = text_extractor
        self.metadata_extractor = metadata_extractor
        self.asset_extractor = asset_extractor
        self.navigation = navigation_service
        self.reporter = reporter_service

        # Infrastructure
        self.circuit_breaker = CircuitBreaker()
        self.http_cache = HTTPSessionCache(
            max_pool_size=config.asset_workers * 2,
            max_connections_per_host=HTTP_MAX_CONNECTIONS_PER_HOST,
            timeout_total=config.timeout_seconds,
            verify_ssl=True, # Forzado por PRD v4.0
        )
        self.robots_checker = RobotsChecker(self.http_cache)
        self.captcha_detector = CaptchaDetector()

        # Queues - use QueueItem type to allow sentinel values
        self.url_queue: asyncio.Queue[QueueItem] = asyncio.Queue()
        self.asset_queue: asyncio.Queue[QueueItem] = asyncio.Queue()

        # State tracking (Fase 1: TTLCache para prevenir OOM)
        # Limitamos a 100,000 entradas en memoria con TTL de 1 hora
        self.seen_urls: TTLCache[str, bool] = TTLCache(maxsize=100000, ttl=3600)
        self.seen_assets: TTLCache[str, bool] = TTLCache(maxsize=100000, ttl=3600)
        
        # Contadores de progreso (respaldados por DB en setup())
        self._pages_total_count = 0
        self._assets_total_count = 0
        
        self.pages_completed = 0
        self.assets_completed = 0
        self.pages_failed = 0
        self.assets_failed = 0
        self.error_count = 0

        # Concurrency control
        self.semaphore = asyncio.Semaphore(config.default_workers)
        self.report_lock = asyncio.Lock()

        # Runtime state
        self.use_browser_mode = False
        self.activity_log: list[dict[str, Any]] = []
        self.start_time: float = 0
        self._shutdown_event = asyncio.Event()
        self._page_workers: list[asyncio.Task[None]] = []
        self._asset_workers: list[asyncio.Task[None]] = []

        # UI callback (set by UI implementation)
        self.ui_callback: UICallback | None = None

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def get_stats(self) -> EngineStats:
        """Get current engine statistics snapshot."""
        return EngineStats(
            pages_completed=self.pages_completed,
            pages_total=self._pages_total_count,
            assets_completed=self.assets_completed,
            assets_total=self._assets_total_count,
            pages_failed=self.pages_failed,
            assets_failed=self.assets_failed,
            seen_urls=len(self.seen_urls),
            seen_assets=len(self.seen_assets),
            error_count=self.error_count,
            queue_pending=self.url_queue.qsize() + self.asset_queue.qsize(),
        )

    def get_dashboard_state(self, elapsed_seconds: float = 0.0) -> DashboardState:
        """Get complete state for dashboard rendering."""
        return DashboardState(
            base_url=self.navigation.base_url,
            scope=self.navigation.scope.value,
            workers=self.config.default_workers,
            mode="browser" if self.use_browser_mode else "stealth",
            stats=self.get_stats(),
            circuit_state=self.circuit_breaker.get_state(self.navigation.domain),
            recent_activity=[
                ActivityEntry(
                    title=e["title"],
                    engine=e["engine"],
                    timestamp=e["time"],
                )
                for e in self.activity_log[-10:]
            ],
            elapsed_seconds=elapsed_seconds,
        )

    def request_shutdown(self) -> None:
        """Signal graceful shutdown. Workers will finish current tasks."""
        self._shutdown_event.set()
        logger.info("Shutdown requested. Workers will finish current tasks...")

    # ========================================================================
    # CORE OPERATIONS
    # ========================================================================

    async def setup(self) -> None:
        """Initialize state and queues from existing data."""
        await self.state.initialize()
        
        # Fase 2: Lock de Misión
        pid = os.getpid()
        if not await self.state.acquire_mission_lock(self.navigation.domain, pid):
            logger.error(f"Ya existe una misión activa para el dominio: {self.navigation.domain}")
            raise RuntimeError(f"Mission lock for {self.navigation.domain} already held")
            
        await self.state.start_batch_processor()

        # Load existing statistics from database (más eficiente que cargar todo el set)
        stats = await self.state.get_stats(force_refresh=True)
        self.pages_completed = stats.get(MigrationStatus.COMPLETED.value, 0)
        self.pages_failed = stats.get(MigrationStatus.FAILED.value, 0)
        self._pages_total_count = stats.get("total_webpages", 0)
        
        self.assets_completed = stats.get("asset_completed", 0) # Necesitaría ajuste en db_manager si queremos exactitud
        self._assets_total_count = stats.get("total_assets", 0)

        # Queue pending URLs (con paginación para evitar OOM)
        limit = 1000
        offset = 0
        while True:
            pending = await self.state.get_pending_urls(
                max_retries=self.config.max_retries, limit=limit, offset=offset
            )
            if not pending:
                break
            
            for url in pending:
                self.seen_urls[url] = True
                await self.url_queue.put(url)
            
            offset += limit
            if offset > 5000: # No cargar todo a la vez si es enorme
                break

        if self.url_queue.empty() and self._pages_total_count == 0:
            await self.state.add_url(self.navigation.base_url, MigrationStatus.PENDING)
            self.seen_urls[self.navigation.base_url] = True
            await self.url_queue.put(self.navigation.base_url)
            self._pages_total_count += 1

        # Queue pending assets (limitado)
        pending_assets = await self.state.get_pending_urls(
            m_type="asset", max_retries=self.config.max_retries, limit=500
        )
        for asset in pending_assets:
            self.seen_assets[asset] = True
            await self.asset_queue.put(asset)

    async def run(self) -> None:
        """Run scraping engine - creates workers and processes queue."""
        try:
            await self.setup()
        except RuntimeError:
            return # Detener si no se obtuvo el lock
            
        self.start_time = asyncio.get_event_loop().time()

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

        # Build browser args
        dns_args = []
        if self.config.dns_overrides:
            rules = ", ".join(
                f"MAP {domain} {ip}" for domain, ip in self.config.dns_overrides.items()
            )
            dns_args.append(f"--host-resolver-rules={rules}")

        additional_args = {"args": dns_args + ["--disable-gpu", "--no-sandbox"]}

        # Initial UI update
        self._notify_ui()

        async with AsyncStealthySession(
            headless=True,
            max_pages=self.config.default_workers,
            solve_cloudflare=True,
            additional_args=additional_args,
        ) as session:
            # Create workers
            self._page_workers = [
                asyncio.create_task(self._page_worker(session))
                for _ in range(self.config.default_workers)
            ]

            self._asset_workers = []
            if self.extract_assets:
                self._asset_workers = [
                    asyncio.create_task(self._asset_worker())
                    for _ in range(self.config.asset_workers)
                ]

            all_workers = self._page_workers + self._asset_workers

            try:
                consecutive_empty_checks = 0
                while not self._shutdown_event.is_set():
                    self._notify_ui()

                    queue_size = self.url_queue.qsize() + self.asset_queue.qsize()
                    
                    # Criterio de parada: colas vacías y tareas procesadas
                    if queue_size == 0:
                        consecutive_empty_checks += 1
                        if consecutive_empty_checks >= 5: # Más conservador
                            logger.info("✅ Work complete - queues drained")
                            break
                    else:
                        consecutive_empty_checks = 0

                    await asyncio.sleep(0.5)

                if not self._shutdown_event.is_set():
                    logger.info("Work completed. Draining queues...")

                await self.url_queue.join()
                if self.extract_assets:
                    await self.asset_queue.join()

            except* Exception as exc_group:
                for exc in exc_group.exceptions:
                    logger.error(f"Error in worker: {exc}")
                    self.circuit_breaker.record_failure(self.navigation.domain)
                raise

            finally:
                await self._graceful_shutdown(all_workers)
                # Liberar lock de misión
                await self.state.release_mission_lock(self.navigation.domain, os.getpid())

        await self.reporter.generate_summary()
        await self.http_cache.close()

    # ========================================================================
    # WORKERS
    # ========================================================================

    async def _page_worker(self, session: AsyncStealthySession) -> None:
        """Worker that processes pages from the queue."""
        while not self._shutdown_event.is_set():
            try:
                item: QueueItem = await asyncio.wait_for(
                    self.url_queue.get(), timeout=DEFAULT_QUEUE_TIMEOUT_SECONDS
                )
            except asyncio.TimeoutError:
                continue

            if item is _STOP_SENTINEL:
                self.url_queue.task_done()
                break

            url: str = item

            if not self.circuit_breaker.should_allow(self.navigation.domain):
                await self.url_queue.put(url)
                self.url_queue.task_done()
                await asyncio.sleep(1)
                continue

            try:
                async with self.semaphore:
                    # Adaptive Rate Limiting con Jitter (Fase 1)
                    delay = self.config.request_delay + (asyncio.get_event_loop().time() % 0.5)
                    await asyncio.sleep(delay)
                    
                    await self._process_page(session, url)
            except asyncio.CancelledError:
                await self.state.update_status(
                    url, MigrationStatus.PENDING, immediate=True
                )
                raise
            except Exception as e:
                logger.error("Error processing %s: %s", url, e)
            finally:
                self.url_queue.task_done()

    async def _asset_worker(self) -> None:
        """Worker that downloads assets from the queue."""
        while not self._shutdown_event.is_set():
            try:
                item: QueueItem = await asyncio.wait_for(
                    self.asset_queue.get(), timeout=DEFAULT_QUEUE_TIMEOUT_SECONDS
                )
            except asyncio.TimeoutError:
                continue

            if item is _STOP_SENTINEL:
                self.asset_queue.task_done()
                break

            url: str = item

            try:
                await self._download_asset(url)
            except asyncio.CancelledError:
                await self.state.update_status(url, MigrationStatus.PENDING)
                raise
            except Exception as e:
                logger.error("Error downloading %s: %s", url, e)
            finally:
                self.asset_queue.task_done()

    # ========================================================================
    # PROCESSING
    # ========================================================================

    async def _process_page(self, session: AsyncStealthySession, url: str) -> None:
        """Process a single page: fetch, extract, save, queue links."""
        # 1. Cumplimiento Legal: robots.txt (Fase 1)
        if not await self.robots_checker.can_fetch(url):
            logger.warning(f"URL bloqueada por robots.txt: {url}")
            await self.state.update_status(url, MigrationStatus.SKIPPED_ROBOTS if hasattr(MigrationStatus, 'SKIPPED_ROBOTS') else MigrationStatus.FAILED, "Blocked by robots.txt")
            return

        base_scheme = urlparse(self.navigation.base_url).scheme
        if base_scheme == "https" and url.startswith("http://"):
            url = url.replace("http://", "https://", 1)

        try:
            page = await self._fetch_page(session, url)
            if not page:
                raise Exception("Empty content")

            # 2. Detección de CAPTCHA (Fase 2)
            raw_html = self._extract_html(page)
            is_captcha, captcha_type = self.captcha_detector.detect(raw_html)
            if is_captcha:
                logger.error(f"CAPTCHA detectado ({captcha_type}) en {url}")
                await self.state.update_status(url, MigrationStatus.FAILED, f"Blocked by CAPTCHA: {captcha_type}")
                return

            self.circuit_breaker.record_success(self.navigation.domain)

            # Clean and Extract
            clean_html = pre_clean_html(raw_html)

            async with asyncio.TaskGroup() as tg:
                metadata_task = tg.create_task(
                    self.metadata_extractor.extract(raw_html, url)
                )
                text_task = tg.create_task(self.text_extractor.extract(clean_html, url))

            metadata = metadata_task.result()
            text_data = text_task.result()

            # Save markdown
            md_path = await self._save_markdown(url, metadata, text_data["markdown"])
            await asyncio.sleep(0.05)

            # Enqueue new links
            new_pages, new_assets = self.navigation.extract_links(page, url)
            await self._queue_discovered_links(new_pages, new_assets)

            # Update status
            await self.state.update_status(
                url, MigrationStatus.COMPLETED, immediate=False
            )
            self.pages_completed += 1
            self._notify_ui()

        except Exception as e:
            await self._handle_page_error(url, e)

    async def _download_asset(self, asset_url: str) -> None:
        """Download and save an asset."""
        async with self.semaphore:
            try:
                session = await self.http_cache.get_session()
                async with session.get(
                    asset_url,
                    headers={
                        "Referer": self.navigation.base_url,
                        "Origin": self.navigation.base_url,
                    },
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status == 200:
                        content = await response.read()
                        await self.asset_extractor.extract(content, asset_url)
                        await self.state.update_status(
                            asset_url, MigrationStatus.COMPLETED
                        )
                        self.assets_completed += 1
                        self._notify_ui()
                    else:
                        raise Exception(f"HTTP {response.status}")
            except Exception as e:
                self.error_count += 1
                self.assets_failed += 1
                await self.state.update_status(
                    asset_url, MigrationStatus.FAILED, str(e)
                )

    # ========================================================================
    # HELPERS
    # ========================================================================

    async def _fetch_page(self, session: AsyncStealthySession, url: str) -> Any:
        """Fetch a page using stealth or browser mode."""
        encoded_url = smart_url_normalize(url)

        if self.use_browser_mode:
            return await session.fetch(encoded_url, timeout=DEFAULT_BROWSER_TIMEOUT_MS)

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
            return None

        if resp.status in [403, 401, 429]:
            self.use_browser_mode = True
            self._notify_mode_change()
            return await session.fetch(encoded_url, timeout=DEFAULT_BROWSER_TIMEOUT_MS)

        if resp.status == 200:
            return resp

        raise Exception(f"HTTP {resp.status}")

    def _extract_html(self, page: Any) -> str:
        """Extract HTML string from page object."""
        raw_html = getattr(page, "raw_content", "") or getattr(page, "body", "")
        if not isinstance(raw_html, str):
            raw_html = raw_html.decode("utf-8", errors="replace")
        return raw_html

    async def _save_markdown(
        self, url: str, metadata: dict[str, Any], markdown: str
    ) -> Path:
        """Save markdown with frontmatter and compression."""
        rel_path = url.removeprefix(self.navigation.base_url)
        raw_slug = Path(rel_path).stem or "index"
        path_slug = slugify(raw_slug)

        enhanced_markdown = enhance_markdown_for_rag(
            markdown=markdown,
            metadata=metadata,
            base_url=url,
            toc_max_level=3,
            include_toc=True,
        )

        frontmatter_metadata = filter_metadata_for_frontmatter(metadata)
        frontmatter = yaml.dump(
            frontmatter_metadata, allow_unicode=True, sort_keys=False
        )
        content = f"---\n{frontmatter}---\n\n{enhanced_markdown}"

        content_dir = self.asset_extractor.data_dir / "content"
        content_dir.mkdir(parents=True, exist_ok=True)

        md_path = await write_compressed_markdown(
            content_dir / path_slug,
            content,
            compression="zstd",
            compression_level=3,
        )
        return md_path

    async def _queue_discovered_links(
        self, new_pages: list[str], new_assets: list[str]
    ) -> None:
        """Filter and queue newly discovered links."""
        
        # Filtrado optimizado usando cache de memoria y DB fallback
        pages_to_queue = []
        for p in new_pages:
            if p not in self.seen_urls:
                # Doble verificación con DB si el cache expiró
                if not await self.state.exists(p):
                    pages_to_queue.append(p)
                    self.seen_urls[p] = True
                    self._pages_total_count += 1

        assets_to_queue = []
        if self.extract_assets:
            for a in new_assets:
                if a not in self.seen_assets:
                    if not await self.state.exists(a):
                        assets_to_queue.append(a)
                        self.seen_assets[a] = True
                        self._assets_total_count += 1

        if not pages_to_queue and not assets_to_queue:
            return

        async with asyncio.TaskGroup() as tg:
            # Add to database
            assets_to_add = [
                (a, MigrationStatus.PENDING, "asset") for a in assets_to_queue
            ]
            pages_to_add = [
                (p, MigrationStatus.PENDING, "webpage") for p in pages_to_queue
            ]
            tg.create_task(self.state.add_urls_batch(assets_to_add + pages_to_add))

            # Enqueue for processing
            for p in pages_to_queue:
                tg.create_task(self.url_queue.put(p))
            for a in assets_to_queue:
                tg.create_task(self.asset_queue.put(a))

    async def _handle_page_error(self, url: str, error: Exception) -> None:
        """Handle errors during page processing."""
        self.circuit_breaker.record_failure(self.navigation.domain)
        self.error_count += 1

        current_retries = await self.state.increment_retry(url)
        if current_retries < self.config.max_retries:
            await asyncio.sleep(float(2**current_retries))
            await self.url_queue.put(url)
        else:
            await self.state.update_status(url, MigrationStatus.FAILED, str(error))
            self.pages_failed += 1

    async def _graceful_shutdown(self, workers: list[asyncio.Task[None]]) -> None:
        """Gracefully shutdown workers."""
        self._shutdown_event.set()

        for _ in range(len(self._page_workers)):
            await self.url_queue.put(_STOP_SENTINEL)
        for _ in range(len(self._asset_workers)):
            await self.asset_queue.put(_STOP_SENTINEL)

        if workers:
            await asyncio.wait(workers, timeout=MIN_SHUTDOWN_TIMEOUT_SECONDS)
            for w in workers:
                if not w.done():
                    w.cancel()

        await asyncio.sleep(0.5)
        logger.info("✅ Graceful shutdown completed")

    def _notify_ui(self) -> None:
        """Send update to UI callback."""
        if self.ui_callback:
            self.ui_callback.on_progress(self.get_stats())
            self.ui_callback.on_circuit_change(
                self.circuit_breaker.get_state(self.navigation.domain)
            )

    def _notify_mode_change(self) -> None:
        """Notify UI of mode change."""
        if self.ui_callback:
            self.ui_callback.on_mode_change(self.use_browser_mode)

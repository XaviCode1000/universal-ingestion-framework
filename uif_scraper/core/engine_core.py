"""Core engine logic shared between UI implementations.

This module extracts the common scraping logic from engine.py and engine_v2.py,
eliminating ~80% code duplication. UI implementations only need to:
1. Create an EngineCore instance
2. Subscribe to updates via callbacks
3. Call run() and handle shutdown

Reference: AGENTS.md - SRP (Single Responsibility Principle)
"""

import asyncio
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

import aiofiles
import yaml
from loguru import logger
from scrapling.fetchers import AsyncFetcher, AsyncStealthySession

from uif_scraper.config import ScraperConfig
from uif_scraper.core.constants import (
    DEFAULT_BROWSER_TIMEOUT_MS,
    DEFAULT_QUEUE_TIMEOUT_SECONDS,
    DEFAULT_SHUTDOWN_TIMEOUT_SECONDS,
    HTTP_MAX_CONNECTIONS_PER_HOST,
    MAX_CIRCUIT_BREAKER_BACKOFF_SECONDS,
    MIN_SHUTDOWN_TIMEOUT_SECONDS,
)

# Sentinel object to signal workers to stop
# Using a unique object ensures no collision with actual data
_STOP_SENTINEL = object()
from uif_scraper.core.types import ActivityEntry, DashboardState, EngineStats
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

    This class contains all the scraping logic extracted from engine.py/engine_v2.py.
    UI implementations should:
    1. Create EngineCore with dependencies
    2. Set ui_callback for updates
    3. Call run() to start scraping

    Example:
        core = EngineCore(config, state, extractors, ...)
        core.ui_callback = MyRichUI()
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
        )

        # Queues
        self.url_queue: asyncio.Queue[str] = asyncio.Queue()
        self.asset_queue: asyncio.Queue[str] = asyncio.Queue()

        # State tracking
        self.seen_urls: set[str] = set()
        self.seen_assets: set[str] = set()
        self.pages_completed = 0
        self.assets_completed = 0
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
            pages_total=len(self.seen_urls),
            assets_completed=self.assets_completed,
            assets_total=len(self.seen_assets),
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
        await self.state.start_batch_processor()

        # Load existing state from database
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

        # Queue pending URLs
        pending = await self.state.get_pending_urls(max_retries=self.config.max_retries)
        if not pending and not self.seen_urls:
            await self.state.add_url(self.navigation.base_url, MigrationStatus.PENDING)
            self.seen_urls.add(self.navigation.base_url)
            pending = [self.navigation.base_url]

        for url in pending:
            await self.url_queue.put(url)

        # Queue pending assets
        pending_assets = await self.state.get_pending_urls(
            m_type="asset", max_retries=self.config.max_retries
        )
        for asset in pending_assets:
            await self.asset_queue.put(asset)

    async def run(self) -> None:
        """Run scraping engine - creates workers and processes queue.

        This method:
        1. Sets up AsyncStealthySession
        2. Creates page and asset workers
        3. Monitors progress until complete or shutdown
        4. Handles graceful shutdown
        """
        await self.setup()
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
                # Main loop - monitor progress
                while not self._shutdown_event.is_set():
                    self._notify_ui()

                    # Check completion
                    if (
                        self.url_queue.empty()
                        and self.asset_queue.empty()
                        and all(w.done() for w in all_workers)
                    ):
                        break

                    await asyncio.sleep(0.25)

                # Drain queues if not shutting down
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

        await self.reporter.generate_summary()
        await self.http_cache.close()

    # ========================================================================
    # WORKERS
    # ========================================================================

    async def _page_worker(self, session: AsyncStealthySession) -> None:
        """Worker that processes pages from the queue.

        Uses sentinel pattern for graceful shutdown - when _STOP_SENTINEL is
        received, the worker exits cleanly.
        """
        while not self._shutdown_event.is_set():
            try:
                url = await asyncio.wait_for(
                    self.url_queue.get(), timeout=DEFAULT_QUEUE_TIMEOUT_SECONDS
                )
            except asyncio.TimeoutError:
                continue

            # Check for sentinel - signal to stop
            if url is _STOP_SENTINEL:
                logger.debug("Page worker received stop sentinel, exiting")
                self.url_queue.task_done()
                break

            # Early exit for circuit breaker
            if not self.circuit_breaker.should_allow(self.navigation.domain):
                logger.warning(
                    f"Circuit breaker open for {self.navigation.domain}, requeuing {url}"
                )
                await self.url_queue.put(url)
                failures = self.circuit_breaker.failures.get(self.navigation.domain, 0)
                await asyncio.sleep(
                    min(2**failures, MAX_CIRCUIT_BREAKER_BACKOFF_SECONDS)
                )
                self.url_queue.task_done()
                continue

            try:
                async with self.semaphore:
                    # Double-check after acquiring semaphore
                    if not self.circuit_breaker.should_allow(self.navigation.domain):
                        await self.url_queue.put(url)
                        self.url_queue.task_done()
                        continue
                    await self._process_page(session, url)
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

    async def _asset_worker(self) -> None:
        """Worker that downloads assets from the queue.

        Uses sentinel pattern for graceful shutdown - when _STOP_SENTINEL is
        received, the worker exits cleanly.
        """
        while not self._shutdown_event.is_set():
            try:
                url = await asyncio.wait_for(
                    self.asset_queue.get(), timeout=DEFAULT_QUEUE_TIMEOUT_SECONDS
                )
            except asyncio.TimeoutError:
                continue

            # Check for sentinel - signal to stop
            if url is _STOP_SENTINEL:
                logger.debug("Asset worker received stop sentinel, exiting")
                self.asset_queue.task_done()
                break

            try:
                await self._download_asset(url)
            except asyncio.CancelledError:
                logger.warning(
                    "Asset worker cancelled downloading %s, marking as pending", url
                )
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
        if not self.circuit_breaker.should_allow(self.navigation.domain):
            logger.warning(f"Circuit broken. Skipping {url}")
            await self.url_queue.put(url)
            await asyncio.sleep(1)
            return

        try:
            page = await self._fetch_page(session, url)

            if not page:
                raise Exception("Empty content")

            self.circuit_breaker.record_success(self.navigation.domain)

            # Extract content
            raw_html = self._extract_html(page)
            clean_html = pre_clean_html(raw_html)

            # Parallel extraction
            async with asyncio.TaskGroup() as tg:
                metadata_task = tg.create_task(
                    self.metadata_extractor.extract(raw_html, url)
                )
                text_task = tg.create_task(self.text_extractor.extract(clean_html, url))

            metadata = metadata_task.result()
            text_data = text_task.result()

            # Save markdown
            md_path = await self._save_markdown(url, metadata, text_data["markdown"])

            # Extract and queue new links
            new_pages, new_assets = self.navigation.extract_links(page, url)
            await self._queue_discovered_links(new_pages, new_assets)

            # Update status
            await self.state.update_status(
                url, MigrationStatus.COMPLETED, immediate=False
            )
            self.pages_completed += 1

            # Log and notify
            await self._log_event(
                WebPage(
                    url=url,
                    title=metadata["title"],
                    content_md_path=str(md_path),
                    assets=[a for a in new_assets if a not in self.seen_assets],
                ),
                engine=text_data["engine"],
            )

            self._notify_ui()

        except Exception as e:
            await self._handle_page_error(url, e)

    async def _download_asset(self, asset_url: str) -> None:
        """Download and save an asset."""
        async with self.semaphore:
            try:
                session = await self.http_cache.get_session()
                async with session.get(asset_url) as response:
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
                await self.state.update_status(
                    asset_url, MigrationStatus.FAILED, str(e)
                )

    # ========================================================================
    # HELPERS
    # ========================================================================

    async def _fetch_page(self, session: AsyncStealthySession, url: str) -> Any:
        """Fetch a page using stealth or browser mode.

        Returns a page object from scrapling (Response or similar).
        Uses Any because scrapling returns dynamic types.
        """
        encoded_url = smart_url_normalize(url)

        if self.use_browser_mode:
            return await session.fetch(encoded_url, timeout=DEFAULT_BROWSER_TIMEOUT_MS)

        # Try stealth mode first
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
            return None

        if resp.status in [403, 401, 429]:
            # Switch to browser mode
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
        """Save markdown with frontmatter and compression.

        Args:
            url: The page URL (used to generate filename)
            metadata: Page metadata for YAML frontmatter
            markdown: The markdown content

        Returns:
            Path to the saved file
        """
        # Build path from URL
        rel_path = url.removeprefix(self.navigation.base_url)
        raw_slug = Path(rel_path).stem or "index"
        path_slug = slugify(raw_slug)

        # Build content with frontmatter
        frontmatter = yaml.dump(metadata, allow_unicode=True, sort_keys=False)
        content = f"---\n{frontmatter}---\n\n{markdown}"

        # Ensure directory exists before writing
        content_dir = self.asset_extractor.data_dir / "content"
        content_dir.mkdir(parents=True, exist_ok=True)

        # Save with compression
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
        new_assets_filtered = [
            a for a in new_assets if a not in self.seen_assets and self.extract_assets
        ]
        new_pages_filtered = [p for p in new_pages if p not in self.seen_urls]

        async with asyncio.TaskGroup() as tg:
            # Update seen sets
            tg.create_task(
                self._update_seen_sets(new_pages_filtered, new_assets_filtered)
            )

            # Add to database
            assets_to_add = [
                (a, MigrationStatus.PENDING, "asset") for a in new_assets_filtered
            ]
            pages_to_add = [
                (p, MigrationStatus.PENDING, "webpage") for p in new_pages_filtered
            ]
            tg.create_task(self.state.add_urls_batch(assets_to_add + pages_to_add))

            # Enqueue for processing
            tg.create_task(
                self._parallel_enqueue(new_pages_filtered, new_assets_filtered)
            )

    async def _update_seen_sets(self, pages: list[str], assets: list[str]) -> None:
        """Update seen sets (thread-safe)."""
        for p in pages:
            self.seen_urls.add(p)
        for a in assets:
            self.seen_assets.add(a)

    async def _parallel_enqueue(self, pages: list[str], assets: list[str]) -> None:
        """Enqueue URLs in parallel."""
        await asyncio.gather(
            *[self.url_queue.put(p) for p in pages],
            *[self.asset_queue.put(a) for a in assets],
            return_exceptions=True,
        )

    async def _handle_page_error(self, url: str, error: Exception) -> None:
        """Handle errors during page processing."""
        self.circuit_breaker.record_failure(self.navigation.domain)
        self.error_count += 1

        current_retries = await self.state.increment_retry(url)
        logger.warning(
            f"Retry {current_retries}/{self.config.max_retries} for {url}: {error}"
        )

        if current_retries < self.config.max_retries:
            backoff = 2**current_retries
            await asyncio.sleep(float(backoff))
            await self.url_queue.put(url)
        else:
            await self.state.update_status(url, MigrationStatus.FAILED, str(error))

    async def _log_event(self, data: WebPage, engine: str = "unknown") -> None:
        """Log event to file and activity log."""
        report_path = self.asset_extractor.data_dir / "migration_audit.jsonl"

        # Update internal log
        self.activity_log.append(
            {
                "title": data.title,
                "engine": engine,
                "time": asyncio.get_event_loop().time(),
            }
        )

        # Notify UI
        if self.ui_callback:
            self.ui_callback.on_activity(
                ActivityEntry(title=data.title, engine=engine, timestamp=0.0)
            )

        # Write to file
        async with self.report_lock:
            async with aiofiles.open(report_path, "a", encoding="utf-8") as f:
                await f.write(json.dumps(data.model_dump(mode="json")) + "\n")

    async def _graceful_shutdown(self, workers: list[asyncio.Task[None]]) -> None:
        """Gracefully shutdown workers with adaptive timeout."""
        self._shutdown_event.set()

        pending_urls = self.url_queue.qsize()
        pending_assets = self.asset_queue.qsize()
        total_pending = pending_urls + pending_assets

        if total_pending > 0:
            timeout = max(MIN_SHUTDOWN_TIMEOUT_SECONDS, total_pending * 2.0)
            logger.info(
                f"Waiting for {total_pending} pending tasks with {timeout}s timeout"
            )
        else:
            timeout = MIN_SHUTDOWN_TIMEOUT_SECONDS

        if workers:
            done, pending = await asyncio.wait(
                workers, timeout=timeout, return_when=asyncio.ALL_COMPLETED
            )

            if pending:
                for w in pending:
                    logger.warning(f"Worker {w.get_name()} did not finish, cancelling")
                    w.cancel()

                await asyncio.wait(pending, timeout=DEFAULT_SHUTDOWN_TIMEOUT_SECONDS)

    # ========================================================================
    # UI NOTIFICATIONS
    # ========================================================================

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

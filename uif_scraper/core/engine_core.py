"""Core engine logic for UIF Migration Engine (v4.0).

Refactored for SRP: Orchestrator, WorkerPool, and StatsTracker.
"""

from __future__ import annotations

import asyncio
import enum
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import aiohttp
import yaml
from cachetools import TTLCache
from loguru import logger
from scrapling.fetchers import AsyncFetcher, AsyncStealthySession

from uif_scraper.config import ScraperConfig
from uif_scraper.core.constants import (
    DB_PAGINATION_LIMIT,
    DEFAULT_BROWSER_TIMEOUT_MS,
    DEFAULT_JITTER_MAX,
    DEFAULT_QUEUE_TIMEOUT_SECONDS,
    HTTP_MAX_CONNECTIONS_PER_HOST,
    MIN_SHUTDOWN_TIMEOUT_SECONDS,
    SEEN_ASSETS_CACHE_MAXSIZE,
    SEEN_CACHE_TTL_SECONDS,
    SEEN_URLS_CACHE_MAXSIZE,
)
from uif_scraper.core.stats_tracker import StatsTracker
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
# FRONTMATTER FILTERING
# ============================================================================

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
    filtered = {k: v for k, v in metadata.items() if k in FRONTMATTER_FIELDS}
    return {k: v for k, v in filtered.items() if v is not None and v != []}


class _Sentinel(enum.Enum):
    STOP = object()


_STOP_SENTINEL = _Sentinel.STOP
QueueItem = str | _Sentinel


class UICallback(ABC):
    @abstractmethod
    def on_progress(self, stats: EngineStats) -> None: ...
    @abstractmethod
    def on_activity(self, entry: ActivityEntry) -> None: ...
    @abstractmethod
    def on_mode_change(self, browser_mode: bool) -> None: ...
    @abstractmethod
    def on_circuit_change(self, state: str) -> None: ...


class EngineCore:
    """Orchestrator for the scraping process."""

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
        self.extract_assets = extract_assets
        self.state = state
        self.text_extractor = text_extractor
        self.metadata_extractor = metadata_extractor
        self.asset_extractor = asset_extractor
        self.navigation = navigation_service
        self.reporter = reporter_service

        # Infrastructure
        self.stats = StatsTracker()
        self.circuit_breaker = CircuitBreaker()
        self.http_cache = HTTPSessionCache(
            max_pool_size=config.asset_workers * 2,
            max_connections_per_host=HTTP_MAX_CONNECTIONS_PER_HOST,
            timeout_total=config.timeout_seconds,
            verify_ssl=True,
        )
        self.robots_checker = RobotsChecker(self.http_cache)
        self.captcha_detector = CaptchaDetector()

        # Queues
        self.url_queue: asyncio.Queue[QueueItem] = asyncio.Queue()
        self.asset_queue: asyncio.Queue[QueueItem] = asyncio.Queue()

        # Memory Tracking
        self.seen_urls: TTLCache[str, bool] = TTLCache(
            maxsize=SEEN_URLS_CACHE_MAXSIZE, ttl=SEEN_CACHE_TTL_SECONDS
        )
        self.seen_assets: TTLCache[str, bool] = TTLCache(
            maxsize=SEEN_ASSETS_CACHE_MAXSIZE, ttl=SEEN_CACHE_TTL_SECONDS
        )

        # Concurrency
        self.semaphore = asyncio.Semaphore(config.default_workers)
        self.report_lock = asyncio.Lock()

        # State
        self.use_browser_mode = False
        self.activity_log: list[dict[str, Any]] = []
        self.start_time: float = 0
        self._shutdown_event = asyncio.Event()
        self._page_workers: list[asyncio.Task[None]] = []
        self._asset_workers: list[asyncio.Task[None]] = []
        self.ui_callback: UICallback | None = None

    def get_stats(self) -> EngineStats:
        self.stats.seen_urls_count = len(self.seen_urls)
        self.stats.seen_assets_count = len(self.seen_assets)
        return self.stats.get_stats(
            queue_pending=self.url_queue.qsize() + self.asset_queue.qsize()
        )

    def get_dashboard_state(self, elapsed_seconds: float = 0.0) -> DashboardState:
        return DashboardState(
            base_url=self.navigation.base_url,
            scope=self.navigation.scope.value,
            workers=self.config.default_workers,
            mode="browser" if self.use_browser_mode else "stealth",
            stats=self.get_stats(),
            circuit_state=self.circuit_breaker.get_state(self.navigation.domain),
            recent_activity=[
                ActivityEntry(title=e["title"], engine=e["engine"], timestamp=e["time"])
                for e in self.activity_log[-10:]
            ],
            elapsed_seconds=elapsed_seconds,
        )

    async def setup(self) -> None:
        await self.state.initialize()

        if not await self.state.acquire_mission_lock(
            self.navigation.domain, os.getpid()
        ):
            logger.error(f"Mission lock already held for {self.navigation.domain}")
            raise RuntimeError("Mission lock already held")

        await self.state.start_batch_processor()

        db_stats = await self.state.get_stats(force_refresh=True)
        self.stats.pages_completed = db_stats.get(MigrationStatus.COMPLETED.value, 0)
        self.stats.pages_failed = db_stats.get(MigrationStatus.FAILED.value, 0)
        self.stats.pages_total_count = db_stats.get("total_webpages", 0)
        self.stats.assets_total_count = db_stats.get("total_assets", 0)

        # Pagination for memory efficiency
        offset = 0
        while True:
            pending = await self.state.get_pending_urls(
                max_retries=self.config.max_retries,
                limit=DB_PAGINATION_LIMIT,
                offset=offset,
            )
            if not pending:
                break
            for url in pending:
                self.seen_urls[url] = True
                await self.url_queue.put(url)
            offset += DB_PAGINATION_LIMIT
            if offset > 5000:
                break

        if self.url_queue.empty() and self.stats.pages_total_count == 0:
            await self.state.add_url(self.navigation.base_url, MigrationStatus.PENDING)
            self.seen_urls[self.navigation.base_url] = True
            await self.url_queue.put(self.navigation.base_url)
            self.stats.pages_total_count += 1

    async def run(self) -> None:
        try:
            await self.setup()
        except RuntimeError:
            return

        self.start_time = asyncio.get_event_loop().time()
        self._notify_ui()

        async with AsyncStealthySession(
            headless=True,
            max_pages=self.config.default_workers,
            solve_cloudflare=True,
        ) as session:
            self._page_workers = [
                asyncio.create_task(self._page_worker(session))
                for _ in range(self.config.default_workers)
            ]
            if self.extract_assets:
                self._asset_workers = [
                    asyncio.create_task(self._asset_worker())
                    for _ in range(self.config.asset_workers)
                ]

            all_workers = self._page_workers + self._asset_workers

            try:
                checks = 0
                while not self._shutdown_event.is_set():
                    self._notify_ui()
                    if (self.url_queue.qsize() + self.asset_queue.qsize()) == 0:
                        checks += 1
                        if checks >= 5:
                            break
                    else:
                        checks = 0
                    await asyncio.sleep(0.5)

                await self.url_queue.join()
                if self.extract_assets:
                    await self.asset_queue.join()

            finally:
                await self._graceful_shutdown(all_workers)
                await self.state.release_mission_lock(
                    self.navigation.domain, os.getpid()
                )

        await self.reporter.generate_summary()
        await self.http_cache.close()

    async def _page_worker(self, session: AsyncStealthySession) -> None:
        while not self._shutdown_event.is_set():
            try:
                item = await asyncio.wait_for(
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
                    # Adaptive jitter
                    jitter = (os.urandom(1)[0] / 255) * DEFAULT_JITTER_MAX
                    await asyncio.sleep(self.config.request_delay + jitter)
                    await self._process_page(session, url)
            except asyncio.CancelledError:
                await self.state.update_status(
                    url, MigrationStatus.PENDING, immediate=True
                )
                raise
            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
            finally:
                self.url_queue.task_done()

    async def _asset_worker(self) -> None:
        while not self._shutdown_event.is_set():
            try:
                item = await asyncio.wait_for(
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
                logger.error(f"Error downloading {url}: {e}")
            finally:
                self.asset_queue.task_done()

    async def _process_page(self, session: AsyncStealthySession, url: str) -> None:
        if not await self.robots_checker.can_fetch(url):
            await self.state.update_status(
                url, MigrationStatus.SKIPPED_ROBOTS, "Blocked by robots.txt"
            )
            return

        try:
            page = await self._fetch_page(session, url)
            if not page:
                raise Exception("Empty content")

            raw_html = self._extract_html(page)
            is_captcha, c_type = self.captcha_detector.detect(raw_html)
            if is_captcha:
                await self.state.update_status(
                    url, MigrationStatus.FAILED, f"CAPTCHA: {c_type}"
                )
                return

            self.circuit_breaker.record_success(self.navigation.domain)
            clean_html = pre_clean_html(raw_html)

            async with asyncio.TaskGroup() as tg:
                m_task = tg.create_task(self.metadata_extractor.extract(raw_html, url))
                t_task = tg.create_task(self.text_extractor.extract(clean_html, url))

            metadata = m_task.result()
            text_data = t_task.result()

            await self._save_markdown(url, metadata, text_data["markdown"])

            new_pages, new_assets = self.navigation.extract_links(page, url)
            await self._queue_discovered_links(new_pages, new_assets)

            await self.state.update_status(url, MigrationStatus.COMPLETED)
            self.stats.record_page_success()
            self._notify_ui()

        except Exception as e:
            await self._handle_page_error(url, e)

    async def _download_asset(self, asset_url: str) -> None:
        async with self.semaphore:
            try:
                session = await self.http_cache.get_session()
                async with session.get(
                    asset_url,
                    headers={"Referer": self.navigation.base_url},
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as resp:
                    if resp.status == 200:
                        content = await resp.read()
                        await self.asset_extractor.extract(content, asset_url)
                        await self.state.update_status(
                            asset_url, MigrationStatus.COMPLETED
                        )
                        self.stats.record_asset_success()
                        self._notify_ui()
                    else:
                        raise Exception(f"HTTP {resp.status}")
            except Exception as e:
                self.stats.record_asset_failure()
                await self.state.update_status(
                    asset_url, MigrationStatus.FAILED, str(e)
                )

    async def _fetch_page(self, session: AsyncStealthySession, url: str) -> Any:
        encoded_url = smart_url_normalize(url)
        if self.use_browser_mode:
            return await session.fetch(encoded_url, timeout=DEFAULT_BROWSER_TIMEOUT_MS)

        resp = await AsyncFetcher.get(
            encoded_url,
            impersonate="chrome",
            timeout=self.config.timeout_seconds,
            headers={"Referer": self.navigation.base_url},
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
        raw = getattr(page, "raw_content", "") or getattr(page, "body", "")
        return raw if isinstance(raw, str) else raw.decode("utf-8", errors="replace")

    async def _save_markdown(
        self, url: str, metadata: dict[str, Any], markdown: str
    ) -> Path:
        rel_path = url.removeprefix(self.navigation.base_url)
        path_slug = slugify(Path(rel_path).stem or "index")

        enhanced = enhance_markdown_for_rag(
            markdown=markdown, metadata=metadata, base_url=url, include_toc=True
        )

        frontmatter = yaml.dump(
            filter_metadata_for_frontmatter(metadata), allow_unicode=True
        )
        content = f"---\n{frontmatter}---\n\n{enhanced}"

        content_dir = self.asset_extractor.data_dir / "content"
        content_dir.mkdir(parents=True, exist_ok=True)

        return await write_compressed_markdown(content_dir / path_slug, content)

    async def _queue_discovered_links(
        self, new_pages: list[str], new_assets: list[str]
    ) -> None:
        p_queue, a_queue = [], []
        for p in new_pages:
            if p not in self.seen_urls and not await self.state.exists(p):
                p_queue.append(p)
                self.seen_urls[p] = True
                self.stats.pages_total_count += 1

        if self.extract_assets:
            for a in new_assets:
                if a not in self.seen_assets and not await self.state.exists(a):
                    a_queue.append(a)
                    self.seen_assets[a] = True
                    self.stats.assets_total_count += 1

        if not p_queue and not a_queue:
            return

        async with asyncio.TaskGroup() as tg:
            tg.create_task(
                self.state.add_urls_batch(
                    [(p, MigrationStatus.PENDING, "webpage") for p in p_queue]
                    + [(a, MigrationStatus.PENDING, "asset") for a in a_queue]
                )
            )
            for p in p_queue:
                tg.create_task(self.url_queue.put(p))
            for a in a_queue:
                tg.create_task(self.asset_queue.put(a))

    async def _handle_page_error(self, url: str, error: Exception) -> None:
        self.circuit_breaker.record_failure(self.navigation.domain)
        retries = await self.state.increment_retry(url)
        if retries < self.config.max_retries:
            await asyncio.sleep(float(2**retries))
            await self.url_queue.put(url)
        else:
            await self.state.update_status(url, MigrationStatus.FAILED, str(error))
            self.stats.record_page_failure()

    async def _graceful_shutdown(self, workers: list[asyncio.Task[None]]) -> None:
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

    def _notify_ui(self) -> None:
        if self.ui_callback:
            self.ui_callback.on_progress(self.get_stats())
            self.ui_callback.on_circuit_change(
                self.circuit_breaker.get_state(self.navigation.domain)
            )

    def _notify_mode_change(self) -> None:
        if self.ui_callback:
            self.ui_callback.on_mode_change(self.use_browser_mode)

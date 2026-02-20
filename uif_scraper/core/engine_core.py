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
    """Interfaz para callbacks de UI del EngineCore.

    Todos los métodos son opcionales en las implementaciones concretas.
    Los eventos se emiten de forma no bloqueante.
    """

    @abstractmethod
    def on_progress(self, stats: EngineStats) -> None:
        """Notifica progreso del scraping (throttled)."""
        ...

    @abstractmethod
    def on_activity(self, entry: ActivityEntry) -> None:
        """Notifica actividad de página procesada."""
        ...

    @abstractmethod
    def on_mode_change(self, browser_mode: bool) -> None:
        """Notifica cambio de modo stealth ↔ browser."""
        ...

    @abstractmethod
    def on_circuit_change(self, state: str) -> None:
        """Notifica cambio de estado del circuit breaker."""
        ...

    @abstractmethod
    def on_error(self, url: str, error_type: str, message: str) -> None:
        """Notifica error de procesamiento (sin throttle)."""
        ...

    @abstractmethod
    def on_state_change(
        self, state: str, mode: str, previous_state: str | None, reason: str | None
    ) -> None:
        """Notifica cambio de estado del engine."""
        ...


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
        self._pause_event = asyncio.Event()  # Para pause/resume real
        self._pause_event.set()  # Inicia despausado
        self._engine_state: str = (
            "starting"  # starting, running, paused, stopping, stopped, error
        )
        self._page_workers: list[asyncio.Task[None]] = []
        self._asset_workers: list[asyncio.Task[None]] = []
        self.ui_callback: UICallback | None = None

        # Speed tracking
        self._last_speed_check: float = 0.0
        self._pages_since_last_check: int = 0
        self._current_speed: float = 0.0

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
        """Ejecuta el engine principal con soporte para pause/resume."""
        try:
            await self.setup()
        except RuntimeError:
            return

        self.start_time = asyncio.get_event_loop().time()
        self._last_speed_check = self.start_time
        self._notify_state_change("running", reason="mission_started")
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
                    # Verificar si está pausado
                    if not self._pause_event.is_set():
                        # Esperar a que se reanude
                        await self._pause_event.wait()

                    self._notify_ui()
                    self._update_speed()

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
                self._notify_state_change("stopping", reason="mission_completed")
                await self._graceful_shutdown(all_workers)
                await self.state.release_mission_lock(
                    self.navigation.domain, os.getpid()
                )

        self._notify_state_change("stopped", reason="mission_completed")
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
        """Procesa una página: fetch, extract, save, notify."""
        # Esperar si está pausado
        await self._pause_event.wait()

        if not await self.robots_checker.can_fetch(url):
            await self.state.update_status(
                url, MigrationStatus.SKIPPED_ROBOTS, "Blocked by robots.txt"
            )
            return

        start_time = asyncio.get_event_loop().time()

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

            # Emitir actividad
            elapsed_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            self._notify_activity(
                url=url,
                title=metadata.get("title", url),
                engine=text_data.get("engine", "unknown"),
                status="success",
                elapsed_ms=elapsed_ms,
                size_bytes=len(raw_html),
            )

            # Actualizar velocidad
            self._pages_since_last_check += 1
            self._update_speed()
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
        """Maneja errores de procesamiento de página."""
        self.circuit_breaker.record_failure(self.navigation.domain)
        retries = await self.state.increment_retry(url)

        # Emitir evento de error
        error_type = type(error).__name__
        error_msg = str(error)[:500]  # Truncar a 500 chars
        self._notify_error(
            url=url,
            error_type=error_type,
            message=error_msg,
            retry_count=retries,
            is_fatal=retries >= self.config.max_retries,
        )

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

    def _notify_activity(
        self,
        url: str,
        title: str,
        engine: str,
        status: str,
        elapsed_ms: float,
        size_bytes: int = 0,
    ) -> None:
        """Emite evento de actividad cuando se procesa una página."""
        now = asyncio.get_event_loop().time()

        if self.ui_callback:
            entry = ActivityEntry(title=title, engine=engine, timestamp=now)
            self.ui_callback.on_activity(entry)

        # También agregar al log interno
        self.activity_log.append(
            {
                "url": url,
                "title": title,
                "engine": engine,
                "status": status,
                "time": asyncio.get_event_loop().time(),
                "elapsed_ms": elapsed_ms,
                "size_bytes": size_bytes,
            }
        )

    def _notify_error(
        self,
        url: str,
        error_type: str,
        message: str,
        retry_count: int = 0,
        is_fatal: bool = False,
    ) -> None:
        """Emite evento de error (sin throttle)."""
        if self.ui_callback:
            self.ui_callback.on_error(url, error_type, message)

    def _notify_state_change(self, new_state: str, reason: str | None = None) -> None:
        """Emite evento de cambio de estado del engine."""
        previous = self._engine_state
        self._engine_state = new_state

        if self.ui_callback:
            self.ui_callback.on_state_change(
                state=new_state,
                mode="browser" if self.use_browser_mode else "stealth",
                previous_state=previous,
                reason=reason,
            )

    def _update_speed(self) -> None:
        """Actualiza métricas de velocidad cada segundo."""
        now = asyncio.get_event_loop().time()

        if now - self._last_speed_check >= 1.0:
            elapsed = now - self._last_speed_check
            if elapsed > 0:
                self._current_speed = self._pages_since_last_check / elapsed
            self._pages_since_last_check = 0
            self._last_speed_check = now

    def pause(self) -> None:
        """Pausa el engine (no bloqueante)."""
        self._pause_event.clear()
        self._notify_state_change("paused", reason="user_request")

    def resume(self) -> None:
        """Reanuda el engine después de pausa."""
        self._pause_event.set()
        self._notify_state_change("running", reason="user_request")

    def is_paused(self) -> bool:
        """Retorna True si el engine está pausado."""
        return not self._pause_event.is_set()

    def get_queue_status(self) -> list[dict[str, Any]]:
        """Retorna el estado de las URLs en la cola.

        Returns:
            Lista de diccionarios con: url, status, retries, error
        """
        # Obtener URLs del activity log reciente
        status_list = []

        # URLs completadas (del activity log)
        seen_urls = set()
        for entry in self.activity_log[-100:]:  # Últimas 100
            url = entry.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                status_list.append(
                    {
                        "url": url,
                        "status": entry.get("status", "completed"),
                        "retries": 0,
                        "error": None,
                        "engine": entry.get("engine", "unknown"),
                        "elapsed_ms": entry.get("elapsed_ms", 0),
                    }
                )

        return status_list

    def get_error_list(self) -> list[dict[str, Any]]:
        """Retorna la lista de errores recientes.

        Returns:
            Lista de diccionarios con: url, error_type, error_message, retry_count
        """
        # Por ahora retornamos errores del activity log con status error
        errors = []
        for entry in self.activity_log[-50:]:
            if entry.get("status") == "error":
                errors.append(
                    {
                        "url": entry.get("url", ""),
                        "error_type": "ProcessingError",
                        "error_message": entry.get("error", "Unknown error"),
                        "retry_count": 0,
                        "timestamp": entry.get("time", 0),
                    }
                )
        return errors

    def get_logs(self, level: str = "ALL", limit: int = 100) -> list[dict[str, Any]]:
        """Retorna los logs del engine.

        Args:
            level: Filtrar por nivel (DEBUG, INFO, WARNING, ERROR, ALL)
            limit: Número máximo de entradas a retornar

        Returns:
            Lista de diccionarios con: timestamp, level, message, source
        """
        logs = []
        level_upper = level.upper()

        # Usar activity_log como fuente de logs
        for entry in self.activity_log[-limit:]:
            # Determinar el nivel basado en el status
            status = entry.get("status", "info")
            if status == "error":
                log_level = "ERROR"
            elif status == "warning":
                log_level = "WARNING"
            else:
                log_level = "INFO"

            # Filtrar por nivel si no es ALL
            if level_upper != "ALL" and log_level != level_upper:
                continue

            # Construir mensaje
            url = entry.get("url", "")
            message = (
                entry.get("title", "")
                or entry.get("error", "")
                or entry.get("status", "")
            )

            if url:
                message = f"{message}: {url}"

            logs.append(
                {
                    "timestamp": entry.get("time", 0),
                    "level": log_level,
                    "message": message,
                    "source": entry.get("engine", "engine"),
                }
            )

        return logs

    def get_config(self) -> dict[str, Any]:
        """Retorna la configuración actual del engine.

        Returns:
            Diccionario con: workers, request_delay, timeout, mode
        """
        return {
            "workers": self.semaphore._value
            if hasattr(self.semaphore, "_value")
            else self.config.default_workers,
            "request_delay": int(
                self.config.request_delay * 1000
            ),  # Convertir de segundos a ms
            "timeout": self.config.timeout_seconds,
            "mode": "browser" if self.use_browser_mode else "stealth",
        }

    def update_config(
        self,
        workers: int | None = None,
        request_delay: int | None = None,
        timeout: int | None = None,
        mode: str | None = None,
        scope: str | None = None,
    ) -> dict[str, Any]:
        """Actualiza la configuración del engine en runtime.

        Args:
            workers: Nuevo número de workers
            request_delay: Nuevo delay entre requests (ms)
            timeout: Nuevo timeout (segundos)
            mode: Modo ('stealth' o 'browser')
            scope: Alcance (no implementado aún, pero acepatdo por compatibilidad)

        Returns:
            Diccionario con la configuración actualizada
        """
        if workers is not None and 1 <= workers <= 10:
            # Recrear el semáforo con el nuevo valor
            self.semaphore = asyncio.Semaphore(workers)
            logger.info(f"Workers updated to {workers}")

        if request_delay is not None and request_delay >= 0:
            self.config.request_delay = (
                request_delay / 1000.0
            )  # Convertir de ms a segundos
            logger.info(f"Request delay updated to {request_delay}ms")

        if timeout is not None and timeout >= 5:
            self.config.timeout_seconds = timeout
            logger.info(f"Timeout updated to {timeout}s")

        if mode is not None:
            self.use_browser_mode = mode == "browser"
            logger.info(f"Mode updated to {mode}")

        # scope no está implementado en la configuración actual
        _ = scope  # Ignorar por compatibilidad

        return self.get_config()

"""UIF Migration Engine with Textual TUI.

This is a thin wrapper around EngineCore that adds Textual UI integration.
The heavy lifting is done by EngineCore - this file only handles UI setup.

Lines reduced: ~520 → ~80 (85% reduction)
"""

import asyncio
from typing import TYPE_CHECKING

from loguru import logger
from scrapling.fetchers import AsyncStealthySession

from uif_scraper.config import ScraperConfig
from uif_scraper.core.engine_core import (
    EngineCore,
    _STOP_SENTINEL,
)
from uif_scraper.db_manager import StateManager
from uif_scraper.extractors.asset_extractor import AssetExtractor
from uif_scraper.extractors.metadata_extractor import MetadataExtractor
from uif_scraper.extractors.text_extractor import TextExtractor
from uif_scraper.navigation import NavigationService
from uif_scraper.reporter import ReporterService

if TYPE_CHECKING:
    from uif_scraper.tui.app import UIFDashboardApp


class TextualUICallback:
    """Adapter to forward EngineCore updates to Textual TUI.

    Implements the observer pattern - EngineCore calls these methods
    and we forward to the Textual app via message passing.
    """

    def __init__(self, app: "UIFDashboardApp", core: EngineCore) -> None:
        self._app = app
        self._core = core

    def update(self) -> None:
        """Send full state update to TUI."""
        # Progress
        stats = self._core.get_stats()
        self._app.update_progress(
            pages_completed=stats.pages_completed,
            pages_total=stats.pages_total,
            assets_completed=stats.assets_completed,
            assets_total=stats.assets_total,
            seen_urls=stats.seen_urls,
            seen_assets=stats.seen_assets,
        )

        # Status
        self._app.update_status(
            circuit_state=self._core.circuit_breaker.get_state(
                self._core.navigation.domain
            ),
            queue_pending=stats.queue_pending,
            error_count=stats.error_count,
            browser_mode=self._core.use_browser_mode,
        )

    def on_activity(self, title: str, engine: str) -> None:
        """Add activity entry."""
        self._app.add_activity(title, engine)


class UIFMigrationEngineV2:
    """Migration engine with Textual TUI dashboard.

    This class is now a thin orchestrator that:
    1. Creates EngineCore with all dependencies
    2. Sets up UI callback
    3. Runs the core and updates UI periodically

    All scraping logic is in EngineCore.
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
        tui_app: "UIFDashboardApp | None" = None,
    ) -> None:
        # Create core engine with all dependencies
        self._core = EngineCore(
            config=config,
            state=state,
            text_extractor=text_extractor,
            metadata_extractor=metadata_extractor,
            asset_extractor=asset_extractor,
            navigation_service=navigation_service,
            reporter_service=reporter_service,
            extract_assets=extract_assets,
        )

        # UI setup
        self._tui_app = tui_app
        self._ui_callback: TextualUICallback | None = None

        # Expose core properties for backward compatibility
        self.config = config
        self.navigation = navigation_service
        self.request_shutdown = self._core.request_shutdown

    async def run(self) -> None:
        """Run scraping with Textual TUI updates.

        This is designed to be called as a background task from within
        the Textual app's on_mount handler.
        """
        # Set up UI callback if app is available
        if self._tui_app:
            self._ui_callback = TextualUICallback(self._tui_app, self._core)

        # Run the core engine
        await self._run_with_ui_updates()

    async def _run_with_ui_updates(self) -> None:
        """Run core engine with periodic UI updates."""
        # Setup
        await self._core.setup()

        logger.info(
            "Starting scraping mission",
            extra={
                "url": self._core.navigation.base_url,
                "scope": self._core.navigation.scope.value,
                "workers": self._core.config.default_workers,
                "asset_workers": self._core.config.asset_workers,
                "timeout_seconds": self._core.config.timeout_seconds,
            },
        )

        # Build browser args
        dns_args = []
        if self._core.config.dns_overrides:
            rules = ", ".join(
                f"MAP {domain} {ip}"
                for domain, ip in self._core.config.dns_overrides.items()
            )
            dns_args.append(f"--host-resolver-rules={rules}")

        additional_args = {"args": dns_args + ["--disable-gpu", "--no-sandbox"]}

        # Initial UI update
        self._update_ui()

        # Run with browser session
        async with AsyncStealthySession(
            headless=True,
            max_pages=self._core.config.default_workers,
            solve_cloudflare=True,
            additional_args=additional_args,
        ) as session:
            # Create workers
            page_workers = [
                asyncio.create_task(self._core._page_worker(session))  # noqa: SLF001
                for _ in range(self._core.config.default_workers)
            ]

            asset_workers = []
            if self._core.extract_assets:
                asset_workers = [
                    asyncio.create_task(self._core._asset_worker())  # noqa: SLF001
                    for _ in range(self._core.config.asset_workers)
                ]

            all_workers = page_workers + asset_workers

            try:
                # Main loop
                while not self._core._shutdown_event.is_set():  # noqa: SLF001
                    self._update_ui()

                    # Check completion - queues empty means all work is done
                    url_queue_empty = self._core.url_queue.empty()
                    asset_queue_empty = self._core.asset_queue.empty()
                    # Workers are blocked on queue.get(), so we check queues only
                    if url_queue_empty and asset_queue_empty:
                        logger.info("All work completed. Sending stop sentinels...")
                        # Send sentinel to each worker to signal graceful exit
                        for _ in range(self._core.config.default_workers):
                            await self._core.url_queue.put(_STOP_SENTINEL)  # type: ignore[arg-type]
                        for _ in range(self._core.config.asset_workers):
                            await self._core.asset_queue.put(_STOP_SENTINEL)  # type: ignore[arg-type]
                        # Wait for workers to drain and exit
                        try:
                            await asyncio.wait_for(
                                self._core.url_queue.join(), timeout=5.0
                            )
                        except asyncio.TimeoutError:
                            logger.warning("URL queue join timed out after sentinel")

                        if self._core.extract_assets:
                            try:
                                await asyncio.wait_for(
                                    self._core.asset_queue.join(), timeout=5.0
                                )
                            except asyncio.TimeoutError:
                                logger.warning(
                                    "Asset queue join timed out after sentinel"
                                )

                        # Wait for workers to actually finish
                        await asyncio.gather(*all_workers, return_exceptions=True)
                        logger.info("All workers exited cleanly")
                        break

                    await asyncio.sleep(0.25)

                # Check if shutdown was requested (Ctrl+C or signal)
                if self._core._shutdown_event.is_set():  # noqa: SLF001
                    logger.info("Shutdown requested, cancelling workers...")
                    # Cancel all workers immediately
                    for w in all_workers:
                        if not w.done():
                            w.cancel()
                    # Wait for cancellation to complete
                    await asyncio.gather(*all_workers, return_exceptions=True)

            except* Exception as exc_group:
                for exc in exc_group.exceptions:
                    logger.error(f"Error in worker: {exc}")
                    self._core.circuit_breaker.record_failure(
                        self._core.navigation.domain
                    )
                raise

            finally:
                # Graceful shutdown with force cancel after timeout
                self._core._shutdown_event.set()  # noqa: SLF001
                await self._core._graceful_shutdown(all_workers)  # noqa: SLF001

        await self._core.reporter.generate_summary()
        await self._core.http_cache.close()

    def _update_ui(self) -> None:
        """Send update to Textual TUI."""
        if self._ui_callback:
            self._ui_callback.update()

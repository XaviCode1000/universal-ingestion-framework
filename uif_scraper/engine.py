"""UIF Migration Engine with Rich TUI.

This is a thin wrapper around EngineCore that adds Rich UI.
The heavy lifting is done by EngineCore - this file only handles UI setup.

Lines reduced: ~600 → ~80 (87% reduction)
"""

import asyncio

from loguru import logger
from scrapling.fetchers import AsyncStealthySession

from uif_scraper.config import ScraperConfig
from uif_scraper.core.engine_core import EngineCore
from uif_scraper.db_manager import StateManager
from uif_scraper.extractors.asset_extractor import AssetExtractor
from uif_scraper.extractors.metadata_extractor import MetadataExtractor
from uif_scraper.extractors.text_extractor import TextExtractor
from uif_scraper.navigation import NavigationService
from uif_scraper.reporter import ReporterService
from uif_scraper.ui.rich_adapter import RichDashboard


class UIFMigrationEngine:
    """Migration engine with Rich TUI dashboard.

    This class is now a thin orchestrator that:
    1. Creates EngineCore with all dependencies
    2. Sets up Rich dashboard
    3. Runs the core and updates dashboard periodically

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

        # Dashboard (created in run())
        self._dashboard: RichDashboard | None = None

        # Expose core properties for backward compatibility
        self.config = config
        self.navigation = navigation_service
        self.request_shutdown = self._core.request_shutdown

    async def run(self) -> None:
        """Run scraping with Rich TUI dashboard."""
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

        # Setup dashboard
        self._dashboard = RichDashboard(self._core)
        self._dashboard.setup()

        # Run with Rich Live display
        with self._dashboard.live():
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
                    # Main loop - update dashboard and check completion
                    while not self._core._shutdown_event.is_set():  # noqa: SLF001
                        self._dashboard.update()

                        if (
                            self._core.url_queue.empty()
                            and self._core.asset_queue.empty()
                            and all(w.done() for w in all_workers)
                        ):
                            break

                        await asyncio.sleep(0.25)

                    # Drain queues
                    if not self._core._shutdown_event.is_set():  # noqa: SLF001
                        logger.info("Work completed. Draining queues...")

                    await self._core.url_queue.join()
                    if self._core.extract_assets:
                        await self._core.asset_queue.join()

                except* Exception as exc_group:
                    for exc in exc_group.exceptions:
                        logger.error(f"Error in worker: {exc}")
                        self._core.circuit_breaker.record_failure(
                            self._core.navigation.domain
                        )
                    raise

                finally:
                    # Graceful shutdown
                    self._core._shutdown_event.set()  # noqa: SLF001
                    await self._core._graceful_shutdown(all_workers)  # noqa: SLF001

        await self._core.reporter.generate_summary()
        await self._core.http_cache.close()

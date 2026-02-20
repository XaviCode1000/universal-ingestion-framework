# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.0.0] - 2026-02-20

### Added
- **Resilience & Scale Architecture**: Complete overhaul of the core engine.
- **Memory Management**: Implemented `TTLCache` (via `cachetools`) for seen URLs/assets tracking, preventing OOM in large missions.
- **Mission Lock**: New locking mechanism per domain using SQLite to prevent multiple concurrent instances processing the same target.
- **Robots.txt Compliance**: Automatic detection and enforcement of `robots.txt` directives with per-domain caching.
- **Anti-Scraping Detection**: New `CaptchaDetector` service to identify Cloudflare IUAM, Turnstile, and other challenges.
- **Strict SSL**: Forced SSL/TLS verification using `certifi` for production-grade security.
- **Adaptive Rate Limiting**: Added request delay with jitter to minimize IP banning risks.

### Changed
- **Architectural Refactoring**: Split `EngineCore` into `Orchestrator` and `StatsTracker` for better SRP compliance.
- **Atomic Operations**: Database updates now use SQLite `RETURNING` clause for atomic retry increments.
- **Centralized Constants**: Extracted all magic numbers to `uif_scraper/core/constants.py`.
- **Memory-Efficient Setup**: Initial queue loading now uses DB pagination to avoid loading millions of records into RAM.

### Fixed
- Fixed race conditions in multi-instance environments via Mission Locks.
- Resolved potential "Seen URL" loss via double-check (Cache + DB fallback).

## [3.0.1] - 2026-02-18

### Added
- Graceful shutdown with `asyncio.Event` for clean process termination.
- SIGTERM/SIGINT signal handlers with cross-platform fallback (Unix/Windows).
- `__slots__` to `CircuitBreaker` for memory optimization.
- Comprehensive test suite with 75 tests passing.

### Changed
- Migrated type hints to Python 3.12+ syntax (`list[]`, `dict[]`, `X | None`).
- `WebPage` model is now immutable (`frozen=True`).
- Improved exception logging in `TextExtractor` with conditional traceback.
- Test URLs updated to use webscraper.io test sites.

### Fixed
- Fixed `task_done()` always called regardless of shutdown state.
- Fixed `shutdown_monitor` task cleanup on normal exit.
- Fixed URL loss on `CancelledError` during processing (re-queues URL as pending).

### Removed
- Removed unused `polars` dependency from pyproject.toml.

## [3.0.0] - 2026-01-19

### Added
- Modular architectural design following SOLID principles.
- Persistent configuration system (YAML + Env vars) following XDG Base Directory Spec.
- SQLite Connection Pool with WAL mode for high concurrency.
- Circuit Breaker pattern for domain-specific fault tolerance.
- Type-safe implementation with `mypy --strict` compliance.
- Automated test suite with 85% global coverage.
- New CLI tool `uif-scraper` with interactive setup wizard.
- Professional logging with rotation and compression using `loguru`.

### Changed
- Refactored `UIFMigrationEngine` to use Dependency Injection.
- Decoupled extraction logic into specialized modules (`TextExtractor`, `MetadataExtractor`, `AssetExtractor`).
- Improved URL normalization to industry standards (RFC 3986).
- Migrated dependency management to `uv`.

### Fixed
- Fixed SQLite race conditions by implementing connection pooling.
- Resolved "mojibake" issues using `ftfy` normalization.
- Prevented disk saturation by adding log rotation.

## [2.2.0] - Previous Version

- Monolithic implementation.
- Basic scraping functionality.

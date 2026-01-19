# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

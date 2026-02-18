# 🛸 Universal Ingestion Framework (UIF)

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Architecture: Multi-Layer](https://img.shields.io/badge/architecture-multi--layer-orange.svg)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)]()
[![Tests: 75 passing](https://img.shields.io/badge/tests-75%20passing-brightgreen.svg)]()

[🇪🇸 Leer en Español](README.es.md)

UIF is a high-fidelity knowledge ingestion engine designed to transform legacy web infrastructures and binary document assets into Markdown databases optimized for LLMs and RAG (Retrieval-Augmented Generation) systems.

---

## 🛑 ELITE CAPABILITIES

- **Hybrid Multimodal Ingestion**: High-fidelity conversion for `PDF`, `DOCX`, `XLSX`, and `PPTX` via **MarkItDown**, and superior semantic extraction for HTML via **Trafilatura**.
- **Industrial-Grade Cleaning**: Pre-pruning pipeline with **Selectolax**, sanitization with **nh3**, and Unicode normalization with **ftfy** to eliminate 100% of noise and *mojibake*.
- **Intelligent Navigation (Scope Control)**: `SMART`, `STRICT`, and `BROAD` strategies to surgically control crawl scope (preventing leaks outside of sub-sites or specific documentation).
- **Enriched RAG Context**: Automatic injection of **YAML Frontmatter** (URL, author, date, title) into every file for seamless indexing in vector databases.
- **Industrial Resilience**: State management using **SQLite in WAL mode**, allowing real concurrency and automatic recovery from failures.
- **Graceful Shutdown**: Clean process termination with `SIGTERM`/`SIGINT` signal handling, ensuring no data loss during interruptions.
- **Conversational UX**: Interactive Wizard for guided configuration of scope, processes, and content types.

---

## 🏗️ TECHNICAL ARCHITECTURE (v3.0.1 - Modular Enterprise)

The engine operates across four layers of refinement:

1. **Navigation Layer (Scrapling + Scope Logic)**: Asynchronous orchestration with block evasion and intelligent scope filtering based on seed URL depth.
2. **Purification Layer (Selectolax + Density Analysis)**: Massive noise elimination via static selectors and a **Link Density Algorithm** that detects and removes menus/sidebars even in non-semantic sites.
3. **Hybrid Conversion Layer**: Dynamic selection of the best engine with a **Waterfall Title Strategy** to guarantee accurate metadata, using **Trafilatura** and **MarkItDown**.
4. **Refinement Layer (ftfy + YAML)**: Final text normalization (mojibake fix) and structured metadata enrichment for maximum compatibility with RAG systems.

### Key Technical Features

- **Python 3.12+ Type Hints**: Modern syntax (`list[]`, `dict[]`, `X | None`) for better code clarity.
- **Immutable Data Models**: Pydantic models with `frozen=True` for thread-safe data handling.
- **Memory Optimized**: `__slots__` in high-frequency classes like `CircuitBreaker`.
- **Async-First**: Built with `asyncio.TaskGroup` patterns and semaphore-based concurrency control.

---

## 🧪 TESTING

UIF includes a comprehensive test suite with **75+ tests** covering unit, integration, and end-to-end scenarios:

```bash
# Run all tests
uv run pytest tests/ -v

# Run quick tests only (skip browser-based e2e)
uv run pytest tests/ -v -k "not browser"

# Run with coverage report
uv run pytest tests/ -v --cov=uif_scraper --cov-report=html

# Run only end-to-end tests (requires internet)
uv run pytest tests/test_e2e.py tests/test_e2e_browser.py -v
```

### Test Coverage

| Category | Tests | Description |
|----------|-------|-------------|
| Unit Tests | 51 | Navigation, extractors, DB, utils |
| E2E (HTTP) | 4 | Real HTTP requests to webscraper.io |
| E2E (Browser) | 3 | Full browser automation with Chromium |
| Integration | 17 | Engine orchestration, shutdown, reporting |

---

## 🚀 INSTALLATION AND USAGE

This project uses `uv` for ultra-fast, deterministic dependency management.

### Prerequisites
```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and lock file
uv sync
```

### Browser Setup (Optional - for E2E tests with browser)
```bash
# Install Chromium for Playwright (required for browser-based E2E tests)
uv run playwright install chromium
```

### Interactive Execution (Recommended)
Simply run the engine and follow the visual assistant:
```bash
uv run uif-scraper --setup
```

### Automatic Execution (CLI)
For automated workflows or shell scripts:
```bash
uv run uif-scraper https://example.com --workers 10 --scope smart
```

### CLI Options

| Option | Description |
|--------|-------------|
| `--setup` | Run interactive configuration wizard |
| `--config <path>` | Use custom config file |
| `--scope <smart\|strict\|broad>` | Set crawl scope |
| `--workers <n>` | Number of concurrent workers |
| `--only-text` | Skip asset downloads |

---

## 📁 OUTPUT STRUCTURE

Each project generates an independent data capsule:

```text
data/
└── domain_com/
    ├── content/              # Pure Markdown from web pages
    ├── media/
    │   ├── images/           # Downloaded visual assets
    │   └── docs/             # PDFs/Office + their .md mirrors
    ├── state_domain_com.db  # State database (WAL)
    └── migration_audit.jsonl # Low-level audit log
```

---

## 🧪 MAINTENANCE

To perform a controlled purge of the data environment and caches before a new migration:
```bash
uv run clean.py
```

---

## 📚 Documentation

- [CHANGELOG.md](docs/CHANGELOG.md) - Version history and changes
- [MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md) - Migration guide from v2.2 to v3.0

---

**Architect:** "In UIF, we don't scrape data; we curate knowledge. Every generated file is a pure signal ready to be understood by the next generation of AIs."

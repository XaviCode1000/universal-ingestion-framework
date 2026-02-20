# 🛸 Universal Ingestion Framework (UIF)

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Architecture: v4.0 Resilience](https://img.shields.io/badge/architecture-v4.0%20resilience-orange.svg)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)]()
[![Tests: 102 passing](https://img.shields.io/badge/tests-102%20passing-brightgreen.svg)]()
[![Coverage: 90%](https://img.shields.io/badge/coverage-90%25-success.svg)]()

[🇪🇸 Leer en Español](README.es.md)

UIF is a high-fidelity knowledge ingestion engine designed to transform legacy web infrastructures and binary document assets into Markdown databases optimized for LLMs and RAG (Retrieval-Augmented Generation) systems.

---

## 🛑 ELITE CAPABILITIES (v4.0 "Resilience & Scale")

- **Memory-Safe Ingestion**: Zero-leak architecture using **TTLCache** and DB fallbacks, allowing missions with millions of URLs on consumer hardware.
- **Legal & Ethical Compliance**: Native **Robots.txt** enforcement and user-agent management with per-domain caching.
- **Production Security**: Mandatory **SSL/TLS verification** via `certifi` and mission locks to prevent race conditions.
- **Anti-Scraping Detection**: Advanced detection of **Cloudflare**, reCAPTCHA, and hCaptcha challenges to ensure data quality.
- **Hybrid Multimodal Ingestion**: High-fidelity conversion for `PDF`, `DOCX`, `XLSX`, and `PPTX` via **MarkItDown**.
- **Industrial Resilience**: Multi-instance safety with **Mission Locks** and persistent state in **SQLite WAL mode**.
- **RAG-Ready Output**: Automatic injection of hierarchical TOCs and YAML Frontmatter optimized for vector databases.

---

## 📦 STACK TÉCNICO

| Category | Technology |
|----------|------------|
| **Runtime** | [uv](https://github.com/astral-sh/uv) (Package & Project Manager) |
| **Core** | Python 3.12+ (Type hints, TaskGroups, Inmutable Models) |
| **Data Validation** | Pydantic V2 (`frozen=True`) |
| **Fetching** | Scrapling (AsyncStealthySession + Chrome Impersonation) |
| **Database** | aiosqlite (WAL mode + Atomic RETURNING) |
| **Caching** | cachetools (TTLCache for OOM prevention) |
| **Markdown** | MarkItDown (Multimodal conversion) |
| **UI/UX** | Textual (TUI) & Rich (CLI) |

---

## 🚀 INSTALLATION

This project uses `uv` for ultra-fast, deterministic dependency management. **pip/poetry are not supported.**

### 1. Prerequisites
Install `uv` if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Setup
Clone the repository and sync the environment:
```bash
git clone https://github.com/your-repo/universal-ingestion-framework.git
cd universal-ingestion-framework
uv sync
```

### 3. Browser Setup (Optional)
Required for websites with heavy JavaScript or protection challenges:
```bash
uv run playwright install chromium
```

---

## 🏗️ USAGE

### Interactive Mode (Recommended)
Run the interactive wizard to configure your mission step-by-step:
```bash
uv run uif-scraper --setup
```

### Direct CLI Mode
Start a mission immediately from the command line:
```bash
uv run uif-scraper https://example.com --workers 10 --scope smart
```

---

## 📁 PROJECT STRUCTURE

```text
universal-ingestion-framework/
├── data/                    # Ingested data (sanitized by domain)
│   └── domain_com/
│       ├── raw/             # Raw HTML and source files
│       ├── processed/       # Optimized Parquet/JSONL datasets
│       ├── content/         # Final Markdown with RAG enhancements
│       └── logs/            # Domain-specific ingestion logs
├── src/uif_scraper/         # Main framework source
│   ├── core/                # Orchestrator, Stats, and Constants
│   ├── extractors/          # Specialized metadata & content extractors
│   ├── utils/               # Robots, Captcha, SSL, and URL tools
│   └── models.py            # Strict Pydantic schemas
├── tests/                   # 100+ tests (Unit, E2E, Integration)
└── pyproject.toml           # uv project configuration
```

---

## 🏗️ ARCHITECTURE LAYERS (v4.0)

1. **Governance Layer (RobotsChecker + MissionLock)**: Ensures legal compliance and prevents resource contention in multi-instance deployments.
2. **Orchestration Layer (EngineCore + WorkerPool)**: Manages concurrent TaskGroups with adaptive rate limiting and memory-safe URL tracking.
3. **Extraction Layer (Metadata + MarkItDown)**: Transforms messy structures into clean, RAG-optimized Markdown with enhanced frontmatter.
4. **Persistence Layer (aiosqlite + Batch Flushing)**: Guarantees data integrity with minimal disk I/O impact.

---

## 🧪 TESTING

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=uif_scraper --cov-report=term-missing
```

---

## 📚 DOCUMENTATION

- [CHANGELOG.md](docs/CHANGELOG.md) - Release history
- [PRD.md](PRD.md) - Product Requirements and Roadmap
- [AGENTS.md](AGENTS.md) - Rules for AI Agents and Contributors

---

**Architect:** "In UIF, we curate knowledge. v4.0 isn't just a scraper; it's a resilient infrastructure for the era of Large Language Models."

# 🤖 AGENTS.MD - Engineering Protocol for UIF

This document defines the operating standards, execution commands, and design philosophies for autonomous agents and developers in the `scraping` repository.

## 🛠️ MANDATORY TECHNOLOGY STACK

- **Environment Manager**: `uv` (exclusively).
- **Language**: Python 3.12+ (leveraging `Generic Alias Types` and `TaskGroups`).
- **Data Validation**: `Pydantic V2` for all schemas and configurations.
- **Data Processing**: `Polars` (Lazy API preferred) for audits and summaries.
- **Concurrency**: `asyncio` with semaphores for I/O pressure control.
- **Persistence**: `aiosqlite` with `PRAGMA journal_mode=WAL` enabled.
- **Extraction**: `Scrapling` (Navigation) + `MarkItDown` (Semantic conversion).

## 🚀 DEVELOPMENT COMMANDS

### Build and Execution
- **Interactive Mode (Wizard)**: `uv run argelia-scraper --setup`
- **CLI Execution**: `uv run argelia-scraper <URL> --workers 10`
- **Environment Cleanup**: `uv run clean.py`

### Quality and Style (Strict Mode)
- **Linting**: `uv run ruff check . --fix`
- **Formatting**: `uv run ruff format .`
- **Strict Typing**: `uv run mypy . --strict`

### Testing (Pytest)
- **Run all tests**: `uv run pytest`
- **Coverage**: `uv run pytest --cov=argelia_scraper`

## 📐 STYLE AND ARCHITECTURE GUIDELINES

### 1. "Immutability by Default" Philosophy
Use Pydantic's `BaseModel` with `frozen=True` when data should not change after initial validation.

### 2. Naming Conventions
- **Classes**: `PascalCase` (e.g., `ArgeliaMigrationEngine`).
- **Functions/Variables**: `snake_case`.
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`).
- **Privates**: `_` prefix for internal class methods.

### 3. Import Management (Ruff Order)
1. Standard Library (`asyncio`, `pathlib`, etc.)
2. Third-party Libraries (`pydantic`, `polars`, `scrapling`)
3. Local Modules

### 4. Error Handling and Resilience
- **Do not silence exceptions**: Use `try...except` only if the error will be logged or a retry will be attempted.
- **Auto-healing**: Implement retry logic based on DB state (see `StateManager.increment_retry`).
- **Log Truncation**: DB error messages should be truncated (e.g., `error_msg[:500]`) to avoid bloating.

### 5. Type Hinting
- Use of `typing` is mandatory for all function arguments and return values.
- Prefer `list[]`, `dict[]` over `List[]`, `Dict[]` (Python 3.12 standard).

## 🔒 SECURITY AND PRIVACY
- **Block Evasion**: Always use `impersonate="chrome"` in fetchers.
- **Sanitization**: All file paths must pass through `slugify()` to prevent path injection.

## 📁 OUTPUT STRUCTURE (DATA LAYER)
Agents must respect the atomized structure to avoid collisions:
- `data/{domain}/content/` -> Markdown generated from HTML.
- `data/{domain}/media/images/` -> Visual assets.
- `data/{domain}/media/docs/` -> Original PDFs/Office documents + .md mirrors.
- `data/{domain}/state_{domain}.db` -> SQLite Master State database.
- `data/{domain}/migration_audit.jsonl` -> Deep audit log.

---
**Architect:** "In UIF, code is infrastructure. Maintain type purity and event loop efficiency. Technical debt is the only real enemy."

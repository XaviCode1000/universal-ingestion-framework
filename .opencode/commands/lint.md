---
description: Run linting and type checking
model: opencode/minimax-m2.5-free
subtask: true
---

Run Ruff and Mypy on the UIF codebase.

## Commands

Ruff check:
!`uv run ruff check .`

Ruff format:
!`uv run ruff format .`

Mypy strict:
!`uv run mypy --strict uif_scraper/`

## Rules from AGENTS.md

- Type hints must use Python 3.12+ syntax: `list[str]`, `dict[str, Any]`
- Imports must follow Ruff order: stdlib → third-party → local
- All Pydantic models must have `model_config = {"frozen": True}`

Fix any issues found.

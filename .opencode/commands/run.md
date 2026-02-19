---
description: Run the UIF scraper engine
model: opencode/minimax-m2.5-free
subtask: true
---

Run the UIF scraper with the specified arguments.

## Commands

Run engine:
!`uv run python engine.py`

Run CLI:
!`uv run uif-scraper $ARGUMENTS`

Run with specific module:
!`uv run python -m uif_scraper.cli $ARGUMENTS`

## Environment

- Use `uv run` (NOT pip or poetry)
- Python 3.12+ required
- Data goes to `data/{domain}/` structure

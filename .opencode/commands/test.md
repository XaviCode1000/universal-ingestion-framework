---
description: Run pytest tests with coverage
model: opencode/kimi-k2.5-free
subtask: true
---

Execute the test suite for the UIF project.

## Commands

Run all tests:
!`uv run pytest tests/ -v --cov=uif_scraper --cov-report=term-missing`

Run specific test file:
!`uv run pytest tests/$ARGUMENTS -v`

Run with coverage report:
!`uv run pytest tests/ -v --cov=uif_scraper --cov-report=html`

## Guidelines

- Use `uv run pytest` (NOT pip or poetry)
- Tests are in `tests/` directory
- Use `-v` for verbose output
- Use `--cov` for coverage
- Coverage reports go to `htmlcov/`

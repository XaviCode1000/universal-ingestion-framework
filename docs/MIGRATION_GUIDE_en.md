# Migration Guide: UIF Scraper v2.2 -> v3.0

This version introduces significant architectural changes to improve scalability and maintainability.

## Main Changes

1. **Modular Structure**: The code is no longer a single file. It is now a Python package (`uif_scraper`).
2. **Configuration System**: `ScraperConfig` is used, supporting YAML files and environment variables.
3. **Persistence**: SQLite now uses a connection pool and WAL mode.
4. **CLI**: New `uif-scraper` command.

## Steps to Migrate

1. **Install Dependencies**:
   ```bash
   uv sync
   ```

2. **Initial Configuration**:
   Run the wizard to create your configuration file:
   ```bash
   uv run uif-scraper --setup
   ```

3. **Update Scripts**:
   If you had scripts calling `engine.py`, you can now use `uif-scraper` directly.

   **Before:**
   ```bash
   python engine.py https://example.com --workers 10
   ```

   **After:**
   ```bash
   uv run uif-scraper https://example.com --workers 10
   ```

4. **Environment Variables**:
   You can configure the data directory globally:
   ```bash
   export SCRAPER_DATA_DIR=/path/to/data
   ```

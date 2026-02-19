# scrape.fish - Universal Ingestion Framework CLI wrapper
# High-fidelity knowledge ingestion engine for LLMs and RAG systems

function scrape -d "Universal Ingestion Framework - Transform web content to Markdown"
    # Option specifications
    argparse -n scrape \
        'h/help' \
        's/setup' \
        'u/url=' \
        'c/config=' \
        'w/workers=' \
        'scope=' \
        'o/only-text' \
        'v/verbose' \
        'q/quiet' \
        'dry-run' \
        'list-scopes' \
        -- $argv

    # Handle parse errors
    or return 1

    # Project directory
    set -l project_dir "$HOME/Dev/my_apps/universal-ingestion-framework"

    # Show help
    if set -ql _flag_help[1]
        _scrape_show_help
        return 0
    end

    # List available scopes
    if set -ql _flag_list_scopes[1]
        echo "Available scopes:"
        echo "  smart  - Auto-detect: root domain = broad, subdirectory = strict"
        echo "  strict - Only URLs under the seed URL path"
        echo "  broad  - All URLs within the same domain"
        return 0
    end

    # Build command
    set -l cmd uv run uif-scraper

    # Setup mode
    if set -ql _flag_setup[1]
        echo "🛸 Launching UIF Scraper setup wizard..."
        cd $project_dir
        eval $cmd --setup
        return $status
    end

    # Config file
    if set -ql _flag_config[1]
        set -a cmd --config $_flag_config
    end

    # Workers
    if set -ql _flag_workers[1]
        set -a cmd --workers $_flag_workers
    end

    # Scope
    if set -ql _flag_scope[1]
        set -a cmd --scope $_flag_scope
    end

    # Only text (skip assets)
    if set -ql _flag_only_text[1]
        set -a cmd --only-text
    end

    # URL from flag or positional argument
    set -l target_url
    if set -ql _flag_url[1]
        set target_url $_flag_url
    else if test (count $argv) -gt 0
        set target_url $argv[1]
    end

    # Validate URL is provided (unless dry-run or setup)
    if not set -ql _flag_dry_run[1]
        if test -z "$target_url"
            echo "Error: URL is required." >&2
            echo "Usage: scrape <URL> [options]" >&2
            echo "Run 'scrape --help' for more information." >&2
            return 1
        end
    end

    # Dry run - show what would be executed
    if set -ql _flag_dry_run[1]
        echo "📋 Dry run - command that would be executed:"
        echo "  cd $project_dir"
        echo "  $cmd $target_url"
        return 0
    end

    # Verbose mode
    if set -ql _flag_verbose[1]
        echo "🚀 Starting UIF Scraper..."
        echo "   URL: $target_url"
        echo "   Workers: "(set -ql _flag_workers[1] && echo $_flag_workers || echo "default (5)")
        echo "   Scope: "(set -ql _flag_scope[1] && echo $_flag_scope || echo "smart")
        echo "   Assets: "(set -ql _flag_only_text[1] && echo "disabled" || echo "enabled")
        echo ""
    end

    # Quiet mode
    if set -ql _flag_quiet[1]
        set -a cmd 2>/dev/null
    end

    # Execute
    cd $project_dir
    eval $cmd $target_url

    return $status
end

function _scrape_show_help
    echo ""
    echo "🛸 Universal Ingestion Framework (UIF) v3.0"
    echo ""
    echo "USAGE"
    echo "    scrape <URL> [OPTIONS]"
    echo "    scrape --setup"
    echo ""
    echo "DESCRIPTION"
    echo "    High-fidelity knowledge ingestion engine that transforms web content"
    echo "    and binary documents into Markdown optimized for LLMs and RAG systems."
    echo ""
    echo "OPTIONS"
    echo "    -h, --help          Show this help message"
    echo "    -s, --setup         Launch interactive setup wizard"
    echo "    -u, --url=URL       Target URL to scrape"
    echo "    -c, --config=FILE   Use custom config file (YAML)"
    echo "    -w, --workers=N     Number of concurrent workers (default: 5)"
    echo "    --scope=SCOPE       Crawling scope: smart, strict, broad (default: smart)"
    echo "    -o, --only-text     Skip asset downloads (images, PDFs)"
    echo "    -v, --verbose       Show detailed execution info"
    echo "    -q, --quiet         Suppress non-error output"
    echo "    --dry-run           Show command without executing"
    echo "    --list-scopes       Show available scope options"
    echo ""
    echo "SCOPE OPTIONS"
    echo "    smart   Auto-detect based on seed URL:"
    echo "            - Root domain (e.g., example.com/) → broad scope"
    echo "            - Subdirectory (e.g., example.com/blog/) → strict scope"
    echo ""
    echo "    strict  Only crawl URLs that start with the seed URL path."
    echo "            Ideal for scraping specific sections of a site."
    echo ""
    echo "    broad   Crawl all URLs within the same domain."
    echo "            Use with caution on large sites."
    echo ""
    echo "EXAMPLES"
    echo "    # Basic usage"
    echo "    scrape https://example.com"
    echo ""
    echo "    # With custom workers and scope"
    echo "    scrape https://example.com/blog --workers 10 --scope strict"
    echo ""
    echo "    # Text only, no assets"
    echo "    scrape https://docs.python.org/3/ --only-text"
    echo ""
    echo "    # Interactive setup"
    echo "    scrape --setup"
    echo ""
    echo "    # Dry run to preview command"
    echo "    scrape https://example.com --dry-run"
    echo ""
    echo "OUTPUT STRUCTURE"
    echo "    data/"
    echo "    └── example_com/"
    echo "        ├── content/              # Markdown files (.md.zst compressed)"
    echo "        ├── media/"
    echo "        │   ├── images/           # Downloaded images"
    echo "        │   └── docs/             # PDFs + converted .md"
    echo "        └── state.db              # SQLite state (WAL mode, batched)"
    echo ""
    echo "FEATURES"
    echo "    - 4-level fallback text extraction (Trafilatura → MarkItDown → BS4)"
    echo "    - Zstandard compression for markdown (30-40% smaller)"
    echo "    - Async batch processing with connection pooling"
    echo "    - SQLite WAL mode with automatic retry on lock"
    echo ""
    echo "DOCUMENTATION"
    echo "    Project: ~/Dev/my_apps/universal-ingestion-framework"
    echo "    Changelog: docs/CHANGELOG.md"
    echo ""
    echo "AUTHOR"
    echo "    UIF Scraper - Universal Ingestion Framework"
    echo ""
end

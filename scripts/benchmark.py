#!/usr/bin/env python3
"""Benchmark baseline script for UIF v3.3 Performance Scaling.

This script establishes the baseline performance metrics BEFORE any optimizations:
- TaskGroup migration
- uvloop integration
- Zero-copy persistence

Usage:
    # Basic run (measures time and throughput)
    uv run python scripts/benchmark_baseline.py

    # With memory profiling (requires memray)
    memray run --live python scripts/benchmark_baseline.py
    memray run -o memory_benchmark.bin python scripts/benchmark_baseline.py
    memray flamegraph memory_benchmark.bin  # Generate flamegraph

Output:
    - Console: Summary metrics
    - File: benchmark_results.json (if --output specified)
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import aiohttp
from rich.console import Console
from rich.table import Table

# Static list of documentation URLs for deterministic benchmarks
# These are reliable, fast-responding URLs for consistent measurements
BENCHMARK_URLS: list[str] = [
    # Python official docs (fast, reliable)
    "https://docs.python.org/3/",
    "https://docs.python.org/3/library/",
    "https://docs.python.org/3/library/asyncio.html",
    "https://docs.python.org/3/library/json.html",
    "https://docs.python.org/3/tutorial/",
    "https://docs.python.org/3/howto/",
    # PyPI (reliable)
    "https://pypi.org/",
    "https://pypi.org/project/requests/",
    "https://pypi.org/project/httpx/",
    # GitHub docs (reliable)
    "https://docs.github.com/en",
    "https://docs.github.com/en/get-started",
    # MDN Web Docs (reliable)
    "https://developer.mozilla.org/en-US/docs/Web/JavaScript",
    "https://developer.mozilla.org/en-US/docs/Web/HTML",
    # Misc reliable docs
    "https://www.scrapehero.com/how-to-scrape-websites/",
    "https://www.wikipedia.org/",
    # Fast API docs
    "https://fastapi.tiangolo.com/",
    "https://fastapi.tiangolo.com/tutorial/",
    # SQLAlchemy docs
    "https://docs.sqlalchemy.org/en/20/",
    # Django docs
    "https://docs.djangoproject.com/en/5.0/",
    # Docker docs
    "https://docs.docker.com/",
    # Kubernetes docs
    "https://kubernetes.io/docs/",
    # Rust docs
    "https://doc.rust-lang.org/book/",
    # Go docs
    "https://go.dev/doc/",
    # Node.js docs
    "https://nodejs.org/docs/latest/api/",
    # React docs
    "https://react.dev/",
    # Vue docs
    "https://vuejs.org/guide/",
    # TypeScript docs
    "https://www.typescriptlang.org/docs/",
    # JSON Schema
    "https://json-schema.org/learn/",
    # YAML docs
    "https://yaml.org/spec/1.2.2/",
    # PostgreSQL docs
    "https://www.postgresql.org/docs/",
    # MySQL docs
    "https://dev.mysql.com/doc/",
    # SQLite docs
    "https://www.sqlite.org/docs.html",
    # Redis docs
    "https://redis.io/docs/",
    # MongoDB docs
    "https://www.mongodb.com/docs/",
    # AWS docs
    "https://docs.aws.amazon.com/",
    # Azure docs
    "https://learn.microsoft.com/en-us/azure/",
    # GCP docs
    "https://cloud.google.com/docs/",
    # Terraform docs
    "https://developer.hashicorp.com/terraform/docs",
    # Ansible docs
    "https://docs.ansible.com/",
    # Nginx docs
    "https://nginx.org/en/docs/",
    # Apache docs
    "https://httpd.apache.org/docs/",
    # Curl docs
    "https://curl.se/docs/",
    # OpenSSL docs
    "https://www.openssl.org/docs/",
    # Linux docs
    "https://www.kernel.org/doc/html/latest/",
    # Arch wiki
    "https://wiki.archlinux.org/",
    # Debian docs
    "https://www.debian.org/doc/",
    # Ubuntu docs
    "https://docs.ubuntu.com/",
    # Fedora docs
    "https://docs.fedoraproject.org/",
]

# Limit to first N URLs for faster benchmark (configurable)
DEFAULT_URL_COUNT = 30


def get_memory_usage_mb() -> float:
    """Get current process memory usage in MB (RSS)."""
    try:
        import psutil

        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        # Fallback: parse /proc/self/status
        try:
            with open("/proc/self/status", "r") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        # VmRSS is in kB
                        return int(line.split()[1]) / 1024
        except Exception:
            pass
    return 0.0


async def fetch_url(
    session: Any, url: str, semaphore: asyncio.Semaphore
) -> tuple[bool, str]:
    """Fetch a single URL with semaphore rate limiting."""
    async with semaphore:
        try:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    content = await resp.text()
                    return True, url
                return False, f"HTTP {resp.status}"
        except Exception as e:
            return False, str(e)


async def run_benchmark(
    url_count: int = DEFAULT_URL_COUNT,
    workers: int = 5,
    output_file: str | None = None,
) -> dict[str, Any]:
    """Run the benchmark with specified parameters."""

    import aiohttp

    console = Console()

    # Select subset of URLs
    urls_to_scrape = BENCHMARK_URLS[:url_count]

    console.print(f"\n[bold cyan]📊 UIF v3.3 Baseline Benchmark[/]")
    console.print(f"   URLs: {len(urls_to_scrape)}")
    console.print(f"   Workers: {workers}")
    console.print(f"   Python: {sys.version.split()[0]}")
    console.print()

    # Track metrics
    start_time = time.perf_counter()
    start_memory = get_memory_usage_mb()
    peak_memory = start_memory

    # Results tracking
    results_list: list[tuple[bool, str]] = []

    # Create semaphore for rate limiting
    semaphore = asyncio.Semaphore(workers)

    console.print("[yellow]⏳ Running benchmark...[/]\n")

    # Use aiohttp ClientSession with default HTTP/1.1
    # Note: This is the BASELINE - no uvloop, no curl_cffi yet
    async with aiohttp.ClientSession() as session:
        # Memory tracking task
        memory_samples: list[float] = []

        async def track_memory():
            """Track memory in background."""
            while True:
                mem = get_memory_usage_mb()
                memory_samples.append(mem)
                await asyncio.sleep(0.5)

        memory_task = asyncio.create_task(track_memory())

        try:
            # Create tasks for all URLs
            tasks = [fetch_url(session, url, semaphore) for url in urls_to_scrape]

            # Wait for all tasks to complete
            results_list = await asyncio.gather(*tasks)

        except Exception as e:
            console.print(f"[red]❌ Benchmark error: {e}[/]")
        finally:
            memory_task.cancel()
            try:
                await memory_task
            except asyncio.CancelledError:
                pass

    end_time = time.perf_counter()
    end_memory = get_memory_usage_mb()

    # Calculate metrics
    elapsed_time = end_time - start_time
    successful = sum(1 for success, _ in results_list if success)
    failed = len(results_list) - successful

    throughput = successful / elapsed_time if elapsed_time > 0 else 0
    memory_delta = peak_memory - start_memory

    # Build results
    results = {
        "timestamp": datetime.now().isoformat(),
        "configuration": {
            "url_count": len(urls_to_scrape),
            "workers": workers,
            "python_version": sys.version.split()[0],
            "transport": "aiohttp (baseline - no uvloop/curl_cffi)",
            "url_sample": urls_to_scrape[:5],
        },
        "metrics": {
            "elapsed_time_seconds": round(elapsed_time, 2),
            "pages_completed": successful,
            "pages_failed": failed,
            "throughput_urls_per_second": round(throughput, 2),
            "start_memory_mb": round(start_memory, 2),
            "peak_memory_mb": round(peak_memory, 2),
            "end_memory_mb": round(end_memory, 2),
            "memory_delta_mb": round(memory_delta, 2),
            "memory_samples_count": len(memory_samples),
        },
        "status": "completed" if successful > 0 else "failed",
    }

    # Display results
    table = Table(title="📊 Benchmark Results - BASELINE (aiohttp)")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Elapsed Time", f"{results['metrics']['elapsed_time_seconds']:.2f}s")
    table.add_row("Pages Completed", str(results["metrics"]["pages_completed"]))
    table.add_row("Pages Failed", str(results["metrics"]["pages_failed"]))
    table.add_row(
        "Throughput", f"{results['metrics']['throughput_urls_per_second']:.2f} URLs/s"
    )
    table.add_row("Start Memory", f"{results['metrics']['start_memory_mb']:.2f} MB")
    table.add_row("Peak Memory", f"{results['metrics']['peak_memory_mb']:.2f} MB")
    table.add_row("Memory Delta", f"{results['metrics']['memory_delta_mb']:.2f} MB")

    console.print(table)

    # Show failed URLs if any
    if failed > 0:
        console.print(f"\n[yellow]⚠️ Failed URLs ({failed}):[/]")
        for success, error in results_list:
            if not success:
                console.print(f"  - {error[:80]}")

    # Save results if output file specified
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        console.print(f"\n[green]✅ Results saved to: {output_path}[/]")

    return results


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="UIF Baseline Benchmark")
    parser.add_argument(
        "--urls",
        "-n",
        type=int,
        default=DEFAULT_URL_COUNT,
        help=f"Number of URLs to scrape (default: {DEFAULT_URL_COUNT})",
    )
    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=5,
        help="Number of concurrent workers (default: 5)",
    )
    parser.add_argument(
        "--output", "-o", type=str, default=None, help="Output JSON file for results"
    )

    args = parser.parse_args()

    # Run benchmark
    results = asyncio.run(
        run_benchmark(
            url_count=args.urls,
            workers=args.workers,
            output_file=args.output,
        )
    )

    # Exit code based on success
    sys.exit(0 if results["status"] == "completed" else 1)


if __name__ == "__main__":
    main()

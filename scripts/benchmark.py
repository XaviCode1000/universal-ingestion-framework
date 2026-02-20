#!/usr/bin/env python3
"""Benchmark script for UIF v3.3 Performance Scaling.

This script compares performance with and without uvloop to measure the improvement.

Usage:
    # Compare baseline vs uvloop
    uv run python scripts/benchmark.py --compare

    # Only baseline (asyncio)
    uv run python scripts/benchmark.py --baseline

    # Only uvloop
    uv run python scripts/benchmark.py --uvloop
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import aiohttp
from rich.console import Console
from rich.table import Table

# Static list of documentation URLs for deterministic benchmarks
BENCHMARK_URLS: list[str] = [
    # Python official docs
    "https://docs.python.org/3/",
    "https://docs.python.org/3/library/",
    "https://docs.python.org/3/library/asyncio.html",
    "https://docs.python.org/3/library/json.html",
    "https://docs.python.org/3/tutorial/",
    "https://docs.python.org/3/howto/",
    # PyPI
    "https://pypi.org/",
    "https://pypi.org/project/requests/",
    "https://pypi.org/project/httpx/",
    # GitHub docs
    "https://docs.github.com/en",
    "https://docs.github.com/en/get-started",
    # MDN Web Docs
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

DEFAULT_URL_COUNT = 30


def get_memory_usage_mb() -> float:
    """Get current process memory usage in MB (RSS)."""
    try:
        import psutil

        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        try:
            with open("/proc/self/status", "r") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
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
                    return True, url
                return False, f"HTTP {resp.status}"
        except Exception as e:
            return False, str(e)


async def run_benchmark_async(url_count: int, workers: int) -> dict[str, Any]:
    """Run benchmark with standard asyncio."""
    urls_to_scrape = BENCHMARK_URLS[:url_count]

    start_time = time.perf_counter()
    start_memory = get_memory_usage_mb()
    peak_memory = start_memory

    results_list: list[tuple[bool, str]] = []
    semaphore = asyncio.Semaphore(workers)

    async with aiohttp.ClientSession() as session:
        memory_samples: list[float] = []

        async def track_memory():
            while True:
                mem = get_memory_usage_mb()
                memory_samples.append(mem)
                await asyncio.sleep(0.5)

        memory_task = asyncio.create_task(track_memory())

        try:
            tasks = [fetch_url(session, url, semaphore) for url in urls_to_scrape]
            results_list = await asyncio.gather(*tasks)
        except Exception as e:
            pass
        finally:
            memory_task.cancel()
            try:
                await memory_task
            except asyncio.CancelledError:
                pass

    end_time = time.perf_counter()
    end_memory = get_memory_usage_mb()

    elapsed_time = end_time - start_time
    successful = sum(1 for success, _ in results_list if success)
    failed = len(results_list) - successful
    throughput = successful / elapsed_time if elapsed_time > 0 else 0

    return {
        "elapsed_time_seconds": round(elapsed_time, 2),
        "pages_completed": successful,
        "pages_failed": failed,
        "throughput_urls_per_second": round(throughput, 2),
        "start_memory_mb": round(start_memory, 2),
        "peak_memory_mb": round(peak_memory, 2),
        "end_memory_mb": round(end_memory, 2),
    }


async def run_uvloop_benchmark_async(url_count: int, workers: int) -> dict[str, Any]:
    """Run benchmark with uvloop."""
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    return await run_benchmark_async(url_count, workers)


def run_benchmark(url_count: int, workers: int, use_uvloop: bool) -> dict[str, Any]:
    """Run benchmark with optional uvloop."""
    if use_uvloop:
        import uvloop

        return uvloop.run(run_uvloop_benchmark_async(url_count, workers))
    else:
        return asyncio.run(run_benchmark_async(url_count, workers))


def main():
    import argparse

    parser = argparse.ArgumentParser(description="UIF Benchmark with uvloop")
    parser.add_argument("--urls", "-n", type=int, default=DEFAULT_URL_COUNT)
    parser.add_argument("--workers", "-w", type=int, default=10)
    parser.add_argument("--baseline", action="store_true", help="Run baseline only")
    parser.add_argument("--uvloop", action="store_true", help="Run uvloop only")
    parser.add_argument("--compare", action="store_true", help="Compare both")
    parser.add_argument("--output", "-o", type=str, default=None)

    args = parser.parse_args()

    console = Console()

    # Check uvloop availability
    has_uvloop = importlib.util.find_spec("uvloop") is not None

    console.print(f"\n[bold cyan]📊 UIF v3.3 Benchmark[/]")
    console.print(f"   URLs: {args.urls}")
    console.print(f"   Workers: {args.workers}")
    console.print(f"   Python: {sys.version.split()[0]}")
    console.print(f"   uvloop available: {has_uvloop}")
    console.print()

    results = {}

    # Run baseline
    if args.baseline or args.compare:
        console.print("[yellow]⏳ Running baseline (asyncio)...[/]")
        results["baseline"] = run_benchmark(args.urls, args.workers, use_uvloop=False)
        results["baseline"]["transport"] = "asyncio (baseline)"

    # Run uvloop
    if args.uvloop or args.compare:
        if not has_uvloop:
            console.print("[red]⚠️ uvloop not available![/]")
        else:
            console.print("[yellow]⏳ Running with uvloop...[/]")
            results["uvloop"] = run_benchmark(args.urls, args.workers, use_uvloop=True)
            results["uvloop"]["transport"] = "uvloop"

    # Display results
    if "baseline" in results:
        table = Table(title="📊 Benchmark Results - BASELINE (asyncio)")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        r = results["baseline"]
        table.add_row("Elapsed Time", f"{r['elapsed_time_seconds']:.2f}s")
        table.add_row("Pages Completed", str(r["pages_completed"]))
        table.add_row("Pages Failed", str(r["pages_failed"]))
        table.add_row("Throughput", f"{r['throughput_urls_per_second']:.2f} URLs/s")

        console.print(table)

    if "uvloop" in results:
        table = Table(title="📊 Benchmark Results - UVLOOP")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        r = results["uvloop"]
        table.add_row("Elapsed Time", f"{r['elapsed_time_seconds']:.2f}s")
        table.add_row("Pages Completed", str(r["pages_completed"]))
        table.add_row("Pages Failed", str(r["pages_failed"]))
        table.add_row("Throughput", f"{r['throughput_urls_per_second']:.2f} URLs/s")

        console.print(table)

    # Comparison
    if "baseline" in results and "uvloop" in results:
        table = Table(title="📈 Comparison: Baseline vs uvloop")
        table.add_column("Metric", style="cyan")
        table.add_column("Baseline", style="yellow")
        table.add_column("uvloop", style="green")
        table.add_column("Improvement", style="magenta")

        b = results["baseline"]
        u = results["uvloop"]

        imp = (
            (u["throughput_urls_per_second"] - b["throughput_urls_per_second"])
            / b["throughput_urls_per_second"]
            * 100
        )

        table.add_row(
            "Throughput",
            f"{b['throughput_urls_per_second']:.2f} URLs/s",
            f"{u['throughput_urls_per_second']:.2f} URLs/s",
            f"{imp:+.1f}%",
        )

        console.print(table)

    # Save results
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        console.print(f"\n[green]✅ Results saved to: {args.output}[/]")


if __name__ == "__main__":
    main()

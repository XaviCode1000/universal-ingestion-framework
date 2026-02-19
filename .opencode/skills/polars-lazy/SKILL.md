---
name: polars-lazy
description: Polars Lazy API patterns for UIF - optimal data processing with query optimization
---

## Use this when

- Processing large datasets that exceed memory
- Building data transformation pipelines
- Optimizing query performance with predicate pushdown

## MANDATORY: Lazy API

Always use `.lazy()` before operations, `.collect()` at the end:

```python
import polars as pl


def process_data(file_path: str) -> pl.DataFrame:
    """Procesa datos usando Lazy API."""
    return (
        pl.scan_csv(file_path)
        .filter(pl.col("status") == "active")
        .select(["url", "content", "timestamp"])
        .collect()
    )
```

## Query Optimization

Polars Lazy optimizes automatically:
- **Predicate pushdown**: Filters applied at scan time
- **Projection pushdown**: Only needed columns loaded
- **Streaming**: Process data larger than RAM

```python
# GOOD - Lazy with optimization
df = (
    pl.scan_parquet("data/large.parquet")
    .filter(pl.col("domain") == "example.com")  # Pushed down
    .select(["url", "title"])  # Only needed columns
    .collect()
)

# BAD - Eager (loads all data)
df = pl.read_parquet("data/large.parquet")
df = df.filter(pl.col("domain") == "example.com")
```

## Common Patterns

### Filter and aggregate
```python
result = (
    pl.scan_jsonl("data/scraped.jsonl")
    .filter(pl.col("status_code") == 200)
    .group_by("domain")
    .agg(
        pl.len().alias("count"),
        pl.col("content").str.len_chars().mean().alias("avg_content_len"),
    )
    .collect()
)
```

### Join datasets
```python
result = (
    pl.scan_parquet("data/pages.parquet")
    .join(
        pl.scan_parquet("data/links.parquet"),
        on="url",
        how="left",
    )
    .collect()
)
```

### Write Parquet
```python
df.lazy().sink_parquet("data/output.parquet")
```

### Streaming for large files
```python
# Process in batches without loading all into memory
for batch in pl.scan_parquet("huge.parquet").collect_batches():
    process_batch(batch)
```

## Expressions

```python
# String operations
pl.col("url").str.extract(r"https?://([^/]+)")
pl.col("title").str.to_lowercase()
pl.col("content").str.len_chars()

# Datetime operations
pl.col("timestamp").str.to_datetime("%Y-%m-%d %H:%M:%S")
pl.col("date").dt.year()

# Conditional
pl.when(pl.col("status") == 200).then(pl.lit("success")).otherwise(pl.lit("error"))
```

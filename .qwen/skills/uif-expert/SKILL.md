# UIF-EXPERT: Universal Ingestion Framework Skill

> Skill especializado para desarrollo con el stack técnico UIF: Python 3.12+, Pydantic V2, Polars, asyncio, Scrapling, aiosqlite.

## Descripción

Este skill proporciona patrones, mejores prácticas y código de referencia para desarrollar dentro del Universal Ingestion Framework. Activa automáticamente las reglas de arquitectura, validación de tipos y optimización de rendimiento definidas en el proyecto.

## Disparadores (Triggers)

- Cuando el usuario trabaja con Python 3.12+ en el proyecto
- Cuando se menciona: Polars, Pydantic, asyncio, Scrapling, aiosqlite
- Cuando se solicita procesamiento de datos, scraping, o ingesta
- Cuando se pide crear modelos, esquemas, o pipelines de datos

---

## STACK TÉCNICO OBLIGATORIO

### Runtime & Package Manager
```bash
# ✅ CORRECTO
uv add requests
uv sync
uv run python script.py

# ❌ PROHIBIDO
pip install requests
poetry add requests
```

### Type Hinting Python 3.12+
```python
# ✅ CORRECTO - Sintaxis moderna
def process_data(items: list[str]) -> dict[str, Any]:
    ...

# ❌ INCORRECTO - Sintaxis legacy
from typing import List, Dict
def process_data(items: List[str]) -> Dict[str, Any]:
    ...
```

### Pydantic V2 Inmutable
```python
from pydantic import BaseModel, Field, HttpUrl


class ExtractionResult(BaseModel):
    """Esquema inmutable para resultados de extracción."""

    model_config = {"frozen": True}

    url: HttpUrl
    content_md: str
    extracted_at: str
    metadata: dict[str, str] = Field(default_factory=dict)
    status: str = "success"
```

### Polars Lazy API
```python
import polars as pl


def process_large_dataset(path: str) -> pl.DataFrame:
    """Procesa dataset grande con Lazy API."""
    return (
        pl.scan_parquet(path)
        .filter(pl.col("status") == "active")
        .with_columns(
            pl.col("created_at").str.to_datetime("%Y-%m-%d"),
            pl.col("price").cast(pl.Float64),
        )
        .group_by("category")
        .agg(
            pl.col("price").mean().alias("avg_price"),
            pl.col("id").n_unique().alias("count"),
        )
        .collect()
    )
```

### Asyncio con TaskGroups
```python
import asyncio
from collections.abc import Coroutine


async def process_concurrent[T](
    tasks: list[Coroutine[Any, Any, T]],
    max_concurrency: int = 10,
) -> list[T]:
    """Ejecuta tareas concurrentes con límite de concurrencia."""
    semaphore = asyncio.Semaphore(max_concurrency)

    async def bounded_task(task: Coroutine[Any, Any, T]) -> T:
        async with semaphore:
            return await task

    async with asyncio.TaskGroup() as tg:
        futures = [tg.create_task(bounded_task(t)) for t in tasks]

    return [f.result() for f in futures]
```

### Scrapling para Web Scraping
```python
from scrapling import Fetcher


async def fetch_page(url: str) -> str:
    """Obtiene contenido HTML con evasión de detección."""
    fetcher = Fetcher(impersonate="chrome")
    response = fetcher.fetch(url)
    return response.content
```

### aiosqlite con WAL
```python
import aiosqlite


async def init_db(db_path: str) -> aiosqlite.Connection:
    """Inicializa base de datos con WAL mode."""
    conn = await aiosqlite.connect(db_path)
    await conn.execute("PRAGMA journal_mode=WAL")
    await conn.execute("PRAGMA synchronous=NORMAL")
    return conn


async def insert_record(
    conn: aiosqlite.Connection,
    table: str,
    data: dict[str, Any],
) -> None:
    """Inserta registro de forma segura."""
    columns = ", ".join(data.keys())
    placeholders = ", ".join("?" * len(data))
    sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    await conn.execute(sql, tuple(data.values()))
    await conn.commit()
```

---

## PATRONES DE DISEÑO

### Factory para Extractores
```python
from abc import ABC, abstractmethod
from typing import override


class BaseExtractor(ABC):
    """Extractor base para todos los dominios."""

    @abstractmethod
    async def extract(self, url: str) -> dict[str, Any]:
        """Extrae datos de una URL."""
        ...


class JSONExtractor(BaseExtractor):
    """Extractor para APIs JSON."""

    @override
    async def extract(self, url: str) -> dict[str, Any]:
        # Implementación específica
        ...


class HTMLExtractor(BaseExtractor):
    """Extractor para páginas HTML."""

    @override
    async def extract(self, url: str) -> dict[str, Any]:
        # Implementación específica
        ...


def get_extractor(content_type: str) -> BaseExtractor:
    """Factory para crear extractores."""
    extractors: dict[str, type[BaseExtractor]] = {
        "json": JSONExtractor,
        "html": HTMLExtractor,
    }
    return extractors.get(content_type, HTMLExtractor)()
```

### Strategy para Transformadores
```python
from typing import Protocol


class TransformStrategy(Protocol):
    """Protocolo para estrategias de transformación."""

    def transform(self, df: pl.LazyFrame) -> pl.LazyFrame:
        ...


class CleanStrategy:
    """Estrategia de limpieza de datos."""

    def transform(self, df: pl.LazyFrame) -> pl.LazyFrame:
        return df.filter(pl.col("value").is_not_null())


class EnrichStrategy:
    """Estrategia de enriquecimiento."""

    def transform(self, df: pl.LazyFrame) -> pl.LazyFrame:
        return df.with_columns(
            pl.col("price").round(2).alias("price_rounded"),
            pl.col("date").str.to_datetime().alias("parsed_date"),
        )
```

---

## SEGURIDAD

### Sanitización de Rutas
```python
from pathlib import Path
from slugify import slugify


def safe_path(domain: str, filename: str, extension: str = "jsonl") -> Path:
    """Genera ruta segura sanitizada."""
    safe_domain = slugify(domain)
    safe_filename = slugify(filename)
    return Path("data") / safe_domain / "raw" / f"{safe_filename}.{extension}"
```

### Manejo de Errores
```python
import logging
from typing import Never

logger = logging.getLogger(__name__)


class UIFError(Exception):
    """Error base del framework."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        self.message = message[:500]  # Truncar para DB
        self.context = context or {}
        super().__init__(self.message)


def raise_unsupported(feature: str) -> Never:
    """Lanza error para features no soportadas."""
    raise UIFError(f"Feature no soportada: {feature}")
```

---

## COMANDOS DE VERIFICACIÓN

```bash
# Verificar tipos
uv run mypy --strict src/

# Linting y formato
uv run ruff check .
uv run ruff format .

# Ejecutar tests
uv run pytest tests/ -v --cov=src/

# Verificar imports
uv run ruff check --select I src/
```

---

## CHECKLIST PRE-COMMIT

Antes de commit, verificar:

- [ ] Todos los modelos Pydantic tienen `model_config = {"frozen": True}`
- [ ] Rutas sanitizadas con `slugify()`
- [ ] Errores truncados a 500 caracteres máximo
- [ ] Imports ordenados según Ruff
- [ ] Type hints usan sintaxis Python 3.12+
- [ ] Polars Lazy API para procesamiento de datos
- [ ] asyncio.TaskGroups para concurrencia
- [ ] `mypy --strict` pasa sin errores
- [ ] `ruff check .` pasa sin errores

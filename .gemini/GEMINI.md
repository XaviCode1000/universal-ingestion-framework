# GEMINI.md - Contexto del Proyecto UIF

> **Universal Ingestion Framework** - Motor de ingesta de datos con arquitectura resiliente

---

## 🎯 Identidad del Proyecto

**UIF-ARE** (Universal Ingestion Framework - Architect & Refactoring Engine) es un framework de ingesta de datos diseñado con principios de Clean Architecture, tipado estricto y procesamiento asíncrono de alto rendimiento.

---

## 📦 Stack Técnico Obligatorio

| Categoría | Tecnología | Restricciones |
|-----------|------------|---------------|
| **Runtime** | `uv` | ❌ PROHIBIDO pip/poetry |
| **Core** | Python 3.12+ | Type hints: `list[str]`, `dict[str, Any]` |
| **Validación** | Pydantic V2 | `model_config = {"frozen": True}` |
| **Procesamiento** | Polars | Lazy API: `.lazy()` → `.collect()` |
| **Async** | asyncio | TaskGroups para concurrencia |
| **Scraping** | Scrapling | `impersonate="chrome"` |
| **Database** | aiosqlite | Modo WAL habilitado |
| **HTML→MD** | MarkItDown | Para pipelines RAG |

---

## 📁 Estructura de Carpetas

```
universal-ingestion-framework/
├── data/
│   └── {domain}/           # Cada dominio tiene su carpeta
│       ├── raw/            # Datos crudos (.html, .jsonl)
│       ├── processed/      # Datos procesados (.parquet)
│       └── logs/           # Logs específicos del dominio
├── src/
│   └── uif/
│       ├── core/           # Lógica central
│       ├── extractors/     # Extractores por dominio
│       └── models/         # Esquemas Pydantic
├── tests/
├── .gemini/                # Configuración Gemini CLI
│   ├── settings.json
│   ├── GEMINI.md
│   ├── skills/
│   └── hooks/
└── AGENTS.md               # Protocolo completo
```

---

## ⚠️ Reglas Inamovibles

### 1. Inmutabilidad
```python
# ✅ CORRECTO
class MyModel(BaseModel):
    model_config = {"frozen": True}
    field: str

# ❌ INCORRECTO
class MyModel(BaseModel):  # Sin frozen=True
    field: str
```

### 2. Seguridad de Rutas
```python
# ✅ CORRECTO - Siempre sanitizar
from slugify import slugify
safe_path = f"data/{slugify(domain)}/{slugify(filename)}.jsonl"

# ❌ INCORRECTO - Path injection vulnerable
unsafe_path = f"data/{domain}/{filename}.jsonl"
```

### 3. Logs en Base de Datos
```python
# ✅ CORRECTO - Truncar errores a 500 chars
error_msg = str(e)[:500]
```

### 4. Orden de Imports (Ruff)
```python
# 1. Standard library
# 2. Third-party
# 3. Local imports
import asyncio
from pathlib import Path

import polars as pl
from pydantic import BaseModel

from uif.config import Settings
```

---

## 🚀 Comandos de Desarrollo

```bash
# Instalar dependencias
uv sync

# Ejecutar script
uv run python src/uif/engine.py

# Linting
uv run ruff check .
uv run ruff format .

# Type checking
uv run mypy --strict src/

# Tests
uv run pytest tests/ -v
```

---

## 🧠 Patrones de Diseño

### Factory para Extractores
```python
from abc import ABC, abstractmethod
from typing import override


class BaseExtractor(ABC):
    @abstractmethod
    async def extract(self, url: str) -> dict[str, Any]: ...


class JSONExtractor(BaseExtractor):
    @override
    async def extract(self, url: str) -> dict[str, Any]:
        # Implementación específica
        ...
```

### Strategy para Transformadores
```python
from typing import Protocol


class TransformStrategy(Protocol):
    def transform(self, df: pl.LazyFrame) -> pl.LazyFrame: ...
```

---

## 📊 Procesamiento con Polars Lazy

```python
import polars as pl


def process_large_dataset(path: str) -> pl.DataFrame:
    """Procesa dataset grande con Lazy API."""
    return (
        pl.scan_parquet(path)
        .filter(pl.col("status") == "active")
        .with_columns(
            pl.col("created_at").str.to_datetime("%Y-%m-%d"),
        )
        .group_by("category")
        .agg(pl.col("id").n_unique().alias("count"))
        .collect()
    )
```

---

## ⚡ Concurrencia con TaskGroups

```python
import asyncio


async def process_concurrent[T](
    tasks: list[Coroutine[Any, Any, T]],
    max_concurrency: int = 10,
) -> list[T]:
    """Ejecuta tareas concurrentes con límite."""
    semaphore = asyncio.Semaphore(max_concurrency)

    async def bounded_task(task: Coroutine[Any, Any, T]) -> T:
        async with semaphore:
            return await task

    async with asyncio.TaskGroup() as tg:
        futures = [tg.create_task(bounded_task(t)) for t in tasks]

    return [f.result() for f in futures]
```

---

## 🔒 Skills Disponibles

- **uif-expert**: Patrones avanzados del framework
- **python-strict**: Validación de código Python 3.12+
- **exa-search**: Búsqueda web con Exa AI (documentación, código, papers)

---

## 📝 Notas para el Agente

1. **SIEMPRE** responde en español (Rioplatense con voseo)
2. **SIEMPRE** usa `frozen=True` en modelos Pydantic
3. **SIEMPRE** sanitiza rutas con `slugify()`
4. **SIEMPRE** trunca errores a 500 caracteres
5. **SIEMPRE** usa Polars Lazy para datasets grandes
6. **SIEMPRE** usa TaskGroups para concurrencia

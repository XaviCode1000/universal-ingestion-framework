# 🤖 AGENTS.MD - Protocolo de Ingeniería para UIF

Este documento define los estándares operativos, comandos de ejecución y filosofías de diseño para agentes autónomos y desarrolladores en el repositorio `scraping`.

## 🛠️ STACK TECNOLÓGICO OBLIGATORIO

- **Gestor de Entorno**: `uv` (exclusivamente).
- **Lenguaje**: Python 3.12+ (aprovechando `Generic Alias Types` y `TaskGroups`).
- **Validación de Datos**: `Pydantic V2` para todos los esquemas y configuraciones.
- **Procesamiento de Datos**: `Polars` (Lazy API preferida) para auditorías y resúmenes.
- **Concurrencia**: `asyncio` con semáforos para control de presión de I/O.
- **Persistencia**: `aiosqlite` con `PRAGMA journal_mode=WAL` habilitado.
- **Extracción**: `Scrapling` (Navegación) + `MarkItDown` (Conversión semántica).

## 🚀 COMANDOS DE DESARROLLO

### Construcción y Ejecución
- **Modo Interactivo (Wizard)**: `uv run engine.py`
- **Ejecución CLI**: `uv run engine.py <URL> --workers 10`
- **Limpieza de Entorno**: `uv run clean.py`

### Calidad y Estilo (Strict Mode)
- **Linting**: `uv run ruff check . --fix`
- **Formateo**: `uv run ruff format .`
- **Tipado Estricto**: `uv run mypy . --strict`

### Testing (Pytest)
- **Ejecutar todos los tests**: `uv run pytest`
- **Ejecutar un archivo específico**: `uv run pytest tests/test_engine.py`
- **Ejecutar un test único**: `uv run pytest tests/test_engine.py::test_slugify_logic`
- **Cobertura**: `uv run pytest --cov=.`

## 📐 GUÍAS DE ESTILO Y ARQUITECTURA

### 1. Filosofía de "Inmutabilidad por Defecto"
Utilizar `BaseModel` de Pydantic con `frozen=True` cuando los datos no deban cambiar tras la validación inicial.

### 2. Convenciones de Nomenclatura
- **Clases**: `PascalCase` (ej. `ArgeliaMigrationEngine`).
- **Funciones/Variables**: `snake_case`.
- **Constantes**: `UPPER_SNAKE_CASE` (ej. `MAX_RETRIES`).
- **Privados**: Prefijo `_` para métodos internos de clase.

### 3. Gestión de Imports (Orden Ruff)
1. Standard Library (`asyncio`, `pathlib`, etc.)
2. Third-party Libraries (`pydantic`, `polars`, `scrapling`)
3. Local Modules

### 4. Tratamiento de Errores y Resiliencia
- **No silenciar excepciones**: Usar `try...except` solo si se va a registrar el error o intentar un reintento.
- **Auto-healing**: Implementar lógica de reintentos basada en el estado de la DB (ver `StateManager.increment_retry`).
- **Truncado de Logs**: Los errores en DB deben truncarse (ej. `error_msg[:500]`) para evitar bloating.

### 5. Tipado (Type Hinting)
- El uso de `typing` es obligatorio en todos los argumentos y retornos de funciones.
- Preferir `list[]`, `dict[]` sobre `List[]`, `Dict[]` (Python 3.12 standard).

## 🔒 SEGURIDAD Y PRIVACIDAD
- **Evasión de Bloqueos**: Usar siempre `impersonate="chrome"` en los fetchers.
- **Sanitización**: Todas las rutas de archivos deben pasar por `slugify()` para evitar inyecciones de path.

## 📁 ESTRUCTURA DE SALIDA (DATA LAYER)
Los agentes deben respetar la estructura atomizada para evitar colisiones:
- `data/{domain}/content/` -> Markdown generado a partir de HTML.
- `data/{domain}/media/images/` -> Assets visuales.
- `data/{domain}/media/docs/` -> PDFs y documentos Office originales + mirrors .md.
- `data/{domain}/state_{domain}.db` -> Base de datos SQLite (Estado Maestro).
- `data/{domain}/migration_audit.jsonl` -> Log de auditoría profunda.

---
**Arquitecto:** "En UIF, el código es infraestructura. Mantén la pureza del tipo y la eficiencia del ciclo de evento. La deuda técnica es el único enemigo real."

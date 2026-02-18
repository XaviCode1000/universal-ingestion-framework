# 🛸 Universal Ingestion Framework (UIF)

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Architecture: Multi-Layer](https://img.shields.io/badge/architecture-multi--layer-orange.svg)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)]()
[![Tests: 75 passing](https://img.shields.io/badge/tests-75%20passing-brightgreen.svg)]()

[🇺🇸 Leer en Inglés](README.md)

UIF es un motor de ingesta de conocimiento de alta fidelidad diseñado para transformar infraestructuras web legacy y activos documentales binarios en bases de datos Markdown optimizadas para LLMs y sistemas RAG (Retrieval-Augmented Generation).

---

## 🛑 CAPACIDADES DE ÉLITE

- **Ingesta Multimodal Híbrida**: Conversión de alta fidelidad para `PDF`, `DOCX`, `XLSX` y `PPTX` vía **MarkItDown**, y extracción semántica superior para HTML vía **Trafilatura**.
- **Limpieza de "Grado Industrial"**: Pipeline de pre-poda con **Selectolax**, sanitización con **nh3** y normalización Unicode con **ftfy** para eliminar el 100% del ruido y el *mojibake*.
- **Navegación Inteligente (Scope Control)**: Estrategias `SMART`, `STRICT` y `BROAD` para controlar con precisión quirúrgica el alcance del rastreo (evitando salir de sub-sitios o documentación específica).
- **Contexto RAG Enriquecido**: Inyección automática de **YAML Frontmatter** (URL, autor, fecha, título) en cada archivo para facilitar la indexación en bases de datos vectoriales.
- **Resiliencia Industrial**: Gestión de estado mediante **SQLite en modo WAL**, permitiendo concurrencia real y recuperación automática tras fallos.
- **UX Conversacional**: Asistente interactivo (Wizard) para configuración guiada de alcance, procesos y tipos de contenido.

---

## 🏗️ ARQUITECTURA TÉCNICA (Pipeline v3.0.0 - Modular Enterprise)

El motor opera en cuatro capas de refinamiento:

1. **Capa de Navegación (Scrapling + Scope Logic)**: Orquestación asíncrona con evasión de bloqueos y filtrado de alcance inteligente basado en la profundidad de la URL semilla.
2. **Capa de Purificación (Selectolax + Density Analysis)**: Eliminación masiva de ruido mediante selectores estáticos y un **Algoritmo de Densidad de Enlaces** que detecta y elimina menús/sidebars incluso en sitios no semánticos.
3. **Capa de Conversión Híbrida**: Selección dinámica del mejor motor con **Estrategia de Título en Cascada** (Waterfall) para garantizar metadatos precisos, usando **Trafilatura** y **MarkItDown**.
4. **Capa de Refinamiento (ftfy + YAML)**: Normalización final del texto (mojibake fix) y enriquecimiento con metadatos estructurados para máxima compatibilidad con sistemas RAG.

---

## 🧪 TESTING

UIF incluye una suite de tests completa con **75+ tests** cubriendo escenarios unitarios, de integración y end-to-end:

```bash
# Ejecutar todos los tests
uv run pytest tests/ -v

# Solo tests rápidos (sin browser e2e)
uv run pytest tests/ -v -k "not browser"

# Con reporte de cobertura
uv run pytest tests/ -v --cov=uif_scraper --cov-report=html

# Solo tests end-to-end (requiere internet)
uv run pytest tests/test_e2e.py tests/test_e2e_browser.py -v
```

### Cobertura de Tests

| Categoría | Tests | Descripción |
|-----------|-------|-------------|
| Unit Tests | 51 | Navegación, extractores, DB, utils |
| E2E (HTTP) | 4 | Peticiones HTTP reales a webscraper.io |
| E2E (Browser) | 3 | Automatización completa con Chromium |
| Integration | 17 | Orquestación del engine, shutdown, reportes |

---

## 🚀 INSTALACIÓN Y USO

Este proyecto utiliza `uv` para una gestión de dependencias ultrarrápida y determinista.

### Pre-requisitos
```bash
# Instalar uv si no lo tienes
curl -LsSf https://astral.sh/uv/install.sh | sh

# Instalar dependencias y lock file
uv sync
```

### Configuración del Navegador (Opcional - para tests E2E con browser)
```bash
# Instalar Chromium para Playwright (requerido para tests E2E con browser)
uv run playwright install chromium
```

### Ejecución Interactiva (Recomendado)
Simplemente ejecuta el motor y sigue al asistente visual:
```bash
uv run uif-scraper --setup
```

### Ejecución Automática (CLI)
Para flujos de trabajo automatizados o scripts de shell:
```bash
uv run uif-scraper https://ejemplo.com --workers 10 --scope smart
```

---

## 📁 ESTRUCTURA DE SALIDA

Cada proyecto genera una cápsula de datos independiente:

```text
data/
└── dominio_com/
    ├── content/              # Markdown puro de páginas web
    ├── media/
    │   ├── images/           # Assets visuales descargados
    │   └── docs/             # PDFs/Office + sus espejos .md
    ├── state_dominio_com.db  # Base de datos de estado (WAL)
    └── migration_audit.jsonl # Auditoría de bajo nivel
```

---

## 🧪 MANTENIMIENTO

Para realizar una purga controlada del entorno de datos y caches antes de una nueva migración:
```bash
uv run clean.py
```

---

**Arquitecto:** "En UIF, no scrapeamos datos; curamos conocimiento. Cada archivo generado es una señal pura lista para ser comprendida por la próxima generación de IAs."

# 🛸 Universal Ingestion Framework (UIF)

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Architecture: Multi-Layer](https://img.shields.io/badge/architecture-multi--layer-orange.svg)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)]()

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

## 🏗️ ARQUITECTURA TÉCNICA (Pipeline v2.0)

El motor opera en cuatro capas de refinamiento:

1. **Capa de Navegación (Scrapling + Scope Logic)**: Orquestación asíncrona con evasión de bloqueos y filtrado de alcance inteligente basado en la profundidad de la URL semilla.
2. **Capa de Purificación (Selectolax + nh3)**: Eliminación masiva de scripts, estilos y nodos irrelevantes en milisegundos, garantizando un HTML seguro y ligero.
3. **Capa de Conversión Híbrida**: Selección dinámica del mejor motor: **Trafilatura** para bloques de texto semántico y **MarkItDown** para layouts complejos y activos binarios.
4. **Capa de Refinamiento (ftfy + YAML)**: Normalización final del texto y enriquecimiento con metadatos estructurados para máxima compatibilidad con LLMs.

---

## 🚀 INSTALACIÓN Y USO

Este proyecto utiliza `uv` para una gestión de dependencias ultrarrápida y determinista.

### Pre-requisitos
```bash
# Instalar uv si no lo tienes
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Ejecución Interactiva (Recomendado)
Simplemente ejecuta el motor y sigue al asistente visual:
```bash
uv run engine.py
```

### Ejecución Automática (CLI)
Para flujos de trabajo automatizados o scripts de shell:
```bash
uv run engine.py https://ejemplo.com --workers 10 --scope smart --only-text
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

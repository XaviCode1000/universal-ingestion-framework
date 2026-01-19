# 🛸 Universal Ingestion Framework (UIF)

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Architecture: Multi-Layer](https://img.shields.io/badge/architecture-multi--layer-orange.svg)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)]()

UIF es un motor de ingesta de conocimiento de alta fidelidad diseñado para transformar infraestructuras web legacy y activos documentales binarios en bases de datos Markdown optimizadas para LLMs y sistemas RAG (Retrieval-Augmented Generation).

---

## 🛑 CAPACIDADES DE ÉLITE

- **Ingesta Multimodal**: Conversión proactiva de `PDF`, `DOCX`, `XLSX` y `PPTX` a Markdown semántico utilizando el motor **Microsoft MarkItDown**.
- **Aislamiento Multitenant**: Estructura de datos atomizada por dominio (`data/{domain}/`) para evitar colisiones en ingestas masivas.
- **Resiliencia Industrial**: Gestión de estado mediante **SQLite en modo WAL** (Write-Ahead Logging), permitiendo concurrencia real sin bloqueos de base de datos.
- **Poda Semántica**: Integración con **Scrapling** para extraer quirúrgicamente el contenido relevante (`main`, `article`), eliminando el 95% del ruido web (menús, footers).
- **UX Conversacional**: Asistente interactivo (Wizard) para configuración rápida sin necesidad de memorizar flags.

---

## 🏗️ ARQUITECTURA TÉCNICA

El motor opera en tres capas de refinamiento:

1. **Capa de Navegación (Scrapling)**: Orquestación de sesiones asíncronas con evasión de bloqueos e identificación semántica de contenedores.
2. **Capa de Conversión (MarkItDown)**: Traducción de fragmentos HTML y documentos binarios a un estándar Markdown de alta calidad de Microsoft.
3. **Capa de Auditoría (Polars)**: Procesamiento de resultados en tiempo real con análisis estadístico de fallos (HTTP 5xx, 4xx) para garantizar la integridad del 100% de la migración.

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
uv run engine.py https://ejemplo.com --workers 10 --only-text
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

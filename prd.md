# PRD: Universal Multimodal Ingestion Engine (Elite Edition)

## 1. Identidad del Proyecto
- **Nombre**: Universal Ingestion Framework (UIF)
- **Target**: Agnostico al dominio (Input vía CLI o Wizard Interactivo).
- **Propósito**: Transformación de infraestructuras web legacy y documentos binarios en bases de conocimiento optimizadas para LLMs (RAG-Ready).

## 2. Arquitectura de Ingesta (Multi-Layer Pipeline)

### Fase 1: Discovery & Orchestration
- **Motor**: Crawling asíncrono puro con `AsyncStealthySession`.
- **Checkpointing**: Persistencia atómica en SQLite con modo **WAL (Write-Ahead Logging)** para permitir concurrencia masiva de lectura/escritura sin bloqueos.
- **Namespacing**: Aislamiento total de datos por dominio (`data/{domain}/`).

### Fase 2: Purificación y Extracción Semántica Híbrida (The Signal Master)
- **Poda por Densidad de Enlaces**: Algoritmo dinámico que detecta y elimina bloques de navegación (menús, sidebars) basándose en la relación texto/link, superando las limitaciones de sitios no semánticos.
- **Detección de Título en Cascada**: Estrategia Waterfall (OG -> Title -> H1) ejecutada sobre el DOM original para evitar la contaminación de metadatos por footers o sidebars.
- **Sanitización de Seguridad**: Integración de `nh3` para asegurar la neutralidad del contenido.
- **Motor Híbrido**: Orquestación entre `Trafilatura` (excelencia semántica) y `MarkItDown` (fidelidad en documentos binarios).
- **Normalización Post-Procesado**: Aplicación de `ftfy` para garantizar texto libre de mojibake.

### Fase 3: Navegación Inteligente y Asset Intelligence
- **Control de Alcance (Scope)**: Estrategias de navegación granular (Smart, Strict, Broad) para evitar la explosión del crawling.
- **Multimodalidad**: Conversión proactiva de PDFs, Word, Excel y PowerPoint a Markdown enriquecido.
- **Control de Flujo**: Semáforos asíncronos y reintentos basados en el estado de la base de datos (Auto-healing).

## 3. Arsenal Tecnológico (The 2026 Stack)
- **Runtime**: Python 3.12+ (Optimizado para `uv`).
- **Navegación**: Scrapling (Stealthy) + Scope Control Logic.
- **Limpieza**: Selectolax + nh3 + ftfy.
- **Conversión**: Trafilatura + Microsoft MarkItDown + PDFMiner.six.
- **Data Layer**: SQLite WAL (Estado), Pydantic V2 (Contratos), Polars (Auditoría e Inteligencia de Datos), PyYAML.
- **UX**: `Questionary` (Wizard Interactivo) + `Rich` (Visualización Industrial).

## 4. Estructura de Salida Dinámica
```text
data/{domain_slug}/
├── content/                     # Markdown de páginas extraídas
├── media/
│   ├── images/                  # Activos visuales
│   └── docs/                    # Binarios + sus versiones .md extraídas
├── state_{domain_slug}.db       # Base de datos atómica de estado
└── migration_audit.jsonl        # Log de auditoría de bajo nivel
```

## 5. Estándares de Calidad y Éxito
- **Pureza de Señal**: El Markdown resultante debe tener un ratio de señal/ruido > 95% (H1 directo, sin menús).
- **Aislamiento**: Cero interferencia entre proyectos concurrentes.
- **Autocuración**: Capacidad de reanudar el 100% del trabajo pendiente tras un fallo de red o interrupción del usuario.
- **Eficiencia de Ingesta**: Capacidad para procesar 1000+ assets en una sola ejecución sin fugas de memoria.

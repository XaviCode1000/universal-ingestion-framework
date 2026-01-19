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

### Fase 2: Extracción Semántica Híbrida (The Signal Engine)
- **Poda Quirúrgica**: Uso de `Scrapling` para localizar el núcleo de contenido (`main`, `article`, etc.) eliminando el 90% del ruido visual.
- **Conversión de Alta Fidelidad**: Integración de **`MarkItDown` (Microsoft)** para transformar el residuo HTML y activos binarios en Markdown semántico.
- **Fallback de Resiliencia**: Mecanismo de extracción de texto plano automático si el motor de conversión encuentra estructuras corruptas.

### Fase 3: Asset Intelligence Pipeline
- **Multimodalidad**: Conversión proactiva de PDFs, Word, Excel y PowerPoint a Markdown gemelo durante la descarga.
- **Control de Flujo**: `Semaphore` dinámico y reintentos exponenciales para errores de infraestructura (HTTP 5xx).
- **Políticas de Ingesta**: Filtrado configurable vía flags (`--only-text`, `--only-images`, `--only-docs`).

## 3. Arsenal Tecnológico (The 2026 Stack)
- **Runtime**: Python 3.12+ (Optimizado para `uv`).
- **Core**: Scrapling (Navegación Stealthy).
- **Conversion**: Microsoft MarkItDown + PDFMiner.six.
- **Data Layer**: SQLite WAL (Estado), Pydantic V2 (Contratos), Polars (Auditoría e Inteligencia de Datos).
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

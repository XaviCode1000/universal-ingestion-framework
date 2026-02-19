📂 SKILLS.MD - Matriz de Competencias de Élite (UIF-ARE)

Este documento define las habilidades técnicas avanzadas y los patrones de ejecución que el agente debe aplicar para garantizar la excelencia arquitectónica.

1. 🧠 INGENIERÍA DE SOFTWARE AVANZADA

    Patrones de Diseño: Implementación de Strategy para diversos fetchers, Factory para esquemas Pydantic dinámicos y Observer para el monitoreo de tareas asíncronas.

    Clean Architecture: Separación estricta entre la lógica de extracción (Domain), el motor de red (Infrastructure) y la transformación de datos (Application).

    Optimización de Memoria: Uso de __slots__ en clases de bajo nivel y generadores (yield) para procesar flujos de datos infinitos sin saturar la RAM.

2. ⚡ DOMINIO ASÍNCRONO Y CONCURRENCIA (Python 3.12+)

    Task Management: Uso experto de asyncio.TaskGroup para gestionar ciclos de vida de tareas concurrentes con manejo de errores atómico.

    Control de Presión (Backpressure): Implementación de asyncio.Semaphore para limitar el paralelismo y evitar el baneo de IPs o el agotamiento de recursos del sistema.

    Graceful Shutdown: Diseño de sistemas que cierran conexiones SQLite y liberan memoria limpiamente ante señales SIGTERM o excepciones fatales.

3. 📊 DATA ENGINEERING CON POLARS (Elite Level)

    Lazy Evaluation: Uso obligatorio de .lazy() para construir planes de consulta optimizados antes de ejecutar .collect().

    Streaming & Parquet: Capacidad para procesar datasets que superan la memoria RAM mediante el uso de archivos Parquet y procesamiento por fragmentos (streaming mode).

    Auditoría Estructural: Implementación de verificaciones de integridad de datos entre el estado de aiosqlite y los archivos jsonl de auditoría.

4. 🕵️ EXTRACCIÓN Y EVASIÓN (Scrapling Expert)

    Fingerprinting: Configuración avanzada de impersonate para mimetizar comportamientos humanos (headers, TLS fingerprints, orden de cipher suites).

    Análisis Semántico: Uso de MarkItDown para convertir estructuras HTML complejas en Markdown limpio, facilitando la ingesta por parte de LLMs o sistemas RAG.

    Estrategias de Reintento: Lógica de reintento exponencial (Exponential Backoff) con jitter para evitar patrones detectables por WAFs (Cloudflare, Akamai).

5. 🛡️ CALIDAD Y RESILIENCIA

    Tipado Fantasma (Literal/Generic): Uso de typing.Literal y Generic para crear APIs internas auto-documentadas y seguras.

    Test-Driven Refactoring: Capacidad para generar tests de pytest que validen que la refactorización no ha introducido efectos colaterales.

    Zero-Downtime Schema: Gestión de migraciones en aiosqlite sin bloquear la base de datos, aprovechando el modo WAL.

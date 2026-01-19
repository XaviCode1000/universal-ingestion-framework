# PRD: Refactorización Arquitectónica - Argelia Scraper v3.0

**Documento de Requisitos de Producto - Nivel Production**  
**Fecha:** 2026-01-19  
**Autor:** Neo (Arquitecto Senior)  
**Estado:** Draft para Revisión  
**Prioridad:** P0 (Bloqueante para Escalabilidad)

---

## 📋 ÍNDICE

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Contexto y Justificación](#contexto-y-justificación)
3. [Objetivos Técnicos](#objetivos-técnicos)
4. [Arquitectura Propuesta](#arquitectura-propuesta)
5. [Plan de Implementación](#plan-de-implementación)
6. [Testing y QA](#testing-y-qa)
7. [Métricas de Éxito](#métricas-de-éxito)
8. [Riesgos y Mitigación](#riesgos-y-mitigación)
9. [Timeline y Recursos](#timeline-y-recursos)

---

## 1. RESUMEN EJECUTIVO

### 1.1 Problema Actual

El scraper actual (v2.2) funciona pero presenta **deuda técnica crítica** que impide:
- Escalabilidad más allá de 10 workers concurrentes
- Mantenimiento por equipos distribuidos
- Testing automatizado
- Configuración flexible entre entornos

### 1.2 Solución Propuesta

Refactorización completa hacia una **arquitectura modular** siguiendo principios SOLID, con:
- Sistema de configuración persistente (XDG-compliant)
- Connection pooling para SQLite
- Separación de responsabilidades en módulos independientes
- Logging profesional con rotación
- Suite de tests unitarios y de integración

### 1.3 Impacto Esperado

| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| Workers concurrentes estables | 5 | 20 | +300% |
| Tiempo de onboarding (nuevo dev) | 4 horas | 30 min | -87% |
| Cobertura de tests | 0% | 85% | ∞ |
| Configuración entre entornos | Manual | Automática | N/A |

---

## 2. CONTEXTO Y JUSTIFICACIÓN

### 2.1 Estado Actual del Código

**Archivo Monolítico:** 850 líneas en un solo archivo  
**Acoplamiento:** Alto (todas las clases dependen entre sí)  
**Configuración:** Hardcodeada en constantes globales  
**Persistencia:** Conexiones SQLite sin pool  
**Logging:** JSONL sin rotación (riesgo de saturar disco)

### 2.2 Pain Points Identificados

#### 🔴 Crítico
1. **PATH hardcodeado sin alternativas** → Usuarios no pueden elegir destino
2. **DNS override específico de un sitio** → Falla silenciosamente en otros dominios
3. **Fuga de conexiones SQLite** → Race conditions con >10 workers
4. **Logging sin límite** → Archivos de 8GB+ observados en producción

#### 🟡 Alto
5. **Mezcla de responsabilidades** → Clase Engine hace 7 cosas distintas
6. **Sin tests** → Imposible refactorizar con confianza
7. **Configuración no persistente** → Cada ejecución pide lo mismo

#### 🟢 Medio
8. **Duplicación de lógica de limpieza HTML** → 3 funciones hacen cosas similares
9. **Manejo de errores inconsistente** → Algunos se loguean, otros se ignoran
10. **Sin telemetría** → No sabemos dónde se gasta el tiempo real

### 2.3 ¿Por Qué Ahora?

- **Adopción creciente:** 3 equipos internos quieren usar el scraper
- **Caso de uso crítico:** Migración de 50K+ páginas de cliente enterprise
- **Deuda técnica acumulada:** Cada hotfix añade más complejidad

---

## 3. OBJETIVOS TÉCNICOS

### 3.1 Objetivos Primarios (MUST HAVE)

#### OBJ-1: Sistema de Configuración Profesional
**Descripción:** Implementar gestión de config siguiendo XDG Base Directory Spec  
**Criterio de Éxito:**
- [ ] Config cargable desde archivo YAML
- [ ] Variables de entorno tienen prioridad sobre archivo
- [ ] Wizard interactivo en primera ejecución
- [ ] Validación con Pydantic
- [ ] Paths expandibles (`~`, variables de entorno)

**Archivo:** `argelia_scraper/config.py`

**Schema Config:**
```python
class ScraperConfig(BaseModel):
    data_dir: Path                    # Dónde se guardan resultados
    cache_dir: Path                   # Cache temporal
    max_retries: int = 3              # Reintentos por URL
    timeout_seconds: int = 30         # Timeout HTTP
    default_workers: int = 5          # Concurrencia por defecto
    asset_workers: int = 8            # Workers específicos para assets
    dns_overrides: dict[str, str]     # Opcional: {"domain.com": "1.2.3.4"}
    log_rotation_mb: int = 50         # Tamaño antes de rotar logs
    log_level: str = "INFO"           # DEBUG|INFO|WARNING|ERROR
```

**Ubicaciones de búsqueda (en orden):**
1. `--config /ruta/personalizada/config.yaml` (CLI arg)
2. `$XDG_CONFIG_HOME/argelia-scraper/config.yaml`
3. `~/.config/argelia-scraper/config.yaml`
4. `/etc/argelia-scraper/config.yaml`
5. Valores por defecto (hardcoded)

**Variable de entorno para override:**
```bash
export SCRAPER_DATA_DIR=/mnt/external/scrapes
export SCRAPER_MAX_WORKERS=20
```

---

#### OBJ-2: Connection Pool para SQLite
**Descripción:** Evitar race conditions y mejorar throughput de DB  
**Criterio de Éxito:**
- [ ] Pool reutilizable de N conexiones (default: 5)
- [ ] Context manager async para acquire/release
- [ ] Configuración WAL + NORMAL synchronous
- [ ] Timeout configurable por conexión
- [ ] Cleanup automático al finalizar

**Archivo:** `argelia_scraper/db_pool.py`

**API Propuesta:**
```python
class SQLitePool:
    async def acquire(self) -> aiosqlite.Connection
    async def close_all(self) -> None
    
# Uso en StateManager:
async with self.pool.acquire() as db:
    await db.execute(...)
```

**Configuración de SQLite:**
```sql
PRAGMA journal_mode=WAL;          -- Write-Ahead Logging
PRAGMA synchronous=NORMAL;        -- Balance seguridad/velocidad
PRAGMA cache_size=-64000;         -- 64MB de cache
PRAGMA busy_timeout=5000;         -- 5s antes de fallar
```

---

#### OBJ-3: Separación de Responsabilidades (Modular Architecture)
**Descripción:** Dividir el monolito en módulos especializados  
**Criterio de Éxito:**
- [ ] Cada módulo tiene una responsabilidad única
- [ ] Testeable en aislamiento
- [ ] Interfaces claras entre módulos
- [ ] Sin dependencias circulares

**Estructura de Archivos:**
```
argelia_scraper/
├── __init__.py                 # Exports públicos
├── config.py                   # ScraperConfig
├── db_pool.py                  # SQLitePool
├── db_manager.py               # StateManager
├── models.py                   # Pydantic models (WebPage, etc.)
├── utils/
│   ├── __init__.py
│   ├── url_utils.py            # smart_url_normalize, slugify
│   ├── html_cleaner.py         # pre_clean_html, prune_by_density
│   └── text_utils.py           # ftfy wrappers, sanitización
├── extractors/
│   ├── __init__.py
│   ├── base.py                 # BaseExtractor (interface)
│   ├── text_extractor.py       # Trafilatura + MarkItDown
│   ├── metadata_extractor.py   # Open Graph, Schema.org
│   └── asset_extractor.py      # Descarga imágenes/PDFs
├── engine.py                   # ArgeliaMigrationEngine (orquestador)
├── cli.py                      # main() + argparse + wizard
└── version.py                  # __version__ = "3.0.0"
```

**Dependencias entre Módulos:**
```
cli.py → engine.py → [extractors/*, db_manager.py]
                  → config.py
                  → db_pool.py
```

---

#### OBJ-4: Logging Profesional
**Descripción:** Sistema de logs enterprise con rotación y niveles  
**Criterio de Éxito:**
- [ ] Rotación automática por tamaño
- [ ] Compresión de logs antiguos
- [ ] Retención configurable
- [ ] Formato estructurado (JSON para parseo)
- [ ] Niveles de log respetados

**Implementación:**
```python
from loguru import logger

logger.add(
    config.data_dir / "scraper_{time:YYYY-MM-DD}.log",
    rotation=f"{config.log_rotation_mb} MB",
    retention="10 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level=config.log_level,
    enqueue=True,  # Thread-safe
)
```

**Estructura de Logs:**
```json
{
  "timestamp": "2026-01-19T14:30:00Z",
  "level": "INFO",
  "module": "engine",
  "function": "process_page",
  "message": "Página procesada exitosamente",
  "context": {
    "url": "https://ejemplo.com/page1",
    "duration_ms": 1234,
    "markdown_size": 45678
  }
}
```

---

### 3.2 Objetivos Secundarios (SHOULD HAVE)

#### OBJ-5: Suite de Tests
**Descripción:** Cobertura mínima del 85% en módulos críticos  
**Framework:** pytest + pytest-asyncio + pytest-cov

**Estructura:**
```
tests/
├── conftest.py                 # Fixtures globales
├── test_config.py              # Tests de ScraperConfig
├── test_db_pool.py             # Tests de SQLitePool
├── test_url_utils.py           # Tests de normalización
├── test_html_cleaner.py        # Tests de limpieza
├── test_extractors/
│   ├── test_text.py
│   ├── test_metadata.py
│   └── test_assets.py
└── integration/
    └── test_full_scrape.py     # Test end-to-end
```

**Fixtures Requeridos:**
```python
@pytest.fixture
async def test_config():
    """Config temporal para tests"""
    
@pytest.fixture
async def mock_html_response():
    """HTML de prueba controlado"""
    
@pytest.fixture
async def temp_db():
    """SQLite en memoria para tests"""
```

---

#### OBJ-6: Telemetría y Profiling
**Descripción:** Métricas internas para optimización  
**Criterio de Éxito:**
- [ ] Tiempo promedio por página
- [ ] Distribución de errores por tipo
- [ ] Uso de memoria por worker
- [ ] Throughput de DB (queries/seg)

**Implementación con Prometheus (opcional):**
```python
from prometheus_client import Counter, Histogram

pages_processed = Counter('pages_processed_total', 'Total pages scraped')
page_duration = Histogram('page_processing_seconds', 'Time to process page')
```

---

## 4. ARQUITECTURA PROPUESTA

### 4.1 Diagrama de Componentes

```
```
SEMANA 1: Fundación
├─ Día 1-2: Estructura modular + ScraperConfig
├─ Día 3-4: SQLitePool + Tests
└─ Día 5: Logging setup + Documentación

SEMANA 2: Separación de Responsabilidades  
├─ Día 1-2: Utils (URL, HTML, Text)
├─ Día 3-4: Extractors (Text, Metadata, Assets)
└─ Día 5: StateManager refactor + Integration tests

SEMANA 3: Integración y Optimización
├─ Día 1-2: Engine refactor + Dependency injection
├─ Día 3: Pipeline optimization
├─ Día 4: DNS override configurable
└─ Día 5: Performance benchmarks

SEMANA 4: Testing y Hardening
├─ Día 1-2: Suite completa de tests
├─ Día 3: Error handling + Circuit breakers
├─ Día 4: Documentación completa
└─ Día 5: Release Candidate + Beta testing

SEMANA 5: Release y Rollout (Buffer)
├─ Día 1-2: Fixes de beta testing
├─ Día 3: Migration guide final
├─ Día 4: Release v3.0.0
└─ Día 5: Post-release monitoring
```

### 9.2 Recursos Necesarios

#### Equipo Core

| Rol | Dedicación | Horas/Semana | Total Horas |
|-----|-----------|--------------|-------------|
| **Senior Backend Engineer** | 100% | 40h | 200h |
| **QA Engineer** | 50% | 20h | 100h |
| **Tech Writer** | 20% | 8h | 40h |
| **Tech Lead (Reviewer)** | 10% | 4h | 20h |
| **TOTAL** | - | **72h/semana** | **360h** |

#### Herramientas y Servicios

**Desarrollo:**
- ✅ GitHub (Ya disponible)
- ✅ GitHub Actions (CI/CD) - Plan Free suficiente
- ⚠️ **Requerido:** pytest-cov, pre-commit, mypy (instalar con uv)

**Monitoreo Post-Release:**
- 🟡 **Opcional pero Recomendado:** Sentry (Free tier: 5K eventos/mes)
- 🟡 **Opcional:** Datadog o similar (para profiling en producción)

**Costo Estimado:**
- Herramientas: $0 (usando free tiers)
- Infraestructura: $0 (desarrollo local + GitHub Actions)
- **Costo Total Monetario: $0**

#### Hardware Mínimo (Para Load Testing)

```yaml
Test Machine:
  CPU: 4 cores mínimo (8 recomendado para 20 workers)
  RAM: 8GB mínimo (16GB recomendado)
  Storage: 50GB libres (para test de 10K URLs)
  Network: 100Mbps+ (para simular scraping real)
```

---

### 9.3 Dependencias Críticas Entre Fases

```
FASE 1 (Fundación)
└─ 🔒 Bloqueante para FASE 2
   └─ Requerido: SQLitePool funcionando
   └─ Requerido: ScraperConfig validado

FASE 2 (Modularización)  
└─ 🔒 Bloqueante para FASE 3
   └─ Requerido: Extractors testeados
   └─ Requerido: 0 dependencias circulares

FASE 3 (Optimización)
└─ 🔒 Bloqueante para FASE 4
   └─ Requerido: Throughput >50 pág/min
   └─ Requerido: Engine refactorizado

FASE 4 (Testing)
└─ 🔒 Bloqueante para RELEASE
   └─ Requerido: Cobertura >85%
   └─ Requerido: Load test passing
```

**REGLA DE ORO:** 
No se puede empezar una fase hasta que la anterior tenga **todos sus tests passing** y **code review aprobado**.

---

### 9.4 Puntos de Validación (Checkpoints)

**Estos son momentos OBLIGATORIOS de pausa para validación:**

#### ⚠️ Checkpoint 1.1 - Fin Día 1
**Validación:** ¿Estructura modular creada correctamente?  
**Criterio:** `pytest` debe encontrar y ejecutar tests dummy  
**Responsable:** Tech Lead  
**Tiempo:** 30 minutos

#### ⚠️ Checkpoint 1.5 - Fin Semana 1  
**Validación:** ¿Fundación sólida?  
**Criterio:** 
- Config funcional con wizard
- Pool probado con 100 queries concurrentes
- Logging rotando correctamente  
**Responsable:** Tech Lead + QA  
**Tiempo:** 1 hora (incluye demo)

#### ⚠️ Checkpoint 2.5 - Fin Semana 2
**Validación:** ¿Módulos independientes?  
**Criterio:**
- Cada extractor puede usarse standalone
- StateManager no tiene código duplicado
- 0 dependencias circulares (verificar con `pydeps`)  
**Responsable:** Tech Lead  
**Tiempo:** 1 hora

#### ⚠️ Checkpoint 3.4 - Jueves Semana 3
**Validación:** ¿Performance aceptable?  
**Criterio:**
- Throughput >50 pág/min en benchmark de 1000 URLs
- Uso de memoria <2GB con 20 workers  
**Responsable:** QA + Tech Lead  
**Tiempo:** 2 horas (incluye profiling)

#### ⚠️ Checkpoint 4.5 - Viernes Semana 4
**Validación:** ¿Listo para Beta?  
**Criterio:**
- Cobertura >85%
- Load test (10K URLs) sin crashes
- Documentación completa  
**Responsable:** Todo el equipo  
**Tiempo:** 2 horas (Go/No-Go meeting)

#### ⚠️ Checkpoint 5.2 - Martes Semana 5
**Validación:** ¿Listo para Release?  
**Criterio:**
- Fixes de beta completados
- Smoke tests en 3 OS passing
- Release notes aprobadas  
**Responsable:** Product Owner + Tech Lead  
**Tiempo:** 1 hora (Final Go/No-Go)

---

### 9.5 Plan de Contingencia (Buffers)

**Escenario 1: Un módulo crítico falla en testing**  
**Tiempo perdido:** 1-2 días  
**Acción:**
- Asignar Senior BE al 100% en ese módulo
- Posponer features no-críticos de siguiente fase
- Usar Día 5 de cada semana como buffer

**Escenario 2: Load test falla en Semana 4**  
**Tiempo perdido:** 2-3 días  
**Acción:**
- Activar Semana 5 como buffer completo
- Priorizar solo fixes de performance
- Considerar release como v3.0.0-beta si no se resuelve

**Escenario 3: Enfermedad/Ausencia de BE**  
**Tiempo perdido:** Variable  
**Acción:**
- QA asume tareas de testing simples
- Tech Lead asume desarrollo crítico (temporal)
- Extender timeline 1 semana si ausencia >3 días

**Escenario 4: Scope creep (Features nuevos solicitados)**  
**Acción:**
- **NO se aceptan features nuevos** durante refactorización
- Crear tickets en backlog para v3.1
- Mantener foco en objetivos del PRD

---

### 9.6 Estimación de Esfuerzo (Story Points)

**Conversión:** 1 Story Point = 4 horas de trabajo efectivo

| Fase | Tasks | Story Points | Horas | Días (8h) |
|------|-------|--------------|-------|-----------|
| FASE 1: Fundación | 12 | 20 SP | 80h | 10 días |
| FASE 2: Modularización | 18 | 32 SP | 128h | 16 días |
| FASE 3: Optimización | 14 | 24 SP | 96h | 12 días |
| FASE 4: Testing | 16 | 20 SP | 80h | 10 días |
| FASE 5: Release | 8 | 8 SP | 32h | 4 días |
| **TOTAL** | **68** | **104 SP** | **416h** | **52 días** |

**Con equipo de 72h/semana efectivas:**
- Timeline teórico: 416h / 72h = **5.8 semanas**
- Timeline con buffer (20%): **7 semanas** ✅

**Conclusión:** El cronograma de 5 semanas es **ajustado pero realista** si:
- No hay scope creep
- El equipo está 100% dedicado
- Los checkpoints se respetan

---

### 9.7 Calendario Real (Fechas Absolutas)

**Fecha de Inicio:** Lunes 20 de Enero, 2026

| Semana | Fechas | Fase | Entregable |
|--------|--------|------|------------|
| **W1** | 20-24 Enero | Fundación | feat/foundation branch |
| **W2** | 27-31 Enero | Modularización | feat/modularization branch |
| **W3** | 3-7 Febrero | Optimización | feat/optimization branch |
| **W4** | 10-14 Febrero | Testing | v3.0.0-rc1 |
| **W5** | 17-21 Febrero | Release | **v3.0.0 GA** 🚀 |

**Release Target:** Viernes 21 de Febrero, 2026

**Festivos/Días no laborables (ajustar según región):**
- ⚠️ Verificar calendario local antes de confirmar fechas
- Añadir 1 semana de buffer si hay festivos en este rango

---

### 9.8 Comunicación y Reportes

**Daily Standup:** 09:00 AM (15 minutos)
- ¿Qué hice ayer?
- ¿Qué haré hoy?
- ¿Tengo blockers?

**Weekly Demo:** Viernes 16:30 (30 minutos)
- Demo del milestone alcanzado
- Métricas de progreso (cobertura, performance)
- Decisiones para siguiente semana

**Checkpoint Reviews:** Según calendario (1-2 horas)
- Formato: Presentación técnica + Q&A
- Aprobadores deben estar presentes
- Salida: Go/No-Go explícito

**Canales de Comunicación:**
```
Slack:
  #argelia-refactor        → Updates diarios
  #argelia-alerts          → Errores críticos de CI/CD

GitHub:
  Issues                   → Bugs y tasks
  Pull Requests            → Code reviews
  Projects (Kanban)        → Tracking visual
  
Email:
  Weekly Summary           → Stakeholders no-técnicos
```

---

## 10. CHECKLIST DE ENTREGA

### 10.1 Definition of Done (DoD)

#### Código
- [ ] Todos los módulos en estructura propuesta
- [ ] 0 warnings de mypy (type checking)
- [ ] 0 errores de pylint (score >9.0)
- [ ] Formatted con black + isort
- [ ] Sin TODOs en código de producción

#### Tests
- [ ] Cobertura >85% en core modules
- [ ] 3 tests de integración passing
- [ ] 1 load test documentado (10K URLs)
- [ ] CI/CD verde en todas las branches

#### Documentación
- [ ] README.md actualizado
- [ ] MIGRATION_GUIDE.md completo
- [ ] API reference (autogenerada con Sphinx)
- [ ] Changelog siguiendo Keep a Changelog

#### Release
- [ ] Tag de versión `v3.0.0`
- [ ] PyPI package publicado
- [ ] Docker image actualizado
- [ ] Anuncio en canales internos

---

## 11. POST-LAUNCH

### 11.1 Monitoreo (Primeras 2 Semanas)

**Métricas a Observar:**
```python
# Dashboard Sentry/Datadog
- Error rate (target: <0.1%)
- P95 latency (target: <5s)
- Memory usage (target: <2GB)
- Crash rate (target: 0)
```

**Alertas:**
- Error rate >1% → Slack alert inmediato
- Memory >3GB → Investigar leak
- Crash → Rollback automático a v2.2

### 11.2 Iteraciones Post-Launch

**v3.1 (1 mes después):**
- Optimizaciones basadas en telemetría real
- Features solicitados por early adopters

**v3.2 (3 meses después):**
- Soporte para PostgreSQL (alternativa a SQLite)
- API REST para integración con otros sistemas

---

## 12. APÉNDICES

### A. Glosario Técnico

| Término | Definición |
|---------|-----------|
| **XDG** | X Desktop Group - Estándar para ubicación de archivos config en Linux |
| **WAL** | Write-Ahead Logging - Modo de journaling de SQLite |
| **Connection Pool** | Conjunto reutilizable de conexiones DB para reducir overhead |
| **Circuit Breaker** | Patrón que previene llamadas a servicios fallando |
| **Backoff Exponencial** | Estrategia de retry con delays crecientes (1s, 2s, 4s...) |

### B. Referencias

- [XDG Base Directory Spec](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html)
- [SQLite WAL Mode](https://www.sqlite.org/wal.html)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [pytest Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)

### C. Decisiones de Arquitectura (ADRs)

#### ADR-001: ¿Por Qué SQLite en Lugar de PostgreSQL?
**Contexto:** Necesitamos persistencia para estado de URLs  
**Decisión:** SQLite con WAL mode  
**Razones:**
- Zero-config (no requiere servidor externo)
- Suficiente para <100K URLs
- File-based = Fácil backup/restauración
- Pool de conexiones mitiga limitaciones

**Alternativa Descartada:** PostgreSQL  
**Motivo:** Overkill para caso de uso actual, añade complejidad de deployment

#### ADR-002: ¿Loguru vs Standard Logging?
**Contexto:** Necesitamos logging con rotación  
**Decisión:** Loguru  
**Razones:**
- API más simple que stdlib logging
- Rotación built-in
- Thread-safe por defecto
- Mejor DX (developer experience)

**Alternativa Descartada:** stdlib logging + TimedRotatingFileHandler  
**Motivo:** Configuración verbosa, sin compresión automática

---

## 13. FIRMA Y APROBACIÓN

**Preparado por:** Neo (Arquitecto Senior)  
**Fecha:** 2026-01-19  

**Requiere Aprobación de:**
- [ ] Tech Lead (Arquitectura)
- [ ] Engineering Manager (Timeline/Recursos)
- [ ] Product Owner (Priorización)

**Próximo Paso:** Crear GitHub Project con tasks del PRD────┐
│                   CLI Layer                     │
│  (cli.py - Argumentos + Wizard + Output)        │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│              Configuration Layer                │
│  (config.py - ScraperConfig + Validation)       │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│               Orchestration Layer               │
│  (engine.py - ArgeliaMigrationEngine)           │
│   - Gestión de colas                            │
│   - Coordinación de workers                     │
│   - Progress tracking                           │
└─────┬───────────────────────────────────┬───────┘
      │                                   │
      ▼                                   ▼
┌──────────────────┐           ┌──────────────────┐
│ Extraction Layer │           │ Persistence Layer│
│  (extractors/*)  │           │  (db_manager.py) │
│ - Text           │           │  - StateManager  │
│ - Metadata       │◄──────────┤  - SQLitePool    │
│ - Assets         │           │  - Transactions  │
└──────────────────┘           └──────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────┐
│                 Utilities Layer                 │
│  (utils/* - URL, HTML, Text processing)         │
└─────────────────────────────────────────────────┘
```

### 4.2 Flujo de Datos

```
1. Usuario ejecuta CLI
   ↓
2. CLI carga config (archivo/env/wizard)
   ↓
3. Engine inicializa con config
   ↓
4. StateManager crea/conecta DB via Pool
   ↓
5. Engine puebla colas desde DB
   ↓
6. Workers procesan URLs en paralelo:
   a. Fetcher descarga contenido
   b. HTMLCleaner poda basura
   c. TextExtractor → Markdown
   d. MetadataExtractor → Frontmatter
   e. AssetExtractor → Descarga media
   ↓
7. StateManager actualiza progreso en DB
   ↓
8. Engine genera reporte final
```

### 4.3 Interfaces Críticas

#### IExtractor (Base para todos los extractors)
```python
from abc import ABC, abstractmethod

class IExtractor(ABC):
    @abstractmethod
    async def extract(self, content: str, url: str) -> dict:
        """
        Extrae información específica del contenido
        
        Args:
            content: HTML crudo o respuesta HTTP
            url: URL original (para contexto)
        
        Returns:
            Dict con datos extraídos (estructura específica por tipo)
        """
        pass
```

#### IStateManager (Contrato de persistencia)
```python
class IStateManager(ABC):
    @abstractmethod
    async def add_url(self, url: str, status: MigrationStatus) -> None:
        pass
    
    @abstractmethod
    async def update_status(self, url: str, status: MigrationStatus) -> None:
        pass
    
    @abstractmethod
    async def get_pending_urls(self) -> List[str]:
        pass
```

---

## 5. PLAN DE IMPLEMENTACIÓN

### 5.1 Fases del Proyecto

#### FASE 1: Fundación (Semana 1)
**Objetivo:** Establecer infraestructura base sin romper funcionalidad actual

**Tareas:**
1. [ ] **Crear estructura de directorios modular**
   - Mover código a `argelia_scraper/` package
   - Crear `__init__.py` con exports
   
2. [ ] **Implementar ScraperConfig completo**
   - Archivo: `config.py`
   - Tests: `tests/test_config.py`
   - Wizard interactivo funcional
   
3. [ ] **Implementar SQLitePool**
   - Archivo: `db_pool.py`
   - Tests: `tests/test_db_pool.py`
   - Benchmark: Comparar throughput antes/después
   
4. [ ] **Setup de logging con loguru**
   - Configurar rotación
   - Migrar prints a logger
   
**Entregables:**
- Branch `feat/foundation` con tests passing
- Documento de migración de config para usuarios actuales

---

#### FASE 2: Separación de Responsabilidades (Semana 2)

**Objetivo:** Modularizar código sin cambiar API pública

**Tareas:**
1. [ ] **Extraer Utils**
   - `utils/url_utils.py`: Mover `smart_url_normalize`, `slugify`
   - `utils/html_cleaner.py`: Mover `pre_clean_html`, `prune_by_density`
   - `utils/text_utils.py`: Wrappers de ftfy
   - Tests unitarios para cada función
   
2. [ ] **Crear Extractors**
   - `extractors/base.py`: Interface `IExtractor`
   - `extractors/text_extractor.py`: Lógica Trafilatura + MarkItDown
   - `extractors/metadata_extractor.py`: Open Graph, Schema.org
   - `extractors/asset_extractor.py`: Descarga + conversión
   - Tests con HTML fixtures
   
3. [ ] **Refactorizar StateManager**
   - Integrar SQLitePool
   - Separar lógica de queries en métodos privados
   - Agregar transacciones explícitas
   
**Entregables:**
- Todos los módulos funcionando independientemente
- Cobertura de tests >80% en nuevos módulos

---

#### FASE 3: Integración y Optimización (Semana 3)

**Objetivo:** Unir módulos y optimizar pipeline

**Tareas:**
1. [ ] **Refactorizar ArgeliaMigrationEngine**
   - Inyectar dependencias (config, state, extractors)
   - Delegar procesamiento a extractors
   - Simplificar lógica de workers
   
2. [ ] **Optimizar Pipeline de Extracción**
   - Paralelizar extractors independientes
   - Cache de resultados de limpieza HTML
   - Batch inserts en DB
   
3. [ ] **Implementar DNS Override Configurable**
   - Leer de `config.dns_overrides`
   - Construir args de browser dinámicamente
   
**Entregables:**
- Engine refactorizado con 50% menos líneas
- Benchmarks de rendimiento (antes/después)

---

#### FASE 4: Testing y Hardening (Semana 4)

**Objetivo:** Asegurar robustez y preparar para producción

**Tareas:**
1. [ ] **Suite de Tests Completa**
   - Tests unitarios: 85% cobertura
   - Tests de integración: 3 escenarios críticos
   - Tests de carga: 20 workers, 1000 URLs
   
2. [ ] **Manejo de Errores Mejorado**
   - Excepciones tipadas por categoría
   - Retry con backoff exponencial
   - Circuit breaker para sitios problemáticos
   
3. [ ] **Documentación**
   - README actualizado con nueva arquitectura
   - Docstrings en todos los módulos públicos
   - Guía de migración desde v2.2
   
**Entregables:**
- Suite de tests passing al 100%
- Documentación completa
- Release candidate v3.0.0-rc1

---

### 5.2 Estrategia de Migración

#### Para Usuarios Actuales

**Opción 1: Migración Manual (Recomendado)**
```bash
# 1. Backup del proyecto actual
cp -r scraper_v2 scraper_v2_backup

# 2. Instalar nueva versión
uv pip install argelia-scraper==3.0.0

# 3. Ejecutar wizard de config
argelia-scraper --setup

# 4. Migrar datos antiguos (script provisto)
python migrate_v2_to_v3.py --old-data ./data --new-config ~/.config/argelia-scraper/config.yaml
```

**Opción 2: Coexistencia (Transición Gradual)**
```bash
# Mantener v2.2 para proyectos en curso
python scraper_old.py --url https://sitio1.com

# Usar v3.0 para nuevos proyectos
argelia-scraper scrape --url https://sitio2.com
```

#### Breaking Changes

| Feature | v2.2 | v3.0 | Acción Requerida |
|---------|------|------|------------------|
| Path de datos | `./data` hardcoded | Configurable | Ejecutar wizard o set `SCRAPER_DATA_DIR` |
| CLI args | `--only-text` | `--extract text` | Actualizar scripts |
| DB schema | Sin versión | Versionado | Auto-migración en primera ejecución |
| Imports | `from scraper import Engine` | `from argelia_scraper import Engine` | Actualizar imports |

---

## 6. TESTING Y QA

### 6.1 Estrategia de Testing

#### Tests Unitarios (Target: 85% cobertura)
**Herramientas:** pytest, pytest-asyncio, pytest-cov

**Módulos Críticos:**
- [ ] `config.py`: 100% (carga, validación, guardado)
- [ ] `db_pool.py`: 95% (acquire, release, cleanup)
- [ ] `utils/url_utils.py`: 100% (casos edge de URLs)
- [ ] `utils/html_cleaner.py`: 90% (distintos tipos de basura)
- [ ] `extractors/text_extractor.py`: 85% (formatos variados)

**Ejemplo de Test:**
```python
@pytest.mark.asyncio
async def test_url_normalize_double_encoding():
    """Verifica que no se encode dos veces"""
    url = "https://site.com/búsqueda?q=café con leche"
    normalized = smart_url_normalize(url)
    
    # No debe tener %25 (encoding de %)
    assert "%25" not in normalized
    # Debe manejar tildes correctamente
    assert "caf%C3%A9" in normalized or "café" in normalized
```

---

#### Tests de Integración (Escenarios Críticos)

**Escenario 1: Scraping End-to-End**
```python
@pytest.mark.integration
async def test_full_scrape_small_site(tmp_path):
    """Scraping completo de un sitio de 10 páginas"""
    config = ScraperConfig(data_dir=tmp_path, default_workers=2)
    engine = ArgeliaMigrationEngine(config, url="http://example-test.com")
    
    await engine.run()
    
    # Assertions
    assert (tmp_path / "content").exists()
    assert len(list((tmp_path / "content").glob("*.md"))) == 10
    assert engine.pages_completed == 10
```

**Escenario 2: Recuperación de Fallos**
```python
@pytest.mark.integration
async def test_retry_on_network_failure(mock_server):
    """Verifica que URLs fallidas se reintentan"""
    mock_server.add_failure("http://flaky.com/page1", times=2)
    
    engine = ArgeliaMigrationEngine(...)
    await engine.run()
    
    # Debe haber intentado 3 veces (1 inicial + 2 retries)
    assert mock_server.request_count("http://flaky.com/page1") == 3
```

**Escenario 3: Concurrencia Alta**
```python
@pytest.mark.slow
async def test_high_concurrency_no_corruption():
    """20 workers procesando 100 URLs simultáneas"""
    config = ScraperConfig(default_workers=20)
    engine = ArgeliaMigrationEngine(config, ...)
    
    await engine.run()
    
    # Verificar integridad de DB (no race conditions)
    async with aiosqlite.connect(engine.state.db_path) as db:
        cursor = await db.execute("SELECT COUNT(DISTINCT url) FROM urls")
        unique_urls = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM urls")
        total_urls = (await cursor.fetchone())[0]
        
        assert unique_urls == total_urls  # No duplicados
```

---

### 6.2 Testing de Carga

**Objetivo:** Validar que el sistema aguanta casos enterprise

**Perfil de Carga:**
- 10,000 URLs únicas
- 20 workers concurrentes
- Mix de contenido: 70% HTML, 20% imágenes, 10% PDFs
- Duración estimada: 2 horas

**Métricas a Monitorear:**
```python
# Script de monitoreo
import psutil
import time

def monitor_scraper(pid):
    process = psutil.Process(pid)
    
    while process.is_running():
        print(f"CPU: {process.cpu_percent()}%")
        print(f"RAM: {process.memory_info().rss / 1024**2:.2f} MB")
        print(f"Threads: {process.num_threads()}")
        print(f"Open Files: {len(process.open_files())}")
        time.sleep(30)
```

**Criterios de Éxito:**
- [ ] CPU <80% promedio
- [ ] RAM <2GB (sin memory leaks)
- [ ] Sin file descriptor leaks
- [ ] Throughput >50 páginas/min

---

## 7. MÉTRICAS DE ÉXITO

### 7.1 KPIs Técnicos

| Métrica | Baseline (v2.2) | Target (v3.0) | Medición |
|---------|-----------------|---------------|----------|
| **Rendimiento** |
| Workers estables | 5 | 20 | Load test 1h |
| Throughput | 30 pág/min | 50 pág/min | Benchmark real |
| Latencia P95 | 8s | 5s | Prometheus |
| **Confiabilidad** |
| Tasa de fallos | 5% | <1% | Logs análisis |
| Recovery automático | 60% | 95% | Retry tests |
| **Mantenibilidad** |
| Cobertura tests | 0% | 85% | pytest-cov |
| Complejidad ciclomática | 45 | <15 | radon |
| Líneas por función | 80 avg | <30 avg | pylint |
| **Usabilidad** |
| Tiempo setup nuevo dev | 4h | 30min | Onboarding real |
| Config manual | Sí | No | Wizard funcional |

### 7.2 Validación de Negocio

**Caso de Uso Real:** Migración sitio enterprise (50K páginas)

**Checklist de Validación:**
- [ ] Completado en <48h (vs 1 semana actual)
- [ ] 0 intervenciones manuales
- [ ] Logs analizables para reportes cliente
- [ ] Todos los assets críticos descargados
- [ ] Markdown de calidad suficiente para RAG

---

## 8. RIESGOS Y MITIGACIÓN

### 8.1 Riesgos Técnicos

#### RIESGO-1: Breaking Changes Inesperados
**Probabilidad:** Alta  
**Impacto:** Alto  
**Mitigación:**
- Mantener v2.2 en branch `legacy` por 6 meses
- Script de migración automático
- Release notes detallados
- Beta testing con 3 usuarios clave antes de GA

#### RIESGO-2: Regresión de Performance
**Probabilidad:** Media  
**Impacto:** Crítico  
**Mitigación:**
- Benchmarks obligatorios en CI/CD
- Si rendimiento cae >10%, bloquear merge
- Profiling con py-spy en cada fase

#### RIESGO-3: SQLite Pool Bugs
**Probabilidad:** Media  
**Impacto:** Alto  
**Mitigación:**
- Usar librerías battle-tested (aiosqlite + asyncio.Queue)
- Load tests específicos para pool
- Fallback a conexiones directas si pool falla

#### RIESGO-4: Scope Creep
**Probabilidad:** Alta  
**Impacto:** Timeline  
**Mitigación:**
- PRD firmado por stakeholders
- Tablero Kanban con límites WIP
- Reuniones de checkpoint cada 3 días

---

### 8.2 Riesgos de Proyecto

#### RIESGO-5: Desarrollador Bloqueado
**Probabilidad:** Media  
**Impacto:** Timeline  
**Mitigación:**
- Pair programming en componentes críticos
- Code reviews dentro de 4h
- Documentación inline clara

#### RIESGO-6: Testing Insuficiente
**Probabilidad:** Media  
**Impacto:** Calidad  
**Mitigación:**
- Gate de cobertura en CI (mínimo 80%)
- QA manual de casos edge antes de release
- Beta testing 1 semana antes de GA

---

## 9. TIMELINE Y RECURSOS

### 9.1 Cronograma Detallado

#### Formato de Lectura
- **[BE]** = Backend Engineer (Full-time)
- **[QA]** = QA Engineer (Part-time)
- **[TW]** = Tech Writer (Part-time)
- **⚠️** = Punto de validación obligatorio
- **🔒** = Tarea bloqueante para siguiente fase

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           SEMANA 1: FUNDACIÓN                              │
│                    Objetivo: Infraestructura sin romper v2.2               │
└────────────────────────────────────────────────────────────────────────────┘

DÍA 1 (Lunes) - Setup Inicial
├─ 09:00-10:00 [BE] Kickoff + Revisión del PRD
├─ 10:00-12:00 [BE] 🔒 Crear estructura modular de directorios
│                    Output: argelia_scraper/__init__.py con exports
├─ 12:00-13:00      ALMUERZO
├─ 13:00-15:00 [BE] Mover modelos a models.py (sin cambiar lógica)
├─ 15:00-17:00 [BE] Setup de pytest + conftest.py base
└─ 17:00-17:30 [BE] ⚠️ Checkpoint: Tests dummy passing en CI

DÍA 2 (Martes) - Sistema de Configuración
├─ 09:00-11:00 [BE] Implementar ScraperConfig completo
│                    Archivo: config.py (150 líneas aprox)
├─ 11:00-12:00 [BE] Wizard interactivo con questionary
├─ 12:00-13:00      ALMUERZO
├─ 13:00-15:00 [BE] Tests de config.py (10 test cases)
│                    - test_load_from_yaml()
│                    - test_env_override()
│                    - test_wizard_flow()
│                    - test_path_expansion()
├─ 15:00-16:30 [QA] Review de tests + casos edge
└─ 16:30-17:00 [BE] ⚠️ Code Review: config.py (aprobar antes de continuar)

DÍA 3 (Miércoles) - Connection Pool
├─ 09:00-11:30 [BE] 🔒 Implementar SQLitePool
│                    Archivo: db_pool.py (120 líneas aprox)
│                    Features:
│                    - async context manager
│                    - pool de 5 conexiones default
│                    - PRAGMA optimizations
├─ 11:30-12:00 [BE] Documentar API de pool (docstrings)
├─ 12:00-13:00      ALMUERZO
├─ 13:00-15:00 [BE] Tests de db_pool.py (8 test cases)
│                    - test_acquire_release()
│                    - test_concurrent_access()
│                    - test_pool_exhaustion()
├─ 15:00-16:00 [BE] Benchmark: Pool vs Direct connections
└─ 16:00-17:00 [QA] Load test del pool (100 concurrent queries)

DÍA 4 (Jueves) - Logging Setup
├─ 09:00-10:30 [BE] Configurar loguru con rotación
│                    - Migrar todos los print() a logger
│                    - Setup de niveles (DEBUG, INFO, WARNING)
├─ 10:30-12:00 [BE] Integrar logger en StateManager
├─ 12:00-13:00      ALMUERZO
├─ 13:00-14:30 [BE] Tests de logging (verificar rotación)
├─ 14:30-16:00 [TW] Iniciar README.md (Sección: Getting Started)
└─ 16:00-17:00 [BE] ⚠️ Integration test: Config + Pool + Logging

DÍA 5 (Viernes) - Consolidación Fase 1
├─ 09:00-11:00 [BE] Refactorizar StateManager para usar Pool
│                    Cambio crítico: Reemplazar aiosqlite.connect()
│                    con self.pool.acquire()
├─ 11:00-12:00 [BE] Tests de StateManager refactorizado
├─ 12:00-13:00      ALMUERZO
├─ 13:00-14:00 [QA] Smoke tests completos de Fase 1
├─ 14:00-15:30 [BE] Fix de bugs encontrados por QA
├─ 15:30-16:30 [TW] Documentar cambios de Fase 1
└─ 16:30-17:00      ⚠️ MILESTONE 1: Demo interno + Retrospectiva

ENTREGABLES SEMANA 1:
✅ Estructura modular funcional
✅ ScraperConfig con wizard operativo
✅ SQLitePool integrado y testeado
✅ Logging con rotación activo
✅ Cobertura de tests: >80% en módulos nuevos
✅ Branch feat/foundation listo para merge


┌────────────────────────────────────────────────────────────────────────────┐
│                  SEMANA 2: SEPARACIÓN DE RESPONSABILIDADES                 │
│              Objetivo: Modularizar sin cambiar comportamiento              │
└────────────────────────────────────────────────────────────────────────────┘

DÍA 1 (Lunes) - Utils Layer
├─ 09:00-10:30 [BE] Crear utils/url_utils.py
│                    Mover: smart_url_normalize(), slugify()
├─ 10:30-12:00 [BE] Tests de url_utils.py (12 casos edge)
│                    URLs con: tildes, espacios, %encode doble,
│                    queries complejas, fragments
├─ 12:00-13:00      ALMUERZO
├─ 13:00-14:30 [BE] Crear utils/text_utils.py
│                    Wrappers de ftfy con logging
├─ 14:30-16:00 [BE] Tests de text_utils.py
└─ 16:00-17:00 [QA] Verificar que utils NO tienen side effects

DÍA 2 (Martes) - HTML Cleaner
├─ 09:00-11:00 [BE] 🔒 Crear utils/html_cleaner.py
│                    Mover: pre_clean_html(), prune_by_density()
│                    get_text_density()
├─ 11:00-12:00 [BE] Optimizar algoritmo de poda (si es posible)
├─ 12:00-13:00      ALMUERZO
├─ 13:00-15:30 [BE] Tests con HTML fixtures reales (10 sitios)
│                    - Sitio con menús gigantes
│                    - Sitio con popups
│                    - Sitio con sidebar
│                    - Sitio limpio (no debe romper)
├─ 15:30-16:30 [QA] Review de limpieza (inspección manual)
└─ 16:30-17:00 [BE] ⚠️ Code Review: Utils layer completo

DÍA 3 (Miércoles) - Extractors Base
├─ 09:00-10:30 [BE] Crear extractors/base.py
│                    Interface IExtractor (abstract class)
├─ 10:30-12:00 [BE] Crear extractors/text_extractor.py
│                    Mover lógica de Trafilatura + MarkItDown
├─ 12:00-13:00      ALMUERZO
├─ 13:00-15:00 [BE] Tests de text_extractor con 5 formatos HTML
│                    - Artículo blog
│                    - Página corporativa
│                    - Documentación técnica
│                    - FAQ
│                    - Landing page
├─ 15:00-16:30 [BE] Crear extractors/metadata_extractor.py
└─ 16:30-17:00 [BE] Tests de metadata (Open Graph, Schema.org)

DÍA 4 (Jueves) - Asset Extractor
├─ 09:00-11:00 [BE] Crear extractors/asset_extractor.py
│                    Lógica de descarga + conversión PDF/Office
├─ 11:00-12:00 [BE] Implementar filtrado por tipo (only_images, etc)
├─ 12:00-13:00      ALMUERZO
├─ 13:00-15:00 [BE] Tests con mocks de descarga
│                    - Imagen válida
│                    - PDF válido
│                    - Archivo corrupto
│                    - 404 en asset
├─ 15:00-16:00 [QA] Integration test: Descargar 100 assets reales
└─ 16:00-17:00 [BE] ⚠️ Code Review: Extractors completos

DÍA 5 (Viernes) - StateManager Refactor
├─ 09:00-11:30 [BE] Refactorizar StateManager para separar concerns
│                    Métodos privados para queries complejas
│                    Transacciones explícitas
├─ 11:30-12:00 [BE] Documentar API pública de StateManager
├─ 12:00-13:00      ALMUERZO
├─ 13:00-14:30 [BE] Tests de StateManager (15 casos)
├─ 14:30-15:30 [QA] Integration tests: Extractors + StateManager
├─ 15:30-16:30 [TW] Actualizar README con nueva arquitectura
└─ 16:30-17:00      ⚠️ MILESTONE 2: Review de arquitectura modular

ENTREGABLES SEMANA 2:
✅ Módulo utils completo (url, text, html)
✅ Extractors funcionando independientemente
✅ StateManager refactorizado
✅ Cobertura de tests: >85% acumulado
✅ 0 dependencias circulares (verificar con pydeps)
✅ Branch feat/modularization listo


┌────────────────────────────────────────────────────────────────────────────┐
│                  SEMANA 3: INTEGRACIÓN Y OPTIMIZACIÓN                      │
│           Objetivo: Unir módulos y mejorar performance crítico             │
└────────────────────────────────────────────────────────────────────────────┘

DÍA 1 (Lunes) - Engine Refactor (Parte 1)
├─ 09:00-10:00 [BE] Diseñar dependency injection para Engine
│                    Constructor: (config, state, extractors)
├─ 10:00-12:00 [BE] 🔒 Refactorizar __init__ de Engine
│                    Inyectar todas las dependencias
├─ 12:00-13:00      ALMUERZO
├─ 13:00-15:00 [BE] Refactorizar process_page() para usar extractors
│                    Separar: fetch → clean → extract → persist
├─ 15:00-16:30 [BE] Tests de process_page() con mocks
└─ 16:30-17:00 [BE] Benchmark: Comparar velocidad con v2.2

DÍA 2 (Martes) - Engine Refactor (Parte 2)
├─ 09:00-11:00 [BE] Refactorizar download_asset() para usar AssetExtractor
├─ 11:00-12:00 [BE] Simplificar lógica de workers (delegar a extractors)
├─ 12:00-13:00      ALMUERZO
├─ 13:00-15:00 [BE] Implementar DNS override configurable
│                    Leer de config.dns_overrides
│                    Construir browser_args dinámicamente
├─ 15:00-16:30 [BE] Tests con DNS custom
└─ 16:30-17:00 [QA] ⚠️ Smoke test: Scraping end-to-end

DÍA 3 (Miércoles) - Optimización de Pipeline
├─ 09:00-11:00 [BE] Implementar paralelización de extractors
│                    asyncio.gather([text, metadata, assets])
├─ 11:00-12:00 [BE] Cache de resultados de limpieza HTML
│                    LRU cache para evitar re-procesar
├─ 12:00-13:00      ALMUERZO
├─ 13:00-14:30 [BE] Implementar batch inserts en StateManager
│                    Agrupar 50 URLs antes de escribir DB
├─ 14:30-16:00 [BE] Profiling con py-spy
│                    Identificar bottlenecks reales
├─ 16:00-17:00 [BE] Optimizar top 3 bottlenecks detectados

DÍA 4 (Jueves) - Scope Control y Edge Cases
├─ 09:00-10:30 [BE] Mejorar lógica de Scope (STRICT/BROAD/SMART)
│                    Asegurar que respeta config correctamente
├─ 10:30-12:00 [BE] Tests de scope con sitios reales
│                    - Blog en subdirectorio
│                    - Portal con múltiples secciones
│                    - Sitio multi-idioma
├─ 12:00-13:00      ALMUERZO
├─ 13:00-15:00 [BE] Implementar circuit breaker para sitios lentos
│                    Si 5 timeouts seguidos → pausar dominio 5min
├─ 15:00-16:30 [QA] Load test con 20 workers
└─ 16:30-17:00 [BE] ⚠️ Performance review: Throughput >50 pág/min

DÍA 5 (Viernes) - Consolidación Fase 3
├─ 09:00-11:00 [BE] Integration test completo (1000 URLs)
├─ 11:00-12:00 [BE] Fix de bugs encontrados
├─ 12:00-13:00      ALMUERZO
├─ 13:00-14:30 [QA] Verificar que NO hay regresión vs v2.2
│                    Comparar output de 10 sitios reales
├─ 14:30-16:00 [TW] Documentar optimizaciones y benchmarks
└─ 16:00-17:00      ⚠️ MILESTONE 3: Demo de performance

ENTREGABLES SEMANA 3:
✅ Engine refactorizado (50% menos líneas)
✅ Pipeline optimizado (throughput +40%)
✅ DNS override configurable
✅ Circuit breaker implementado
✅ Benchmarks documentados
✅ Branch feat/optimization listo


┌────────────────────────────────────────────────────────────────────────────┐
│                    SEMANA 4: TESTING Y HARDENING                           │
│              Objetivo: Asegurar calidad enterprise-grade                   │
└────────────────────────────────────────────────────────────────────────────┘

DÍA 1 (Lunes) - Suite de Tests Unitarios
├─ 09:00-10:00 [QA] Audit de cobertura actual (debe estar >80%)
├─ 10:00-12:00 [BE] Completar tests faltantes para llegar a 85%
│                    Foco en: error handling, edge cases
├─ 12:00-13:00      ALMUERZO
├─ 13:00-15:00 [QA] Diseñar 3 escenarios de integration tests
│                    1. Scraping end-to-end (10 páginas)
│                    2. Retry con network failures
│                    3. High concurrency (20 workers)
├─ 15:00-17:00 [BE] Implementar integration tests diseñados por QA

DÍA 2 (Martes) - Error Handling
├─ 09:00-10:30 [BE] Crear excepciones tipadas por categoría
│                    - NetworkError
│                    - ParsingError
│                    - StorageError
├─ 10:30-12:00 [BE] Implementar retry con backoff exponencial
│                    1s → 2s → 4s → 8s (max 3 retries)
├─ 12:00-13:00      ALMUERZO
├─ 13:00-15:00 [BE] Mejorar logging de errores (incluir context)
├─ 15:00-16:30 [QA] Tests de error scenarios (15 casos)
└─ 16:30-17:00 [BE] ⚠️ Code Review: Error handling

DÍA 3 (Miércoles) - Load Testing
├─ 09:00-12:00 [QA] 🔒 Ejecutar load test completo
│                    10,000 URLs | 20 workers | 2 horas
│                    Monitorear: CPU, RAM, open files
├─ 12:00-13:00      ALMUERZO
├─ 13:00-15:00 [BE] Analizar resultados + Fix de memory leaks
├─ 15:00-16:30 [QA] Re-run load test (validar fixes)
└─ 16:30-17:00      ⚠️ Checkpoint: ¿Pasó criterios de performance?

DÍA 4 (Jueves) - Documentación
├─ 09:00-11:00 [TW] README.md completo
│                    - Installation
│                    - Quick Start
│                    - Configuration
│                    - CLI Usage
│                    - Troubleshooting
├─ 11:00-12:00 [TW] MIGRATION_GUIDE.md (v2.2 → v3.0)
├─ 12:00-13:00      ALMUERZO
├─ 13:00-14:30 [TW] API Reference (autogen con Sphinx)
├─ 14:30-16:00 [BE] Docstrings en todos los módulos públicos
├─ 16:00-17:00 [TW] CHANGELOG.md siguiendo Keep a Changelog

DÍA 5 (Viernes) - Release Candidate
├─ 09:00-10:00 [BE] Tag de versión v3.0.0-rc1
├─ 10:00-11:00 [BE] Build de package para PyPI (test)
├─ 11:00-12:00 [QA] Instalación desde scratch (validar wizard)
├─ 12:00-13:00      ALMUERZO
├─ 13:00-15:00      Beta testing con 3 usuarios clave
│                    Recoger feedback en GitHub Issues
├─ 15:00-16:30 [BE] Triage de feedback + Quick fixes
└─ 16:30-17:00      ⚠️ MILESTONE 4: Go/No-Go para release

ENTREGABLES SEMANA 4:
✅ Cobertura de tests: >85%
✅ Load test passing (10K URLs sin crashes)
✅ Documentación completa
✅ Release Candidate publicado
✅ Feedback de beta testing procesado
✅ Branch feat/testing listo


┌────────────────────────────────────────────────────────────────────────────┐
│                    SEMANA 5: RELEASE Y ROLLOUT (Buffer)                    │
│                  Objetivo: Lanzamiento estable a producción                │
└────────────────────────────────────────────────────────────────────────────┘

DÍA 1 (Lunes) - Fixes Post-Beta
├─ 09:00-12:00 [BE] Implementar fixes de feedback crítico
│                    (Bugs P0 y P1 del beta testing)
├─ 12:00-13:00      ALMUERZO
├─ 13:00-15:00 [QA] Regression test completo
├─ 15:00-17:00 [BE] Actualizar docs con cambios finales

DÍA 2 (Martes) - Pre-Release Validation
├─ 09:00-11:00 [QA] Final smoke tests en 3 entornos
│                    - Linux (Fedora)
│                    - macOS
│                    - Windows (WSL)
├─ 11:00-12:00 [BE] Build final de package
├─ 12:00-13:00      ALMUERZO
├─ 13:00-15:00 [TW] Preparar release notes
├─ 15:00-16:00 [BE] Tag de versión v3.0.0 (final)
└─ 16:00-17:00      ⚠️ Final Go/No-Go meeting

DÍA 3 (Miércoles) - Release Day 🚀
├─ 09:00-10:00 [BE] Publicar en PyPI
│                    uv pip install argelia-scraper==3.0.0
├─ 10:00-11:00 [BE] Actualizar Docker image
├─ 11:00-12:00      Anuncio interno (Slack, Email)
├─ 12:00-13:00      ALMUERZO (Celebración 🎉)
├─ 13:00-15:00      Monitoreo activo (Sentry, logs)
├─ 15:00-17:00      Soporte a early adopters

DÍA 4 (Jueves) - Post-Release Monitoring
├─ 09:00-12:00      Analizar métricas de uso real
│                    - Error rate
│                    - Performance real
│                    - Adoption rate
├─ 12:00-13:00      ALMUERZO
├─ 13:00-15:00 [BE] Hotfix de issues críticos (si existen)
├─ 15:00-17:00 [TW] Documentar issues comunes (FAQ)

DÍA 5 (Viernes) - Retrospectiva
├─ 09:00-11:00      Team retrospective
│                    - ¿Qué salió bien?
│                    - ¿Qué mejorar?
│                    - Lecciones aprendidas
├─ 11:00-12:00      Planificar v3.1 (próximo sprint)
├─ 12:00-13:00      ALMUERZO
├─ 13:00-15:00      Documentar decisiones de arquitectura (ADRs)
├─ 15:00-16:00      Actualizar roadmap
└─ 16:00-17:00      ⚠️ Cierre formal del proyecto

ENTREGABLES SEMANA 5:
✅ v3.0.0 publicado en PyPI
✅ Docker image actualizado
✅ 0 bugs críticos en producción
✅ Documentación post-release completa
✅ Retrospectiva documentada
✅ Roadmap v3.1 definido
```

---

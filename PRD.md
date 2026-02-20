Aquí tienes el **Product Requirements Document (PRD)** para la actualización del *Universal Ingestion Framework*, incorporando y aprobando todas las notas críticas, medias y bajas identificadas en la auditoría técnica.

---

# 📄 PRD: Universal Ingestion Framework v4.0 "Resilience & Scale"

**Estado:** Borrador Aprobado para Desarrollo
**Fecha:** 24 de Mayo de 2024
**Prioridad:** Crítica (Bloqueante para Producción)

---

## 1. Resumen Ejecutivo

La versión actual del *Universal Ingestion Framework* (v3.x) presenta una arquitectura sólida pero carece de mecanismos críticos de seguridad, estabilidad de memoria y cumplimiento legal, impidiendo su despliegue en entornos de producción reales. Este PRD define los requisitos para la versión 4.0, enfocándose en eliminar cuellos de botella de memoria, asegurar el cumplimiento ético/legal y mejorar la resiliencia del sistema.

**Objetivo Principal:** Elevar la calificación del proyecto de 67/100 a >90/100, garantizando estabilidad en escenarios de alta carga.

---

## 2. Objetivos Clave (KPIs)

| Métrica | Estado Actual (v3.x) | Objetivo (v4.0) |
| :--- | :--- | :--- |
| **Estabilidad de Memoria** | OOM con >100k URLs | Uso estable <500MB para 1M URLs |
| **Cumplimiento Legal** | No verifica `robots.txt` | Cumplimiento automático por defecto |
| **Seguridad** | SSL deshabilitado | SSL/TLS forzado con validación completa |
| **Calidad de Datos** | CAPTCHA procesado como contenido | Detección y exclusión de CAPTCHA >95% |
| **Concurrencia** | Race conditions en DB | Operaciones atómicas y Lock de misión |

---

## 3. Alcance de los Cambios

### 3.1. Cambios Aprobados (Basados en Auditoría)

Se aprueban e incluyen en este sprint las 25 notas de la auditoría, priorizadas en tres fases de implementación.

#### 🔴 FASE 1: Correcciones Críticas (Bloqueantes)

*Estos cambios son obligatorios para el pase a producción.*

1. **Refactor de Memoria (`seen_urls`):**
    - **Problema:** `set[str]` ilimitado causa OOM.
    - **Requisito:** Reemplazar `seen_urls` y `seen_assets` con `TTLCache` (cachetools) o una solución respaldada por DB.
    - **Archivo:** `engine_core.py:186-187`.

2. **Cumplimiento Legal (`robots.txt`):**
    - **Problema:** Riesgo legal por ignorar directivas.
    - **Requisito:** Implementar `RobotsChecker` asíncrono. Por defecto `respect_robots_txt = True`.
    - **Archivo:** Nuevo archivo `utils/robots_checker.py`.

3. **Seguridad SSL:**
    - **Problema:** `ssl=False` vulnerable a MITM.
    - **Requisito:** Habilitar verificación SSL usando `certifi`. Eliminar flag `ssl=False`.
    - **Archivo:** `utils/http_session.py`.

4. **Rate Limiting Explícito:**
    - **Problema:** Riesgo de baneo de IP.
    - **Requisito:** Implementar `AdaptiveRateLimiter` con delay configurable y jitter.
    - **Archivo:** `engine_core.py`.

#### 🟡 FASE 2: Mejoras de Calidad y Seguridad

*Estos cambios previenen corrupción de datos y mejoran la fiabilidad.*

1. **Detección de CAPTCHA:**
    - **Requisito:** Implementar `CaptchaDetector` antes de la extracción de contenido. No guardar páginas que sean desafíos de seguridad.
    - **Archivo:** Nuevo archivo `utils/captcha_detector.py`.

2. **Atomicidad de Base de Datos:**
    - **Problema:** Race conditions en `increment_retry` y multi-instancia.
    - **Requisito:** Usar cláusula `RETURNING` en SQLite. Implementar `acquire_mission_lock` para prevenir ejecución simultánea sobre el mismo dominio.
    - **Archivo:** `db_manager.py`.

3. **Sanitización de Logs:**
    - **Problema:** Tokens en URLs se guardan en logs.
    - **Requisito:** Implementar `sanitize_url_for_logging` para redactar parámetros sensibles.
    - **Archivo:** `utils/url_utils.py`.

#### 🟢 FASE 3: Mantenibilidad y Refactoring Técnico

*Deuda técnica y mejora del código.*

1. **Refactoring de God Objects:**
    - Dividir `engine_core.py` (891 líneas) en `Orchestrator`, `WorkerPool` y `StatsTracker`.
    - Dividir `_extract_metadata_pure` en sub-clases especializadas.

2. **Extracción de Constantes:**
    - Mover todos los "magic numbers" a `core/constants.py` con documentación justificativa.

---

## 4. Especificaciones Funcionales Detalladas

### RF-01: Sistema de Control de Memoria (TTL Cache)

**Descripción:** El motor debe limitar la cantidad de URLs rastreadas en memoria activa.
**Lógica:**

- Utilizar `TTLCache` con un límite de 100,000 entradas y TTL de 1 hora.
- Si una URL sale del caché, se verifica su estado en la base de datos antes de procesar.
**Criterio de Aceptación:** El consumo de RAM permanece estable al procesar 500,000 URLs.

### RF-02: Motor de Cumplimiento (Robots.txt)

**Descripción:** El scraper debe respetar las reglas definidas en `/robots.txt` antes de realizar cualquier petición.
**Lógica:**

- Cacheo de parsers `robots.txt` por dominio (TTL 1 hora).
- Si `Disallow: /` existe para el path, marcar URL como `SKIPPED_ROBOTS` en DB y no procesar.
**Criterio de Aceptación:** Logs muestran omisión de URLs bloqueadas. Tests unitarios validan reglas comunes.

### RF-03: Detección de Contenido Anti-Scraping

**Descripción:** Identificar y aislar páginas que presentan desafíos CAPTCHA o errores de verificación.
**Firmas Detectadas:** Cloudflare, reCAPTCHA, hCaptcha.
**Acción:** Si se detecta CAPTCHA con confianza > 0.8, marcar URL como `BLOCKED_CAPTCHA` y no generar archivo Markdown.
**Criterio de Aceptación:** No se generan archivos `.md` que contengan código HTML de CAPTCHA.

---

## 5. Especificaciones Técnicas (No Funcionales)

### RNF-01: Rendimiento

- **Bloqueo de Event Loop:** Las operaciones CPU-bound (limpieza HTML, compresión) deben ejecutarse en un `ThreadPoolExecutor` dedicado para no bloquear el loop async.
- **Paginación:** `db_manager.get_pending_urls` debe usar `LIMIT` y `OFFSET` obligatorios.

### RNF-02: Seguridad

- **SSL:** Conexiones a sitios con certificados inválidos deben fallar de inmediato (a menos que se configure explícitamente un entorno de desarrollo inseguro, pero nunca por defecto).
- **PII:** Los archivos de log no deben contener parámetros de URL sensibles (tokens, session_ids).

### RNF-03: Concurrencia

- **Lock de Misión:** Solo una instancia del scraper puede procesar un dominio específico a la vez, utilizando bloqueos a nivel de DB o Redis.

---

## 6. Plan de Implementación y Cronograma

| Sprint | Duración | Actividades Clave | Entregable |
| :--- | :--- | :--- | :--- |
| **Sprint 1** | 3 días | Fixes de Memoria, SSL, Robots.txt | Versión 4.0-alpha (Estable) |
| **Sprint 2** | 3 días | CAPTCHA Det., Rate Limiter, Atomic DB | Versión 4.0-beta (Segura) |
| **Sprint 3** | 3 días | Refactoring código, Constantes, Docs | Versión 4.0-rc (Release Candidate) |
| **Sprint 4** | 2 días | Testing E2E masivo, ajustes finales | **Release v4.0** |

---

## 7. Casos de Prueba (Testing)

1. **Test de Carga:** Ejecutar scraper contra un sitio espejo con 200k URLs. Verificar que la memoria RAM no supere el umbral definido.
2. **Test Legal:** Configurar un servidor mock con `robots.txt` restrictivo. Verificar que el scraper no descarga ninguna página prohibida.
3. **Test de CAPTCHA:** Apuntar el scraper a un sitio protegido por Cloudflare. Verificar que detecta el desafío y no guarda el HTML del desafío.
4. **Test de Multi-instancia:** Lanzar dos procesos simultáneos contra el mismo dominio. Verificar que uno adquiere el lock y el otro se retira gracefully o espera.

---

## 8. Aprobación Final

Con este PRD, se aprueba la refactorización y actualización del código base. Se autoriza la inversión de tiempo estimada (aprox. 64 horas / 8 días hábiles) para llevar el proyecto a un estado de "Producción Lista".

**Firma del Arquitecto:** *Aprobado.*
**Fecha:** 24/05/2024

---

*Este documento sirve como la única fuente de verdad para el equipo de desarrollo durante el ciclo de actualización v4.0.*

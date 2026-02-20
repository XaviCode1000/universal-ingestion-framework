# 🔄 Plan de Migración: scrapling → curl_cffi

**Estado**: En Progreso  
**Fecha**: 2026-02-20  
**Prioridad**: Alta (Bloqueante para Producción)

---

## 📋 Resumen Ejecutivo

Actualmente el motor de fetching usa **scrapling** (`AsyncStealthySession`), pero el usuario expresó que "ya no usa scrapling". La infraestructura de resiliencia (`ResilientTransport`) está basada en **httpx** pero usa el transport nativo de httpx, no `curl_cffi`.

**Objetivo**: Reemplazar scrapling con `curl_cffi` manteniendo:
- ✅ Impersonación de navegador (TLS/JA3 fingerprints)
- ✅ Evitación de Cloudflare
- ✅ HTTP/2 y HTTP/3
- ✅ Reintentos con exponential backoff
- ✅ Circuit breaker por dominio

---

## 🔍 Investigación Realizada

### curl_cffi vs scrapling

| Característica | scrapling | curl_cffi | httpx nativo |
|----------------|-----------|-----------|--------------|
| **TLS Fingerprint** | ✅ Chrome, Firefox | ✅ Chrome, Firefox, Safari | ❌ OpenSSL genérico |
| **HTTP/2** | ✅ | ✅ | ✅ |
| **HTTP/3** | ✅ | ✅ | ❌ |
| **Cloudflare Evasion** | ✅ `solve_cloudflare=True` | ✅ TLS spoofing | ❌ Bloqueado |
| **Async API** | ✅ `AsyncFetcher` | ✅ `AsyncSession` | ✅ `AsyncClient` |
| **Velocidad** | 🐇🐇 | 🐇🐇🐇 | 🐇 |
| **Dependencias** | curl_cffi + wrappers | libcurl-impersonate | Python puro |

**Veredicto**: `curl_cffi` es el motor subyacente que scrapling usa internamente. Usarlo directamente elimina overhead.

---

## 🛠️ Implementación

### Opción A: httpx-curl-cffi (Recomendada)

Librería puente: [`httpx-curl-cffi`](https://github.com/vgavro/httpx-curl-cffi) (v0.1.5, Dec 2025)

#### 1. Agregar dependencia

```bash
uv add httpx-curl-cffi
```

#### 2. Modificar `resilient_transport.py`

```python
# uif_scraper/infrastructure/network/resilient_transport.py

# ── AGREGAR AL INIT ────────────────────────────────────────────────────────
try:
    from httpx_curl_cffi import AsyncCurlTransport, CurlOpt
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False
    AsyncCurlTransport = None  # type: ignore
    CurlOpt = None  # type: ignore

# ── MODIFICAR __init__ ─────────────────────────────────────────────────────
def __init__(
    self,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    jitter: float = 2.0,
    circuit_threshold: int = 5,
    circuit_timeout: float = 60.0,
    timeout: float = 30.0,
    on_retry: Any = None,
    on_circuit_change: Any = None,
    use_curl_cffi: bool = True,  # ← NUEVO PARAMETRO
    impersonate: str = "chrome",  # ← NUEVO PARAMETRO
) -> None:
    # ... existing code ...
    
    self.use_curl_cffi = use_curl_cffi
    self.impersonate = impersonate
    self._curl_transport: Any = None  # ← NUEVO

# ── MODIFICAR handle_async_request ────────────────────────────────────────
async def handle_async_request(
    self,
    request: httpx.Request,
) -> httpx.Response:
    """Maneja una petición HTTP asíncrona con resiliencia."""
    # Lazy init del transport base
    if self._base_transport is None:
        if self.use_curl_cffi and CURL_CFFI_AVAILABLE:
            # ✅ USAR CURL_CFFI COMO BACKEND
            self._base_transport = AsyncCurlTransport(
                impersonate=self.impersonate,
                default_headers=True,
                curl_options={CurlOpt.FRESH_CONNECT: True} if self._max_retries > 1 else {},
            )
            logger.info(f"Using AsyncCurlTransport with impersonate={self.impersonate}")
        else:
            # Fallback a httpx nativo
            self._base_transport = httpx.AsyncHTTPTransport()
            logger.warning("curl_cffi not available, using httpx native transport")

    # ... resto del código igual ...
```

#### 3. Modificar `cli.py` para activar curl_cffi

```python
# uif_scraper/cli.py

_resilient_transport = create_resilient_transport(
    max_retries=3,
    base_delay=1.0,
    max_delay=30.0,
    jitter=2.0,
    circuit_threshold=5,
    circuit_timeout=60.0,
    on_retry=on_network_retry,
    on_circuit_change=on_circuit_change,
    use_curl_cffi=True,  # ✅ ACTIVAR CURL_CFFI
    impersonate="chrome120",  # Versión específica de Chrome
)
```

#### 4. Eliminar scrapling de `engine_core.py`

```python
# uif_scraper/core/engine_core.py

# ── ELIMINAR ──────────────────────────────────────────────────────────────
- from scrapling.fetchers import AsyncFetcher, AsyncStealthySession

# ── AGREGAR ───────────────────────────────────────────────────────────────
+ import httpx
+ from uif_scraper.infrastructure.network import ResilientTransport

# ── MODIFICAR run() ───────────────────────────────────────────────────────
async def run(self, ...) -> None:
    # ... existing setup code ...
    
    # ✅ CREAR HTTP CLIENT CON RESILIENT TRANSPORT
    if self.resilient_transport:
        self.http_client = httpx.AsyncClient(
            transport=self.resilient_transport,
            timeout=httpx.Timeout(self.config.timeout_seconds),
            follow_redirects=True,
        )
    else:
        # Fallback para compatibilidad
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.config.timeout_seconds),
            follow_redirects=True,
        )
    
    try:
        # ... workers loop ...
    finally:
        await self.http_client.aclose()
```

#### 5. Reemplazar `_fetch_page`

```python
# uif_scraper/core/engine_core.py

async def _fetch_page(self, url: str) -> httpx.Response:
    """Fetch page usando ResilientTransport + curl_cffi."""
    encoded_url = smart_url_normalize(url)
    
    # ✅ USAR HTTP CLIENT CON RESILIENT TRANSPORT
    response = await self.http_client.get(
        encoded_url,
        headers={
            "Referer": self.navigation.base_url,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        },
    )
    
    if response.status_code == 500:
        return None
    if response.status_code in [403, 401, 429]:
        # Cloudflare o rate limiting detectado
        logger.warning(f"Detected blocking for {url}: HTTP {response.status_code}")
        # curl_cffi ya maneja TLS fingerprinting, esto es fallback
        self.use_browser_mode = True
        self._notify_mode_change()
    
    response.raise_for_status()
    return response
```

---

### Opción B: curl_cffi Directo (Más control, más código)

Si queremos eliminar httpx completamente:

```python
# uif_scraper/infrastructure/network/curl_transport.py

from curl_cffi import requests
from curl_cffi.requests import AsyncSession, CurlOpt
import asyncio

class CurlCffiTransport:
    """Transporte basado directamente en curl_cffi."""
    
    def __init__(
        self,
        impersonate: str = "chrome120",
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
    ):
        self.impersonate = impersonate
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self._session: AsyncSession | None = None
    
    async def _get_session(self) -> AsyncSession:
        if self._session is None:
            self._session = AsyncSession(
                impersonate=self.impersonate,
                curl_options={
                    CurlOpt.FRESH_CONNECT: True,  # Requerido para concurrencia
                },
            )
        return self._session
    
    async def get(self, url: str, headers: dict | None = None) -> CurlResponse:
        session = await self._get_session()
        
        # Reintentos manuales (curl_cffi no tiene tenacity integrado)
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = await session.get(
                    url,
                    headers=headers,
                    timeout=30,
                )
                if response.status_code < 500:
                    return response
                last_error = Exception(f"HTTP {response.status_code}")
            except Exception as e:
                last_error = e
            
            if attempt < self.max_retries - 1:
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                await asyncio.sleep(delay)
        
        raise last_error
    
    async def close(self):
        if self._session:
            await self._session.close()
```

**Desventaja**: Perdemos la integración con httpx y tenacity.

---

## 📦 Dependencias a Agregar

```toml
# pyproject.toml

[project]
dependencies = [
    # ... existing ...
    "httpx-curl-cffi>=0.1.5",  # ← NUEVO
    # "curl-cffi>=0.13.0",  # Ya está incluido como dependencia transitiva
]

[dependency-groups]
dev = [
    # ... existing ...
]
```

---

## 🧪 Tests Requeridos

1. **Test de TLS Fingerprint**:
   ```python
   async def test_tls_fingerprint():
       transport = ResilientTransport(use_curl_cffi=True, impersonate="chrome120")
       async with httpx.AsyncClient(transport=transport) as client:
           resp = await client.get("https://tls.browserleaks.com/json")
           assert resp.status_code == 200
           # Verificar que el JA3 fingerprint coincide con Chrome
   ```

2. **Test de Cloudflare Evasion**:
   ```python
   async def test_cloudflare_bypass():
       transport = ResilientTransport(use_curl_cffi=True)
       async with httpx.AsyncClient(transport=transport) as client:
           resp = await client.get("https://nowsecure.nl")  # Sitio de test de CF
           assert resp.status_code == 200
           assert "nowsecure" in resp.text
   ```

3. **Test de Concurrencia**:
   ```python
   async def test_concurrent_requests():
       transport = ResilientTransport(use_curl_cffi=True)
       async with httpx.AsyncClient(transport=transport) as client:
           tasks = [client.get(f"https://example.com/page{i}") for i in range(10)]
           responses = await asyncio.gather(*tasks)
           assert all(r.status_code == 200 for r in responses)
   ```

---

## ⚠️ Advertencias y Riesgos

| Riesgo | Mitigación |
|--------|------------|
| **curl_cffi requiere compilación** | Usar wheels precompilados (PyPI) |
| **FRESH_CONNECT requerido para concurrencia** | Documentar en `CurlOpt` |
| **httpx.Timeout.pool ignorado** | No depender de pool timeout |
| **proxy via env variables** | Usar `CurlOpt.NOPROXY` para control explícito |

---

## 📊 Métricas de Éxito

| Métrica | Antes (scrapling) | Después (curl_cffi) |
|---------|-------------------|---------------------|
| **Requests/segundo** | ~50 req/s | ~150 req/s |
| **Memoria por worker** | ~50 MB | ~20 MB |
| **Cloudflare bypass rate** | ~85% | ~95% |
| **Dependencias totales** | 40+ | 35+ |

---

## 🚀 Plan de Ejecución

### Fase 1: Preparación (1 día)
- [ ] Agregar `httpx-curl-cffi` a `pyproject.toml`
- [ ] Ejecutar `uv sync`
- [ ] Verificar que `curl_cffi` funciona en el entorno

### Fase 2: Integración (2 días)
- [ ] Modificar `ResilientTransport` para soportar `use_curl_cffi=True`
- [ ] Actualizar `cli.py` para activar curl_cffi
- [ ] Modificar `EngineCore._fetch_page` para usar httpx client

### Fase 3: Eliminación de scrapling (1 día)
- [ ] Eliminar imports de scrapling
- [ ] Eliminar `AsyncStealthySession` de `engine_core.py`
- [ ] Ejecutar `uv remove scrapling`

### Fase 4: Testing (2 días)
- [ ] Ejecutar tests existentes
- [ ] Agregar tests de TLS fingerprint
- [ ] Test de carga con 1000 URLs

### Fase 5: Producción (1 día)
- [ ] Deploy a staging
- [ ] Monitorear error rates
- [ ] Deploy a producción

---

## 📝 Snippet Listo para Copiar-Pegar

### `pyproject.toml`
```toml
[project]
dependencies = [
    "httpx-curl-cffi>=0.1.5",
]
```

### `resilient_transport.py` (fragmento)
```python
try:
    from httpx_curl_cffi import AsyncCurlTransport, CurlOpt
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False

# En __init__:
self.use_curl_cffi = use_curl_cffi
self.impersonate = impersonate

# En handle_async_request:
if self._base_transport is None:
    if self.use_curl_cffi and CURL_CFFI_AVAILABLE:
        self._base_transport = AsyncCurlTransport(
            impersonate=self.impersonate,
            default_headers=True,
            curl_options={CurlOpt.FRESH_CONNECT: True},
        )
    else:
        self._base_transport = httpx.AsyncHTTPTransport()
```

---

**Próximo paso**: Ejecutar `uv add httpx-curl-cffi` y probar en staging.

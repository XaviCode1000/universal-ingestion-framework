"""Resilient HTTP Transport with retry policies and per-domain circuit breaker.

Este módulo implementa un transport de httpx que automáticamente:
1. Reintenta peticiones fallidas con Exponential Backoff + Jitter
2. Protege contra fallos en cascada usando un Circuit Breaker por dominio
3. Notifica eventos de red para visualización en la TUI

Uso:
    from httpx import AsyncClient
    from uif_scraper.infrastructure.network import ResilientTransport

    transport = ResilientTransport(
        max_retries=3,
        base_delay=1.0,
        max_delay=30.0,
        circuit_threshold=5,
        circuit_timeout=60.0,
    )

    async with AsyncClient(transport=transport) as client:
        response = await client.get("https://example.com")
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from typing import Any, Callable

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# CALLBACKS PARA LA TUI
# ═══════════════════════════════════════════════════════════════════════════════

# Versión con dataclasses (original)
NetworkRetryCallback = Callable[["NetworkRetryInfo"], None]
CircuitStateCallback = Callable[["CircuitStateInfo"], None]

# Versión simple con parámetros individuales (más fácil de usar)
NetworkRetryCallbackSimple = Callable[[str, int, float, str], None]
"""Callback simple para reintentos.

Args:
    url: URL que se está reintentando
    attempt_number: Número de intento
    wait_time: Segundos de espera
    reason: Razón del fallo
"""

CircuitStateCallbackSimple = Callable[[str, str, str, int], None]
"""Callback simple para cambios de circuit breaker.

Args:
    domain: Dominio afectado
    old_state: Estado anterior
    new_state: Nuevo estado
    failure_count: Cantidad de fallos
"""


@dataclass(frozen=True)
class NetworkRetryInfo:
    """Información sobre un evento de retry."""

    url: str
    attempt_number: int
    wait_time: float
    reason: str


@dataclass(frozen=True)
class CircuitStateInfo:
    """Información sobre cambio de estado del circuit breaker."""

    domain: str
    old_state: str
    new_state: str
    failure_count: int


# ═══════════════════════════════════════════════════════════════════════════════
# EXCEPCIONES CUSTOM
# ═══════════════════════════════════════════════════════════════════════════════


class CircuitOpenError(Exception):
    """Excepción lanzada cuando el circuit breaker está abierto."""

    def __init__(self, domain: str, retry_after: float) -> None:
        self.domain = domain
        self.retry_after = retry_after
        super().__init__(
            f"Circuit breaker open for {domain}. Retry after {retry_after:.1f}s"
        )


class MaxRetriesExceededError(Exception):
    """Excepción lanzada cuando se agotan los reintentos."""

    def __init__(self, url: str, attempts: int, last_reason: str) -> None:
        self.url = url
        self.attempts = attempts
        self.last_reason = last_reason
        super().__init__(f"Max retries ({attempts}) exceeded for {url}: {last_reason}")


# ═══════════════════════════════════════════════════════════════════════════════
# CIRCUIT BREAKER SIMPLE (POR DOMINIO)
# ═══════════════════════════════════════════════════════════════════════════════


class DomainCircuitBreaker:
    """Circuit breaker simple por dominio.

    Estados:
    - closed: Operación normal
    - open: Bloqueando peticiones por excesivos fallos
    - half-open: Probando recuperación
    """

    def __init__(
        self,
        fail_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ) -> None:
        self._fail_threshold = fail_threshold
        self._recovery_timeout = recovery_timeout
        self._failures: dict[str, int] = {}
        self._blocked_until: dict[str, float] = {}

    def can_execute(self, domain: str) -> tuple[bool, float]:
        """Verifica si se puede ejecutar una petición para el dominio.

        Returns:
            (puede_ejecutar, tiempo_restante)
        """
        if domain in self._blocked_until:
            remaining = self._blocked_until[domain] - time.time()
            if remaining > 0:
                return False, remaining
            # Timeout expirado, pasar a half-open
            self._failures[domain] = 0
            del self._blocked_until[domain]
            return True, 0.0
        return True, 0.0

    def record_success(self, domain: str) -> None:
        """Registra éxito para el dominio."""
        self._failures[domain] = 0
        if domain in self._blocked_until:
            del self._blocked_until[domain]

    def record_failure(self, domain: str) -> None:
        """Registra fallo para el dominio."""
        self._failures[domain] = self._failures.get(domain, 0) + 1
        if self._failures[domain] >= self._fail_threshold:
            self._blocked_until[domain] = time.time() + self._recovery_timeout

    def get_state(self, domain: str) -> str:
        """Obtiene el estado actual del circuit breaker para el dominio."""
        if domain in self._blocked_until:
            if time.time() < self._blocked_until[domain]:
                return "open"
            return "half-open"
        return "closed"

    def get_failure_count(self, domain: str) -> int:
        """Obtiene la cantidad de fallos consecutivos para el dominio."""
        return self._failures.get(domain, 0)


# ═══════════════════════════════════════════════════════════════════════════════
# IMPLEMENTACIÓN DEL TRANSPORT
# ═══════════════════════════════════════════════════════════════════════════════


class ResilientTransport(httpx.AsyncBaseTransport):
    """Transport HTTP asíncrono con resiliencia incorporada.

    Características:
    - Reintentos automáticos con Exponential Backoff + Jitter
    - Circuit Breaker por dominio (no global)
    - Callbacks para eventos de red (retry, circuit state)
    - Completamente asíncrono (no bloquea la TUI)

    Args:
        max_retries: Máximo número de reintentos por petición
        base_delay: Delay base para exponential backoff (segundos)
        max_delay: Delay máximo entre reintentos (segundos)
        jitter: Jitter máximo agregado al delay (segundos)
        circuit_threshold: Fallos consecutivos para abrir el circuito
        circuit_timeout: Segundos antes de intentar half-open
        timeout: Timeout total para la petición (segundos)
        on_retry: Callback para eventos de retry
        on_circuit_change: Callback para cambios de estado del circuit breaker
    """

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
    ) -> None:
        super().__init__()
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._max_delay = max_delay
        self._jitter = jitter
        self._timeout = timeout

        # Circuit breakers por dominio - NO global
        self._circuit_breakers: dict[str, DomainCircuitBreaker] = {}
        self._circuit_threshold = circuit_threshold
        self._circuit_timeout = circuit_timeout
        self._circuit_lock = asyncio.Lock()

        # Callbacks para la TUI
        self._on_retry_simple = on_retry
        self._on_circuit_change_simple = on_circuit_change

        # Wrappers para compatibilidad con el tipo interno
        self._on_retry: NetworkRetryCallback | None = self._wrap_retry_callback()
        self._on_circuit_change: CircuitStateCallback | None = (
            self._wrap_circuit_callback()
        )

        # Transport base para delegar peticiones
        self._base_transport: httpx.AsyncHTTPTransport | None = None

    def _wrap_retry_callback(self) -> NetworkRetryCallback | None:
        """Convierte callback simple a formato dataclass."""
        if self._on_retry_simple is None:
            return None
        callback = self._on_retry_simple

        def wrapped(info: NetworkRetryInfo) -> None:
            callback(info.url, info.attempt_number, info.wait_time, info.reason)

        return wrapped

    def _wrap_circuit_callback(self) -> CircuitStateCallback | None:
        """Convierte callback simple a formato dataclass."""
        if self._on_circuit_change_simple is None:
            return None
        callback = self._on_circuit_change_simple

        def wrapped(info: CircuitStateInfo) -> None:
            callback(info.domain, info.old_state, info.new_state, info.failure_count)

        return wrapped

    async def _get_circuit_breaker(self, domain: str) -> DomainCircuitBreaker:
        """Obtiene o crea un circuit breaker para el dominio."""
        async with self._circuit_lock:
            if domain not in self._circuit_breakers:
                self._circuit_breakers[domain] = DomainCircuitBreaker(
                    fail_threshold=self._circuit_threshold,
                    recovery_timeout=self._circuit_timeout,
                )
            return self._circuit_breakers[domain]

    def _extract_domain(self, url: httpx.URL) -> str:
        """Extrae el dominio de una URL."""
        return url.host or "unknown"

    def _calculate_wait_time(self, attempt: int) -> float:
        """Calcula el tiempo de espera para un intento dado."""
        exp_delay: float = min(self._base_delay * (2 ** (attempt - 1)), self._max_delay)
        jitter_val: float = random.uniform(0, self._jitter)
        return exp_delay + jitter_val

    async def _notify_retry(
        self, url: str, attempt: int, wait_time: float, reason: str
    ) -> None:
        """Notifica retry al callback de forma segura."""
        if self._on_retry:
            try:
                info = NetworkRetryInfo(
                    url=url,
                    attempt_number=attempt,
                    wait_time=wait_time,
                    reason=reason,
                )
                self._on_retry(info)
            except Exception as e:
                logger.error(f"Error in retry callback: {e}")

    async def _notify_circuit_change(
        self, domain: str, old_state: str, new_state: str, failure_count: int
    ) -> None:
        """Notifica cambio de circuit breaker al callback de forma segura."""
        if self._on_circuit_change:
            try:
                info = CircuitStateInfo(
                    domain=domain,
                    old_state=old_state,
                    new_state=new_state,
                    failure_count=failure_count,
                )
                self._on_circuit_change(info)
            except Exception as e:
                logger.error(f"Error in circuit callback: {e}")

    async def handle_async_request(
        self,
        request: httpx.Request,
    ) -> httpx.Response:
        """Maneja una petición HTTP asíncrona con resiliencia.

        Este es el método principal que httpx llama cuando se hace una petición.
        """
        # Lazy init del transport base
        if self._base_transport is None:
            self._base_transport = httpx.AsyncHTTPTransport()

        domain = self._extract_domain(request.url)
        circuit_breaker = await self._get_circuit_breaker(domain)

        # Verificar circuit breaker
        can_execute, retry_after = circuit_breaker.can_execute(domain)
        if not can_execute:
            logger.warning(f"Circuit open for {domain}, rejecting request")
            return httpx.Response(
                status_code=421,
                content=f"Circuit breaker open for {domain}".encode(),
                headers={"Retry-After": str(int(retry_after))},
                request=request,
            )

        # Obtener estado anterior para callbacks
        old_state = circuit_breaker.get_state(domain)

        # Reintentos con tenacity
        try:
            async for attempt in AsyncRetrying(
                retry=retry_if_exception_type(
                    (
                        httpx.ConnectError,
                        httpx.ConnectTimeout,
                        httpx.ReadTimeout,
                        httpx.RemoteProtocolError,
                    )
                ),
                stop=stop_after_attempt(self._max_retries),
                wait=wait_exponential_jitter(
                    initial=self._base_delay,
                    max=self._max_delay,
                    jitter=self._jitter,
                ),
                reraise=True,
            ):
                with attempt:
                    try:
                        # Verificar circuit breaker antes de cada intento
                        can_execute, _ = circuit_breaker.can_execute(domain)
                        if not can_execute:
                            raise CircuitOpenError(domain, self._circuit_timeout)

                        # Ejecutar la petición
                        response = await self._base_transport.handle_async_request(
                            request
                        )

                        # Verificar status codes que indican error
                        if response.status_code >= 500:
                            raise httpx.HTTPStatusError(
                                f"Server error: {response.status_code}",
                                request=request,
                                response=response,
                            )

                        # Éxito
                        circuit_breaker.record_success(domain)

                        # Notificar cambio de estado si hubo cambio
                        new_state = circuit_breaker.get_state(domain)
                        if old_state != new_state:
                            await self._notify_circuit_change(
                                domain,
                                old_state,
                                new_state,
                                circuit_breaker.get_failure_count(domain),
                            )

                        return response

                    except (
                        httpx.ConnectError,
                        httpx.ConnectTimeout,
                        httpx.ReadTimeout,
                        httpx.RemoteProtocolError,
                        httpx.HTTPStatusError,
                    ) as e:
                        # Registrar fallo
                        circuit_breaker.record_failure(domain)

                        # Notificar retry
                        attempt_num = attempt.retry_state.attempt_number
                        wait_time = self._calculate_wait_time(attempt_num)
                        await self._notify_retry(
                            str(request.url), attempt_num, wait_time, type(e).__name__
                        )

                        # Notificar cambio de estado
                        new_state = circuit_breaker.get_state(domain)
                        if old_state != new_state:
                            await self._notify_circuit_change(
                                domain,
                                old_state,
                                new_state,
                                circuit_breaker.get_failure_count(domain),
                            )

                        raise

        except CircuitOpenError:
            return httpx.Response(
                status_code=421,
                content=f"Circuit breaker open for {domain}".encode(),
                headers={"Retry-After": str(int(self._circuit_timeout))},
                request=request,
            )

        except Exception as e:
            # Agotaron los reintentos
            logger.error(f"Max retries exceeded for {request.url}: {e}")
            return httpx.Response(
                status_code=504,
                content=str(e).encode(),
                request=request,
            )

        # Fallback: nunca debería llegar aquí pero mypy lo requiere
        return httpx.Response(
            status_code=500,
            content=b"Internal error in resilient transport",
            request=request,
        )

    async def aclose(self) -> None:
        """Cierra el transport y libera recursos."""
        if self._base_transport:
            await self._base_transport.aclose()

        # Limpiar circuit breakers
        async with self._circuit_lock:
            self._circuit_breakers.clear()

    def get_circuit_state(self, domain: str) -> str:
        """Obtiene el estado actual del circuit breaker para un dominio."""
        if domain in self._circuit_breakers:
            return self._circuit_breakers[domain].get_state(domain)
        return "closed"


# ═══════════════════════════════════════════════════════════════════════════════
# FACTORY FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════


def create_resilient_transport(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    jitter: float = 2.0,
    circuit_threshold: int = 5,
    circuit_timeout: float = 60.0,
    timeout: float = 30.0,
    on_retry: Any = None,
    on_circuit_change: Any = None,
) -> ResilientTransport:
    """Factory function para crear un ResilientTransport configurado.

    Args:
        max_retries: Máximo número de reintentos
        base_delay: Delay base para exponential backoff
        max_delay: Delay máximo entre reintentos
        jitter: Jitter máximo
        circuit_threshold: Fallos para abrir el circuito
        circuit_timeout: Timeout del circuit breaker
        timeout: Timeout de la petición
        on_retry: Callback para eventos de retry
        on_circuit_change: Callback para cambios de circuit breaker

    Returns:
        Instancia configurada de ResilientTransport
    """
    return ResilientTransport(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        jitter=jitter,
        circuit_threshold=circuit_threshold,
        circuit_timeout=circuit_timeout,
        timeout=timeout,
        on_retry=on_retry,
        on_circuit_change=on_circuit_change,
    )

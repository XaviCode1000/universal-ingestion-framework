#!/usr/bin/env python3
"""Chaos Test - Prueba de estrés del ResilientTransport.

Este script prueba el ResilientTransport haciendo peticiones a endpoints
que fallan para observar:
1. Reintentos con exponential backoff
2. Circuit breaker abriendo después de threshold
3. Circuit breaker pasando a half-open después del timeout

Uso:
    uv run python test_chaos.py
"""

import asyncio
import sys

import httpx

from uif_scraper.infrastructure.network.resilient_transport import (
    create_resilient_transport,
)


# Contadores para callbacks
retry_count = 0
circuit_changes = []


def on_retry(url: str, attempt: int, wait: float, reason: str) -> None:
    """Callback para reintentos."""
    global retry_count
    retry_count += 1
    print(f"🔄 RETRY {attempt}: {url} - {reason} (esperando {wait:.2f}s)")


def on_circuit_change(domain: str, old: str, new: str, failures: int) -> None:
    """Callback para cambios de circuit breaker."""
    circuit_changes.append((domain, old, new, failures))
    emoji = "🟢" if new == "closed" else "🟡" if new == "half-open" else "🔴"
    print(f"{emoji} CIRCUIT {domain}: {old} -> {new} ({failures} fallos)")


async def test_resilient_transport():
    """Prueba el transport resiliente."""
    global retry_count, circuit_changes

    print("=" * 60)
    print("🧪 CHAOS TEST - ResilientTransport")
    print("=" * 60)

    # Crear transport con umbrales bajos para prueba rápida
    transport = create_resilient_transport(
        max_retries=3,
        base_delay=0.5,
        max_delay=2.0,
        jitter=0.5,
        circuit_threshold=3,  # Abrir después de 3 fallos
        circuit_timeout=3.0,  # Probar después de 3 segundos
        on_retry=on_retry,
        on_circuit_change=on_circuit_change,
    )

    # Crear cliente con el transport
    async with httpx.AsyncClient(transport=transport) as client:
        # Test 1: Peticiones exitosas
        print("\n📋 Test 1: Peticiones exitosas")
        try:
            response = await client.get("https://httpbin.org/get")
            print(f"   ✅ Éxito: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Test 2: Forzar fallos para abrir el circuit breaker
        print("\n📋 Test 2: Forzar fallos (abrir circuit breaker)")
        for i in range(5):
            try:
                # httpbin.org/status/500 devuelve 500 Internal Server Error
                response = await client.get("https://httpbin.org/status/500")
                print(f"   Petición {i + 1}: {response.status_code}")
            except Exception as e:
                print(f"   Petición {i + 1} exception: {type(e).__name__}")
            await asyncio.sleep(0.1)

        # Test 3: Verificar circuit abierto
        print("\n📋 Test 3: Verificar circuit abierto")
        state = transport.get_circuit_state("httpbin.org")
        print(f"   Estado del circuit: {state}")

        # Test 4: Intentar más peticiones (deberían ser bloqueadas)
        print("\n📋 Test 4: Peticiones con circuit abierto")
        for i in range(3):
            try:
                response = await client.get("https://httpbin.org/get")
                print(
                    f"   Petición {i + 1}: {response.status_code} (content: {response.text[:50]}...)"
                )
            except Exception as e:
                print(f"   Petición {i + 1}: {type(e).__name__}: {e}")
            await asyncio.sleep(0.1)

        # Test 5: Esperar a half-open
        print("\n📋 Test 5: Esperar a half-open (3 segundos)")
        await asyncio.sleep(3.5)
        state = transport.get_circuit_state("httpbin.org")
        print(f"   Estado después de esperar: {state}")

        # Test 6: Intentar con half-open
        print("\n📋 Test 6: Peticiones en half-open")
        for i in range(3):
            try:
                response = await client.get("https://httpbin.org/get")
                print(f"   Petición {i + 1}: {response.status_code}")
            except Exception as e:
                print(f"   Petición {i + 1}: {type(e).__name__}")
            await asyncio.sleep(0.2)

    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    print(f"   Total de reintentos: {retry_count}")
    print(f"   Cambios de circuit: {len(circuit_changes)}")
    for domain, old, new, failures in circuit_changes:
        print(f"      {domain}: {old} -> {new} ({failures} fallos)")
    print()


async def main():
    """Entry point."""
    try:
        await test_resilient_transport()
    except KeyboardInterrupt:
        print("\n⚠️  Prueba interrumpida")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error en la prueba: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

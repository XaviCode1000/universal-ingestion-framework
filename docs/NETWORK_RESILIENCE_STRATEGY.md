# Network Resilience Strategy - Sprint Document

## Overview
This document outlines the strategy for implementing network resilience in UIF v3.1, leveraging the observability infrastructure built in Sprint v3.0.

## Research Findings

### Circuit Breaker Libraries

| Library | Status | Features | Recommendation |
|---------|--------|----------|----------------|
| **pybreaker** | ✅ Active | Thread-safe, Redis backing, async support | ⭐ RECOMMENDED |
| **circuitbreaker** | ✅ Active | Simple decorator, async support | Good for simple cases |
| **httpx-retries** | ✅ Active | Transport layer retries | Use for httpx integration |
| **base-client** | ⚠️ New | httpx + CB + retries | Evaluate for v3.1 |

### Key Libraries

1. **pybreaker** (v2.x) - Most mature, Redis support for distributed systems
2. **httpx-retries** - Best integration with existing httpx usage
3. **tenacity** - General-purpose retry logic (backup)

## Architecture Proposal

```
EngineCore
    │
    ├── HTTPClient (httpx)
    │       │
    │       └── RetryTransport (httpx-retries)
    │               │
    │               └── CircuitBreaker (pybreaker)
    │
    └── NetworkEventEmitter
            │
            ├── NetworkFailure(url, attempt, reason)
            ├── RetryAttempt(url, attempt, backoff)
            └── CircuitStateChanged(domain, state)
```

## Implementation Plan

### Phase 1: Circuit Breaker Integration
- [ ] Integrate pybreaker with httpx client
- [ ] Configure failure_threshold=5, reset_timeout=60
- [ ] Emit CircuitStateChanged events to TUI

### Phase 2: Retry Policies
- [ ] Configure httpx-retries with exponential backoff
- [ ] Implement jitter for randomization
- [ ] Handle rate limiting (429) with longer backoff

### Phase 3: Event Integration
- [ ] Emit NetworkFailure events with retry count
- [ ] Show retry counter in ActivityFeed (yellow color)
- [ ] Display circuit breaker state in SystemStatus

## Event Schema

```python
class NetworkFailure(TUIEvent):
    url: str
    attempt: int
    max_retries: int
    error_type: str  # ConnectionError, Timeout, RateLimit
    backoff_ms: int
    will_retry: bool

class CircuitStateEvent(TUIEvent):
    domain: str
    state: Literal["closed", "open", "half-open"]
    failure_count: int
    next_retry_ms: int
```

## UI Integration

| Event | Display | Color |
|-------|---------|-------|
| `NetworkFailure` | "🔄 Retrying example.com (2/5)... | Yellow |
| `CircuitOpen` | "🛡️ Circuit OPEN: example.com blocked" | Red |
| `CircuitHalfOpen` | "🧪 Testing: example.com" | Cyan |
| `CircuitClosed` | "✅ Recovered: example.com" | Green |

## References

- [pybreaker Documentation](https://pybreaker.readthedocs.io/)
- [httpx-retries GitHub](https://github.com/will-ockmore/httpx-retries)
- [Martin Fowler: Circuit Breaker](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Release It! - Michael Nygard](https://pragprog.com/titles/mnee2/release-it-second-edition/)

---

**Created**: 2026-02-20  
**Sprint**: Network Resilience v3.1  
**Status**: Research Complete ✅

import time
from uif_scraper.utils.circuit_breaker import CircuitBreaker


def test_circuit_breaker_threshold():
    cb = CircuitBreaker(threshold=2, timeout=1)
    domain = "test.com"

    assert cb.should_allow(domain) is True

    cb.record_failure(domain)
    assert cb.should_allow(domain) is True

    cb.record_failure(domain)
    assert cb.should_allow(domain) is False


def test_circuit_breaker_reset():
    cb = CircuitBreaker(threshold=1, timeout=0.1)
    domain = "test.com"

    cb.record_failure(domain)
    assert cb.should_allow(domain) is False

    time.sleep(0.15)
    assert cb.should_allow(domain) is True


def test_circuit_breaker_success_reset():
    cb = CircuitBreaker(threshold=5)
    domain = "test.com"
    cb.record_failure(domain)
    cb.record_success(domain)
    assert cb.failures[domain] == 0

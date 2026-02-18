import time

from uif_scraper.utils.circuit_breaker import CircuitBreaker

# Valid test domain from webscraper.io
TEST_DOMAIN = "webscraper.io"


def test_circuit_breaker_threshold():
    cb = CircuitBreaker(threshold=2, timeout=1)

    assert cb.should_allow(TEST_DOMAIN) is True

    cb.record_failure(TEST_DOMAIN)
    assert cb.should_allow(TEST_DOMAIN) is True

    cb.record_failure(TEST_DOMAIN)
    assert cb.should_allow(TEST_DOMAIN) is False


def test_circuit_breaker_reset():
    cb = CircuitBreaker(threshold=1, timeout=0.1)

    cb.record_failure(TEST_DOMAIN)
    assert cb.should_allow(TEST_DOMAIN) is False

    time.sleep(0.15)
    assert cb.should_allow(TEST_DOMAIN) is True


def test_circuit_breaker_success_reset():
    cb = CircuitBreaker(threshold=5)
    cb.record_failure(TEST_DOMAIN)
    cb.record_success(TEST_DOMAIN)
    assert cb.failures[TEST_DOMAIN] == 0

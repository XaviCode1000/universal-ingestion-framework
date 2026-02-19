import time


class CircuitBreaker:
    """Circuit breaker pattern for protecting against cascading failures.

    Tracks failures per domain and blocks requests when threshold is exceeded.
    """

    __slots__ = ("threshold", "timeout", "failures", "blocked_until")

    def __init__(self, threshold: int = 5, timeout: float = 300.0):
        self.threshold = threshold
        self.timeout = timeout
        self.failures: dict[str, int] = {}
        self.blocked_until: dict[str, float] = {}

    def should_allow(self, domain: str) -> bool:
        if domain in self.blocked_until:
            if time.time() < self.blocked_until[domain]:
                return False
            del self.blocked_until[domain]
            self.failures[domain] = 0
        return True

    def record_failure(self, domain: str) -> None:
        self.failures[domain] = self.failures.get(domain, 0) + 1
        if self.failures[domain] >= self.threshold:
            self.blocked_until[domain] = time.time() + self.timeout

    def record_success(self, domain: str) -> None:
        self.failures[domain] = 0
        if domain in self.blocked_until:
            del self.blocked_until[domain]

    def get_state(self, domain: str) -> str:
        """Get circuit breaker state for a domain.

        Returns:
            "closed" - normal operation
            "open" - blocked, rejecting requests
            "half-open" - recovering, allowing test requests
        """
        if domain in self.blocked_until:
            if time.time() < self.blocked_until[domain]:
                return "open"
            # Expired, entering half-open
            return "half-open"
        return "closed"

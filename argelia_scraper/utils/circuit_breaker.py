import time
from typing import Dict


class CircuitBreaker:
    def __init__(self, threshold: int = 5, timeout: int = 300):
        self.threshold = threshold
        self.timeout = timeout
        self.failures: Dict[str, int] = {}
        self.blocked_until: Dict[str, float] = {}

    def should_allow(self, domain: str) -> bool:
        if domain in self.blocked_until:
            if time.time() < self.blocked_until[domain]:
                return False
            else:
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

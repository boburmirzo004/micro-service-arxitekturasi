import time
import logging

logger = logging.getLogger(__name__)


class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_time=30, slow_threshold=2.0):
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.slow_threshold = slow_threshold
        self._failures = {}
        self._slow_count = {}
        self._open_until = {}

    def is_open(self, service: str) -> bool:
        if service in self._open_until:
            if time.time() < self._open_until[service]:
                return True
            else:
                del self._open_until[service]
                self._failures[service] = 0
                self._slow_count[service] = 0
                logger.info(f"Circuit yopildi, qayta urinish: {service}")
        return False

    def record_success(self, service: str):
        self._failures[service] = 0
        self._slow_count[service] = 0

    def record_failure(self, service: str):
        self._failures[service] = self._failures.get(service, 0) + 1
        if self._failures[service] >= self.failure_threshold:
            self._open_until[service] = time.time() + self.recovery_time
            logger.warning(f"Circuit OCHILDI (xato): {service}, {self.recovery_time}s bloklanadi")

    def record_slow(self, service: str, duration: float):
        if duration > self.slow_threshold:
            self._slow_count[service] = self._slow_count.get(service, 0) + 1
            logger.warning(
                f"Sekin javob: {service} - {duration:.2f}s "
                f"({self._slow_count[service]}/{self.failure_threshold})"
            )
            if self._slow_count[service] >= self.failure_threshold:
                self._open_until[service] = time.time() + self.recovery_time
                logger.warning(f"Circuit OCHILDI (sekin): {service}, {self.recovery_time}s bloklanadi")

    def get_stats(self) -> dict:
        return {
            "open_circuits": {
                s: round(t - time.time(), 1)
                for s, t in self._open_until.items()
                if time.time() < t
            },
            "failures": dict(self._failures),
            "slow_counts": dict(self._slow_count),
        }
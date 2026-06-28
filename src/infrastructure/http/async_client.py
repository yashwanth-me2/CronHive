import time
import httpx
from src.domain.exceptions import CircuitOpenError

class HttpClientWithCircuitBreaker:
    """
    HTTP client wrapped with a circuit breaker pattern.
    If a target URL fails repeatedly, the circuit opens to prevent hammering it.
    """
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.client = httpx.AsyncClient()
        self.state = self.CLOSED
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = 0.0

    async def close(self):
        await self.client.aclose()

    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Executes HTTP request, managing circuit breaker state."""
        if self.state == self.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = self.HALF_OPEN
            else:
                raise CircuitOpenError(f"Circuit is open for HTTP client. Try again later.")

        try:
            response = await self.client.request(method, url, **kwargs)
            # If we get here and it's half open, it succeeded, so close circuit
            if self.state == self.HALF_OPEN and response.status_code < 500:
                self._reset()
            elif response.status_code >= 500:
                # 5xx errors count as failures
                self._record_failure()
                
            return response
            
        except (httpx.RequestError, httpx.TimeoutException) as e:
            self._record_failure()
            raise e

    def _record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = self.OPEN

    def _reset(self):
        self.state = self.CLOSED
        self.failure_count = 0

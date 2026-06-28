class DomainException(Exception):
    """Base exception for domain errors."""
    pass

class JobNotFoundError(DomainException):
    """Raised when a job is not found."""
    pass

class TenantNotFoundError(DomainException):
    """Raised when a tenant is not found."""
    pass

class RateLimitExceededError(DomainException):
    """Raised when tenant exceeds rate limits."""
    pass

class CircuitOpenError(DomainException):
    """Raised when the circuit breaker is open, preventing requests."""
    pass

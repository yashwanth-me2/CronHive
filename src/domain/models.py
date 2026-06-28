from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from uuid import UUID, uuid4

class JobStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    DELETED = "deleted"

class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

@dataclass
class Job:
    """Domain model for a scheduled Job."""
    tenant_id: UUID
    name: str
    target_url: str
    cron_expression: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    description: Optional[str] = None
    http_method: str = "POST"
    headers: Dict[str, str] = field(default_factory=dict)
    payload: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 10
    max_retries: int = 3
    retry_backoff_base: int = 2
    status: JobStatus = JobStatus.ACTIVE
    id: UUID = field(default_factory=uuid4)
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    idempotency_key: Optional[str] = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

@dataclass
class Execution:
    """Domain model for a single job execution."""
    job_id: UUID
    attempt_number: int = 1
    status: ExecutionStatus = ExecutionStatus.PENDING
    id: UUID = field(default_factory=uuid4)
    http_status_code: Optional[int] = None
    response_body_preview: Optional[str] = None
    duration_ms: float = 0.0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=utc_now)

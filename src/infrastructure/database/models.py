from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID as PGUUID
from sqlmodel import SQLModel, Field

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Tenant(SQLModel, table=True):
    __tablename__ = "tenants"
    
    id: UUID = Field(default_factory=uuid4, sa_column=Column(PGUUID(as_uuid=True), primary_key=True))
    name: str = Field(index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    api_key: str = Field(unique=True, index=True)
    max_jobs: int = Field(default=100)
    rate_limit_per_min: int = Field(default=60)
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(TIMESTAMP(timezone=True)))
    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(TIMESTAMP(timezone=True)))

class DBJob(SQLModel, table=True):
    __tablename__ = "jobs"
    
    id: UUID = Field(default_factory=uuid4, sa_column=Column(PGUUID(as_uuid=True), primary_key=True))
    tenant_id: UUID = Field(sa_column=Column(PGUUID(as_uuid=True), ForeignKey("tenants.id"), index=True))
    name: str = Field(index=True)
    description: Optional[str] = None
    cron_expression: Optional[str] = None
    scheduled_at: Optional[datetime] = Field(default=None, sa_column=Column(TIMESTAMP(timezone=True)))
    target_url: str
    http_method: str = Field(default="POST")
    headers: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))
    payload: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))
    status: str = Field(default="active", index=True)
    timeout_seconds: int = Field(default=10)
    max_retries: int = Field(default=3)
    retry_backoff_base: int = Field(default=2)
    next_run_at: Optional[datetime] = Field(default=None, sa_column=Column(TIMESTAMP(timezone=True), index=True))
    last_run_at: Optional[datetime] = Field(default=None, sa_column=Column(TIMESTAMP(timezone=True)))
    idempotency_key: Optional[str] = Field(default=None, unique=True, index=True)
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(TIMESTAMP(timezone=True)))
    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(TIMESTAMP(timezone=True)))

class DBExecution(SQLModel, table=True):
    __tablename__ = "executions"
    
    id: UUID = Field(default_factory=uuid4, sa_column=Column(PGUUID(as_uuid=True), primary_key=True))
    job_id: UUID = Field(sa_column=Column(PGUUID(as_uuid=True), ForeignKey("jobs.id"), index=True))
    attempt_number: int = Field(default=1)
    status: str = Field(default="pending", index=True)
    http_status_code: Optional[int] = None
    response_body_preview: Optional[str] = None
    duration_ms: float = Field(default=0.0)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = Field(default=None, sa_column=Column(TIMESTAMP(timezone=True)))
    completed_at: Optional[datetime] = Field(default=None, sa_column=Column(TIMESTAMP(timezone=True)))
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(TIMESTAMP(timezone=True), index=True))

class DeadLetterEntry(SQLModel, table=True):
    __tablename__ = "dead_letter_queue"
    
    id: UUID = Field(default_factory=uuid4, sa_column=Column(PGUUID(as_uuid=True), primary_key=True))
    execution_id: UUID = Field(sa_column=Column(PGUUID(as_uuid=True), ForeignKey("executions.id"), unique=True))
    job_id: UUID = Field(sa_column=Column(PGUUID(as_uuid=True), ForeignKey("jobs.id"), index=True))
    last_request_snapshot: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))
    failure_reason: str
    reprocessed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(TIMESTAMP(timezone=True)))

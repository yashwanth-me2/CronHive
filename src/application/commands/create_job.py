from uuid import UUID
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from src.domain.models import Job, JobStatus
from src.domain.services.scheduler import calculate_next_run
from src.infrastructure.database.repositories.job_repo import JobRepository
from src.infrastructure.queue.redis_queue import RedisQueue

async def create_job_command(
    tenant_id: UUID,
    name: str,
    target_url: str,
    job_repo: JobRepository,
    queue: RedisQueue,
    cron_expression: Optional[str] = None,
    scheduled_at: Optional[datetime] = None,
    description: Optional[str] = None,
    http_method: str = "POST",
    headers: Optional[Dict[str, str]] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> Job:
    """
    Creates a new job and enqueues it if active.
    """
    if not cron_expression and not scheduled_at:
        raise ValueError("Either cron_expression or scheduled_at must be provided")

    next_run = None
    if cron_expression:
        next_run = calculate_next_run(cron_expression, datetime.now(timezone.utc))
    elif scheduled_at:
        next_run = scheduled_at

    job = Job(
        tenant_id=tenant_id,
        name=name,
        target_url=target_url,
        cron_expression=cron_expression,
        scheduled_at=scheduled_at,
        description=description,
        http_method=http_method,
        headers=headers or {},
        payload=payload or {},
        next_run_at=next_run
    )

    created_job = await job_repo.create(job)

    if created_job.status == JobStatus.ACTIVE and created_job.next_run_at:
        await queue.enqueue(created_job.id, created_job.next_run_at.timestamp())

    return created_job

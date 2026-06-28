from uuid import UUID
from datetime import datetime, timezone
from src.domain.models import JobStatus
from src.domain.exceptions import JobNotFoundError
from src.domain.services.scheduler import calculate_next_run
from src.infrastructure.database.repositories.job_repo import JobRepository
from src.infrastructure.queue.redis_queue import RedisQueue

async def resume_job_command(
    tenant_id: UUID,
    job_id: UUID,
    job_repo: JobRepository,
    queue: RedisQueue,
) -> None:
    job = await job_repo.get_by_tenant_and_id(tenant_id, job_id)
    if not job:
        raise JobNotFoundError(f"Job {job_id} not found")

    if job.status == JobStatus.ACTIVE:
        return

    job.status = JobStatus.ACTIVE
    
    # Calculate next run
    now = datetime.now(timezone.utc)
    if job.cron_expression:
        job.next_run_at = calculate_next_run(job.cron_expression, now)
    else:
        job.next_run_at = job.scheduled_at if job.scheduled_at and job.scheduled_at > now else now

    await job_repo.update(job)
    if job.next_run_at:
        await queue.enqueue(job.id, job.next_run_at.timestamp())

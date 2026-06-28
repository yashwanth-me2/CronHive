from uuid import UUID
from src.domain.models import JobStatus
from src.domain.exceptions import JobNotFoundError
from src.infrastructure.database.repositories.job_repo import JobRepository
from src.infrastructure.queue.redis_queue import RedisQueue

async def pause_job_command(
    tenant_id: UUID,
    job_id: UUID,
    job_repo: JobRepository,
    queue: RedisQueue,
) -> None:
    """
    Pauses an active job and removes it from the scheduling queue.
    """
    job = await job_repo.get_by_tenant_and_id(tenant_id, job_id)
    if not job:
        raise JobNotFoundError(f"Job {job_id} not found")

    if job.status == JobStatus.PAUSED:
        return

    job.status = JobStatus.PAUSED
    await job_repo.update(job)
    
    # Remove from Redis queue so the poller doesn't pick it up
    await queue.remove(job.id)

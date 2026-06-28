from uuid import UUID
import time
from src.domain.exceptions import JobNotFoundError
from src.infrastructure.database.repositories.job_repo import JobRepository
from src.infrastructure.queue.redis_queue import RedisQueue

async def trigger_job_command(
    tenant_id: UUID,
    job_id: UUID,
    job_repo: JobRepository,
    queue: RedisQueue,
) -> None:
    job = await job_repo.get_by_tenant_and_id(tenant_id, job_id)
    if not job:
        raise JobNotFoundError(f"Job {job_id} not found")

    # Enqueue immediately
    await queue.enqueue(job.id, time.time())

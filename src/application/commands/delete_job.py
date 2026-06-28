from uuid import UUID
from src.domain.exceptions import JobNotFoundError
from src.infrastructure.database.repositories.job_repo import JobRepository
from src.infrastructure.queue.redis_queue import RedisQueue

async def delete_job_command(
    tenant_id: UUID,
    job_id: UUID,
    job_repo: JobRepository,
    queue: RedisQueue,
) -> None:
    job = await job_repo.get_by_tenant_and_id(tenant_id, job_id)
    if not job:
        raise JobNotFoundError(f"Job {job_id} not found")

    deleted = await job_repo.delete(tenant_id, job_id)
    if deleted:
        # Best effort removal from queue
        import time
        await queue.redis.zrem(queue.queue_key, str(job.id))

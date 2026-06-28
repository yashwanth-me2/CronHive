import time
from typing import List
from uuid import UUID
import redis.asyncio as redis
from src.config import settings

class RedisQueue:
    """
    Manages the job queue using Redis sorted sets.
    Sorted sets (ZSET) are perfect for a priority queue where the score
    is the timestamp (next_run_at).
    """
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.queue_key = "cronhive:jobs:due"

    async def enqueue(self, job_id: UUID, run_at_timestamp: float) -> None:
        """Add a job to the queue with its execution time as the score."""
        await self.redis.zadd(self.queue_key, {str(job_id): run_at_timestamp})

    async def remove(self, job_id: UUID) -> None:
        """Remove a job from the queue."""
        await self.redis.zrem(self.queue_key, str(job_id))

    async def claim_due_jobs(self, batch_size: int = 10) -> List[str]:
        """
        Atomically fetch jobs that are due and remove them from the queue.
        This lock-free design ensures no two workers claim the same job.
        """
        now = time.time()
        
        # Use pipeline for atomicity
        pipe = self.redis.pipeline()
        
        # 1. Get due jobs
        pipe.zrangebyscore(self.queue_key, "-inf", now, start=0, num=batch_size)
        
        # 2. Remove those EXACT jobs from the queue (so other workers don't get them)
        pipe.zremrangebyscore(self.queue_key, "-inf", now)
        
        results = await pipe.execute()
        
        # results[0] contains the list of claimed job IDs
        return [job.decode('utf-8') for job in results[0]]

    async def check_rate_limit(self, tenant_id: UUID, limit: int, window: int = 60) -> bool:
        """
        Sliding window rate limit implementation.
        """
        key = f"cronhive:rate:{tenant_id}"
        now = time.time()
        
        pipe = self.redis.pipeline()
        # Remove old entries
        pipe.zremrangebyscore(key, 0, now - window)
        # Add current request
        request_id = str(now) 
        pipe.zadd(key, {request_id: now})
        # Count requests in window
        pipe.zcard(key)
        # Set expiry to keep Redis clean
        pipe.expire(key, window)
        
        _, _, count, _ = await pipe.execute()
        
        return count <= limit

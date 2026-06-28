import asyncio
import logging
import signal
import sys
import uuid
import datetime
from datetime import timezone
import httpx
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.infrastructure.database.connection import async_session_maker
from src.infrastructure.queue.redis_queue import RedisQueue
from src.infrastructure.http.async_client import HttpClientWithCircuitBreaker
from src.infrastructure.database.repositories.job_repo import JobRepository
from src.infrastructure.database.repositories.execution_repo import ExecutionRepository
from src.domain.models import Job, Execution, ExecutionStatus
from src.domain.services.scheduler import calculate_next_run
from src.domain.services.retry import calculate_backoff
from src.domain.services.executor import execute_http_request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Worker:
    def __init__(self):
        self.redis_client = redis.from_url(settings.redis_url)
        self.queue = RedisQueue(self.redis_client)
        self.http_client = HttpClientWithCircuitBreaker()
        self.running = True

    def setup_signal_handlers(self):
        """Handle SIGTERM and SIGINT for graceful shutdown."""
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._signal_handler)

    def _signal_handler(self):
        logger.info("Received shutdown signal, draining in-flight jobs...")
        self.running = False

    async def run(self):
        """Main worker loop."""
        self.setup_signal_handlers()
        logger.info("Queue poller started.")

        while self.running:
            try:
                # 1. Claim jobs from Redis (atomic)
                job_ids = await self.queue.claim_due_jobs(batch_size=10)
                
                if not job_ids:
                    await asyncio.sleep(1) # Wait before polling again
                    continue
                    
                # 2. Process jobs concurrently
                tasks = [self.process_job(job_id) for job_id in job_ids]
                await asyncio.gather(*tasks)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                await asyncio.sleep(5)
                
        # Graceful shutdown
        await self.http_client.close()
        await self.redis_client.close()
        logger.info("Queue poller shutdown complete.")

    async def process_job(self, job_id_str: str):
        """Executes a single job."""
        job_id = uuid.UUID(job_id_str)
        
        async with async_session_maker() as session:
            job_repo = JobRepository(session)
            exec_repo = ExecutionRepository(session)
            
            job = await job_repo.get_by_id(job_id)
            if not job or job.status.value != "active":
                return # Job was deleted or paused since it was enqueued
                
            # Create execution record
            execution = Execution(job_id=job.id)
            execution = await exec_repo.create(execution)
            
            # Execute HTTP request
            status, http_code, body_preview, duration, error_msg = await execute_http_request(
                self.http_client,
                job.http_method,
                job.target_url,
                job.headers,
                job.payload,
                job.timeout_seconds
            )
            
            # Update execution
            execution.status = status
            execution.http_status_code = http_code
            execution.response_body_preview = body_preview
            execution.duration_ms = duration
            execution.error_message = error_msg
            execution.completed_at = datetime.datetime.now(timezone.utc)
            await exec_repo.update(execution)
            
            job.last_run_at = execution.completed_at
            
            if status == ExecutionStatus.SUCCESS:
                if job.cron_expression:
                    # Calculate next run and re-enqueue
                    job.next_run_at = calculate_next_run(job.cron_expression, execution.completed_at)
                    await self.queue.enqueue(job.id, job.next_run_at.timestamp())
                else:
                    # One-time job finished
                    job.next_run_at = None
            else:
                # Handle Failure / Retry
                if execution.attempt_number < job.max_retries:
                    # Retry
                    delay = calculate_backoff(execution.attempt_number, job.retry_backoff_base)
                    job.next_run_at = datetime.datetime.now(timezone.utc) + datetime.timedelta(seconds=delay)
                    await self.queue.enqueue(job.id, job.next_run_at.timestamp())
                else:
                    # Max retries exhausted - move to Dead Letter Queue
                    logger.error(f"Job {job.id} exhausted retries. Dead lettered.")
                    if job.cron_expression:
                         # Keep cron running even if this specific instance failed fully
                         job.next_run_at = calculate_next_run(job.cron_expression, execution.completed_at)
                         await self.queue.enqueue(job.id, job.next_run_at.timestamp())
                    else:
                         job.next_run_at = None
                    
            await job_repo.update(job)

if __name__ == "__main__":
    worker = Worker()
    asyncio.run(worker.run())

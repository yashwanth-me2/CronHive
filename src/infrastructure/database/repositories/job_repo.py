from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from src.infrastructure.database.models import DBJob, Tenant
from src.domain.models import Job, JobStatus

def to_domain(db_job: DBJob) -> Job:
    return Job(
        id=db_job.id,
        tenant_id=db_job.tenant_id,
        name=db_job.name,
        target_url=db_job.target_url,
        cron_expression=db_job.cron_expression,
        scheduled_at=db_job.scheduled_at,
        description=db_job.description,
        http_method=db_job.http_method,
        headers=db_job.headers,
        payload=db_job.payload,
        timeout_seconds=db_job.timeout_seconds,
        max_retries=db_job.max_retries,
        retry_backoff_base=db_job.retry_backoff_base,
        status=JobStatus(db_job.status),
        next_run_at=db_job.next_run_at,
        last_run_at=db_job.last_run_at,
        idempotency_key=db_job.idempotency_key,
        created_at=db_job.created_at,
        updated_at=db_job.updated_at
    )

def to_db(job: Job) -> DBJob:
    return DBJob(
        id=job.id,
        tenant_id=job.tenant_id,
        name=job.name,
        target_url=job.target_url,
        cron_expression=job.cron_expression,
        scheduled_at=job.scheduled_at,
        description=job.description,
        http_method=job.http_method,
        headers=job.headers,
        payload=job.payload,
        timeout_seconds=job.timeout_seconds,
        max_retries=job.max_retries,
        retry_backoff_base=job.retry_backoff_base,
        status=job.status.value,
        next_run_at=job.next_run_at,
        last_run_at=job.last_run_at,
        idempotency_key=job.idempotency_key,
        created_at=job.created_at,
        updated_at=job.updated_at
    )

class JobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, job: Job) -> Job:
        db_job = to_db(job)
        self.session.add(db_job)
        await self.session.commit()
        await self.session.refresh(db_job)
        return to_domain(db_job)

    async def get_by_id(self, job_id: UUID) -> Optional[Job]:
        stmt = select(DBJob).where(DBJob.id == job_id)
        result = await self.session.execute(stmt)
        db_job = result.scalar_one_or_none()
        return to_domain(db_job) if db_job else None

    async def get_by_tenant_and_id(self, tenant_id: UUID, job_id: UUID) -> Optional[Job]:
        stmt = select(DBJob).where(DBJob.id == job_id, DBJob.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        db_job = result.scalar_one_or_none()
        return to_domain(db_job) if db_job else None

    async def update(self, job: Job) -> Job:
        db_job = to_db(job)
        merged = await self.session.merge(db_job)
        await self.session.commit()
        return to_domain(merged)

    async def list_by_tenant(self, tenant_id: UUID, skip: int = 0, limit: int = 100) -> Tuple[List[Job], int]:
        count_stmt = select(func.count()).where(DBJob.tenant_id == tenant_id).select_from(DBJob)
        total_count = (await self.session.execute(count_stmt)).scalar()
        
        stmt = select(DBJob).where(DBJob.tenant_id == tenant_id).order_by(DBJob.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        jobs = [to_domain(j) for j in result.scalars().all()]
        
        return jobs, total_count

    async def find_due_jobs(self, limit: int = 100) -> List[Job]:
        """Finds jobs that are due for execution right now."""
        now = datetime.now(timezone.utc)
        stmt = select(DBJob).where(
            DBJob.status == JobStatus.ACTIVE.value,
            DBJob.next_run_at <= now
        ).order_by(DBJob.next_run_at.asc()).limit(limit)
        
        result = await self.session.execute(stmt)
        return [to_domain(j) for j in result.scalars().all()]

    async def delete(self, tenant_id: UUID, job_id: UUID) -> bool:
        from src.infrastructure.database.models import DBExecution
        # First delete executions
        await self.session.execute(delete(DBExecution).where(DBExecution.job_id == job_id))
        # Then delete job
        result = await self.session.execute(
            delete(DBJob).where(DBJob.id == job_id, DBJob.tenant_id == tenant_id)
        )
        await self.session.commit()
        return result.rowcount > 0

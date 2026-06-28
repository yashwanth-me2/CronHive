from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.infrastructure.database.models import DBExecution
from src.domain.models import Execution, ExecutionStatus

def to_domain(db_exec: DBExecution) -> Execution:
    return Execution(
        id=db_exec.id,
        job_id=db_exec.job_id,
        attempt_number=db_exec.attempt_number,
        status=ExecutionStatus(db_exec.status),
        http_status_code=db_exec.http_status_code,
        response_body_preview=db_exec.response_body_preview,
        duration_ms=db_exec.duration_ms,
        error_message=db_exec.error_message,
        started_at=db_exec.started_at,
        completed_at=db_exec.completed_at,
        created_at=db_exec.created_at
    )

def to_db(execution: Execution) -> DBExecution:
    return DBExecution(
        id=execution.id,
        job_id=execution.job_id,
        attempt_number=execution.attempt_number,
        status=execution.status.value,
        http_status_code=execution.http_status_code,
        response_body_preview=execution.response_body_preview,
        duration_ms=execution.duration_ms,
        error_message=execution.error_message,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        created_at=execution.created_at
    )

class ExecutionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, execution: Execution) -> Execution:
        db_exec = to_db(execution)
        self.session.add(db_exec)
        await self.session.commit()
        await self.session.refresh(db_exec)
        return to_domain(db_exec)

    async def get_by_id(self, execution_id: UUID) -> Optional[Execution]:
        stmt = select(DBExecution).where(DBExecution.id == execution_id)
        result = await self.session.execute(stmt)
        db_exec = result.scalar_one_or_none()
        return to_domain(db_exec) if db_exec else None

    async def update(self, execution: Execution) -> Execution:
        db_exec = to_db(execution)
        merged = await self.session.merge(db_exec)
        await self.session.commit()
        return to_domain(merged)

    async def list_by_job(self, job_id: UUID, limit: int = 10) -> List[Execution]:
        stmt = select(DBExecution).where(DBExecution.job_id == job_id).order_by(DBExecution.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return [to_domain(e) for e in result.scalars().all()]

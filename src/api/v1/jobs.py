from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, List
import redis.asyncio as redis
from src.dependencies import get_db_session, get_current_tenant, get_redis
from src.infrastructure.database.models import Tenant
from src.infrastructure.database.repositories.job_repo import JobRepository
from src.infrastructure.database.repositories.execution_repo import ExecutionRepository
from src.infrastructure.queue.redis_queue import RedisQueue
from src.api.v1.schemas.job_schemas import JobCreate, JobResponse, ExecutionResponse
from src.application.commands.create_job import create_job_command
from src.application.commands.pause_job import pause_job_command
from src.application.commands.resume_job import resume_job_command
from src.application.commands.trigger_job import trigger_job_command
from src.application.commands.delete_job import delete_job_command

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])

@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_in: JobCreate,
    tenant: Annotated[Tenant, Depends(get_current_tenant)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    redis_client: Annotated[redis.Redis, Depends(get_redis)]
):
    job_repo = JobRepository(session)
    queue = RedisQueue(redis_client)
    
    try:
        job = await create_job_command(
            tenant_id=tenant.id,
            name=job_in.name,
            target_url=job_in.target_url,
            job_repo=job_repo,
            queue=queue,
            cron_expression=job_in.cron_expression,
            scheduled_at=job_in.scheduled_at,
            description=job_in.description,
            http_method=job_in.http_method,
            headers=job_in.headers,
            payload=job_in.payload
        )
        return job
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=List[JobResponse])
async def list_jobs(
    tenant: Annotated[Tenant, Depends(get_current_tenant)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    skip: int = 0,
    limit: int = 100
):
    job_repo = JobRepository(session)
    jobs, total = await job_repo.list_by_tenant(tenant.id, skip, limit)
    return jobs

@router.post("/{job_id}/pause", status_code=status.HTTP_200_OK)
async def pause_job(
    job_id: str,
    tenant: Annotated[Tenant, Depends(get_current_tenant)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    redis_client: Annotated[redis.Redis, Depends(get_redis)]
):
    import uuid
    job_repo = JobRepository(session)
    queue = RedisQueue(redis_client)
    try:
        await pause_job_command(tenant.id, uuid.UUID(job_id), job_repo, queue)
        return {"detail": "Job paused"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{job_id}/resume", status_code=status.HTTP_200_OK)
async def resume_job(
    job_id: str,
    tenant: Annotated[Tenant, Depends(get_current_tenant)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    redis_client: Annotated[redis.Redis, Depends(get_redis)]
):
    import uuid
    job_repo = JobRepository(session)
    queue = RedisQueue(redis_client)
    try:
        await resume_job_command(tenant.id, uuid.UUID(job_id), job_repo, queue)
        return {"detail": "Job resumed"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{job_id}/trigger", status_code=status.HTTP_200_OK)
async def trigger_job(
    job_id: str,
    tenant: Annotated[Tenant, Depends(get_current_tenant)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    redis_client: Annotated[redis.Redis, Depends(get_redis)]
):
    import uuid
    job_repo = JobRepository(session)
    queue = RedisQueue(redis_client)
    try:
        await trigger_job_command(tenant.id, uuid.UUID(job_id), job_repo, queue)
        return {"detail": "Job triggered for immediate execution"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{job_id}/executions", response_model=List[ExecutionResponse])
async def list_executions(
    job_id: str,
    tenant: Annotated[Tenant, Depends(get_current_tenant)],
    session: Annotated[AsyncSession, Depends(get_db_session)]
):
    import uuid
    job_repo = JobRepository(session)
    exec_repo = ExecutionRepository(session)
    job = await job_repo.get_by_tenant_and_id(tenant.id, uuid.UUID(job_id))
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    executions = await exec_repo.list_by_job(job.id, limit=20)
    return executions

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: str,
    tenant: Annotated[Tenant, Depends(get_current_tenant)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    redis_client: Annotated[redis.Redis, Depends(get_redis)]
):
    import uuid
    job_repo = JobRepository(session)
    queue = RedisQueue(redis_client)
    try:
        await delete_job_command(tenant.id, uuid.UUID(job_id), job_repo, queue)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

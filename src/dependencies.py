from typing import AsyncGenerator, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings
from src.infrastructure.database.connection import get_db_session
from src.infrastructure.database.models import Tenant
from sqlalchemy import select
from src.infrastructure.auth.jwt_handler import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    client = redis.from_url(settings.redis_url)
    try:
        yield client
    finally:
        await client.close()

async def get_current_tenant(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> Tenant:
    tenant_id = decode_token(token)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    stmt = select(Tenant).where(Tenant.id == tenant_id)
    result = await session.execute(stmt)
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

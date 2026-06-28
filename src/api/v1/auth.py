from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from src.infrastructure.database.connection import get_db_session
from src.infrastructure.database.models import Tenant
from src.infrastructure.auth.jwt_handler import hash_password, verify_password, create_access_token, generate_api_key
from src.api.v1.schemas.auth_schemas import TenantRegister, TenantResponse, Token

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/register", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def register(tenant_in: TenantRegister, session: Annotated[AsyncSession, Depends(get_db_session)]):
    stmt = select(Tenant).where(Tenant.email == tenant_in.email)
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    tenant = Tenant(
        name=tenant_in.name,
        email=tenant_in.email,
        hashed_password=hash_password(tenant_in.password),
        api_key=generate_api_key()
    )
    session.add(tenant)
    await session.commit()
    return tenant

@router.post("/login", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: Annotated[AsyncSession, Depends(get_db_session)]):
    stmt = select(Tenant).where(Tenant.email == form_data.username)
    tenant = (await session.execute(stmt)).scalar_one_or_none()
    if not tenant or not verify_password(form_data.password, tenant.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    access_token = create_access_token(tenant_id=str(tenant.id))
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/demo", response_model=Token)
async def login_demo(session: Annotated[AsyncSession, Depends(get_db_session)]):
    """Creates or logs into a demo tenant. Useful for the dashboard."""
    demo_email = "demo@cronhive.com"
    stmt = select(Tenant).where(Tenant.email == demo_email)
    tenant = (await session.execute(stmt)).scalar_one_or_none()
    
    if not tenant:
        tenant = Tenant(
            name="Demo User",
            email=demo_email,
            hashed_password=hash_password("demo123"),
            api_key=generate_api_key()
        )
        session.add(tenant)
        await session.commit()
        await session.refresh(tenant)
        
    access_token = create_access_token(tenant_id=str(tenant.id))
    return {"access_token": access_token, "token_type": "bearer"}

from src.dependencies import get_current_tenant

@router.get("/me", response_model=TenantResponse)
async def get_me(tenant: Annotated[Tenant, Depends(get_current_tenant)]):
    return tenant

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from src.config import settings
from src.infrastructure.database.models import Tenant, DBJob, DBExecution
from src.domain.models import JobStatus

async def seed():
    engine = create_async_engine(settings.database_url.replace("postgresql://", "postgresql+asyncpg://"))
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(select(Tenant).where(Tenant.email == "demo@cronhive.com"))
        tenant = result.scalar_one_or_none()
        if not tenant:
            from src.infrastructure.auth.jwt_handler import hash_password, generate_api_key
            tenant = Tenant(
                name="Demo User",
                email="demo@cronhive.com",
                hashed_password=hash_password("demo123"),
                api_key=generate_api_key()
            )
            session.add(tenant)
            await session.commit()
            await session.refresh(tenant)
            
        await session.execute(DBExecution.__table__.delete())
        await session.execute(DBJob.__table__.delete())
        
        jobs = [
            DBJob(
                tenant_id=tenant.id,
                name="Nightly Database Backup (Prod)",
                target_url="https://api.internal.cronhive.com/v1/backups/start",
                cron_expression="0 2 * * *",
                description="Triggers full pg_dump and uploads to S3",
                status=JobStatus.ACTIVE.value
            ),
            DBJob(
                tenant_id=tenant.id,
                name="Sync Stripe Customers",
                target_url="https://api.billing.cronhive.com/sync",
                cron_expression="*/15 * * * *",
                description="Syncs latest Stripe webhooks to internal DB",
                status=JobStatus.ACTIVE.value
            ),
            DBJob(
                tenant_id=tenant.id,
                name="Send Marketing Engagement Emails",
                target_url="https://api.marketing.cronhive.com/campaigns/daily",
                cron_expression="0 9 * * *",
                description="Sends the morning digest to active users",
                status=JobStatus.ACTIVE.value
            ),
            DBJob(
                tenant_id=tenant.id,
                name="Purge Stale Cache",
                target_url="https://api.cache.cronhive.com/purge",
                cron_expression="0 * * * *",
                description="Clears Redis keys older than 24h",
                status=JobStatus.PAUSED.value
            )
        ]
        
        session.add_all(jobs)
        await session.commit()
        print("Seeded professional jobs successfully.")

if __name__ == "__main__":
    asyncio.run(seed())

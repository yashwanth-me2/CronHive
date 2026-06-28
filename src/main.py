from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from src.config import settings
from src.api.v1 import auth, jobs

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize resources
    from src.infrastructure.database.connection import engine
    from src.infrastructure.database.models import SQLModel
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    # Shutdown: Clean up resources

app = FastAPI(
    title="CronHive API",
    description="A reliable job scheduling and webhook delivery service.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
os.makedirs(frontend_dir, exist_ok=True)
app.mount("/dashboard", StaticFiles(directory=frontend_dir, html=True), name="frontend")

@app.get("/")
async def root():
    return RedirectResponse(url="/dashboard/")

app.include_router(auth.router)
app.include_router(jobs.router)

@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "environment": settings.environment}

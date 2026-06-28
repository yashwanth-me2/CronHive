from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class JobCreate(BaseModel):
    name: str
    target_url: str
    cron_expression: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    description: Optional[str] = None
    http_method: str = "POST"
    headers: Dict[str, str] = {}
    payload: Dict[str, Any] = {}

class JobResponse(BaseModel):
    id: UUID
    name: str
    target_url: str
    status: str
    cron_expression: Optional[str]
    next_run_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ExecutionResponse(BaseModel):
    id: UUID
    job_id: UUID
    attempt_number: int
    status: str
    http_status_code: Optional[int]
    duration_ms: float
    error_message: Optional[str]
    completed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

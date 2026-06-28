import jwt
from datetime import datetime, timedelta, timezone
import bcrypt
import secrets
from typing import Optional
from src.config import settings

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(tenant_id: str, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        
    to_encode = {"sub": tenant_id, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm="HS256")
    return encoded_jwt

def decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        tenant_id: str = payload.get("sub")
        return tenant_id
    except jwt.PyJWTError:
        return None

def generate_api_key() -> str:
    """Generate a secure random API key."""
    return f"ch_{secrets.token_urlsafe(32)}"

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    database_url: str
    redis_url: str
    jwt_secret: str
    environment: str = "development"
    
    # Scheduling settings
    max_jobs_per_tenant: int = 100
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

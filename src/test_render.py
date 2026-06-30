import os
import sys

# Simulate Render environment
os.environ["DATABASE_URL"] = "postgres://user:pass@host/db"

from src.config import settings
print(f"DATABASE_URL: {os.environ['DATABASE_URL']}")
print(f"settings.database_url: {settings.database_url}")
print(f"settings.get_database_url: {settings.get_database_url}")

# Test Alembic Config
from alembic.config import Config
alembic_cfg = Config("alembic.ini")
section = alembic_cfg.get_section(alembic_cfg.config_ini_section, {})
print(f"Original alembic section url: {section.get('sqlalchemy.url')}")

try:
    from alembic import command
    command.upgrade(alembic_cfg, "head")
except Exception as e:
    import traceback
    traceback.print_exc()

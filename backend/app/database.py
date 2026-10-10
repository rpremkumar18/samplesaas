import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models.base import Base

DATABASE_URL: str = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    try:
        from app.config import get_settings

        DATABASE_URL = str(get_settings().DATABASE_URL)
    except Exception:  # settings missing or invalid
        DATABASE_URL = ""

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

__all__ = ["Base", "engine", "SessionLocal", "get_db"]


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

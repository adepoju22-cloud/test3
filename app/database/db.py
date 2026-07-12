"""
SQLAlchemy engine, session factory, and declarative base for the
Security Compliance Dashboard. Uses SQLite as the local, file-based
database so the entire project runs without any external services.
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.utils.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# SQLite requires this connect_arg when used with multiple threads, which is
# the case for a FastAPI app running under uvicorn's worker threads.
connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()


def init_db() -> None:
    """Create all database tables if they do not already exist."""
    from app.database import models  # noqa: F401  (ensures models are registered)

    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized at %s", settings.database_url)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session and guarantees it is
    closed after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Context manager for use outside of FastAPI request handling (e.g. in the
    scanner service or CLI scripts). Commits on success, rolls back on error.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

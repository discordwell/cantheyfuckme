import logging
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import DATABASE_URL

logger = logging.getLogger(__name__)

Base = declarative_base()
db_engine = None
SessionLocal = None
_tables_ready = False


def utcnow() -> datetime:
    """Naive UTC timestamp, matching the DateTime columns and existing rows.

    datetime.utcnow() is deprecated on Python 3.12; this keeps its semantics.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _ensure_tables() -> bool:
    """Create tables if not yet created; safe to retry while the DB comes up."""
    global _tables_ready
    if _tables_ready or db_engine is None:
        return _tables_ready
    try:
        Base.metadata.create_all(bind=db_engine)
        _tables_ready = True
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning("Database table creation failed (will retry on next request): %s", e)
    return _tables_ready


def init_db():
    global db_engine, SessionLocal
    if DATABASE_URL:
        db_url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        # pre_ping revalidates pooled connections, so a Postgres restart does
        # not surface as one-off errors on the requests that follow it.
        db_engine = create_engine(db_url, pool_pre_ping=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
        _ensure_tables()
        return True
    logger.info("DATABASE_URL not set - running without database storage")
    return False


def get_db():
    if SessionLocal is None:
        return None
    if not _tables_ready:
        _ensure_tables()
    return SessionLocal()

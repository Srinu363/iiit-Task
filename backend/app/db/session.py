"""Database session management."""

from sqlalchemy.orm import sessionmaker, Session

from backend.app.db.base import get_engine

_session_factory: sessionmaker | None = None


def get_session_factory() -> sessionmaker:
    """Get or create the session factory (lazy singleton)."""
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    return _session_factory


def get_db() -> Session:
    """FastAPI dependency that yields a database session."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session  # type: ignore[misc]
    finally:
        session.close()

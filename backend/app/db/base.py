"""SQLAlchemy database base and engine setup."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase

from backend.app.core.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""
    pass


def get_engine():
    """Create the database engine."""
    connect_args = {}
    if settings.database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_engine(
        settings.database_url,
        connect_args=connect_args,
        echo=settings.debug,
    )

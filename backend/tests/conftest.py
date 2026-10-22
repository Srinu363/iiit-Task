"""Test fixtures and shared test configuration."""

import sys
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker, Session

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.app.db.base import Base
from backend.app.db.session import get_db

# Single shared in-memory engine using StaticPool so all connections
# share the same in-memory database
_test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(autouse=True)
def _setup_tables():
    """Create tables before each test and drop after."""
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


_TestSession = sessionmaker(bind=_test_engine, expire_on_commit=False)


def _get_test_db() -> Generator[Session, None, None]:
    """Replacement for get_db that uses the test engine."""
    session = _TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client with test database."""
    from backend.app.main import create_app

    app = create_app()
    app.dependency_overrides[get_db] = _get_test_db

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_image_bytes() -> bytes:
    """Generate a minimal valid PNG image for testing."""
    import numpy as np
    import cv2

    img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    _, buffer = cv2.imencode(".png", img)
    return buffer.tobytes()

"""Structured logging with request IDs."""

import logging
import sys
import uuid
from contextvars import ContextVar

from backend.app.core.config import settings

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class RequestIdFilter(logging.Filter):
    """Injects request_id into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get("")  # type: ignore[attr-defined]
        return True


def setup_logging() -> logging.Logger:
    """Configure structured logging for the application."""
    logger = logging.getLogger("iqd")
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIdFilter())

    fmt = "[%(asctime)s] %(levelname)s [%(request_id)s] %(name)s: %(message)s"
    handler.setFormatter(logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S"))

    logger.addHandler(handler)
    return logger


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return uuid.uuid4().hex[:12]


logger = setup_logging()

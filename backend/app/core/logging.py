"""Structured logging configuration (structlog). No print() anywhere in the app."""

import logging
import sys

import structlog

from app.core.config import settings


def configure_logging() -> None:
    """Configure structlog: JSON in production, human-friendly console in dev."""
    level = logging.getLevelName(settings.log_level.upper())
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level)

    renderer = (
        structlog.dev.ConsoleRenderer() if settings.debug else structlog.processors.JSONRenderer()
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)

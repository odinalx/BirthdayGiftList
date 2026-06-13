"""Structured logging configuration for the backend."""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from app.config import settings


class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add location info
        if record.pathname and record.lineno:
            log_entry["location"] = {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        extra_keys = set(record.__dict__.keys()) - {
            "name",
            "msg",
            "args",
            "created",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "exc_info",
            "exc_text",
            "thread",
            "threadName",
            "taskName",
            "message",
        }
        for key in extra_keys:
            log_entry[key] = getattr(record, key)

        return json.dumps(log_entry)


class StandardFormatter(logging.Formatter):
    """Standard formatter for development/readable logs."""

    def format(self, record: logging.LogRecord) -> str:
        # Include extra fields in the message
        extra_keys = set(record.__dict__.keys()) - {
            "name",
            "msg",
            "args",
            "created",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "exc_info",
            "exc_text",
            "thread",
            "threadName",
            "taskName",
            "message",
        }
        extras = {k: getattr(record, k) for k in extra_keys}

        base_msg = super().format(record)
        if extras:
            extra_str = " | " + " ".join(f"{k}={v}" for k, v in extras.items())
            return base_msg + extra_str
        return base_msg


def setup_logging() -> None:
    """Configure logging for the application."""
    # Determine log level
    log_level = logging.DEBUG if settings.debug else logging.INFO

    # Choose formatter based on environment
    # Use JSON in production, standard format in development for readability
    if settings.debug:
        formatter = StandardFormatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        formatter = JsonFormatter()

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Add stdout handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.debug else logging.WARNING
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name.

    Usage:
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        logger.info("User logged in", extra={"user_id": user.id})
    """
    return logging.getLogger(name)

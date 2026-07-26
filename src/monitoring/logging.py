"""
Structured logging configuration for Azure AI Infrastructure Platform

This module provides:
- Structured logging in JSON format
- Correlation ID tracking
- Log level configuration
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from src.config.settings import get_settings


class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for logs"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add correlation ID if available
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id

        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging():
    """Configure structured logging"""
    settings = get_settings()

    # Set log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(level=log_level)

    # Create JSON handler
    json_handler = logging.StreamHandler()
    json_handler.setFormatter(StructuredFormatter())

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers = [json_handler]
    root_logger.setLevel(log_level)

    # Set Azure SDK logging
    azure_logger = logging.getLogger("azure")
    azure_logger.setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str, correlation_id: Optional[str] = None) -> logging.Logger:
    """
    Get a logger with optional correlation ID

    Args:
        name: Logger name
        correlation_id: Optional correlation ID

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)

    if correlation_id:
        logger = logging.LoggerAdapter(logger, {"correlation_id": correlation_id})

    return logger


class CorrelationIdFilter(logging.Filter):
    """Filter to add correlation ID to all logs"""

    def __init__(self, correlation_id: str):
        self.correlation_id = correlation_id
        super().__init__()

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = self.correlation_id
        return True


def generate_correlation_id() -> str:
    """Generate a unique correlation ID"""
    return str(uuid.uuid4())

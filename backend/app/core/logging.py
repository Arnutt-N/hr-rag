"""Structured logging configuration using structlog.

Usage:
    import structlog
    logger = structlog.get_logger()
    
    logger.info("user_login", user_id=123, ip="192.168.1.1")
    logger.warning("rate_limit_exceeded", ip="...", endpoint="/auth/login")
    logger.error("request_failed", error=str(e), path="/api/chat")
"""

import sys
import structlog
import logging


def setup_logging() -> None:
    """Configure structlog for JSON structured logging."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structlog logger instance.
    
    Args:
        name: Optional logger name (typically __name__)
        
    Returns:
        Configured structlog bound logger
    """
    return structlog.get_logger(name)

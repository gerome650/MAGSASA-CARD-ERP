"""
Structured JSON logger with automatic trace context injection.

Provides structured logging that integrates seamlessly with distributed tracing.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from observability.tracing.otel_tracer import get_trace_context


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON with trace context.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format
        
        Returns:
            JSON-formatted log string
        """
        # Get trace context
        trace_context = get_trace_context()
        
        # Build base log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": trace_context.get("trace_id"),
            "span_id": trace_context.get("span_id")
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)
        
        # Add standard fields
        log_entry["module"] = record.module
        log_entry["function"] = record.funcName
        log_entry["line"] = record.lineno
        
        return json.dumps(log_entry)


class StructuredLogger:
    """
    Structured logger wrapper that automatically injects trace context.
    """
    
    def __init__(self, name: str, level: int = logging.INFO):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name (typically __name__)
            level: Logging level
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Add structured handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(handler)
        
        # Prevent propagation to avoid duplicate logs
        self.logger.propagate = False
    
    def _log(self, level: int, message: str, extra_fields: Optional[Dict[str, Any]] = None):
        """
        Internal log method with extra fields support.
        
        Args:
            level: Log level
            message: Log message
            extra_fields: Additional fields to include in log
        """
        if extra_fields:
            # Create a LogRecord with extra fields
            record = self.logger.makeRecord(
                self.logger.name,
                level,
                "(unknown file)",
                0,
                message,
                (),
                None
            )
            record.extra_fields = extra_fields
            self.logger.handle(record)
        else:
            self.logger.log(level, message)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional extra fields"""
        self._log(logging.DEBUG, message, kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message with optional extra fields"""
        self._log(logging.INFO, message, kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional extra fields"""
        self._log(logging.WARNING, message, kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with optional extra fields"""
        self._log(logging.ERROR, message, kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with optional extra fields"""
        self._log(logging.CRITICAL, message, kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        self._log(logging.ERROR, message, kwargs)


# Global logger cache
_loggers: Dict[str, StructuredLogger] = {}


def get_logger(name: str = __name__, level: int = logging.INFO) -> StructuredLogger:
    """
    Get or create a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        level: Logging level
    
    Returns:
        StructuredLogger instance
    
    Usage:
        from observability.logging.structured_logger import get_logger
        
        logger = get_logger(__name__)
        
        logger.info("Processing started", user_id="123", order_id="456")
        logger.error("Payment failed", error="Insufficient funds", amount=1000)
    """
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name, level)
    return _loggers[name]


def configure_root_logger(level: int = logging.INFO):
    """
    Configure the root logger with structured formatting.
    
    Args:
        level: Logging level for root logger
    
    Usage:
        from observability.logging.structured_logger import configure_root_logger
        
        configure_root_logger(logging.INFO)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Add structured handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(handler)


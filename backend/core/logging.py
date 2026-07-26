import logging
import json
import sys
from datetime import datetime, timezone


class StructuredFormatter(logging.Formatter):
    """JSON-structured log formatter for production observability."""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Merge structured extras from extra={} kwargs
        standard_attrs = {
            "name", "msg", "args", "created", "filename", "funcName",
            "levelname", "levelno", "lineno", "module", "msecs", "pathname",
            "process", "processName", "relativeCreated", "stack_info",
            "thread", "threadName", "exc_info", "exc_text", "message",
            "taskName",
        }
        for key, value in record.__dict__.items():
            if key not in standard_attrs and not key.startswith("_"):
                log_entry[key] = value
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = str(record.exc_info[1])
        return json.dumps(log_entry, default=str)


class HumanFormatter(logging.Formatter):
    """Human-readable formatter for local development."""
    FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    def __init__(self):
        super().__init__(self.FORMAT)


def setup_logging(log_format: str = "json", level: str = "INFO"):
    """Configure application-wide structured logging.
    
    Args:
        log_format: 'json' for production, 'text' for local dev.
        level: Logging level string.
    """
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    if log_format == "json":
        handler.setFormatter(StructuredFormatter())
    else:
        handler.setFormatter(HumanFormatter())
    root.addHandler(handler)

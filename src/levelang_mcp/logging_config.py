"""Logging configuration for production and development environments.

- **JSON format** (``log_format="json"``): machine-readable, one JSON object
  per line.  Best for cloud / container deployments where logs are ingested
  by a collector (CloudWatch, Datadog, etc.).
- **Text format** (``log_format="text"``): human-readable with timestamps.
  Best for local development and stdio transport.
- **Auto** (``log_format="auto"``): resolved by the caller based on
  transport — JSON for ``streamable-http``, text for ``stdio``.
"""

from __future__ import annotations

import json
import logging

from datetime import UTC, datetime


class JSONFormatter(logging.Formatter):
    """Emit each log record as a single-line JSON object.

    Fields: ``timestamp`` (ISO-8601 UTC), ``level``, ``logger``, ``message``.
    If the record carries exception info it is included under ``exception``.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, str] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data, default=str)


_TEXT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_TEXT_DATEFMT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    *,
    log_level: str = "INFO",
    log_format: str = "text",
) -> None:
    """Configure logging for the ``levelang_mcp`` package.

    Call once at startup (from ``__main__``) before any other work.

    Parameters
    ----------
    log_level:
        Python log level name (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    log_format:
        ``"json"`` for structured JSON output, ``"text"`` for
        human-readable output.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    if log_format == "json":
        formatter: logging.Formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(_TEXT_FORMAT, datefmt=_TEXT_DATEFMT)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    # Configure the package-level logger — all levelang_mcp.* loggers
    # inherit this handler.
    pkg_logger = logging.getLogger("levelang_mcp")
    pkg_logger.setLevel(level)
    pkg_logger.handlers = [handler]
    pkg_logger.propagate = False

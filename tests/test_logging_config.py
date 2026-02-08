"""Tests for logging configuration."""

from __future__ import annotations

import json
import logging

from levelang_mcp.logging_config import JSONFormatter, setup_logging


# ---------------------------------------------------------------------------
# JSONFormatter tests
# ---------------------------------------------------------------------------


class TestJSONFormatter:
    def _make_record(
        self,
        message: str = "hello",
        level: int = logging.INFO,
        name: str = "test.logger",
    ) -> logging.LogRecord:
        return logging.LogRecord(
            name=name,
            level=level,
            pathname="test.py",
            lineno=1,
            msg=message,
            args=(),
            exc_info=None,
        )

    def test_output_is_valid_json(self):
        fmt = JSONFormatter()
        record = self._make_record()
        output = fmt.format(record)
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_contains_required_fields(self):
        fmt = JSONFormatter()
        record = self._make_record(message="test msg", name="my.logger")
        parsed = json.loads(fmt.format(record))
        assert parsed["message"] == "test msg"
        assert parsed["logger"] == "my.logger"
        assert parsed["level"] == "INFO"
        assert "timestamp" in parsed

    def test_timestamp_is_utc_iso8601(self):
        fmt = JSONFormatter()
        record = self._make_record()
        parsed = json.loads(fmt.format(record))
        ts = parsed["timestamp"]
        # ISO 8601 with UTC offset
        assert ts.endswith(("+00:00", "Z"))

    def test_includes_exception_info(self):
        fmt = JSONFormatter()
        try:
            raise ValueError("boom")
        except ValueError:
            import sys

            record = self._make_record()
            record.exc_info = sys.exc_info()
        output = json.loads(fmt.format(record))
        assert "exception" in output
        assert "ValueError" in output["exception"]
        assert "boom" in output["exception"]

    def test_no_exception_key_when_no_error(self):
        fmt = JSONFormatter()
        record = self._make_record()
        output = json.loads(fmt.format(record))
        assert "exception" not in output

    def test_respects_log_level(self):
        fmt = JSONFormatter()
        record = self._make_record(level=logging.WARNING)
        parsed = json.loads(fmt.format(record))
        assert parsed["level"] == "WARNING"

    def test_single_line_output(self):
        fmt = JSONFormatter()
        record = self._make_record(message="line one\nline two")
        output = fmt.format(record)
        # The JSON itself should be a single line (no embedded newlines
        # outside of string values).
        assert output.count("\n") == 0


# ---------------------------------------------------------------------------
# setup_logging tests
# ---------------------------------------------------------------------------


class TestSetupLogging:
    def _cleanup_logger(self) -> None:
        """Remove handlers added by setup_logging."""
        pkg_logger = logging.getLogger("levelang_mcp")
        pkg_logger.handlers.clear()
        pkg_logger.propagate = True
        pkg_logger.setLevel(logging.WARNING)

    def test_json_format_uses_json_formatter(self):
        try:
            setup_logging(log_level="DEBUG", log_format="json")
            pkg_logger = logging.getLogger("levelang_mcp")
            assert len(pkg_logger.handlers) == 1
            assert isinstance(pkg_logger.handlers[0].formatter, JSONFormatter)
        finally:
            self._cleanup_logger()

    def test_text_format_uses_standard_formatter(self):
        try:
            setup_logging(log_level="INFO", log_format="text")
            pkg_logger = logging.getLogger("levelang_mcp")
            assert len(pkg_logger.handlers) == 1
            assert not isinstance(pkg_logger.handlers[0].formatter, JSONFormatter)
        finally:
            self._cleanup_logger()

    def test_sets_log_level(self):
        try:
            setup_logging(log_level="DEBUG", log_format="text")
            pkg_logger = logging.getLogger("levelang_mcp")
            assert pkg_logger.level == logging.DEBUG
        finally:
            self._cleanup_logger()

    def test_child_loggers_inherit(self):
        try:
            setup_logging(log_level="INFO", log_format="text")
            child = logging.getLogger("levelang_mcp.auth")
            # Child should inherit handlers via propagation being disabled
            # on the parent — but the child itself should be able to log
            # through the parent's handler.
            assert child.getEffectiveLevel() == logging.INFO
        finally:
            self._cleanup_logger()

    def test_does_not_propagate_to_root(self):
        try:
            setup_logging(log_level="INFO", log_format="text")
            pkg_logger = logging.getLogger("levelang_mcp")
            assert pkg_logger.propagate is False
        finally:
            self._cleanup_logger()

    def test_invalid_level_defaults_to_info(self):
        try:
            setup_logging(log_level="BANANA", log_format="text")
            pkg_logger = logging.getLogger("levelang_mcp")
            assert pkg_logger.level == logging.INFO
        finally:
            self._cleanup_logger()

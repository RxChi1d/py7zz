"""
Test suite for enhanced logging configuration.

Tests the comprehensive logging features including file logging,
structured logging, performance monitoring, and dynamic configuration.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

import py7zz
from py7zz.logging_config import (
    PerformanceLogger,
    StructuredFormatter,
    get_log_statistics,
    get_logging_config,
    log_performance,
    set_log_level,
)


class TestEnhancedLoggingSetup:
    """Test enhanced logging setup and configuration."""

    def test_basic_logging_setup(self):
        """Test basic logging configuration."""
        py7zz.setup_logging("INFO")
        config = get_logging_config()

        assert config["level"] == "INFO"
        assert config["console_enabled"] is True
        assert config["file_enabled"] is False

    def test_file_logging_setup(self):
        """Test file logging configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"

            py7zz.setup_logging("DEBUG", log_file=log_file)
            config = get_logging_config()

            assert config["file_enabled"] is True
            assert config["file_path"] == log_file

    def test_structured_logging_setup(self):
        """Test structured logging configuration."""
        py7zz.setup_logging("INFO", structured=True)
        config = get_logging_config()

        assert config["structured_logging"] is True

    def test_performance_monitoring_setup(self):
        """Test performance monitoring configuration."""
        py7zz.setup_logging("DEBUG", performance_monitoring=True)
        config = get_logging_config()

        assert config["performance_logging"] is True


class TestStructuredFormatter:
    """Test structured JSON formatter."""

    def test_basic_formatting(self):
        """Test basic structured log formatting."""
        import logging

        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)
        log_data = json.loads(formatted)

        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test.logger"
        assert log_data["message"] == "Test message"
        assert log_data["line"] == 42

    def test_exception_formatting(self):
        """Test exception information in structured logs."""
        import logging
        import sys

        formatter = StructuredFormatter()

        try:
            raise ValueError("Test exception")
        except ValueError:
            exc_info = sys.exc_info()
            record = logging.LogRecord(
                name="test.logger",
                level=logging.ERROR,
                pathname="test.py",
                lineno=42,
                msg="Error occurred",
                args=(),
                exc_info=exc_info,
            )

        formatted = formatter.format(record)
        log_data = json.loads(formatted)

        assert "exception" in log_data
        assert log_data["exception"]["type"] == "ValueError"
        assert log_data["exception"]["message"] == "Test exception"


class TestFileLogging:
    """Test file logging functionality."""

    def test_enable_file_logging(self):
        """Test enabling file logging."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"

            py7zz.enable_file_logging(log_file)

            # Create a test log
            logger = py7zz.logging_config.get_logger("test")
            logger.info("Test file logging")

            assert log_file.exists()
            content = log_file.read_text()
            assert "Test file logging" in content

    def test_disable_file_logging(self):
        """Test disabling file logging."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"

            # Enable then disable
            py7zz.enable_file_logging(log_file)
            py7zz.disable_file_logging()

            config = get_logging_config()
            assert config["file_enabled"] is False


class TestPerformanceLogging:
    """Test performance logging features."""

    def test_performance_context_manager(self):
        """Test PerformanceLogger context manager."""
        with patch("py7zz.logging_config.logging.getLogger") as mock_get_logger:
            mock_logger = mock_get_logger.return_value

            with PerformanceLogger("test_operation"):
                pass

            # Should have called debug twice (start and end)
            assert mock_logger.debug.call_count == 2

    def test_performance_decorator(self):
        """Test log_performance decorator."""
        with patch("py7zz.logging_config.logging.getLogger") as mock_get_logger:
            mock_logger = mock_get_logger.return_value

            @log_performance("decorated_function")
            def test_func():
                return "result"

            result = test_func()

            assert result == "result"
            assert mock_logger.debug.call_count == 2


class TestDynamicConfiguration:
    """Test dynamic logging configuration changes."""

    def test_set_log_level(self):
        """Test dynamic log level changes."""
        py7zz.setup_logging("INFO")

        set_log_level("DEBUG")
        config = get_logging_config()

        assert config["level"] == "DEBUG"

    def test_enable_structured_logging(self):
        """Test enabling structured logging dynamically."""
        py7zz.setup_logging("INFO")
        py7zz.enable_structured_logging(True)

        config = get_logging_config()
        assert config["structured_logging"] is True

    def test_enable_performance_monitoring(self):
        """Test enabling performance monitoring dynamically."""
        py7zz.setup_logging("INFO")
        py7zz.enable_performance_monitoring(True)

        config = get_logging_config()
        assert config["performance_logging"] is True


class TestLoggingStatistics:
    """Test logging statistics and information."""

    def test_get_log_statistics(self):
        """Test getting logging statistics."""
        py7zz.setup_logging("INFO")
        stats = get_log_statistics()

        assert "config" in stats
        assert "active_handlers" in stats
        assert "loggers" in stats
        assert len(stats["loggers"]) >= 1

    def test_get_logging_config(self):
        """Test getting current logging configuration."""
        py7zz.setup_logging("DEBUG", enable_filename_warnings=False)
        config = get_logging_config()

        assert config["level"] == "DEBUG"
        assert config["filename_warnings"] is False


class TestCompatibility:
    """Test backward compatibility with existing logging."""

    def test_legacy_functions_work(self):
        """Test that legacy logging functions still work."""
        # These should not raise exceptions
        py7zz.enable_debug_logging()
        py7zz.disable_warnings()

        config = get_logging_config()
        assert config["level"] == "DEBUG"

    def test_get_logger_function(self):
        """Test get_logger function works correctly."""
        logger = py7zz.logging_config.get_logger("test.module")
        assert logger.name == "py7zz.module"  # Takes last part after dot


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

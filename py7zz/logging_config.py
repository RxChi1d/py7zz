# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""
Logging configuration for py7zz.

Provides centralized logging setup with appropriate levels, formatters,
and logging management features for different types of operations.
Includes support for file logging, structured logging, and performance monitoring.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union, overload

# Global logging configuration state
_logging_config = {
    "level": "INFO",
    "console_enabled": True,
    "file_enabled": False,
    "file_path": None,
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5,
    "filename_warnings": True,
    "performance_logging": False,
    "structured_logging": False,
}

# Active handlers registry
_active_handlers: Dict[str, logging.Handler] = {}


def setup_logging(
    level: str = "INFO",
    enable_filename_warnings: bool = True,
    console_output: bool = True,
    log_file: Optional[Union[str, Path]] = None,
    max_file_size: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    structured: bool = False,
    performance_monitoring: bool = False,
) -> None:
    """
    Logging setup for py7zz with configuration options.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        enable_filename_warnings: Whether to show filename compatibility warnings
        console_output: Whether to output logs to console
        log_file: Path for log file output (enables file logging if provided)
        max_file_size: Maximum size of log file before rotation (bytes)
        backup_count: Number of backup log files to keep
        structured: Whether to use structured JSON logging format
        performance_monitoring: Whether to enable performance logging

    Example:
        >>> import py7zz
        >>> # Basic console logging
        >>> py7zz.setup_logging("DEBUG")

        >>> # File logging with rotation
        >>> py7zz.setup_logging("INFO", log_file="py7zz.log", max_file_size=5*1024*1024)

        >>> # Structured logging for analysis
        >>> py7zz.setup_logging("INFO", structured=True, performance_monitoring=True)
    """
    # Clear existing handlers to avoid duplicates
    clear_logging_handlers()

    # Update global configuration
    _logging_config.update(
        {
            "level": level,
            "console_enabled": console_output,
            "file_enabled": log_file is not None,
            "file_path": log_file,
            "max_file_size": max_file_size,
            "backup_count": backup_count,
            "filename_warnings": enable_filename_warnings,
            "structured_logging": structured,
            "performance_logging": performance_monitoring,
        }
    )

    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Create formatters
    formatter: logging.Formatter
    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s [py7zz.%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Configure main py7zz logger
    py7zz_logger = logging.getLogger("py7zz")
    py7zz_logger.setLevel(numeric_level)
    py7zz_logger.handlers.clear()

    # Setup console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(numeric_level)
        py7zz_logger.addHandler(console_handler)
        _active_handlers["console"] = console_handler

    # Setup file handler with rotation
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_path, maxBytes=max_file_size, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(numeric_level)
        py7zz_logger.addHandler(file_handler)
        _active_handlers["file"] = file_handler

    py7zz_logger.propagate = False

    # Special handling for filename compatibility warnings
    if enable_filename_warnings:
        _setup_filename_warnings(numeric_level, structured, console_output, log_file)

    # Setup performance monitoring if enabled
    if performance_monitoring:
        _setup_performance_logging(numeric_level, structured)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        import json
        import traceback
        from datetime import datetime

        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info and isinstance(record.exc_info, tuple):
            exc_type, exc_value, exc_traceback = record.exc_info
            if exc_type is not None:
                log_data["exception"] = {
                    "type": exc_type.__name__,
                    "message": str(exc_value),
                    "traceback": traceback.format_exception(*record.exc_info),
                }

        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in (
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "exc_info",
                "exc_text",
                "stack_info",
            ):
                if "extra" not in log_data:
                    log_data["extra"] = {}
                extra_dict = log_data["extra"]
                if isinstance(extra_dict, dict):
                    extra_dict[key] = str(value) if value is not None else None

        return json.dumps(log_data, ensure_ascii=False)


def _setup_filename_warnings(
    numeric_level: int,
    structured: bool,
    console_output: bool,
    log_file: Optional[Union[str, Path]],
) -> None:
    """Setup special handling for filename compatibility warnings."""
    sanitizer_logger = logging.getLogger("py7zz.filename_sanitizer")
    sanitizer_logger.setLevel(logging.WARNING)
    sanitizer_logger.handlers.clear()

    # Create formatter for warnings
    warning_formatter: logging.Formatter
    if structured:
        warning_formatter = StructuredFormatter()
    else:
        warning_formatter = logging.Formatter(fmt="%(levelname)s [py7zz] %(message)s")

    # Create separate handler for filename warnings if needed
    if numeric_level > logging.WARNING:
        if console_output:
            warning_handler = logging.StreamHandler(sys.stderr)
            warning_handler.setFormatter(warning_formatter)
            warning_handler.setLevel(logging.WARNING)
            sanitizer_logger.addHandler(warning_handler)
            _active_handlers["filename_warnings"] = warning_handler

        if log_file:
            log_path = Path(log_file)
            file_warning_handler = logging.handlers.RotatingFileHandler(
                log_path,
                maxBytes=int(_logging_config["max_file_size"])
                if isinstance(_logging_config["max_file_size"], (int, str))
                else 10 * 1024 * 1024,
                backupCount=int(_logging_config["backup_count"])
                if isinstance(_logging_config["backup_count"], (int, str))
                else 5,
                encoding="utf-8",
            )
            file_warning_handler.setFormatter(warning_formatter)
            file_warning_handler.setLevel(logging.WARNING)
            sanitizer_logger.addHandler(file_warning_handler)

        sanitizer_logger.propagate = False


def _setup_performance_logging(numeric_level: int, structured: bool) -> None:
    """Setup performance monitoring logging."""
    perf_logger = logging.getLogger("py7zz.performance")
    perf_logger.setLevel(logging.DEBUG)
    perf_logger.handlers.clear()

    # Create performance-specific formatter
    perf_formatter: logging.Formatter
    if structured:
        perf_formatter = StructuredFormatter()
    else:
        perf_formatter = logging.Formatter(
            fmt="%(asctime)s PERF [py7zz.%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S.%f",
        )

    # Use existing handlers but with performance formatter
    if "console" in _active_handlers:
        perf_console_handler = logging.StreamHandler(sys.stderr)
        perf_console_handler.setFormatter(perf_formatter)
        perf_console_handler.setLevel(logging.DEBUG)
        perf_logger.addHandler(perf_console_handler)

    if "file" in _active_handlers:
        log_path = Path(str(_logging_config["file_path"]))
        perf_file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=int(_logging_config["max_file_size"])
            if isinstance(_logging_config["max_file_size"], (int, str))
            else 10 * 1024 * 1024,
            backupCount=int(_logging_config["backup_count"])
            if isinstance(_logging_config["backup_count"], (int, str))
            else 5,
            encoding="utf-8",
        )
        perf_file_handler.setFormatter(perf_formatter)
        perf_file_handler.setLevel(logging.DEBUG)
        perf_logger.addHandler(perf_file_handler)

    perf_logger.propagate = False


def clear_logging_handlers() -> None:
    """Clear all existing py7zz logging handlers."""
    for logger_name in ["py7zz", "py7zz.filename_sanitizer", "py7zz.performance"]:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()

    _active_handlers.clear()


def get_logging_config() -> Dict:
    """Get current logging configuration."""
    return _logging_config.copy()


def get_active_handlers() -> List[str]:
    """Get list of currently active handler types."""
    return list(_active_handlers.keys())


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for py7zz modules with proper integration.

    This function ensures proper integration with Python's standard
    logging system while maintaining py7zz-specific configuration.

    Args:
        name: Module name (should be __name__)

    Returns:
        Configured logger that inherits from py7zz root logger

    Example:
        >>> import logging
        >>> import py7zz
        >>>
        >>> # Standard Python logging configuration
        >>> logging.basicConfig(level=logging.INFO, format='%(name)s: %(message)s')
        >>>
        >>> # py7zz will respect this configuration
        >>> logger = py7zz.logging_config.get_logger(__name__)
        >>> logger.info("This follows standard Python logging patterns")
    """
    # Ensure the name starts with py7zz for proper hierarchy
    if not name.startswith("py7zz"):
        if name.startswith("__main__"):
            logger_name = "py7zz"
        else:
            # Extract module name and create proper hierarchy
            module_name = name.split(".")[-1] if "." in name else name
            logger_name = f"py7zz.{module_name}"
    else:
        logger_name = name

    logger = logging.getLogger(logger_name)

    # Ensure proper integration with standard logging
    if not logger.hasHandlers() and not _default_setup_done:
        ensure_default_logging()

    return logger


def enable_debug_logging() -> None:
    """Enable debug logging for troubleshooting."""
    setup_logging("DEBUG", enable_filename_warnings=True)


def disable_warnings() -> None:
    """Disable filename compatibility warnings."""
    sanitizer_logger = logging.getLogger("py7zz.filename_sanitizer")
    sanitizer_logger.setLevel(logging.ERROR)


def enable_file_logging(
    log_file: Union[str, Path],
    level: Optional[str] = None,
    max_size: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> None:
    """
    Enable file logging with current configuration.

    Args:
        log_file: Path to log file
        level: Logging level (uses current if None)
        max_size: Maximum file size before rotation
        backup_count: Number of backup files to keep
    """
    current_level = level or str(_logging_config["level"])
    setup_logging(
        level=current_level,
        enable_filename_warnings=bool(_logging_config["filename_warnings"]),
        console_output=bool(_logging_config["console_enabled"]),
        log_file=log_file,
        max_file_size=max_size,
        backup_count=backup_count,
        structured=bool(_logging_config["structured_logging"]),
        performance_monitoring=bool(_logging_config["performance_logging"]),
    )


def disable_file_logging() -> None:
    """Disable file logging while keeping console logging."""
    setup_logging(
        level=str(_logging_config["level"]),
        enable_filename_warnings=bool(_logging_config["filename_warnings"]),
        console_output=bool(_logging_config["console_enabled"]),
        log_file=None,
        structured=bool(_logging_config["structured_logging"]),
        performance_monitoring=bool(_logging_config["performance_logging"]),
    )


def enable_structured_logging(enable: bool = True) -> None:
    """
    Enable or disable structured JSON logging.

    Args:
        enable: Whether to enable structured logging
    """
    file_path = _logging_config["file_path"]
    setup_logging(
        level=str(_logging_config["level"]),
        enable_filename_warnings=bool(_logging_config["filename_warnings"]),
        console_output=bool(_logging_config["console_enabled"]),
        log_file=str(file_path) if file_path else None,
        max_file_size=int(_logging_config["max_file_size"])
        if isinstance(_logging_config["max_file_size"], (int, str))
        else 10 * 1024 * 1024,
        backup_count=int(_logging_config["backup_count"])
        if isinstance(_logging_config["backup_count"], (int, str))
        else 5,
        structured=enable,
        performance_monitoring=bool(_logging_config["performance_logging"]),
    )


def enable_performance_monitoring(enable: bool = True) -> None:
    """
    Enable or disable performance monitoring logging.

    Args:
        enable: Whether to enable performance logging
    """
    file_path = _logging_config["file_path"]
    setup_logging(
        level=str(_logging_config["level"]),
        enable_filename_warnings=bool(_logging_config["filename_warnings"]),
        console_output=bool(_logging_config["console_enabled"]),
        log_file=str(file_path) if file_path else None,
        max_file_size=int(_logging_config["max_file_size"])
        if isinstance(_logging_config["max_file_size"], (int, str))
        else 10 * 1024 * 1024,
        backup_count=int(_logging_config["backup_count"])
        if isinstance(_logging_config["backup_count"], (int, str))
        else 5,
        structured=bool(_logging_config["structured_logging"]),
        performance_monitoring=enable,
    )


def set_log_level(level: str) -> None:
    """
    Change the logging level for all py7zz loggers.

    Args:
        level: New logging level (DEBUG, INFO, WARNING, ERROR)
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Update all py7zz loggers
    for logger_name in ["py7zz", "py7zz.filename_sanitizer", "py7zz.performance"]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(numeric_level)

        # Update handler levels too
        for handler in logger.handlers:
            if logger_name == "py7zz.filename_sanitizer":
                # Keep warnings at WARNING level minimum
                handler.setLevel(min(numeric_level, logging.WARNING))
            else:
                handler.setLevel(numeric_level)

    _logging_config["level"] = level


def get_log_statistics() -> Dict:
    """
    Get logging statistics and information.

    Returns:
        Dictionary with logging statistics
    """
    stats = {
        "config": get_logging_config(),
        "active_handlers": get_active_handlers(),
        "loggers": {},
    }

    # Get information about py7zz loggers
    for logger_name in ["py7zz", "py7zz.filename_sanitizer", "py7zz.performance"]:
        logger = logging.getLogger(logger_name)
        logger_stats = {
            "level": logging.getLevelName(logger.level),
            "effective_level": logging.getLevelName(logger.getEffectiveLevel()),
            "handler_count": len(logger.handlers),
            "propagate": logger.propagate,
        }
        loggers_dict = stats["loggers"]
        if isinstance(loggers_dict, dict):
            loggers_dict[logger_name] = logger_stats

    return stats


class PerformanceLogger:
    """Context manager for performance logging."""

    def __init__(
        self,
        operation: str,
        size: Optional[int] = None,
        logger_name: str = "py7zz.performance",
    ) -> None:
        self.operation = operation
        self.size = size
        self.logger = logging.getLogger(logger_name)
        self.start_time: Optional[float] = None

    def __enter__(self) -> "PerformanceLogger":
        import time

        self.start_time = time.perf_counter()
        size_info = f" (size: {self.size} bytes)" if self.size is not None else ""
        self.logger.debug(f"Started: {self.operation}{size_info}")
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[object],
    ) -> None:
        import time

        end_time = time.perf_counter()
        duration = end_time - (self.start_time or 0.0)
        size_info = f" (size: {self.size} bytes)" if self.size is not None else ""

        if exc_type:
            self.logger.error(
                f"Failed: {self.operation} (duration: {duration:.4f}s){size_info}",
                exc_info=True,
            )
        else:
            self.logger.debug(
                f"Completed: {self.operation} (duration: {duration:.4f}s){size_info}"
            )


def performance_decorator(
    operation: str,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator for performance logging.

    Args:
        operation: Description of the operation being logged
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with PerformanceLogger(operation):
                return func(*args, **kwargs)

        return wrapper

    return decorator


# Default logging setup
_default_setup_done = False


@overload
def log_performance(
    name_or_func: str,
    duration: None = None,
    size: Optional[int] = None,
    logger_name: str = "py7zz.performance",
    **kwargs: Any,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    pass


@overload
def log_performance(
    name_or_func: str,
    duration: float,
    size: Optional[int] = None,
    logger_name: str = "py7zz.performance",
    **kwargs: Any,
) -> None:
    pass


def log_performance(
    name_or_func: Union[str, Callable[..., Any]],
    duration: Optional[float] = None,
    size: Optional[int] = None,
    logger_name: str = "py7zz.performance",
    **kwargs: Any,
) -> Optional[Callable[[Callable[..., Any]], Callable[..., Any]]]:
    """
    Log performance data directly or use as decorator.

    Can be used in two ways:
    1. Direct function call: log_performance(name, duration, size=None)
    2. As decorator: @log_performance("operation_name")

    Args:
        name_or_func: Operation name (str) or function being decorated
        duration: Duration in seconds (for direct calls)
        size: Optional size in bytes
        logger_name: Logger name to use
        **kwargs: Additional performance data
    """
    # Check if being used as decorator
    if isinstance(name_or_func, str) and duration is None:
        # Decorator mode
        operation_name = name_or_func

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            def wrapper(*args: Any, **func_kwargs: Any) -> Any:
                import time

                # Log start (similar to PerformanceLogger.__enter__)
                logger = logging.getLogger(logger_name)
                size_info = f" (size: {size} bytes)" if size is not None else ""
                logger.debug(f"Started: {operation_name}{size_info}")

                start_time = time.perf_counter()
                try:
                    result = func(*args, **func_kwargs)
                    end_time = time.perf_counter()
                    actual_duration = end_time - start_time

                    # Log completion (similar to PerformanceLogger.__exit__)
                    logger.debug(
                        f"Completed: {operation_name} (duration: {actual_duration:.4f}s){size_info}"
                    )
                    return result
                except Exception:
                    end_time = time.perf_counter()
                    actual_duration = end_time - start_time

                    # Log failure (similar to PerformanceLogger.__exit__ with exception)
                    logger.error(
                        f"Failed: {operation_name} (duration: {actual_duration:.4f}s){size_info}"
                    )
                    raise

            return wrapper

        return decorator
    else:
        # Direct function call mode
        if isinstance(name_or_func, str) and duration is not None:
            _log_performance_data(name_or_func, duration, size, logger_name, **kwargs)
            return None  # Direct calls don't return a decorator
        else:
            raise ValueError(
                "Direct call mode requires name (str) and duration (float)"
            )


def _log_performance_data(
    name: str,
    duration: float,
    size: Optional[int] = None,
    logger_name: str = "py7zz.performance",
    **kwargs: Any,
) -> None:
    """
    Internal function to log performance data.

    Args:
        name: Operation name
        duration: Duration in seconds
        size: Optional size in bytes
        logger_name: Logger name to use
        **kwargs: Additional performance data
    """
    logger = logging.getLogger(logger_name)

    size_info = f" (size: {size} bytes)" if size is not None else ""
    extra_info = ""
    if kwargs:
        extra_items = [f"{k}: {v}" for k, v in kwargs.items()]
        extra_info = f" ({', '.join(extra_items)})"

    logger.debug(
        f"Performance: {name} (duration: {duration:.4f}s){size_info}{extra_info}"
    )


def ensure_default_logging() -> None:
    """Ensure default logging is set up (called automatically)."""
    global _default_setup_done
    if not _default_setup_done:
        setup_logging()
        _default_setup_done = True

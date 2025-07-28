"""
Logging configuration for py7zz.

Provides centralized logging setup with appropriate levels and formatters
for different types of operations, especially filename compatibility warnings.
"""

import logging
import sys


def setup_logging(level: str = "INFO", enable_filename_warnings: bool = True) -> None:
    """
    Setup logging for py7zz with appropriate configuration.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        enable_filename_warnings: Whether to show filename compatibility warnings
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(levelname)s [py7zz.%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Setup console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)

    # Configure py7zz loggers
    py7zz_logger = logging.getLogger("py7zz")
    py7zz_logger.setLevel(numeric_level)
    py7zz_logger.addHandler(console_handler)
    py7zz_logger.propagate = False

    # Special handling for filename compatibility warnings
    if enable_filename_warnings:
        # Ensure filename compatibility warnings are always shown
        sanitizer_logger = logging.getLogger("py7zz.filename_sanitizer")
        sanitizer_logger.setLevel(logging.WARNING)

        # Create a special formatter for filename warnings
        warning_formatter = logging.Formatter(fmt="%(levelname)s [py7zz] %(message)s")

        # Create separate handler for filename warnings if needed
        if numeric_level > logging.WARNING:
            warning_handler = logging.StreamHandler(sys.stderr)
            warning_handler.setFormatter(warning_formatter)
            warning_handler.setLevel(logging.WARNING)
            sanitizer_logger.addHandler(warning_handler)
            sanitizer_logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for py7zz modules.

    Args:
        name: Module name (should be __name__)

    Returns:
        Configured logger
    """
    # Ensure the name starts with py7zz
    if not name.startswith("py7zz"):
        if name.startswith("__main__"):
            logger_name = "py7zz"
        else:
            logger_name = f"py7zz.{name.split('.')[-1]}"
    else:
        logger_name = name

    return logging.getLogger(logger_name)


def enable_debug_logging() -> None:
    """Enable debug logging for troubleshooting."""
    setup_logging("DEBUG", enable_filename_warnings=True)


def disable_warnings() -> None:
    """Disable filename compatibility warnings."""
    sanitizer_logger = logging.getLogger("py7zz.filename_sanitizer")
    sanitizer_logger.setLevel(logging.ERROR)


# Default logging setup
_default_setup_done = False


def ensure_default_logging() -> None:
    """Ensure default logging is set up (called automatically)."""
    global _default_setup_done
    if not _default_setup_done:
        setup_logging()
        _default_setup_done = True

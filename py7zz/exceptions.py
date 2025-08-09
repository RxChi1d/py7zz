# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""
Unified exception handling system for py7zz.

Provides comprehensive error handling with context tracking, suggestions,
and decorator-based error handling across all API layers.
"""

import subprocess
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union


class Py7zzError(Exception):
    """Enhanced base exception class for all py7zz errors.

    Provides context tracking, error classification, and actionable suggestions.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
    ):
        super().__init__(message)
        self.error_code = error_code
        self.context = context or {}
        self.suggestions = suggestions or []
        self.error_type = self.__class__.__name__

    def get_detailed_info(self) -> Dict[str, Any]:
        """Get detailed error information for debugging."""
        return {
            "error_type": self.error_type,
            "message": str(self),
            "error_code": self.error_code,
            "context": self.context,
            "suggestions": self.suggestions,
        }

    def add_context(self, key: str, value: Any) -> None:
        """Add context information to the error."""
        self.context[key] = value

    def add_suggestion(self, suggestion: str) -> None:
        """Add an actionable suggestion to resolve the error."""
        self.suggestions.append(suggestion)


class FileNotFoundError(Py7zzError):
    """Raised when a required file or directory is not found."""

    def __init__(self, filename: Union[str, Path], message: Optional[str] = None):
        self.filename = str(filename)
        if message is None:
            message = f"File or directory not found: {self.filename}"
        super().__init__(message)


class ArchiveNotFoundError(FileNotFoundError):
    """Raised when an archive file is not found."""

    def __init__(self, archive_path: Union[str, Path]):
        super().__init__(archive_path, f"Archive file not found: {archive_path}")


class CompressionError(Py7zzError):
    """Raised when compression operation fails."""

    def __init__(self, reason: str, returncode: Optional[int] = None):
        self.reason = reason
        self.returncode = returncode
        message = f"Compression failed: {reason}"
        if returncode is not None:
            message += f" (exit code: {returncode})"
        super().__init__(message)


class ExtractionError(Py7zzError):
    """Raised when extraction operation fails."""

    def __init__(self, reason: str, returncode: Optional[int] = None):
        self.reason = reason
        self.returncode = returncode
        message = f"Extraction failed: {reason}"
        if returncode is not None:
            message += f" (exit code: {returncode})"
        super().__init__(message)


class CorruptedArchiveError(Py7zzError):
    """Raised when an archive is corrupted or invalid."""

    def __init__(self, archive_path: Union[str, Path], details: Optional[str] = None):
        self.archive_path = str(archive_path)
        self.details = details
        message = f"Archive is corrupted or invalid: {self.archive_path}"
        if details:
            message += f" ({details})"
        super().__init__(message)


class UnsupportedFormatError(Py7zzError):
    """Raised when trying to work with an unsupported archive format."""

    def __init__(self, format_name: str, supported_formats: Optional[List[str]] = None):
        self.format_name = format_name
        self.supported_formats = supported_formats or []
        message = f"Unsupported archive format: {format_name}"
        if self.supported_formats:
            message += f". Supported formats: {', '.join(self.supported_formats)}"
        super().__init__(message)


class PasswordRequiredError(Py7zzError):
    """Raised when an archive requires a password but none was provided."""

    def __init__(self, archive_path: Union[str, Path]):
        self.archive_path = str(archive_path)
        super().__init__(f"Archive requires a password: {self.archive_path}")


class InvalidPasswordError(Py7zzError):
    """Raised when an incorrect password is provided for an archive."""

    def __init__(self, archive_path: Union[str, Path]):
        self.archive_path = str(archive_path)
        super().__init__(f"Invalid password for archive: {self.archive_path}")


class BinaryNotFoundError(Py7zzError):
    """Raised when the 7zz binary cannot be found."""

    def __init__(self, details: Optional[str] = None):
        message = "7zz binary not found"
        if details:
            message += f": {details}"
        message += ". Please reinstall py7zz or set PY7ZZ_BINARY environment variable."
        super().__init__(message)


class InsufficientSpaceError(Py7zzError):
    """Raised when there's insufficient disk space for operation."""

    def __init__(
        self,
        required_space: Optional[int] = None,
        available_space: Optional[int] = None,
    ):
        self.required_space = required_space
        self.available_space = available_space
        message = "Insufficient disk space for operation"
        if required_space and available_space:
            message += f". Required: {required_space} bytes, Available: {available_space} bytes"
        super().__init__(message)


class ConfigurationError(Py7zzError):
    """Raised when there's an error in configuration parameters."""

    def __init__(self, parameter: str, value: str, reason: str):
        self.parameter = parameter
        self.value = value
        self.reason = reason
        super().__init__(f"Invalid configuration for {parameter}='{value}': {reason}")


class OperationTimeoutError(Py7zzError):
    """Raised when an operation times out."""

    def __init__(self, operation: str, timeout_seconds: int):
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        super().__init__(
            f"Operation '{operation}' timed out after {timeout_seconds} seconds"
        )


class FilenameCompatibilityError(Py7zzError):
    """Raised when filename compatibility issues are encountered during extraction."""

    def __init__(
        self,
        message: str,
        problematic_files: Optional[List[str]] = None,
        sanitized: bool = False,
    ):
        self.problematic_files = problematic_files or []
        self.sanitized = sanitized
        super().__init__(message)


# Decorator-based error handling system
def handle_7z_errors(func: Callable) -> Callable:
    """Decorator to handle 7zz subprocess errors uniformly."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except subprocess.CalledProcessError as e:
            # Analyze error output for specific error types
            stderr = e.stderr.decode() if e.stderr else ""
            stdout = e.stdout.decode() if e.stdout else ""

            # Classify error based on output
            if "Wrong password" in stderr or "Wrong password" in stdout:
                raise InvalidPasswordError("Archive password is incorrect") from e
            elif "Can not open" in stderr:
                if "as archive" in stderr:
                    raise CorruptedArchiveError(
                        "Unknown",
                        "Archive file appears to be corrupted or in unsupported format",
                    ) from e
                else:
                    raise ArchiveNotFoundError("Archive file not found") from e
            elif "No more files" in stderr:
                raise ExtractionError(
                    f"7zz extraction failed: {stderr}", e.returncode
                ) from e
            elif "Insufficient memory" in stderr:
                raise OperationError(
                    "Insufficient memory for operation",
                    error_code=e.returncode,
                    suggestions=[
                        "Try reducing compression level",
                        "Close other applications",
                    ],
                ) from e
            else:
                # Generic operation error
                error_msg = (
                    stderr
                    or stdout
                    or f"7zz command failed with exit code {e.returncode}"
                )
                raise OperationError(error_msg, error_code=e.returncode) from e
        except FileNotFoundError as e:
            raise ValidationError(f"File not found: {e.filename}") from e
        except PermissionError as e:
            raise ValidationError(f"Permission denied: {e.filename}") from e

    return wrapper


def handle_file_errors(func: Callable) -> Callable:
    """Decorator to handle file system errors uniformly."""
    import builtins  # Import builtins to access the built-in FileNotFoundError

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Use built-in exception classes instead of any custom ones
            if isinstance(e, builtins.FileNotFoundError):
                filename = getattr(e, "filename", None) or str(e)
                raise ValidationError(
                    f"File or directory not found: {filename}",
                    suggestions=["Check if the path exists", "Verify file permissions"],
                ) from e
            elif isinstance(e, builtins.PermissionError):
                filename = getattr(e, "filename", None) or str(e)
                raise ValidationError(
                    f"Permission denied: {filename}",
                    suggestions=[
                        "Check file permissions",
                        "Run with appropriate privileges",
                    ],
                ) from e
            elif isinstance(e, OSError):
                # OSError should be after more specific subclasses like FileNotFoundError and PermissionError
                raise OperationError(
                    f"System error: {e}",
                    suggestions=["Check disk space", "Verify path validity"],
                ) from e
            else:
                raise  # Re-raise other exceptions unchanged

    return wrapper


def handle_validation_errors(func: Callable) -> Callable:
    """Decorator to handle input validation errors uniformly."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except (ValueError, TypeError) as e:
            raise ValidationError(
                f"Invalid input: {e}",
                suggestions=[
                    "Check parameter types and values",
                    "Refer to API documentation",
                ],
            ) from e

    return wrapper


# Security-related exceptions
class ZipBombError(Py7zzError):
    """Raised when potential ZIP bomb patterns are detected."""

    def __init__(
        self,
        message: str,
        file_count: Optional[int] = None,
        compression_ratio: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        if file_count is not None:
            self.add_context("file_count", file_count)
        if compression_ratio is not None:
            self.add_context("compression_ratio", compression_ratio)


class SecurityError(Py7zzError):
    """Raised when security limits are exceeded."""

    def __init__(
        self, message: str, limit_type: Optional[str] = None, **kwargs: Any
    ) -> None:
        super().__init__(message, **kwargs)
        if limit_type:
            self.add_context("limit_type", limit_type)


# Enhanced exception classes with automatic error analysis
class ValidationError(Py7zzError):
    """Raised when input validation fails."""

    def __init__(
        self, message: str, parameter: Optional[str] = None, **kwargs: Any
    ) -> None:
        super().__init__(message, **kwargs)
        if parameter:
            self.add_context("parameter", parameter)


class OperationError(Py7zzError):
    """Raised when an operation fails during execution."""

    def __init__(
        self, message: str, operation: Optional[str] = None, **kwargs: Any
    ) -> None:
        super().__init__(message, **kwargs)
        if operation:
            self.add_context("operation", operation)


class CompatibilityError(Py7zzError):
    """Raised when compatibility issues are encountered."""

    def __init__(
        self, message: str, platform: Optional[str] = None, **kwargs: Any
    ) -> None:
        super().__init__(message, **kwargs)
        if platform:
            self.add_context("platform", platform)


# Utility functions for error classification
def classify_error_type(error: Exception) -> str:
    """Classify error type for logging and debugging."""
    if isinstance(error, ValidationError):
        return "validation"
    elif isinstance(error, OperationError):
        return "operation"
    elif isinstance(error, CompatibilityError):
        return "compatibility"
    elif isinstance(error, Py7zzError):
        return "py7zz"
    else:
        return "system"


def get_error_suggestions(error: Exception) -> List[str]:
    """Get actionable suggestions for resolving the error."""
    import builtins  # Import builtins to access built-in exceptions

    if hasattr(error, "suggestions"):
        return list(error.suggestions)

    # Default suggestions based on error type
    # Check both built-in and custom exceptions
    if isinstance(error, (builtins.FileNotFoundError, FileNotFoundError)):
        return ["Check if the file path is correct", "Verify file exists"]
    elif isinstance(error, (builtins.PermissionError, PermissionError)):
        return ["Check file permissions", "Run with administrator privileges"]
    elif isinstance(error, MemoryError):
        return [
            "Close other applications",
            "Try with smaller files",
            "Increase available memory",
        ]
    else:
        return ["Check the error message for details", "Refer to documentation"]


# Aliases for compatibility with standard library exceptions
PyFileNotFoundError = (
    FileNotFoundError  # Avoid conflict with built-in FileNotFoundError
)

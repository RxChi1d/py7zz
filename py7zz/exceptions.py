"""
Custom exception classes for py7zz.

Provides clear, actionable error messages for different failure scenarios.
"""

from pathlib import Path
from typing import List, Optional, Union


class Py7zzError(Exception):
    """Base exception class for all py7zz errors."""

    pass


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

    def __init__(self, required_space: Optional[int] = None, available_space: Optional[int] = None):
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
        super().__init__(f"Operation '{operation}' timed out after {timeout_seconds} seconds")


# Aliases for compatibility with standard library exceptions
PyFileNotFoundError = FileNotFoundError  # Avoid conflict with built-in FileNotFoundError

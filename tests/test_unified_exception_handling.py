# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""
Test suite for Unified Exception Handling System.

Tests all the enhanced exception handling features:
- Enhanced Py7zzError base class
- ValidationError, OperationError, CompatibilityError
- Decorator-based error handling
- Error utility functions
- Context tracking and suggestions
"""

import subprocess

import pytest

import py7zz


class TestEnhancedPy7zzError:
    """Test enhanced Py7zzError base exception class."""

    def test_basic_initialization(self):
        """Test basic Py7zzError initialization."""
        error = py7zz.Py7zzError("Test error message")

        assert str(error) == "Test error message"
        assert error.error_code is None
        assert error.context == {}
        assert error.suggestions == []
        assert error.error_type == "Py7zzError"

    def test_initialization_with_all_parameters(self):
        """Test Py7zzError initialization with all parameters."""
        context = {"operation": "extract", "file": "test.7z"}
        suggestions = ["Check file permissions", "Verify archive integrity"]

        error = py7zz.Py7zzError(
            "Complex error", error_code=2, context=context, suggestions=suggestions
        )

        assert str(error) == "Complex error"
        assert error.error_code == 2
        assert error.context == context
        assert error.suggestions == suggestions

    def test_get_detailed_info(self):
        """Test get_detailed_info method."""
        error = py7zz.Py7zzError(
            "Test error",
            error_code=1,
            context={"file": "test.7z"},
            suggestions=["Check file path"],
        )

        info = error.get_detailed_info()

        assert info["error_type"] == "Py7zzError"
        assert info["message"] == "Test error"
        assert info["error_code"] == 1
        assert info["context"] == {"file": "test.7z"}
        assert info["suggestions"] == ["Check file path"]

    def test_add_context(self):
        """Test adding context information."""
        error = py7zz.Py7zzError("Test error")

        error.add_context("operation", "extract")
        error.add_context("archive", "test.7z")

        assert error.context["operation"] == "extract"
        assert error.context["archive"] == "test.7z"

    def test_add_suggestion(self):
        """Test adding suggestions."""
        error = py7zz.Py7zzError("Test error")

        error.add_suggestion("Check file permissions")
        error.add_suggestion("Verify disk space")

        assert "Check file permissions" in error.suggestions
        assert "Verify disk space" in error.suggestions
        assert len(error.suggestions) == 2


class TestEnhancedExceptionClasses:
    """Test enhanced exception classes."""

    def test_validation_error_basic(self):
        """Test ValidationError basic functionality."""
        error = py7zz.ValidationError("Invalid input")

        assert isinstance(error, py7zz.Py7zzError)
        assert error.error_type == "ValidationError"
        assert str(error) == "Invalid input"

    def test_validation_error_with_parameter(self):
        """Test ValidationError with parameter context."""
        error = py7zz.ValidationError("Invalid preset", parameter="preset")

        assert error.context["parameter"] == "preset"

    def test_operation_error_basic(self):
        """Test OperationError basic functionality."""
        error = py7zz.OperationError("Operation failed")

        assert isinstance(error, py7zz.Py7zzError)
        assert error.error_type == "OperationError"
        assert str(error) == "Operation failed"

    def test_operation_error_with_operation(self):
        """Test OperationError with operation context."""
        error = py7zz.OperationError("Failed", operation="extract")

        assert error.context["operation"] == "extract"

    def test_compatibility_error_basic(self):
        """Test CompatibilityError basic functionality."""
        error = py7zz.CompatibilityError("Platform issue")

        assert isinstance(error, py7zz.Py7zzError)
        assert error.error_type == "CompatibilityError"
        assert str(error) == "Platform issue"

    def test_compatibility_error_with_platform(self):
        """Test CompatibilityError with platform context."""
        error = py7zz.CompatibilityError("Windows issue", platform="Windows")

        assert error.context["platform"] == "Windows"

    def test_enhanced_classes_inheritance(self):
        """Test that enhanced classes inherit all base functionality."""
        error = py7zz.ValidationError("Test")

        # Should have all base class methods
        assert hasattr(error, "get_detailed_info")
        assert hasattr(error, "add_context")
        assert hasattr(error, "add_suggestion")

        # Test they work
        error.add_context("test", "value")
        error.add_suggestion("Test suggestion")

        info = error.get_detailed_info()
        assert info["context"]["test"] == "value"
        assert "Test suggestion" in info["suggestions"]


class TestErrorHandlingDecorators:
    """Test decorator-based error handling."""

    def test_handle_7z_errors_decorator_subprocess_error(self):
        """Test handle_7z_errors decorator with subprocess error."""

        @py7zz.handle_7z_errors
        def mock_7z_operation():
            raise subprocess.CalledProcessError(1, "7zz", stderr=b"Wrong password\n")

        with pytest.raises(py7zz.InvalidPasswordError) as exc_info:
            mock_7z_operation()

        assert "password is incorrect" in str(exc_info.value).lower()

    def test_handle_7z_errors_decorator_can_not_open(self):
        """Test handle_7z_errors decorator with 'Can not open' error."""

        @py7zz.handle_7z_errors
        def mock_7z_operation():
            raise subprocess.CalledProcessError(
                2, "7zz", stderr=b"ERROR: Can not open file as archive\n"
            )

        with pytest.raises(py7zz.CorruptedArchiveError):
            mock_7z_operation()

    def test_handle_7z_errors_decorator_file_not_found(self):
        """Test handle_7z_errors decorator with file not found."""

        @py7zz.handle_7z_errors
        def mock_7z_operation():
            raise subprocess.CalledProcessError(
                2, "7zz", stderr=b"ERROR: Can not open nonexistent.7z\n"
            )

        with pytest.raises(py7zz.ArchiveNotFoundError):
            mock_7z_operation()

    def test_handle_7z_errors_decorator_insufficient_memory(self):
        """Test handle_7z_errors decorator with memory error."""

        @py7zz.handle_7z_errors
        def mock_7z_operation():
            raise subprocess.CalledProcessError(
                2, "7zz", stderr=b"ERROR: Insufficient memory\n"
            )

        with pytest.raises(py7zz.OperationError) as exc_info:
            mock_7z_operation()

        error = exc_info.value
        assert "memory" in str(error).lower()
        assert error.error_code == 2
        assert "reducing compression level" in " ".join(error.suggestions).lower()

    def test_handle_7z_errors_decorator_generic_error(self):
        """Test handle_7z_errors decorator with generic error."""

        @py7zz.handle_7z_errors
        def mock_7z_operation():
            raise subprocess.CalledProcessError(
                3, "7zz", stderr=b"Unknown error occurred\n"
            )

        with pytest.raises(py7zz.OperationError) as exc_info:
            mock_7z_operation()

        error = exc_info.value
        assert error.error_code == 3
        assert "Unknown error occurred" in str(error)

    def test_handle_file_errors_decorator_file_not_found(self):
        """Test handle_file_errors decorator with FileNotFoundError."""

        @py7zz.handle_file_errors
        def mock_file_operation():
            raise FileNotFoundError("test_file.txt")

        with pytest.raises(py7zz.ValidationError) as exc_info:
            mock_file_operation()

        error = exc_info.value
        assert "test_file.txt" in str(error)
        assert any("path exists" in s for s in error.suggestions)

    def test_handle_file_errors_decorator_permission_error(self):
        """Test handle_file_errors decorator with PermissionError."""

        @py7zz.handle_file_errors
        def mock_file_operation():
            error = PermissionError("Permission denied")
            error.filename = "protected_file.txt"
            raise error

        with pytest.raises(py7zz.ValidationError) as exc_info:
            mock_file_operation()

        error = exc_info.value
        assert "permission denied" in str(error).lower()
        assert any("permissions" in s.lower() for s in error.suggestions)

    def test_handle_file_errors_decorator_os_error(self):
        """Test handle_file_errors decorator with OSError."""

        @py7zz.handle_file_errors
        def mock_file_operation():
            raise OSError("Disk full")

        with pytest.raises(py7zz.OperationError) as exc_info:
            mock_file_operation()

        error = exc_info.value
        assert "system error" in str(error).lower()
        assert any("disk space" in s.lower() for s in error.suggestions)

    def test_handle_validation_errors_decorator_value_error(self):
        """Test handle_validation_errors decorator with ValueError."""

        @py7zz.handle_validation_errors
        def mock_validation_operation():
            raise ValueError("Invalid preset: unknown")

        with pytest.raises(py7zz.ValidationError) as exc_info:
            mock_validation_operation()

        error = exc_info.value
        assert "Invalid preset: unknown" in str(error)
        assert any("parameter" in s.lower() for s in error.suggestions)

    def test_handle_validation_errors_decorator_type_error(self):
        """Test handle_validation_errors decorator with TypeError."""

        @py7zz.handle_validation_errors
        def mock_validation_operation():
            raise TypeError("Expected string, got int")

        with pytest.raises(py7zz.ValidationError) as exc_info:
            mock_validation_operation()

        error = exc_info.value
        assert "Expected string, got int" in str(error)

    def test_decorator_chaining(self):
        """Test chaining multiple error handling decorators."""

        @py7zz.handle_file_errors
        @py7zz.handle_validation_errors
        @py7zz.handle_7z_errors
        def mock_complex_operation(error_type):
            if error_type == "subprocess":
                raise subprocess.CalledProcessError(1, "7zz", stderr=b"Wrong password")
            elif error_type == "file":
                raise FileNotFoundError("missing.txt")
            elif error_type == "validation":
                raise ValueError("Invalid input")

        # Test subprocess error handling
        with pytest.raises(py7zz.InvalidPasswordError):
            mock_complex_operation("subprocess")

        # Test file error handling
        with pytest.raises(py7zz.ValidationError):
            mock_complex_operation("file")

        # Test validation error handling
        with pytest.raises(py7zz.ValidationError):
            mock_complex_operation("validation")

    def test_decorator_preserves_function_metadata(self):
        """Test that decorators preserve function metadata."""

        @py7zz.handle_7z_errors
        def example_function():
            """Example function for testing."""
            pass

        assert example_function.__name__ == "example_function"
        assert (
            example_function.__doc__ is not None
            and "Example function" in example_function.__doc__
        )


class TestErrorUtilityFunctions:
    """Test error utility functions."""

    def test_classify_error_type_validation(self):
        """Test classify_error_type with ValidationError."""
        error = py7zz.ValidationError("Invalid input")
        result = py7zz.classify_error_type(error)
        assert result == "validation"

    def test_classify_error_type_operation(self):
        """Test classify_error_type with OperationError."""
        error = py7zz.OperationError("Operation failed")
        result = py7zz.classify_error_type(error)
        assert result == "operation"

    def test_classify_error_type_compatibility(self):
        """Test classify_error_type with CompatibilityError."""
        error = py7zz.CompatibilityError("Platform issue")
        result = py7zz.classify_error_type(error)
        assert result == "compatibility"

    def test_classify_error_type_py7zz(self):
        """Test classify_error_type with base Py7zzError."""
        error = py7zz.CompressionError("Compression failed")
        result = py7zz.classify_error_type(error)
        assert result == "py7zz"

    def test_classify_error_type_system(self):
        """Test classify_error_type with system error."""
        error = ValueError("System error")
        result = py7zz.classify_error_type(error)
        assert result == "system"

    def test_get_error_suggestions_with_suggestions(self):
        """Test get_error_suggestions with error that has suggestions."""
        error = py7zz.Py7zzError("Test error")
        error.add_suggestion("First suggestion")
        error.add_suggestion("Second suggestion")

        suggestions = py7zz.get_error_suggestions(error)
        assert suggestions == ["First suggestion", "Second suggestion"]

    def test_get_error_suggestions_file_not_found(self):
        """Test get_error_suggestions with FileNotFoundError."""
        error = FileNotFoundError("missing.txt")
        suggestions = py7zz.get_error_suggestions(error)

        assert any("file path is correct" in s for s in suggestions)
        assert any("file exists" in s for s in suggestions)

    def test_get_error_suggestions_permission_error(self):
        """Test get_error_suggestions with PermissionError."""
        error = PermissionError("Access denied")
        suggestions = py7zz.get_error_suggestions(error)

        assert any("permissions" in s for s in suggestions)
        assert any("administrator" in s.lower() for s in suggestions)

    def test_get_error_suggestions_memory_error(self):
        """Test get_error_suggestions with MemoryError."""
        error = MemoryError("Out of memory")
        suggestions = py7zz.get_error_suggestions(error)

        assert any("close" in s.lower() for s in suggestions)
        assert any("smaller" in s.lower() for s in suggestions)
        assert any("memory" in s.lower() for s in suggestions)

    def test_get_error_suggestions_generic_error(self):
        """Test get_error_suggestions with generic error."""
        error = RuntimeError("Generic error")
        suggestions = py7zz.get_error_suggestions(error)

        assert any("error message" in s for s in suggestions)
        assert any("documentation" in s for s in suggestions)


class TestErrorHandlingIntegration:
    """Integration tests for error handling system."""

    def test_error_chaining_preservation(self):
        """Test that error chaining is preserved with 'from' clause."""

        @py7zz.handle_7z_errors
        def mock_operation():
            original_error = subprocess.CalledProcessError(
                1, "7zz", stderr=b"Wrong password"
            )
            raise original_error

        with pytest.raises(py7zz.InvalidPasswordError) as exc_info:
            mock_operation()

        # Check that the original error is preserved in the chain
        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, subprocess.CalledProcessError)

    def test_complex_error_context_tracking(self):
        """Test complex error context tracking."""
        error = py7zz.OperationError(
            "Complex operation failed", operation="batch_extract"
        )
        error.add_context("archive_count", 5)
        error.add_context("failed_archive", "corrupted.7z")
        error.add_context("progress", "3/5")
        error.add_suggestion("Check individual archives for corruption")
        error.add_suggestion("Try extracting files one by one")

        info = error.get_detailed_info()

        assert info["context"]["operation"] == "batch_extract"
        assert info["context"]["archive_count"] == 5
        assert info["context"]["failed_archive"] == "corrupted.7z"
        assert info["context"]["progress"] == "3/5"
        assert len(info["suggestions"]) == 2

    def test_error_handling_with_existing_py7zz_errors(self):
        """Test error handling integration with existing py7zz error types."""
        # Test that existing error types still work
        with pytest.raises(py7zz.FileNotFoundError):
            raise py7zz.FileNotFoundError("test.txt")

        with pytest.raises(py7zz.CompressionError):
            raise py7zz.CompressionError("Compression failed")

        with pytest.raises(py7zz.ExtractionError):
            raise py7zz.ExtractionError("Extraction failed")

        # Test that they're still Py7zzError instances
        error = py7zz.CompressionError("Test")
        assert isinstance(error, py7zz.Py7zzError)

    def test_backward_compatibility(self):
        """Test backward compatibility with existing error handling."""
        # Existing error types should still work without enhanced features
        try:
            raise py7zz.CompressionError("Old style error")
        except py7zz.CompressionError as e:
            # Should still be catchable with enhanced message format
            assert str(e) == "Compression failed: Old style error"

        try:
            raise py7zz.ExtractionError("Old style error", returncode=2)
        except py7zz.ExtractionError as e:
            # Should preserve existing attributes
            assert hasattr(e, "returncode")
            assert e.returncode == 2

    def test_decorator_error_analysis(self):
        """Test that decorators provide meaningful error analysis."""

        @py7zz.handle_7z_errors
        def mock_operation_with_detailed_error():
            raise subprocess.CalledProcessError(
                2,
                "7zz",
                stderr=b"ERROR: Can not open file '/path/to/missing.7z' as archive: No such file or directory",
            )

        with pytest.raises(py7zz.CorruptedArchiveError) as exc_info:
            mock_operation_with_detailed_error()

        # Should provide detailed error information
        error = exc_info.value
        assert isinstance(error, py7zz.Py7zzError)
        # The error should contain useful information
        assert "corrupted" in str(error).lower() or "archive" in str(error).lower()


class TestRealWorldErrorScenarios:
    """Test real-world error scenarios."""

    def test_archive_corruption_handling(self):
        """Test handling of archive corruption scenarios."""

        @py7zz.handle_7z_errors
        def extract_corrupted_archive():
            raise subprocess.CalledProcessError(
                2, "7zz", stderr=b"ERROR: Data Error in 'corrupted.7z'. Wrong CRC"
            )

        with pytest.raises(py7zz.OperationError) as exc_info:
            extract_corrupted_archive()

        error = exc_info.value
        assert "data error" in str(error).lower() or "crc" in str(error).lower()
        assert error.error_code == 2

    def test_password_related_errors(self):
        """Test handling of password-related errors."""

        @py7zz.handle_7z_errors
        def wrong_password():
            raise subprocess.CalledProcessError(
                2, "7zz", stderr=b"ERROR: Wrong password : encrypted.7z"
            )

        with pytest.raises(py7zz.InvalidPasswordError):
            wrong_password()

    def test_disk_space_exhaustion(self):
        """Test handling of disk space exhaustion."""

        @py7zz.handle_file_errors
        def extract_to_full_disk():
            error = OSError("No space left on device")
            error.errno = 28  # ENOSPC
            raise error

        with pytest.raises(py7zz.OperationError) as exc_info:
            extract_to_full_disk()

        error = exc_info.value
        suggestions = error.suggestions
        assert any("disk space" in s.lower() for s in suggestions)

    def test_invalid_archive_format(self):
        """Test handling of invalid archive format."""

        @py7zz.handle_7z_errors
        def open_invalid_format():
            raise subprocess.CalledProcessError(
                2, "7zz", stderr=b"ERROR: Can not open 'notanarchive.txt' as archive"
            )

        with pytest.raises(py7zz.CorruptedArchiveError):
            open_invalid_format()

    def test_cascading_error_handling(self):
        """Test cascading error handling in complex operations."""

        @py7zz.handle_file_errors
        @py7zz.handle_7z_errors
        def complex_operation(error_stage):
            if error_stage == "file_access":
                raise FileNotFoundError("source.7z")
            elif error_stage == "archive_processing":
                raise subprocess.CalledProcessError(1, "7zz", stderr=b"Wrong password")

        # Test file access error
        with pytest.raises(py7zz.ValidationError):
            complex_operation("file_access")

        # Test archive processing error
        with pytest.raises(py7zz.InvalidPasswordError):
            complex_operation("archive_processing")

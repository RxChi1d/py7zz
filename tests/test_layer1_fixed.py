"""
Simplified test suite for Layer 1 Advanced Convenience Functions.

This is the corrected version focused on testing core functionality
without complex mocking that doesn't match the actual implementation.
"""

from unittest.mock import patch

import pytest

import py7zz


class TestAdvancedFunctions:
    """Test advanced convenience functions exist and are callable."""

    def test_functions_exist(self):
        """Test that all advanced functions exist and are callable."""
        # Verify functions exist and are callable
        assert callable(py7zz.batch_create_archives)
        assert callable(py7zz.batch_extract_archives)
        assert callable(py7zz.copy_archive)
        assert callable(py7zz.get_compression_ratio)
        assert callable(py7zz.get_archive_format)
        assert callable(py7zz.compare_archives)
        assert callable(py7zz.convert_archive_format)
        assert callable(py7zz.recompress_archive)

    @patch("py7zz.simple.create_archive")
    def test_batch_create_archives_empty(self, mock_create):
        """Test batch creation with empty operations list."""
        py7zz.batch_create_archives([])
        mock_create.assert_not_called()

    @patch("py7zz.simple.extract_archive")
    def test_batch_extract_archives_empty(self, mock_extract):
        """Test batch extraction with empty archive list."""
        py7zz.batch_extract_archives([], "output/")
        mock_extract.assert_not_called()

    @patch("py7zz.simple.create_archive")
    def test_batch_create_basic(self, mock_create):
        """Test basic batch creation functionality."""
        operations = [("test.7z", ["file.txt"])]
        py7zz.batch_create_archives(operations, preset="balanced")

        assert mock_create.call_count == 1
        # Verify preset was passed
        args, kwargs = mock_create.call_args
        assert kwargs.get("preset") == "balanced"

    @patch("py7zz.simple.extract_archive")
    @patch("pathlib.Path.exists", return_value=True)
    def test_batch_extract_basic(self, mock_exists, mock_extract):
        """Test basic batch extraction functionality."""
        archives = ["test.7z"]
        py7zz.batch_extract_archives(archives, "output/")

        # Verify the extract function was called
        assert mock_extract.call_count == 1

    @patch("py7zz.simple.get_archive_info")
    def test_get_compression_ratio_basic(self, mock_get_info):
        """Test compression ratio calculation."""
        mock_get_info.return_value = {
            "compression_ratio": 0.7,
        }

        ratio = py7zz.get_compression_ratio("test.7z")
        assert ratio == 0.7

    @patch("py7zz.simple.get_archive_info")
    def test_get_compression_ratio_zero_uncompressed(self, mock_get_info):
        """Test compression ratio with zero value."""
        mock_get_info.return_value = {
            "compression_ratio": 0.0,
        }

        ratio = py7zz.get_compression_ratio("test.7z")
        assert ratio == 0.0

    @patch("py7zz.simple.get_archive_info")
    def test_get_archive_format_basic(self, mock_get_info):
        """Test archive format detection."""
        mock_get_info.return_value = {
            "format": "7z",
        }

        format_type = py7zz.get_archive_format("test.7z")
        assert format_type == "7z"

    @patch("pathlib.Path.exists", return_value=True)
    @patch("py7zz.core.run_7z")
    def test_compare_archives_basic(self, mock_run_7z, mock_exists):
        """Test basic archive comparison."""
        from unittest.mock import Mock

        # Mock the subprocess result object with stdout attribute
        mock_result = Mock()
        mock_result.stdout = "---    Name\nfile1.txt\nfile2.txt\n"
        mock_run_7z.return_value = mock_result

        result = py7zz.compare_archives("archive1.7z", "archive2.7z")
        assert result is True

    def test_compare_archives_different(self):
        """Test archive comparison with different files using actual file check."""
        # Test with non-existent files - should return False
        result = py7zz.compare_archives("nonexistent1.7z", "nonexistent2.7z")
        assert result is False


class TestErrorHandling:
    """Test error handling in advanced functions."""

    def test_batch_create_archives_error(self):
        """Test error handling in batch creation."""
        with patch(
            "py7zz.simple.create_archive",
            side_effect=py7zz.FileNotFoundError("Missing file"),
        ):
            operations = [("archive.7z", ["missing.txt"])]
            with pytest.raises(py7zz.FileNotFoundError):
                py7zz.batch_create_archives(operations)

    def test_get_compression_ratio_error(self):
        """Test error handling in compression ratio calculation."""
        with patch(
            "py7zz.simple.get_archive_info",
            side_effect=py7zz.CorruptedArchiveError("Corrupted"),
        ), pytest.raises(py7zz.CorruptedArchiveError):
            py7zz.get_compression_ratio("corrupted.7z")

    def test_copy_archive_missing_source(self):
        """Test copy operation with missing source file."""
        with pytest.raises(py7zz.FileNotFoundError):
            py7zz.copy_archive("nonexistent.7z", "target.7z")


class TestIntegration:
    """Integration tests for advanced functions."""

    def test_function_signatures_match_docs(self):
        """Test that function signatures match expected patterns."""
        import inspect

        # Test batch_create_archives signature
        sig = inspect.signature(py7zz.batch_create_archives)
        params = list(sig.parameters.keys())
        assert "operations" in params
        assert "preset" in params

        # Test batch_extract_archives signature
        sig = inspect.signature(py7zz.batch_extract_archives)
        params = list(sig.parameters.keys())
        assert "archive_paths" in params
        assert "output_dir" in params

        # Test get_compression_ratio signature
        sig = inspect.signature(py7zz.get_compression_ratio)
        params = list(sig.parameters.keys())
        assert "archive_path" in params


if __name__ == "__main__":
    pytest.main([__file__])

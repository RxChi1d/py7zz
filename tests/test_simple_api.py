"""
Test suite for py7zz Simple Function API (Layer 1).

This module tests all Layer 1 simple function API including:
1. Basic operations: create_archive, extract_archive, list_archive, test_archive
2. Advanced convenience functions: batch operations, archive analysis, format conversion
3. Error handling and parameter validation

Consolidated from:
- test_layer1_advanced_functions.py (comprehensive functionality tests)
- test_layer1_final.py (existence and signature tests)
- test_layer1_fixed.py (simplified core functionality tests)
"""

import inspect
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

import py7zz


class TestBasicOperations:
    """Test basic Layer 1 operations (create, extract, list, test)."""

    def test_basic_functions_exist(self):
        """Verify all basic functions exist and are callable."""
        basic_functions = [
            "create_archive",
            "extract_archive",
            "list_archive",
            "test_archive",
            "compress_file",
            "compress_directory",
            "get_archive_info",
        ]

        for func_name in basic_functions:
            assert hasattr(py7zz, func_name), f"Function {func_name} not found"
            func = getattr(py7zz, func_name)
            assert callable(func), f"Function {func_name} is not callable"

    def test_basic_function_signatures(self):
        """Test basic function signatures are reasonable."""
        # Test create_archive
        sig = inspect.signature(py7zz.create_archive)
        assert "archive_path" in sig.parameters
        assert "files" in sig.parameters
        assert "preset" in sig.parameters

        # Test extract_archive
        sig = inspect.signature(py7zz.extract_archive)
        assert "archive_path" in sig.parameters
        assert "output_dir" in sig.parameters
        assert "overwrite" in sig.parameters


class TestAdvancedFunctions:
    """Test advanced convenience functions exist and are callable."""

    def test_advanced_functions_exist(self):
        """Verify all Layer 1 advanced functions exist and are callable."""
        advanced_functions = [
            "batch_create_archives",
            "batch_extract_archives",
            "copy_archive",
            "get_compression_ratio",
            "get_archive_format",
            "compare_archives",
            "convert_archive_format",
            "recompress_archive",
        ]

        for func_name in advanced_functions:
            assert hasattr(py7zz, func_name), f"Function {func_name} not found"
            func = getattr(py7zz, func_name)
            assert callable(func), f"Function {func_name} is not callable"

    def test_advanced_function_signatures(self):
        """Test advanced function signatures are reasonable."""
        # Test batch_create_archives
        sig = inspect.signature(py7zz.batch_create_archives)
        assert "operations" in sig.parameters
        assert "preset" in sig.parameters

        # Test batch_extract_archives
        sig = inspect.signature(py7zz.batch_extract_archives)
        assert "archive_paths" in sig.parameters
        assert "output_dir" in sig.parameters

        # Test copy_archive
        sig = inspect.signature(py7zz.copy_archive)
        assert "source_archive" in sig.parameters
        assert "target_archive" in sig.parameters

        # Test get_compression_ratio
        sig = inspect.signature(py7zz.get_compression_ratio)
        assert "archive_path" in sig.parameters

        # Test get_archive_format
        sig = inspect.signature(py7zz.get_archive_format)
        assert "archive_path" in sig.parameters

        # Test compare_archives
        sig = inspect.signature(py7zz.compare_archives)
        assert "archive1" in sig.parameters
        assert "archive2" in sig.parameters


class TestBatchOperations:
    """Test batch archive operations."""

    @patch("py7zz.simple.create_archive")
    def test_batch_create_archives_success(self, mock_create):
        """Test successful batch archive creation."""
        operations = [
            ("archive1.7z", ["file1.txt"]),
            ("archive2.7z", ["file2.txt", "dir/"]),
            ("archive3.7z", ["file3.txt"]),
        ]

        py7zz.batch_create_archives(operations, preset="balanced")

        # Verify create_archive was called for each operation
        assert mock_create.call_count == 3
        # Check that calls were made with proper preset
        for call in mock_create.call_args_list:
            args, kwargs = call
            assert kwargs.get("preset") == "balanced"

    @patch("py7zz.simple.create_archive")
    def test_batch_create_archives_with_options(self, mock_create):
        """Test batch creation with custom options."""
        operations = [("test.7z", ["file.txt"])]

        py7zz.batch_create_archives(
            operations, preset="ultra", overwrite=False, create_dirs=False
        )

        # Verify the function was called with correct preset
        assert mock_create.call_count == 1
        args, kwargs = mock_create.call_args_list[0]
        assert kwargs.get("preset") == "ultra"

    @patch("py7zz.simple.create_archive")
    def test_batch_create_archives_empty(self, mock_create):
        """Test batch creation with empty operations list."""
        py7zz.batch_create_archives([])
        mock_create.assert_not_called()

    @patch("py7zz.simple.extract_archive")
    @patch("pathlib.Path.exists", return_value=True)
    def test_batch_extract_archives_success(self, mock_exists, mock_extract):
        """Test successful batch archive extraction."""
        archives = [Path("archive1.7z"), Path("archive2.7z"), Path("archive3.7z")]

        py7zz.batch_extract_archives(archives, "output/")  # type: ignore

        # Verify extract_archive was called for each archive
        assert mock_extract.call_count == 3

    @patch("py7zz.simple.extract_archive")
    @patch("pathlib.Path.exists", return_value=True)
    def test_batch_extract_archives_with_options(self, mock_exists, mock_extract):
        """Test batch extraction with custom options."""
        archives = [Path("test.7z")]

        py7zz.batch_extract_archives(
            archives,  # type: ignore
            "custom_output/",
            overwrite=False,
            create_dirs=False,
        )

        assert mock_extract.call_count == 1

    @patch("py7zz.simple.extract_archive")
    def test_batch_extract_archives_empty(self, mock_extract):
        """Test batch extraction with empty archive list."""
        py7zz.batch_extract_archives([], "output/")
        mock_extract.assert_not_called()


class TestArchiveCopyOperation:
    """Test archive copy functionality."""

    @patch("py7zz.simple.extract_archive")
    @patch("py7zz.simple.create_archive")
    @patch("tempfile.mkdtemp")
    @patch("shutil.rmtree")
    @patch("pathlib.Path.exists", return_value=True)
    @patch("shutil.copy2")
    def test_copy_archive_simple(
        self,
        mock_copy,
        mock_exists,
        mock_rmtree,
        mock_mkdtemp,
        mock_create,
        mock_extract,
    ):
        """Test simple archive copy without recompression."""
        mock_mkdtemp.return_value = "/tmp/temp_dir"

        py7zz.copy_archive("source.7z", "target.7z", recompress=False)

        # Should use simple file copy when recompress=False
        mock_copy.assert_called_once()
        # Extract and create should not be called for simple copy
        mock_extract.assert_not_called()
        mock_create.assert_not_called()

    @patch("py7zz.simple.extract_archive")
    @patch("py7zz.simple.create_archive")
    @patch("pathlib.Path.exists", return_value=True)
    @patch("tempfile.TemporaryDirectory")
    def test_copy_archive_with_recompression(
        self, mock_temp_dir, mock_exists, mock_create, mock_extract
    ):
        """Test archive copy with recompression."""
        # Mock temporary directory context manager
        mock_temp_dir.return_value.__enter__.return_value = "/tmp/temp_dir"

        # Mock Path.rglob to return some files
        with patch("pathlib.Path.rglob") as mock_rglob:
            mock_file = Mock()
            mock_file.is_file.return_value = True
            mock_rglob.return_value = [mock_file]

            py7zz.copy_archive(
                "source.7z", "target.7z", recompress=True, preset="ultra"
            )

            # Should extract and create with specified preset
            mock_extract.assert_called_once()
            mock_create.assert_called_once()

    @patch("shutil.copy2")
    def test_copy_archive_direct_copy(self, mock_copy):
        """Test direct file copy when recompress=False."""
        with patch("pathlib.Path.exists", return_value=True):
            py7zz.copy_archive("source.7z", "target.7z", recompress=False)
            mock_copy.assert_called_once_with("source.7z", "target.7z")


class TestArchiveAnalysis:
    """Test archive analysis functions."""

    @patch("py7zz.simple.get_archive_info")
    def test_get_compression_ratio_success(self, mock_get_info):
        """Test successful compression ratio calculation."""
        mock_get_info.return_value = {
            "uncompressed_size": 1000,
            "compressed_size": 300,
        }

        ratio = py7zz.get_compression_ratio("test.7z")

        assert ratio == 0.7  # (1000 - 300) / 1000
        mock_get_info.assert_called_once_with("test.7z")

    @patch("py7zz.simple.get_archive_info")
    def test_get_compression_ratio_with_precalculated(self, mock_get_info):
        """Test compression ratio with pre-calculated value."""
        mock_get_info.return_value = {
            "compression_ratio": 0.7,
        }

        ratio = py7zz.get_compression_ratio("test.7z")
        assert ratio == 0.7

    @patch("py7zz.simple.get_archive_info")
    def test_get_compression_ratio_zero_uncompressed(self, mock_get_info):
        """Test compression ratio with zero uncompressed size."""
        mock_get_info.return_value = {
            "uncompressed_size": 0,
            "compressed_size": 100,
        }

        ratio = py7zz.get_compression_ratio("test.7z")

        assert ratio == 0.0

    @patch("py7zz.core.run_7z")
    @patch("pathlib.Path.exists", return_value=True)
    def test_get_archive_format_7z(self, mock_exists, mock_run_7z):
        """Test archive format detection for 7z files."""
        mock_run_7z.return_value = MagicMock(
            returncode=0, stdout="7-Zip [64] 24.07 : Archive type = 7z"
        )

        format_type = py7zz.get_archive_format("test.7z")

        assert format_type == "7z"

    @patch("py7zz.core.run_7z")
    @patch("pathlib.Path.exists", return_value=True)
    def test_get_archive_format_zip(self, mock_exists, mock_run_7z):
        """Test archive format detection for ZIP files."""
        mock_run_7z.return_value = MagicMock(
            returncode=0, stdout="7-Zip [64] 24.07 : Archive type = zip"
        )

        format_type = py7zz.get_archive_format("test.zip")

        assert format_type == "zip"

    @patch("py7zz.core.run_7z")
    @patch("pathlib.Path.exists", return_value=True)
    def test_get_archive_format_unknown(self, mock_exists, mock_run_7z):
        """Test archive format detection for unknown files."""
        mock_run_7z.return_value = MagicMock(
            returncode=1, stdout="Cannot open as archive"
        )

        format_type = py7zz.get_archive_format("unknown.bin")

        assert format_type == "unknown"


class TestArchiveComparison:
    """Test archive comparison functionality."""

    @patch("py7zz.simple.get_archive_info")
    def test_compare_archives_same_basic(self, mock_get_info):
        """Test basic archive comparison (same archives)."""
        mock_get_info.side_effect = [
            {
                "file_count": 3,
                "uncompressed_size": 1000,
                "compressed_size": 300,
                "files": ["file1.txt", "file2.txt", "dir/file3.txt"],
            },
            {
                "file_count": 3,
                "uncompressed_size": 1000,
                "compressed_size": 350,  # Different compressed size is OK
                "files": ["file1.txt", "file2.txt", "dir/file3.txt"],
            },
        ]

        result = py7zz.compare_archives("archive1.7z", "archive2.7z")

        assert result is True

    @patch("py7zz.simple.get_archive_info")
    def test_compare_archives_different_files(self, mock_get_info):
        """Test archive comparison with different file lists."""
        mock_get_info.side_effect = [
            {
                "file_count": 2,
                "uncompressed_size": 1000,
                "compressed_size": 300,
                "files": ["file1.txt", "file2.txt"],
            },
            {
                "file_count": 2,
                "uncompressed_size": 1000,
                "compressed_size": 300,
                "files": ["file1.txt", "different.txt"],
            },
        ]

        result = py7zz.compare_archives("archive1.7z", "archive2.7z")

        assert result is False

    @patch("py7zz.SevenZipFile")
    @patch("pathlib.Path.exists", return_value=True)
    def test_compare_archives_with_content(self, mock_exists, mock_sevenzipfile):
        """Test deep archive comparison with content verification."""
        # Mock the first archive
        mock_sz1 = MagicMock()
        mock_sz1.namelist.return_value = ["file1.txt", "file2.txt"]
        mock_sz1.read.side_effect = [b"content1", b"content2"]
        mock_sz1.__enter__.return_value = mock_sz1
        mock_sz1.__exit__.return_value = None

        # Mock the second archive
        mock_sz2 = MagicMock()
        mock_sz2.namelist.return_value = ["file1.txt", "file2.txt"]
        mock_sz2.read.side_effect = [b"content1", b"content2"]
        mock_sz2.__enter__.return_value = mock_sz2
        mock_sz2.__exit__.return_value = None

        mock_sevenzipfile.side_effect = [mock_sz1, mock_sz2]

        result = py7zz.compare_archives(
            "archive1.7z", "archive2.7z", compare_content=True
        )

        assert result is True

    def test_compare_archives_different_nonexistent(self):
        """Test archive comparison with non-existent files."""
        # Test with non-existent files - should return False
        result = py7zz.compare_archives("nonexistent1.7z", "nonexistent2.7z")
        assert result is False


class TestArchiveConversion:
    """Test archive format conversion."""

    @patch("py7zz.simple.copy_archive")
    @patch("pathlib.Path.exists", return_value=True)
    def test_convert_archive_format_success(self, mock_exists, mock_copy_archive):
        """Test successful archive format conversion."""
        py7zz.convert_archive_format("source.zip", "target.7z", preset="balanced")

        # Should call copy_archive with recompress=True
        mock_copy_archive.assert_called_once()
        args, kwargs = mock_copy_archive.call_args
        assert kwargs.get("recompress") is True
        assert kwargs.get("preset") == "balanced"

    @patch("py7zz.simple.copy_archive")
    @patch("pathlib.Path.exists", return_value=True)
    def test_convert_archive_format_with_target_format(
        self, mock_exists, mock_copy_archive
    ):
        """Test conversion with explicit target format."""
        py7zz.convert_archive_format(
            "source.tar.gz", "target.archive", target_format="7z"
        )

        # Should call copy_archive with recompress=True
        mock_copy_archive.assert_called_once()
        args, kwargs = mock_copy_archive.call_args
        assert kwargs.get("recompress") is True


class TestArchiveRecompression:
    """Test archive recompression functionality."""

    @patch("py7zz.simple.convert_archive_format")
    @patch("shutil.move")
    @patch("shutil.copy2")
    @patch("tempfile.NamedTemporaryFile")
    @patch("pathlib.Path.exists", return_value=True)
    def test_recompress_archive_with_backup(
        self, mock_exists, mock_temp, mock_copy2, mock_move, mock_convert
    ):
        """Test recompression with backup creation."""
        # Mock temporary file
        mock_temp.return_value.__enter__.return_value.name = "/tmp/temp.7z"

        py7zz.recompress_archive("archive.7z", "ultra", backup_original=True)

        # Should create backup using copy2
        mock_copy2.assert_called_once()
        # Should convert archive and move temp file
        mock_convert.assert_called_once()
        mock_move.assert_called_once()

    @patch("py7zz.simple.convert_archive_format")
    @patch("shutil.move")
    @patch("shutil.copy2")
    @patch("tempfile.NamedTemporaryFile")
    @patch("pathlib.Path.exists", return_value=True)
    def test_recompress_archive_custom_backup_suffix(
        self, mock_exists, mock_temp, mock_copy2, mock_move, mock_convert
    ):
        """Test recompression with custom backup suffix."""
        # Mock temporary file
        mock_temp.return_value.__enter__.return_value.name = "/tmp/temp.7z"

        py7zz.recompress_archive("archive.7z", "ultra", backup_suffix=".old")

        # Should create backup with custom suffix
        mock_copy2.assert_called_once()
        # Should convert and move temp file
        mock_convert.assert_called_once()
        mock_move.assert_called_once()


class TestErrorHandling:
    """Test error handling in Layer 1 functions."""

    @patch(
        "py7zz.simple.create_archive",
        side_effect=py7zz.FileNotFoundError("Missing file"),
    )
    def test_batch_create_archives_error(self, mock_create):
        """Test error handling in batch creation."""
        operations = [("archive.7z", ["missing.txt"])]

        with pytest.raises(py7zz.FileNotFoundError):
            py7zz.batch_create_archives(operations)

    @patch(
        "py7zz.simple.extract_archive",
        side_effect=py7zz.ArchiveNotFoundError("Missing archive"),
    )
    @patch("pathlib.Path.exists", return_value=True)
    def test_batch_extract_archives_error(self, mock_exists, mock_extract):
        """Test error handling in batch extraction."""
        archives = [Path("missing.7z")]

        with pytest.raises(py7zz.ArchiveNotFoundError):
            py7zz.batch_extract_archives(archives, "output/")  # type: ignore

    @patch(
        "py7zz.simple.get_archive_info",
        side_effect=py7zz.CorruptedArchiveError("Corrupted"),
    )
    def test_get_compression_ratio_error(self, mock_get_info):
        """Test error handling in compression ratio calculation."""
        with pytest.raises(py7zz.CorruptedArchiveError):
            py7zz.get_compression_ratio("corrupted.7z")

    def test_copy_archive_missing_source(self):
        """Test copy operation with missing source file."""
        with pytest.raises(py7zz.FileNotFoundError):
            py7zz.copy_archive("nonexistent.7z", "target.7z")

    def test_get_compression_ratio_missing_file(self):
        """Test compression ratio with missing file."""
        with pytest.raises(py7zz.FileNotFoundError):
            py7zz.get_compression_ratio("nonexistent.7z")

    def test_get_archive_format_missing_file(self):
        """Test format detection with missing file."""
        with pytest.raises(py7zz.FileNotFoundError):
            py7zz.get_archive_format("nonexistent.7z")


class TestParameterValidation:
    """Test parameter validation for Layer 1 functions."""

    def test_batch_create_empty_operations(self):
        """Test batch creation with empty operations list."""
        # This should not raise an error
        try:
            py7zz.batch_create_archives([])
        except Exception as e:
            pytest.fail(f"batch_create_archives([]) raised {type(e).__name__}: {e}")

    def test_batch_extract_empty_archives(self):
        """Test batch extraction with empty archive list."""
        # This should not raise an error
        try:
            py7zz.batch_extract_archives([], "output/")
        except Exception as e:
            pytest.fail(
                f"batch_extract_archives([], 'output/') raised {type(e).__name__}: {e}"
            )

    def test_batch_create_invalid_operations(self):
        """Test batch creation with invalid operations format."""
        # Test with invalid operation format
        with pytest.raises((ValueError, TypeError)):
            py7zz.batch_create_archives("not_a_list")  # type: ignore

    def test_batch_extract_invalid_type(self):
        """Test batch extraction with invalid archive list type."""
        # The function iterates over string chars, which leads to individual file checks
        # This is expected behavior - each character becomes a "filename" to check
        with pytest.raises(py7zz.FileNotFoundError):
            py7zz.batch_extract_archives("not_a_list", "output/")  # type: ignore


class TestIntegration:
    """Integration tests for Layer 1 API."""

    def test_default_parameters(self):
        """Test that functions work with default parameters."""
        with patch("py7zz.simple.create_archive"):
            py7zz.batch_create_archives([("test.7z", ["file.txt"])])

        with patch("py7zz.simple.extract_archive"), patch(
            "pathlib.Path.exists", return_value=True
        ):
            py7zz.batch_extract_archives(["test.7z"])

        with patch("pathlib.Path.exists", return_value=True), patch("shutil.copy2"):
            py7zz.copy_archive("source.7z", "target.7z")

    def test_function_signatures_match_implementation(self):
        """Test that function signatures match expected patterns."""
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
    pytest.main([__file__, "-v"])

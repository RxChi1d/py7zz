"""
Test suite for Layer 1 Advanced Convenience Functions.

Tests all the enhanced simple API functions added in py7zz 1.0+:
- batch_create_archives
- batch_extract_archives
- copy_archive
- get_compression_ratio
- get_archive_format
- compare_archives
- convert_archive_format
- recompress_archive
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

import py7zz


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
        # Check that calls were made with proper Path objects and preset
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

    @patch("py7zz.simple.extract_archive")
    @patch("pathlib.Path.exists", return_value=True)  # Mock archives exist
    def test_batch_extract_archives_success(self, mock_exists, mock_extract):
        """Test successful batch archive extraction."""
        archives = ["archive1.7z", "archive2.7z", "archive3.7z"]

        py7zz.batch_extract_archives(archives, "output/")

        # Verify extract_archive was called for each archive
        assert mock_extract.call_count == 3

    @patch("py7zz.simple.extract_archive")
    @patch("pathlib.Path.exists", return_value=True)
    def test_batch_extract_archives_with_options(self, mock_exists, mock_extract):
        """Test batch extraction with custom options."""
        archives = ["test.7z"]

        py7zz.batch_extract_archives(
            archives, "custom_output/", overwrite=False, create_dirs=False
        )

        assert mock_extract.call_count == 1

    def test_batch_create_archives_empty_list(self):
        """Test batch creation with empty operations list."""
        with patch("py7zz.simple.create_archive") as mock_create:
            py7zz.batch_create_archives([])
            mock_create.assert_not_called()

    def test_batch_extract_archives_empty_list(self):
        """Test batch extraction with empty archive list."""
        with patch("py7zz.simple.extract_archive") as mock_extract:
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
        self, mock_copy, mock_exists, mock_rmtree, mock_mkdtemp, mock_create, mock_extract
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

            py7zz.copy_archive("source.7z", "target.7z", recompress=True, preset="ultra")

            # Should extract and create with specified preset
            mock_extract.assert_called_once()
            mock_create.assert_called_once()

    @patch("shutil.copy2")
    def test_copy_archive_direct_copy(self, mock_copy):
        """Test direct file copy when recompress=False and same format."""
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
    def test_get_compression_ratio_zero_uncompressed(self, mock_get_info):
        """Test compression ratio with zero uncompressed size."""
        mock_get_info.return_value = {
            "uncompressed_size": 0,
            "compressed_size": 100,
        }

        ratio = py7zz.get_compression_ratio("test.7z")

        assert ratio == 0.0

    @patch("py7zz.core.run_7z")
    def test_get_archive_format_7z(self, mock_run_7z):
        """Test archive format detection for 7z files."""
        mock_run_7z.return_value = MagicMock(
            returncode=0, stdout="7-Zip [64] 24.07 : Archive type = 7z"
        )

        format_type = py7zz.get_archive_format("test.7z")

        assert format_type == "7z"

    @patch("py7zz.core.run_7z")
    def test_get_archive_format_zip(self, mock_run_7z):
        """Test archive format detection for ZIP files."""
        mock_run_7z.return_value = MagicMock(
            returncode=0, stdout="7-Zip [64] 24.07 : Archive type = zip"
        )

        format_type = py7zz.get_archive_format("test.zip")

        assert format_type == "zip"

    @patch("py7zz.core.run_7z")
    def test_get_archive_format_unknown(self, mock_run_7z):
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
    def test_compare_archives_with_content(self, mock_sevenzipfile):
        """Test deep archive comparison with content verification."""
        # Mock the first archive
        mock_sz1 = MagicMock()
        mock_sz1.namelist.return_value = ["file1.txt", "file2.txt"]
        mock_sz1.read.side_effect = [b"content1", b"content2"]

        # Mock the second archive
        mock_sz2 = MagicMock()
        mock_sz2.namelist.return_value = ["file1.txt", "file2.txt"]
        mock_sz2.read.side_effect = [b"content1", b"content2"]

        mock_sevenzipfile.side_effect = [mock_sz1, mock_sz2]

        result = py7zz.compare_archives(
            "archive1.7z", "archive2.7z", compare_content=True
        )

        assert result is True

    @patch("py7zz.SevenZipFile")
    def test_compare_archives_different_content(self, mock_sevenzipfile):
        """Test deep comparison with different content."""
        # Mock archives with same files but different content
        mock_sz1 = MagicMock()
        mock_sz1.namelist.return_value = ["file1.txt"]
        mock_sz1.read.return_value = b"content1"

        mock_sz2 = MagicMock()
        mock_sz2.namelist.return_value = ["file1.txt"]
        mock_sz2.read.return_value = b"different_content"

        mock_sevenzipfile.side_effect = [mock_sz1, mock_sz2]

        result = py7zz.compare_archives(
            "archive1.7z", "archive2.7z", compare_content=True
        )

        assert result is False


class TestArchiveConversion:
    """Test archive format conversion."""

    @patch("py7zz.simple.extract_archive")
    @patch("py7zz.simple.create_archive")
    @patch("tempfile.mkdtemp")
    @patch("shutil.rmtree")
    def test_convert_archive_format_success(
        self, mock_rmtree, mock_mkdtemp, mock_create, mock_extract
    ):
        """Test successful archive format conversion."""
        mock_mkdtemp.return_value = "/tmp/convert_temp"

        py7zz.convert_archive_format("source.zip", "target.7z", preset="balanced")

        mock_extract.assert_called_once_with("source.zip", "/tmp/convert_temp")
        mock_create.assert_called_once()
        mock_rmtree.assert_called_once_with("/tmp/convert_temp")

    @patch("py7zz.simple.extract_archive")
    @patch("py7zz.simple.create_archive")
    @patch("tempfile.mkdtemp")
    @patch("shutil.rmtree")
    def test_convert_archive_format_with_target_format(
        self, mock_rmtree, mock_mkdtemp, mock_create, mock_extract
    ):
        """Test conversion with explicit target format."""
        mock_mkdtemp.return_value = "/tmp/convert_temp"

        py7zz.convert_archive_format(
            "source.tar.gz", "target.archive", target_format="7z"
        )

        # Should still work with explicit format
        mock_extract.assert_called_once()
        mock_create.assert_called_once()


class TestArchiveRecompression:
    """Test archive recompression functionality."""

    @patch("py7zz.simple.extract_archive")
    @patch("py7zz.simple.create_archive")
    @patch("tempfile.mkdtemp")
    @patch("shutil.rmtree")
    @patch("shutil.move")
    def test_recompress_archive_with_backup(
        self, mock_move, mock_rmtree, mock_mkdtemp, mock_create, mock_extract
    ):
        """Test recompression with backup creation."""
        mock_mkdtemp.return_value = "/tmp/recompress_temp"

        py7zz.recompress_archive("archive.7z", "ultra", backup_original=True)

        # Should create backup, extract, and recreate
        mock_move.assert_any_call("archive.7z", "archive.7z.backup")
        mock_extract.assert_called_once()
        mock_create.assert_called_once()

    @patch("py7zz.simple.extract_archive")
    @patch("py7zz.simple.create_archive")
    @patch("tempfile.mkdtemp")
    @patch("shutil.rmtree")
    @patch("os.remove")
    def test_recompress_archive_no_backup(
        self, mock_remove, mock_rmtree, mock_mkdtemp, mock_create, mock_extract
    ):
        """Test recompression without backup."""
        mock_mkdtemp.return_value = "/tmp/recompress_temp"

        py7zz.recompress_archive("archive.7z", "fast", backup_original=False)

        # Should not create backup
        mock_remove.assert_not_called()
        mock_extract.assert_called_once()
        mock_create.assert_called_once()

    @patch("py7zz.simple.extract_archive")
    @patch("py7zz.simple.create_archive")
    @patch("tempfile.mkdtemp")
    @patch("shutil.rmtree")
    @patch("shutil.move")
    def test_recompress_archive_custom_backup_suffix(
        self, mock_move, mock_rmtree, mock_mkdtemp, mock_create, mock_extract
    ):
        """Test recompression with custom backup suffix."""
        mock_mkdtemp.return_value = "/tmp/recompress_temp"

        py7zz.recompress_archive("archive.7z", "ultra", backup_suffix=".old")

        mock_move.assert_any_call("archive.7z", "archive.7z.old")


class TestErrorHandling:
    """Test error handling in advanced functions."""

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
    def test_batch_extract_archives_error(self, mock_extract):
        """Test error handling in batch extraction."""
        archives = ["missing.7z"]

        with pytest.raises(py7zz.ArchiveNotFoundError):
            py7zz.batch_extract_archives(archives, "output/")

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


class TestIntegration:
    """Integration tests for advanced functions."""

    def test_function_signatures(self):
        """Test that all advanced functions have correct signatures."""
        # Verify functions exist and are callable
        assert callable(py7zz.batch_create_archives)
        assert callable(py7zz.batch_extract_archives)
        assert callable(py7zz.copy_archive)
        assert callable(py7zz.get_compression_ratio)
        assert callable(py7zz.get_archive_format)
        assert callable(py7zz.compare_archives)
        assert callable(py7zz.convert_archive_format)
        assert callable(py7zz.recompress_archive)

    def test_default_parameters(self):
        """Test that functions work with default parameters."""
        with patch("py7zz.simple.create_archive"):
            py7zz.batch_create_archives([("test.7z", ["file.txt"])])

        with patch("py7zz.simple.extract_archive"):
            py7zz.batch_extract_archives(["test.7z"])

        with patch("pathlib.Path.exists", return_value=True), patch("shutil.copy2"):
            py7zz.copy_archive("source.7z", "target.7z")

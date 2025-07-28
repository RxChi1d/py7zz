"""
Tests for the redesigned get_archive_info function.

This module tests the redesigned get_archive_info() function that now
provides pure archive statistics without file enumeration, addressing
the previous design issue where file listing was mixed with metadata.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import py7zz
from py7zz.archive_info import ArchiveInfo
from py7zz.detailed_parser import create_archive_summary
from py7zz.exceptions import FileNotFoundError as Py7zzFileNotFoundError
from py7zz.simple import get_archive_info


class TestRedesignedGetArchiveInfo:
    """Test the redesigned get_archive_info function."""

    def test_get_archive_info_with_detailed_parsing(self):
        """Test get_archive_info with successful detailed parsing."""
        mock_archive_path = Path("/mock/test.7z")

        # Create mock archive members for detailed parsing
        mock_file1 = ArchiveInfo("file1.txt")
        mock_file1.file_size = 100
        mock_file1.compress_size = 80
        mock_file1.method = "LZMA2:19"
        mock_file1.type = "file"

        mock_file2 = ArchiveInfo("file2.txt")
        mock_file2.file_size = 200
        mock_file2.compress_size = 150
        mock_file2.method = "LZMA2:19"
        mock_file2.type = "file"

        mock_dir = ArchiveInfo("subdir/")
        mock_dir.file_size = 0
        mock_dir.compress_size = 0
        mock_dir.type = "dir"

        mock_members = [mock_file1, mock_file2, mock_dir]

        # Mock file system stat
        mock_stat = MagicMock()
        mock_stat.st_size = 500  # Archive file size on disk
        mock_stat.st_ctime = 1642239045.0
        mock_stat.st_mtime = 1642239145.0

        with patch("py7zz.simple.Path.exists", return_value=True), patch(
            "py7zz.detailed_parser.get_detailed_archive_info", return_value=mock_members
        ), patch("py7zz.simple.Path.stat", return_value=mock_stat):
            info = get_archive_info(mock_archive_path)

            # Test that only statistics are returned, no file listing
            assert isinstance(info, dict)
            assert "files" not in info  # No file listing
            assert "file_list" not in info  # No file listing

            # Test statistics
            assert info["file_count"] == 2  # Two files
            assert info["directory_count"] == 1  # One directory
            assert info["total_entries"] == 3  # Total entries
            assert info["uncompressed_size"] == 300  # 100 + 200 + 0
            assert info["compressed_size"] == 500  # Archive size on disk
            assert info["compression_ratio"] == pytest.approx(
                0.233333, rel=1e-5
            )  # 1 - (230/300)
            assert info["compression_percentage"] == pytest.approx(23.333333, rel=1e-5)
            assert info["format"] == "7z"
            assert info["path"] == str(mock_archive_path)
            assert info["archive_type"] == "LZMA2:19"
            assert info["created"] == 1642239045.0
            assert info["modified"] == 1642239145.0

    def test_get_archive_info_with_fallback_parsing(self):
        """Test get_archive_info fallback when detailed parsing fails."""
        mock_archive_path = Path("/mock/fallback.7z")

        # Mock file system stat
        mock_stat = MagicMock()
        mock_stat.st_size = 1024
        mock_stat.st_ctime = 1642239045.0
        mock_stat.st_mtime = 1642239145.0

        # Mock SevenZipFile.namelist() for fallback
        mock_namelist = ["file1.txt", "file2.txt", "dir/file3.txt"]

        with patch("py7zz.simple.Path.exists", return_value=True), patch(
            "py7zz.detailed_parser.get_detailed_archive_info",
            side_effect=Exception("Parser failed"),
        ), patch("py7zz.simple.Path.stat", return_value=mock_stat), patch(
            "py7zz.simple.SevenZipFile"
        ) as mock_sz_class:
            # Configure mock SevenZipFile
            mock_sz = MagicMock()
            mock_sz.namelist.return_value = mock_namelist
            mock_sz_class.return_value.__enter__.return_value = mock_sz

            info = get_archive_info(mock_archive_path)

            # Test fallback statistics
            assert info["file_count"] == 3  # Based on namelist length
            assert info["directory_count"] == 0  # Cannot determine in fallback
            assert info["total_entries"] == 3
            assert info["compressed_size"] == 1024  # Archive size on disk
            assert info["uncompressed_size"] == 0  # Cannot determine in fallback
            assert info["compression_ratio"] == 0.0  # Cannot calculate in fallback
            assert info["compression_percentage"] == 0.0
            assert info["format"] == "7z"
            assert info["archive_type"] == "unknown"
            assert info["created"] == 1642239045.0
            assert info["modified"] == 1642239145.0

    def test_get_archive_info_different_formats(self):
        """Test get_archive_info with different archive formats."""
        test_cases = [
            ("/mock/test.zip", "zip"),
            ("/mock/test.tar.gz", "gz"),
            ("/mock/test.rar", "rar"),
            ("/mock/test.tar", "tar"),
            ("/mock/test.bz2", "bz2"),
        ]

        for archive_path_str, expected_format in test_cases:
            mock_archive_path = Path(archive_path_str)

            # Single test file
            mock_file = ArchiveInfo("test.txt")
            mock_file.file_size = 100
            mock_file.compress_size = 80
            mock_file.type = "file"
            mock_file.method = "Deflate" if expected_format == "zip" else "LZMA2:19"

            mock_members = [mock_file]

            mock_stat = MagicMock()
            mock_stat.st_size = 90
            mock_stat.st_ctime = 1642239045.0
            mock_stat.st_mtime = 1642239145.0

            with patch("py7zz.simple.Path.exists", return_value=True), patch(
                "py7zz.detailed_parser.get_detailed_archive_info",
                return_value=mock_members,
            ), patch("py7zz.simple.Path.stat", return_value=mock_stat):
                info = get_archive_info(mock_archive_path)

                assert info["format"] == expected_format
                assert info["path"] == archive_path_str

    def test_get_archive_info_empty_archive(self):
        """Test get_archive_info with an empty archive."""
        mock_archive_path = Path("/mock/empty.7z")

        # Empty members list
        mock_members: list[ArchiveInfo] = []

        mock_stat = MagicMock()
        mock_stat.st_size = 22  # Minimal archive overhead
        mock_stat.st_ctime = 1642239045.0
        mock_stat.st_mtime = 1642239145.0

        with patch("py7zz.simple.Path.exists", return_value=True), patch(
            "py7zz.detailed_parser.get_detailed_archive_info", return_value=mock_members
        ), patch("py7zz.simple.Path.stat", return_value=mock_stat):
            info = get_archive_info(mock_archive_path)

            assert info["file_count"] == 0
            assert info["directory_count"] == 0
            assert info["total_entries"] == 0
            assert info["uncompressed_size"] == 0
            assert info["compressed_size"] == 22
            assert info["compression_ratio"] == 0.0
            assert info["compression_percentage"] == 0.0
            assert info["archive_type"] == "empty"

    def test_get_archive_info_mixed_compression_methods(self):
        """Test get_archive_info with mixed compression methods."""
        mock_archive_path = Path("/mock/mixed.7z")

        # Create files with different compression methods
        mock_file1 = ArchiveInfo("file1.txt")
        mock_file1.file_size = 100
        mock_file1.compress_size = 80
        mock_file1.method = "LZMA2:19"
        mock_file1.type = "file"

        mock_file2 = ArchiveInfo("file2.txt")
        mock_file2.file_size = 200
        mock_file2.compress_size = 180
        mock_file2.method = "Deflate"
        mock_file2.type = "file"

        mock_file3 = ArchiveInfo("file3.txt")
        mock_file3.file_size = 150
        mock_file3.compress_size = 120
        mock_file3.method = "LZMA2:19"  # Same as first, should be predominant
        mock_file3.type = "file"

        mock_members = [mock_file1, mock_file2, mock_file3]

        mock_stat = MagicMock()
        mock_stat.st_size = 400
        mock_stat.st_ctime = 1642239045.0
        mock_stat.st_mtime = 1642239145.0

        with patch("py7zz.simple.Path.exists", return_value=True), patch(
            "py7zz.detailed_parser.get_detailed_archive_info", return_value=mock_members
        ), patch("py7zz.simple.Path.stat", return_value=mock_stat):
            info = get_archive_info(mock_archive_path)

            assert info["file_count"] == 3
            assert info["uncompressed_size"] == 450  # 100 + 200 + 150
            assert info["archive_type"] == "LZMA2:19"  # Most common method

            # Compression ratio should be based on internal compressed sizes
            expected_ratio = 1.0 - (380 / 450)  # 380 = 80 + 180 + 120
            assert info["compression_ratio"] == pytest.approx(expected_ratio, rel=1e-5)

    def test_get_archive_info_nonexistent_file(self):
        """Test get_archive_info with non-existent archive."""
        nonexistent_path = Path("/nonexistent/archive.7z")

        with pytest.raises(Py7zzFileNotFoundError, match="Archive not found"):
            get_archive_info(nonexistent_path)

    def test_get_archive_info_large_files(self):
        """Test get_archive_info with large file sizes."""
        mock_archive_path = Path("/mock/large.7z")

        # Create large files (GB sizes)
        mock_file1 = ArchiveInfo("large1.bin")
        mock_file1.file_size = 2 * 1024 * 1024 * 1024  # 2 GB
        mock_file1.compress_size = 1 * 1024 * 1024 * 1024  # 1 GB
        mock_file1.method = "LZMA2:19"
        mock_file1.type = "file"

        mock_file2 = ArchiveInfo("large2.bin")
        mock_file2.file_size = 3 * 1024 * 1024 * 1024  # 3 GB
        mock_file2.compress_size = 2 * 1024 * 1024 * 1024  # 2 GB
        mock_file2.method = "LZMA2:19"
        mock_file2.type = "file"

        mock_members = [mock_file1, mock_file2]

        mock_stat = MagicMock()
        mock_stat.st_size = 3 * 1024 * 1024 * 1024  # 3 GB archive
        mock_stat.st_ctime = 1642239045.0
        mock_stat.st_mtime = 1642239145.0

        with patch("py7zz.simple.Path.exists", return_value=True), patch(
            "py7zz.detailed_parser.get_detailed_archive_info", return_value=mock_members
        ), patch("py7zz.simple.Path.stat", return_value=mock_stat):
            info = get_archive_info(mock_archive_path)

            assert info["file_count"] == 2
            assert info["uncompressed_size"] == 5 * 1024 * 1024 * 1024  # 5 GB
            assert info["compressed_size"] == 3 * 1024 * 1024 * 1024  # 3 GB

            # Test compression ratio calculation with large numbers
            internal_compressed = (
                3 * 1024 * 1024 * 1024
            )  # Sum of individual compressed sizes
            uncompressed = 5 * 1024 * 1024 * 1024
            expected_ratio = 1.0 - (internal_compressed / uncompressed)
            assert info["compression_ratio"] == pytest.approx(expected_ratio, rel=1e-5)

    def test_get_archive_info_unicode_paths(self):
        """Test get_archive_info with Unicode archive paths."""
        unicode_paths = [
            "/mock/测试文档.7z",
            "/mock/файл.7z",
            "/mock/アーカイブ.7z",
            "/mock/محفوظات.7z",
        ]

        for unicode_path_str in unicode_paths:
            mock_archive_path = Path(unicode_path_str)

            mock_file = ArchiveInfo("test.txt")
            mock_file.file_size = 100
            mock_file.compress_size = 80
            mock_file.type = "file"
            mock_file.method = "LZMA2:19"

            mock_members = [mock_file]

            mock_stat = MagicMock()
            mock_stat.st_size = 90
            mock_stat.st_ctime = 1642239045.0
            mock_stat.st_mtime = 1642239145.0

            with patch("py7zz.simple.Path.exists", return_value=True), patch(
                "py7zz.detailed_parser.get_detailed_archive_info",
                return_value=mock_members,
            ), patch("py7zz.simple.Path.stat", return_value=mock_stat):
                info = get_archive_info(mock_archive_path)

                assert info["path"] == unicode_path_str
                assert info["file_count"] == 1


class TestArchiveSummaryIntegration:
    """Test integration with create_archive_summary function."""

    def test_summary_calculation_consistency(self):
        """Test that summary calculations are consistent."""
        # Create test members
        members = []

        # Add regular files
        for i in range(5):
            file_info = ArchiveInfo(f"file{i}.txt")
            file_info.file_size = (i + 1) * 100
            file_info.compress_size = (i + 1) * 80
            file_info.method = "LZMA2:19"
            file_info.type = "file"
            members.append(file_info)

        # Add directories
        for i in range(2):
            dir_info = ArchiveInfo(f"dir{i}/")
            dir_info.file_size = 0
            dir_info.compress_size = 0
            dir_info.type = "dir"
            members.append(dir_info)

        # Test create_archive_summary directly
        summary = create_archive_summary(members)

        assert summary["file_count"] == 5
        assert summary["directory_count"] == 2
        assert summary["total_file_count"] == 7
        assert summary["total_uncompressed_size"] == 1500  # 100+200+300+400+500
        assert summary["total_compressed_size"] == 1200  # 80+160+240+320+400

        expected_ratio = 1.0 - (1200 / 1500)
        assert summary["compression_ratio"] == pytest.approx(expected_ratio, rel=1e-5)
        assert summary["compression_percentage"] == pytest.approx(
            expected_ratio * 100, rel=1e-5
        )

    def test_summary_edge_cases(self):
        """Test summary calculation edge cases."""
        # Test with zero-size files
        zero_file = ArchiveInfo("empty.txt")
        zero_file.file_size = 0
        zero_file.compress_size = 0
        zero_file.type = "file"

        summary = create_archive_summary([zero_file])

        assert summary["file_count"] == 1
        assert summary["total_uncompressed_size"] == 0
        assert summary["compression_ratio"] == 0.0

        # Test with no compression (store method)
        stored_file = ArchiveInfo("stored.txt")
        stored_file.file_size = 100
        stored_file.compress_size = 100  # No compression
        stored_file.method = "Store"
        stored_file.type = "file"

        summary = create_archive_summary([stored_file])

        assert summary["compression_ratio"] == 0.0  # No compression achieved
        assert summary["archive_type"] == "Store"


class TestGetArchiveInfoFunction:
    """Test the get_archive_info function as used in the public API."""

    def test_public_api_usage(self):
        """Test get_archive_info as it would be used in the public API."""
        mock_archive_path = "/mock/public_api.7z"

        # Test the function as imported in the public API
        mock_file = ArchiveInfo("api_test.txt")
        mock_file.file_size = 500
        mock_file.compress_size = 400
        mock_file.method = "LZMA2:19"
        mock_file.type = "file"

        mock_members = [mock_file]

        mock_stat = MagicMock()
        mock_stat.st_size = 450
        mock_stat.st_ctime = 1642239045.0
        mock_stat.st_mtime = 1642239145.0

        with patch("py7zz.simple.Path.exists", return_value=True), patch(
            "py7zz.detailed_parser.get_detailed_archive_info", return_value=mock_members
        ), patch("py7zz.simple.Path.stat", return_value=mock_stat):
            # Test using py7zz.get_archive_info (public API)
            info = py7zz.get_archive_info(mock_archive_path)

            # Verify it returns the expected structure
            required_fields = [
                "file_count",
                "directory_count",
                "total_entries",
                "compressed_size",
                "uncompressed_size",
                "compression_ratio",
                "compression_percentage",
                "format",
                "path",
                "archive_type",
                "created",
                "modified",
            ]

            for field in required_fields:
                assert field in info, f"Missing required field: {field}"

            # Verify no file listing is returned
            forbidden_fields = ["files", "file_list", "members", "contents"]
            for field in forbidden_fields:
                assert field not in info, f"Unexpected field found: {field}"

    def test_backward_compatibility_structure(self):
        """Test that the new structure maintains essential backward compatibility."""
        mock_archive_path = "/mock/compat_test.7z"

        mock_file = ArchiveInfo("compat.txt")
        mock_file.file_size = 1000
        mock_file.compress_size = 600
        mock_file.method = "LZMA2:19"
        mock_file.type = "file"

        mock_members = [mock_file]

        mock_stat = MagicMock()
        mock_stat.st_size = 650
        mock_stat.st_ctime = 1642239045.0
        mock_stat.st_mtime = 1642239145.0

        with patch("py7zz.simple.Path.exists", return_value=True), patch(
            "py7zz.detailed_parser.get_detailed_archive_info", return_value=mock_members
        ), patch("py7zz.simple.Path.stat", return_value=mock_stat):
            info = get_archive_info(mock_archive_path)

            # Test that essential statistical fields are present
            # (These would be needed for existing user code)
            assert isinstance(info["file_count"], int)
            assert isinstance(info["compressed_size"], int)
            assert isinstance(info["uncompressed_size"], int)
            assert isinstance(info["compression_ratio"], float)
            assert isinstance(info["format"], str)
            assert isinstance(info["path"], str)

            # Test that ratios are in expected ranges
            assert 0.0 <= info["compression_ratio"] <= 1.0
            assert 0.0 <= info["compression_percentage"] <= 100.0

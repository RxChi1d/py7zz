"""
Tests for new SevenZipFile information methods.

This module tests the new industry-standard compatible methods:
- infolist() - zipfile.ZipFile compatible
- getinfo(name) - zipfile.ZipFile compatible
- getmembers() - tarfile.TarFile compatible
- getmember(name) - tarfile.TarFile compatible
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from py7zz.archive_info import ArchiveInfo
from py7zz.core import SevenZipFile


class TestSevenZipFileInfoMethods:
    """Test the new information methods of SevenZipFile."""

    def test_infolist_with_mocked_detailed_info(self):
        """Test infolist() method with mocked detailed info."""
        # Create mock archive
        mock_archive_path = Path("/mock/archive.7z")

        # Create mock ArchiveInfo objects
        mock_file1 = ArchiveInfo("file1.txt")
        mock_file1.file_size = 100
        mock_file1.compress_size = 80
        mock_file1.method = "LZMA2:19"
        mock_file1.type = "file"
        mock_file1.date_time = (2024, 1, 15, 10, 30, 45)

        mock_file2 = ArchiveInfo("dir/file2.txt")
        mock_file2.file_size = 200
        mock_file2.compress_size = 150
        mock_file2.method = "LZMA2:19"
        mock_file2.type = "file"
        mock_file2.date_time = (2024, 1, 15, 11, 0, 0)

        mock_dir = ArchiveInfo("dir/")
        mock_dir.file_size = 0
        mock_dir.compress_size = 0
        mock_dir.type = "dir"

        mock_members = [mock_file1, mock_file2, mock_dir]

        with patch("py7zz.core.Path.exists", return_value=True), patch.object(
            SevenZipFile, "_get_detailed_info", return_value=mock_members
        ):
            sz = SevenZipFile(mock_archive_path, "r")
            members = sz.infolist()

            assert len(members) == 3
            assert isinstance(members[0], ArchiveInfo)
            assert members[0].filename == "file1.txt"
            assert members[0].file_size == 100
            assert members[0].method == "LZMA2:19"

            assert members[1].filename == "dir/file2.txt"
            assert members[1].file_size == 200

            assert members[2].filename == "dir/"
            assert members[2].is_dir() is True

    def test_getinfo_existing_file(self):
        """Test getinfo() method for an existing file."""
        mock_archive_path = Path("/mock/archive.7z")

        # Create mock ArchiveInfo objects
        mock_file1 = ArchiveInfo("file1.txt")
        mock_file1.file_size = 100
        mock_file1.compress_size = 80
        mock_file1.method = "LZMA2:19"

        mock_file2 = ArchiveInfo("file2.txt")
        mock_file2.file_size = 200
        mock_file2.compress_size = 150

        mock_members = [mock_file1, mock_file2]

        with patch("py7zz.core.Path.exists", return_value=True), patch.object(
            SevenZipFile, "_get_detailed_info", return_value=mock_members
        ):
            sz = SevenZipFile(mock_archive_path, "r")

            # Test getting existing file
            info = sz.getinfo("file1.txt")
            assert isinstance(info, ArchiveInfo)
            assert info.filename == "file1.txt"
            assert info.file_size == 100
            assert info.method == "LZMA2:19"

    def test_getinfo_nonexistent_file(self):
        """Test getinfo() method for a non-existent file."""
        mock_archive_path = Path("/mock/archive.7z")

        mock_file1 = ArchiveInfo("file1.txt")
        mock_members = [mock_file1]

        with patch("py7zz.core.Path.exists", return_value=True), patch.object(
            SevenZipFile, "_get_detailed_info", return_value=mock_members
        ):
            sz = SevenZipFile(mock_archive_path, "r")

            # Test getting non-existent file
            with pytest.raises(
                KeyError, match="File 'nonexistent.txt' not found in archive"
            ):
                sz.getinfo("nonexistent.txt")

    def test_getmembers_tarfile_compatibility(self):
        """Test getmembers() method for tarfile compatibility."""
        mock_archive_path = Path("/mock/archive.7z")

        # Create mock ArchiveInfo objects with tarfile-style properties
        mock_file = ArchiveInfo("data.txt")
        mock_file.file_size = 150
        mock_file.compress_size = 120
        mock_file.type = "file"
        mock_file.mode = 0o644
        mock_file.uid = 1000
        mock_file.gid = 1000

        mock_dir = ArchiveInfo("subdir/")
        mock_dir.file_size = 0
        mock_dir.type = "dir"
        mock_dir.mode = 0o755

        mock_members = [mock_file, mock_dir]

        with patch("py7zz.core.Path.exists", return_value=True), patch.object(
            SevenZipFile, "_get_detailed_info", return_value=mock_members
        ):
            sz = SevenZipFile(mock_archive_path, "r")
            members = sz.getmembers()

            assert len(members) == 2
            assert isinstance(members[0], ArchiveInfo)

            # Test tarfile-style methods
            assert members[0].isfile() is True
            assert members[0].isdir() is False
            assert members[0].filename == "data.txt"

            assert members[1].isfile() is False
            assert members[1].isdir() is True
            assert members[1].filename == "subdir/"

    def test_getmember_existing_file(self):
        """Test getmember() method for existing file (tarfile compatibility)."""
        mock_archive_path = Path("/mock/archive.7z")

        mock_file = ArchiveInfo("target.txt")
        mock_file.file_size = 300
        mock_file.type = "file"

        mock_other = ArchiveInfo("other.txt")

        mock_members = [mock_file, mock_other]

        with patch("py7zz.core.Path.exists", return_value=True), patch.object(
            SevenZipFile, "_get_detailed_info", return_value=mock_members
        ):
            sz = SevenZipFile(mock_archive_path, "r")

            member = sz.getmember("target.txt")
            assert isinstance(member, ArchiveInfo)
            assert member.filename == "target.txt"
            assert member.file_size == 300

    def test_getmember_nonexistent_file(self):
        """Test getmember() method for non-existent file."""
        mock_archive_path = Path("/mock/archive.7z")

        mock_file = ArchiveInfo("exists.txt")
        mock_members = [mock_file]

        with patch("py7zz.core.Path.exists", return_value=True), patch.object(
            SevenZipFile, "_get_detailed_info", return_value=mock_members
        ):
            sz = SevenZipFile(mock_archive_path, "r")

            with pytest.raises(
                KeyError, match="File 'missing.txt' not found in archive"
            ):
                sz.getmember("missing.txt")

    def test_infolist_empty_archive(self):
        """Test infolist() with an empty archive."""
        mock_archive_path = Path("/mock/empty.7z")

        with patch("py7zz.core.Path.exists", return_value=True), patch.object(
            SevenZipFile, "_get_detailed_info", return_value=[]
        ):
            sz = SevenZipFile(mock_archive_path, "r")
            members = sz.infolist()

            assert len(members) == 0
            assert isinstance(members, list)

    def test_info_methods_with_detailed_parser_failure(self):
        """Test info methods when detailed parser fails."""
        mock_archive_path = Path("/mock/problematic.7z")

        # Mock _get_detailed_info to raise an exception
        with patch("py7zz.core.Path.exists", return_value=True), patch.object(
            SevenZipFile,
            "_get_detailed_info",
            side_effect=RuntimeError("Parser failed"),
        ):
            sz = SevenZipFile(mock_archive_path, "r")

            # These methods should propagate the runtime error
            with pytest.raises(RuntimeError, match="Parser failed"):
                sz.infolist()

            with pytest.raises(RuntimeError, match="Parser failed"):
                sz.getinfo("any_file.txt")

    def test_info_methods_with_unicode_filenames(self):
        """Test info methods with Unicode filenames."""
        mock_archive_path = Path("/mock/unicode.7z")

        # Create ArchiveInfo with Unicode filenames
        mock_unicode_file = ArchiveInfo("测试文件.txt")
        mock_unicode_file.file_size = 50
        mock_unicode_file.type = "file"

        mock_cyrillic_file = ArchiveInfo("файл.txt")
        mock_cyrillic_file.file_size = 75
        mock_cyrillic_file.type = "file"

        mock_members = [mock_unicode_file, mock_cyrillic_file]

        with patch("py7zz.core.Path.exists", return_value=True), patch.object(
            SevenZipFile, "_get_detailed_info", return_value=mock_members
        ):
            sz = SevenZipFile(mock_archive_path, "r")

            # Test infolist with Unicode
            members = sz.infolist()
            assert len(members) == 2
            assert members[0].filename == "测试文件.txt"
            assert members[1].filename == "файл.txt"

            # Test getinfo with Unicode
            info = sz.getinfo("测试文件.txt")
            assert info.filename == "测试文件.txt"
            assert info.file_size == 50

    def test_info_methods_consistency(self):
        """Test that all info methods return consistent data."""
        mock_archive_path = Path("/mock/consistent.7z")

        # Create test data
        mock_file1 = ArchiveInfo("consistent1.txt")
        mock_file1.file_size = 100
        mock_file1.compress_size = 80
        mock_file1.method = "LZMA2:19"
        mock_file1.type = "file"

        mock_file2 = ArchiveInfo("consistent2.txt")
        mock_file2.file_size = 200
        mock_file2.compress_size = 160
        mock_file2.method = "LZMA2:19"
        mock_file2.type = "file"

        mock_members = [mock_file1, mock_file2]

        with patch("py7zz.core.Path.exists", return_value=True), patch.object(
            SevenZipFile, "_get_detailed_info", return_value=mock_members
        ):
            sz = SevenZipFile(mock_archive_path, "r")

            # Get data using different methods
            infolist_members = sz.infolist()
            getmembers_members = sz.getmembers()
            getinfo_member = sz.getinfo("consistent1.txt")
            getmember_member = sz.getmember("consistent1.txt")

            # Test consistency
            assert len(infolist_members) == len(getmembers_members) == 2

            # All methods should return equivalent data for the same file
            assert (
                infolist_members[0].filename
                == getinfo_member.filename
                == getmember_member.filename
            )
            assert (
                infolist_members[0].file_size
                == getinfo_member.file_size
                == getmember_member.file_size
            )
            assert (
                infolist_members[0].method
                == getinfo_member.method
                == getmember_member.method
            )

            # Test that getinfo and getmember return identical objects
            assert getinfo_member.filename == getmember_member.filename
            assert getinfo_member.file_size == getmember_member.file_size
            assert getinfo_member.compress_size == getmember_member.compress_size

    def test_info_methods_with_special_characters(self):
        """Test info methods with files containing special characters."""
        mock_archive_path = Path("/mock/special.7z")

        # Files with special characters in names
        special_names = [
            "file with spaces.txt",
            "file-with-dashes.txt",
            "file_with_underscores.txt",
            "file.with.dots.txt",
            "file(with)parentheses.txt",
            "file[with]brackets.txt",
            "file{with}braces.txt",
        ]

        mock_members = []
        for i, name in enumerate(special_names):
            member = ArchiveInfo(name)
            member.file_size = (i + 1) * 10
            member.type = "file"
            mock_members.append(member)

        with patch("py7zz.core.Path.exists", return_value=True), patch.object(
            SevenZipFile, "_get_detailed_info", return_value=mock_members
        ):
            sz = SevenZipFile(mock_archive_path, "r")

            # Test infolist with special characters
            members = sz.infolist()
            assert len(members) == len(special_names)

            for i, member in enumerate(members):
                assert member.filename == special_names[i]
                assert member.file_size == (i + 1) * 10

            # Test getinfo with special characters
            for name in special_names:
                info = sz.getinfo(name)
                assert info.filename == name

    def test_info_methods_archive_not_found(self):
        """Test info methods behavior when archive doesn't exist."""
        nonexistent_path = Path("/nonexistent/archive.7z")

        # Don't patch Path.exists so the detailed parser will detect the missing file
        sz = SevenZipFile(nonexistent_path, "r")

        # These should fail because _get_detailed_info will fail
        # when trying to run 7zz on non-existent file
        with pytest.raises(FileNotFoundError, match="Archive not found"):
            sz.infolist()

        with pytest.raises(FileNotFoundError, match="Archive not found"):
            sz.getinfo("any_file.txt")


class TestInfoMethodsIntegration:
    """Integration tests for info methods with real-like scenarios."""

    def test_zipfile_compatibility_interface(self):
        """Test that the interface matches zipfile.ZipFile expectations."""
        mock_archive_path = Path("/mock/zipfile_compat.7z")

        # Create zipfile-like test data
        mock_file = ArchiveInfo("document.txt")
        mock_file.file_size = 1024
        mock_file.compress_size = 512
        mock_file.CRC = 0x12345678
        mock_file.date_time = (2024, 1, 15, 10, 30, 45)
        mock_file.compress_type = "LZMA2:19"
        mock_file.type = "file"

        mock_members = [mock_file]

        with patch("py7zz.core.Path.exists", return_value=True), patch.object(
            SevenZipFile, "_get_detailed_info", return_value=mock_members
        ):
            sz = SevenZipFile(mock_archive_path, "r")

            # Test zipfile-style interface
            info_list = sz.infolist()
            assert hasattr(info_list[0], "filename")
            assert hasattr(info_list[0], "file_size")
            assert hasattr(info_list[0], "compress_size")
            assert hasattr(info_list[0], "CRC")
            assert hasattr(info_list[0], "date_time")
            assert hasattr(info_list[0], "is_dir")

            # Test zipfile-style method calls
            info = sz.getinfo("document.txt")
            assert info.is_dir() is False
            assert info.get_compression_ratio() > 0

    def test_tarfile_compatibility_interface(self):
        """Test that the interface matches tarfile.TarFile expectations."""
        mock_archive_path = Path("/mock/tarfile_compat.7z")

        # Create tarfile-like test data
        mock_file = ArchiveInfo("data.txt")
        mock_file.file_size = 2048
        mock_file.mode = 0o644
        mock_file.uid = 1000
        mock_file.gid = 1000
        mock_file.mtime = 1642239045.0  # Unix timestamp
        mock_file.type = "file"

        mock_dir = ArchiveInfo("subdir/")
        mock_dir.file_size = 0
        mock_dir.mode = 0o755
        mock_dir.type = "dir"

        mock_members = [mock_file, mock_dir]

        with patch("py7zz.core.Path.exists", return_value=True), patch.object(
            SevenZipFile, "_get_detailed_info", return_value=mock_members
        ):
            sz = SevenZipFile(mock_archive_path, "r")

            # Test tarfile-style interface
            members = sz.getmembers()
            assert hasattr(members[0], "isfile")
            assert hasattr(members[0], "isdir")
            assert hasattr(members[0], "islink")
            assert hasattr(members[0], "mode")
            assert hasattr(members[0], "uid")
            assert hasattr(members[0], "gid")

            # Test tarfile-style method calls
            member = sz.getmember("data.txt")
            assert member.isfile() is True
            assert member.isdir() is False
            assert member.islink() is False
            assert member.mode == 0o644

    def test_mixed_api_usage(self):
        """Test using both zipfile and tarfile APIs on the same archive."""
        mock_archive_path = Path("/mock/mixed_api.7z")

        # Create comprehensive test data
        mock_file = ArchiveInfo("mixed.txt")
        mock_file.file_size = 512
        mock_file.compress_size = 256
        mock_file.CRC = 0xABCDEF12
        mock_file.date_time = (2024, 2, 20, 14, 25, 10)
        mock_file.mode = 0o644
        mock_file.uid = 1001
        mock_file.gid = 1001
        mock_file.type = "file"

        mock_members = [mock_file]

        with patch("py7zz.core.Path.exists", return_value=True), patch.object(
            SevenZipFile, "_get_detailed_info", return_value=mock_members
        ):
            sz = SevenZipFile(mock_archive_path, "r")

            # Use zipfile API
            zipfile_info = sz.getinfo("mixed.txt")
            zipfile_list = sz.infolist()

            # Use tarfile API
            tarfile_member = sz.getmember("mixed.txt")
            tarfile_members = sz.getmembers()

            # Both APIs should return the same underlying data
            assert zipfile_info.filename == tarfile_member.filename
            assert zipfile_info.file_size == tarfile_member.file_size
            assert len(zipfile_list) == len(tarfile_members)

            # Both APIs should work on the same object
            assert zipfile_info.is_dir() == (not tarfile_member.isfile())
            assert zipfile_info.CRC == 0xABCDEF12
            assert tarfile_member.mode == 0o644

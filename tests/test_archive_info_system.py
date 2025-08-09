# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""
Test suite for py7zz Archive Information System.

This module tests all archive information functionality including:
1. ArchiveInfo class - zipfile/tarfile compatible archive member information
2. SevenZipFile information methods (infolist, getinfo, getmembers, getmember)
3. Redesigned get_archive_info function - pure archive statistics
4. Archive summary creation and integration
5. Compatibility with zipfile.ZipFile and tarfile.TarFile APIs

Consolidated from:
- test_archive_info.py (ArchiveInfo class functionality)
- test_new_info_methods.py (SevenZipFile information methods)
- test_redesigned_archive_info.py (get_archive_info function)
"""

import datetime
from pathlib import Path
from typing import List
from unittest.mock import MagicMock, patch

import pytest

import py7zz
from py7zz.archive_info import ArchiveInfo
from py7zz.core import SevenZipFile
from py7zz.detailed_parser import create_archive_summary
from py7zz.exceptions import FileNotFoundError as Py7zzFileNotFoundError
from py7zz.simple import get_archive_info


class TestArchiveInfoClass:
    """Test cases for ArchiveInfo class."""

    def test_init_basic(self):
        """Test basic initialization of ArchiveInfo."""
        info = ArchiveInfo("test.txt")

        assert info.filename == "test.txt"
        assert info.orig_filename == "test.txt"
        assert info.file_size == 0
        assert info.compress_size == 0
        assert info.date_time is None
        assert info.mtime is None
        assert info.compress_type is None
        assert info.CRC == 0
        assert info.comment == ""
        assert info.type == "file"

    def test_init_empty(self):
        """Test initialization with empty filename."""
        info = ArchiveInfo()

        assert info.filename == ""
        assert info.orig_filename == ""

    def test_repr_and_str(self):
        """Test string representations."""
        info = ArchiveInfo("test.txt")
        info.file_size = 1024
        info.compress_size = 512
        info.compress_type = "LZMA2"

        repr_str = repr(info)
        assert "ArchiveInfo" in repr_str
        assert "test.txt" in repr_str
        assert "LZMA2" in repr_str
        assert "1024" in repr_str
        assert "512" in repr_str

        str_str = str(info)
        assert "test.txt" in str_str
        assert "1024 bytes" in str_str

    def test_is_dir(self):
        """Test directory detection."""
        # Test with directory type
        dir_info = ArchiveInfo("folder/")
        dir_info.type = "dir"
        assert dir_info.is_dir() is True
        assert dir_info.is_directory is True

        # Test with trailing slash
        slash_info = ArchiveInfo("folder/")
        assert slash_info.is_dir() is True

        # Test regular file
        file_info = ArchiveInfo("file.txt")
        file_info.type = "file"
        assert file_info.is_dir() is False

    def test_tarfile_compatibility_methods(self):
        """Test tarfile.TarInfo compatible methods."""
        # Regular file
        file_info = ArchiveInfo("file.txt")
        file_info.type = "file"

        assert file_info.isfile() is True
        assert file_info.isreg() is True
        assert file_info.isdir() is False
        assert file_info.islink() is False
        assert file_info.issym() is False

        # Directory
        dir_info = ArchiveInfo("folder/")
        dir_info.type = "dir"

        assert dir_info.isfile() is False
        assert dir_info.isdir() is True
        assert dir_info.islink() is False

        # Symbolic link
        link_info = ArchiveInfo("link.txt")
        link_info.type = "link"

        assert link_info.isfile() is False
        assert link_info.isdir() is False
        assert link_info.islink() is True
        assert link_info.issym() is True

    def test_time_handling_from_datetime(self):
        """Test time handling with datetime objects."""
        info = ArchiveInfo("test.txt")
        test_time = datetime.datetime(2024, 1, 15, 10, 30, 45)

        info.set_mtime(test_time)

        assert info.date_time == (2024, 1, 15, 10, 30, 45)
        assert info.mtime == test_time.timestamp()

        retrieved_dt = info.get_datetime()
        assert retrieved_dt == test_time

        retrieved_mtime = info.get_mtime()
        assert retrieved_mtime == test_time.timestamp()

    def test_time_handling_from_timestamp(self):
        """Test time handling with Unix timestamps."""
        info = ArchiveInfo("test.txt")
        test_timestamp = 1705312245.0  # 2024-01-15 (time varies by timezone)

        info.set_mtime(test_timestamp)

        assert info.mtime == test_timestamp
        # Check that date_time is set (exact time depends on local timezone)
        assert info.date_time is not None
        assert len(info.date_time) == 6
        assert info.date_time[0] == 2024  # Year should be correct
        assert info.date_time[1] == 1  # Month should be correct
        assert info.date_time[2] == 15  # Day should be correct

        retrieved_mtime = info.get_mtime()
        assert retrieved_mtime == test_timestamp

    def test_time_handling_no_time(self):
        """Test time handling when no time information is available."""
        info = ArchiveInfo("test.txt")

        assert info.get_mtime() is None
        assert info.get_datetime() is None

    def test_compression_ratio_calculation(self):
        """Test compression ratio calculation."""
        info = ArchiveInfo("test.txt")

        # No compression (0% compression)
        info.file_size = 1000
        info.compress_size = 1000

        assert info.get_compression_ratio() == 0.0
        assert info.get_compression_percentage() == 0.0

        # 50% compression
        info.compress_size = 500

        assert info.get_compression_ratio() == 0.5
        assert info.get_compression_percentage() == 50.0

        # 90% compression
        info.compress_size = 100

        assert info.get_compression_ratio() == 0.9
        assert info.get_compression_percentage() == 90.0

        # Edge case: empty file
        info.file_size = 0
        info.compress_size = 0

        assert info.get_compression_ratio() == 0.0

        # Edge case: compress_size is 0 (impossible but handle gracefully)
        info.file_size = 1000
        info.compress_size = 0

        assert info.get_compression_ratio() == 1.0

    def test_file_path_utilities(self):
        """Test file path utility properties."""
        info = ArchiveInfo("folder/subfolder/file.txt")

        assert info.basename == "file.txt"
        assert info.dirname == "folder/subfolder"

        # Test root file
        root_info = ArchiveInfo("root.txt")
        assert root_info.basename == "root.txt"
        assert root_info.dirname == ""

    def test_validation_basic(self):
        """Test basic validation functionality."""
        # Valid info
        info = ArchiveInfo("test.txt")
        info.file_size = 1000
        info.compress_size = 500
        info.date_time = (2024, 1, 15, 10, 30, 45)

        assert info.validate() is True

        # Invalid: no filename
        info.filename = ""
        assert info.validate() is False

        # Invalid: negative sizes
        info.filename = "test.txt"
        info.file_size = -1
        assert info.validate() is False

        info.file_size = 1000
        info.compress_size = -1
        assert info.validate() is False

    def test_validation_datetime(self):
        """Test datetime validation."""
        info = ArchiveInfo("test.txt")

        # Valid date_time
        info.date_time = (2024, 1, 15, 10, 30, 45)
        assert info.validate() is True

        # Invalid: wrong tuple length
        info.date_time = (2024, 1, 15, 10, 30)
        assert info.validate() is False

        # Invalid: year out of range (too old)
        info.date_time = (1979, 1, 15, 10, 30, 45)
        assert info.validate() is False

        # Invalid: year out of range (too new)
        info.date_time = (2108, 1, 15, 10, 30, 45)
        assert info.validate() is False

        # Invalid: month out of range
        info.date_time = (2024, 13, 15, 10, 30, 45)
        assert info.validate() is False

        # Invalid: day out of range
        info.date_time = (2024, 1, 32, 10, 30, 45)
        assert info.validate() is False

        # Invalid: hour out of range
        info.date_time = (2024, 1, 15, 24, 30, 45)
        assert info.validate() is False

        # Invalid: minute out of range
        info.date_time = (2024, 1, 15, 10, 60, 45)
        assert info.validate() is False

        # Invalid: second out of range
        info.date_time = (2024, 1, 15, 10, 30, 60)
        assert info.validate() is False

    def test_from_zipinfo(self):
        """Test factory method from zipfile.ZipInfo (mock)."""

        # Mock zipfile.ZipInfo object
        class MockZipInfo:
            def __init__(self):
                self.filename = "test.txt"
                self.file_size = 1024
                self.compress_size = 512
                self.date_time = (2024, 1, 15, 10, 30, 45)
                self.CRC = 0x12345678
                self.compress_type = 8  # ZIP_DEFLATED
                self.comment = b"test comment"
                self.extra = b"extra data"
                self.create_system = 0
                self.create_version = 20
                self.extract_version = 20
                self.reserved = 0
                self.flag_bits = 0
                self.volume = 0
                self.internal_attr = 0
                self.external_attr = 32
                self.header_offset = 0

        mock_zipinfo = MockZipInfo()
        info = ArchiveInfo.from_zipinfo(mock_zipinfo)

        assert info.filename == "test.txt"
        assert info.file_size == 1024
        assert info.compress_size == 512
        assert info.date_time == (2024, 1, 15, 10, 30, 45)
        assert info.CRC == 0x12345678
        assert info.compress_type == "8"
        assert info.comment == "test comment"
        assert info.extra == b"extra data"
        assert info.type == "file"

    def test_from_tarinfo(self):
        """Test factory method from tarfile.TarInfo (mock)."""

        # Mock tarfile.TarInfo object
        class MockTarInfo:
            def __init__(self):
                self.name = "test.txt"
                self.size = 1024
                self.mtime = 1705312245.0  # 2024-01-15 10:30:45
                self.mode = 0o644
                self.uid = 1000
                self.gid = 1000
                self.uname = "user"
                self.gname = "group"

            def isfile(self):
                return True

            def isdir(self):
                return False

            def islink(self):
                return False

            def issym(self):
                return False

        mock_tarinfo = MockTarInfo()
        info = ArchiveInfo.from_tarinfo(mock_tarinfo)

        assert info.filename == "test.txt"
        assert info.file_size == 1024
        assert info.compress_size == 1024  # TAR doesn't compress individual files
        assert info.mtime == 1705312245.0
        # Check that date_time is set (exact time depends on local timezone)
        assert info.date_time is not None
        assert len(info.date_time) == 6
        assert info.date_time[0] == 2024  # Year should be correct
        assert info.date_time[1] == 1  # Month should be correct
        assert info.date_time[2] == 15  # Day should be correct
        assert info.mode == 0o644
        assert info.uid == 1000
        assert info.gid == 1000
        assert info.uname == "user"
        assert info.gname == "group"
        assert info.type == "file"

    def test_directory_from_tarinfo(self):
        """Test directory handling from tarfile.TarInfo (mock)."""

        class MockTarInfoDir:
            def __init__(self):
                self.name = "folder/"
                self.size = 0
                self.mtime = 1705312245.0
                self.mode = 0o755
                self.uid = 1000
                self.gid = 1000
                self.uname = "user"
                self.gname = "group"

            def isfile(self):
                return False

            def isdir(self):
                return True

            def islink(self):
                return False

            def issym(self):
                return False

        mock_tarinfo = MockTarInfoDir()
        info = ArchiveInfo.from_tarinfo(mock_tarinfo)

        assert info.filename == "folder/"
        assert info.type == "dir"
        assert info.isdir() is True
        assert info.isfile() is False

    def test_comprehensive_properties(self):
        """Test that all expected properties are present and correctly typed."""
        info = ArchiveInfo("comprehensive_test.txt")

        # Basic properties
        assert hasattr(info, "filename")
        assert hasattr(info, "orig_filename")
        assert hasattr(info, "file_size")
        assert hasattr(info, "compress_size")

        # Time properties
        assert hasattr(info, "date_time")
        assert hasattr(info, "mtime")

        # Compression properties
        assert hasattr(info, "compress_type")
        assert hasattr(info, "CRC")
        assert hasattr(info, "method")
        assert hasattr(info, "solid")
        assert hasattr(info, "encrypted")

        # File system properties
        assert hasattr(info, "mode")
        assert hasattr(info, "uid")
        assert hasattr(info, "gid")
        assert hasattr(info, "uname")
        assert hasattr(info, "gname")
        assert hasattr(info, "type")

        # Additional metadata
        assert hasattr(info, "comment")
        assert hasattr(info, "extra")

        # Verify all properties have sensible default values
        assert isinstance(info.filename, str)
        assert isinstance(info.file_size, int)
        assert isinstance(info.compress_size, int)
        assert isinstance(info.CRC, int)
        assert isinstance(info.comment, str)
        assert isinstance(info.extra, bytes)
        assert isinstance(info.type, str)
        assert isinstance(info.encrypted, bool)


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


class TestGetArchiveInfoFunction:
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
                # Handle cross-platform path format differences
                assert Path(info["path"]).resolve() == Path(archive_path_str).resolve()

    def test_get_archive_info_empty_archive(self):
        """Test get_archive_info with an empty archive."""
        mock_archive_path = Path("/mock/empty.7z")

        # Empty members list
        mock_members: List[ArchiveInfo] = []

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

                # Handle cross-platform path format differences for Unicode paths
                assert Path(info["path"]).resolve() == Path(unicode_path_str).resolve()
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


class TestAPICompatibilityIntegration:
    """Integration tests for API compatibility across different interfaces."""

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

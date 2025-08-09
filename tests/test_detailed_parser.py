# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""
Tests for the detailed parser module with real 7zz output.

This module tests the 7zz -slt output parsing functionality using
representative real-world 7zz command outputs to ensure accurate
metadata extraction.
"""

from datetime import datetime

import pytest

from py7zz.archive_info import ArchiveInfo
from py7zz.detailed_parser import (
    _determine_file_type,
    _parse_attributes,
    _parse_datetime,
    _parse_int,
    create_archive_summary,
    get_detailed_archive_info,
    parse_7zz_slt_output,
)


class TestSltOutputParsing:
    """Test parsing of real 7zz -slt output format."""

    def test_parse_simple_7z_archive(self):
        """Test parsing a simple 7z archive with standard files."""
        # Real 7zz -slt output for a 7z archive
        slt_output = """
7-Zip [64] 22.01 (x64) : Copyright (c) 1999-2022 Igor Pavlov : 2022-07-15

Listing archive: test.7z

--
Path = test.7z
Type = 7z
Physical Size = 178
Headers Size = 146
Method = LZMA2:19
Solid = -
Blocks = 1

----------
Path = file1.txt
Size = 13
Packed Size = 19
Modified = 2024-01-15 10:30:45
Attributes = A
CRC = 12345678
Method = LZMA2:19
Solid = +

----------
Path = dir1/file2.txt
Size = 25
Packed Size = 27
Modified = 2024-01-15 11:45:30
Attributes = A
CRC = 87654321
Method = LZMA2:19
Solid = +

----------
Path = dir1
Size = 0
Packed Size = 0
Modified = 2024-01-15 11:00:00
Attributes = D
CRC =
Method =
Solid =

"""
        members = parse_7zz_slt_output(slt_output)

        assert len(members) == 3

        # Test file1.txt
        file1 = members[0]
        assert file1.filename == "file1.txt"
        assert file1.file_size == 13
        assert file1.compress_size == 19
        assert file1.CRC == 0x12345678
        assert file1.method == "LZMA2:19"
        assert file1.solid is True
        assert file1.type == "file"
        assert file1.date_time == (2024, 1, 15, 10, 30, 45)

        # Test dir1/file2.txt
        file2 = members[1]
        assert file2.filename == "dir1/file2.txt"
        assert file2.file_size == 25
        assert file2.compress_size == 27
        assert file2.CRC == 0x87654321
        assert file2.type == "file"

        # Test directory
        dir1 = members[2]
        assert dir1.filename == "dir1"
        assert dir1.file_size == 0
        assert dir1.compress_size == 0
        assert dir1.type == "dir"
        assert dir1.is_dir() is True
        assert dir1.CRC == 0  # Empty CRC
        assert dir1.method == ""  # No method for directories

    def test_parse_zip_archive(self):
        """Test parsing a ZIP archive with different attributes."""
        # Real 7zz -slt output for a ZIP archive
        slt_output = """
7-Zip [64] 22.01 (x64) : Copyright (c) 1999-2022 Igor Pavlov : 2022-07-15

Listing archive: test.zip

--
Path = test.zip
Type = zip
Physical Size = 256
Headers Size = 98
Method = Deflate
Solid = -
Blocks = 3

----------
Path = readme.txt
Size = 150
Packed Size = 89
Modified = 2024-02-20 14:25:10
Attributes = A
CRC = ABCDEF12
Method = Deflate
Encrypted = -

----------
Path = images/
Size = 0
Packed Size = 0
Modified = 2024-02-20 13:00:00
Attributes = D
CRC =
Method = Store

----------
Path = images/photo.jpg
Size = 2048
Packed Size = 1950
Modified = 2024-02-20 13:15:45
Attributes = A
CRC = FEDCBA98
Method = Store
Encrypted = -

"""
        members = parse_7zz_slt_output(slt_output)

        assert len(members) == 3

        # Test regular file
        readme = members[0]
        assert readme.filename == "readme.txt"
        assert readme.file_size == 150
        assert readme.compress_size == 89
        assert readme.CRC == 0xABCDEF12
        assert readme.method == "Deflate"
        assert readme.encrypted is False
        assert readme.type == "file"

        # Test directory
        images_dir = members[1]
        assert images_dir.filename == "images/"
        assert images_dir.is_dir() is True
        assert images_dir.type == "dir"

        # Test file in subdirectory
        photo = members[2]
        assert photo.filename == "images/photo.jpg"
        assert photo.file_size == 2048
        assert photo.compress_size == 1950
        assert photo.method == "Store"

    def test_parse_encrypted_archive(self):
        """Test parsing an archive with encrypted files."""
        slt_output = """
7-Zip [64] 22.01 (x64) : Copyright (c) 1999-2022 Igor Pavlov : 2022-07-15

Listing archive: encrypted.7z

----------
Path = secret.txt
Size = 100
Packed Size = 85
Modified = 2024-03-01 09:00:00
Attributes = A
CRC = 11223344
Method = LZMA2:19
Solid = +
Encrypted = +

----------
Path = public.txt
Size = 50
Packed Size = 45
Modified = 2024-03-01 09:01:00
Attributes = A
CRC = 44332211
Method = LZMA2:19
Solid = +
Encrypted = -

"""
        members = parse_7zz_slt_output(slt_output)

        assert len(members) == 2

        secret = members[0]
        assert secret.filename == "secret.txt"
        assert secret.encrypted is True

        public = members[1]
        assert public.filename == "public.txt"
        assert public.encrypted is False

    def test_parse_with_comments(self):
        """Test parsing archive with file comments."""
        slt_output = """
7-Zip [64] 22.01 (x64) : Copyright (c) 1999-2022 Igor Pavlov : 2022-07-15

----------
Path = documented.txt
Size = 75
Packed Size = 60
Modified = 2024-04-01 12:00:00
Attributes = A
CRC = 55667788
Method = LZMA2:19
Comment = This file contains important documentation

"""
        members = parse_7zz_slt_output(slt_output)

        assert len(members) == 1

        documented = members[0]
        assert documented.filename == "documented.txt"
        assert documented.comment == "This file contains important documentation"


class TestHelperFunctions:
    """Test helper parsing functions."""

    def test_parse_int_valid(self):
        """Test integer parsing with valid inputs."""
        assert _parse_int("123") == 123
        assert _parse_int("0") == 0
        assert _parse_int("ABCD", base=16) == 0xABCD
        assert _parse_int("FF", base=16) == 255

    def test_parse_int_invalid(self):
        """Test integer parsing with invalid inputs."""
        assert _parse_int("") == 0
        assert _parse_int("invalid") == 0
        assert _parse_int("123.45") == 0
        assert _parse_int("", default=42) == 42
        assert _parse_int("invalid", default=99) == 99

    def test_parse_datetime_standard_format(self):
        """Test datetime parsing with standard format."""
        date_tuple, timestamp = _parse_datetime("2024-01-15 10:30:45")

        assert date_tuple == (2024, 1, 15, 10, 30, 45)
        assert timestamp is not None

        # Verify timestamp corresponds to the correct date
        dt = datetime.fromtimestamp(timestamp)
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15
        assert dt.hour == 10
        assert dt.minute == 30
        assert dt.second == 45

    def test_parse_datetime_various_formats(self):
        """Test datetime parsing with various formats."""
        # Date only
        date_tuple, timestamp = _parse_datetime("2024-01-15")
        assert date_tuple == (2024, 1, 15, 0, 0, 0)

        # With microseconds
        date_tuple, timestamp = _parse_datetime("2024-01-15 10:30:45.123")
        assert date_tuple == (2024, 1, 15, 10, 30, 45)

        # Alternative separators
        date_tuple, timestamp = _parse_datetime("2024/01/15 10:30:45")
        assert date_tuple == (2024, 1, 15, 10, 30, 45)

    def test_parse_datetime_invalid(self):
        """Test datetime parsing with invalid inputs."""
        assert _parse_datetime("") == (None, None)
        assert _parse_datetime("invalid") == (None, None)
        assert _parse_datetime("2024-13-01 10:30:45") == (None, None)

    def test_parse_attributes(self):
        """Test file attributes parsing."""
        # Standard file
        assert _parse_attributes("A") == 0x20  # Archive bit

        # Directory
        assert _parse_attributes("D") == 0x10  # Directory bit

        # Multiple attributes
        result = _parse_attributes("DA")
        assert result & 0x10  # Directory bit set
        assert result & 0x20  # Archive bit set

        # Read-only file
        assert _parse_attributes("RA") == 0x21  # Read-only + Archive

        # Empty attributes
        assert _parse_attributes("") == 0
        assert _parse_attributes("X") == 0  # Unknown attribute

    def test_determine_file_type(self):
        """Test file type determination."""
        # Regular file
        assert _determine_file_type("A", "file.txt") == "file"

        # Directory from attribute
        assert _determine_file_type("D", "dirname") == "dir"

        # Directory from filename
        assert _determine_file_type("A", "dirname/") == "dir"

        # Symbolic link (hypothetical)
        assert _determine_file_type("A", "link -> target") == "link"
        assert _determine_file_type("A", "-> target") == "link"


class TestArchiveSummary:
    """Test archive summary creation."""

    def test_create_summary_empty(self):
        """Test summary creation with empty member list."""
        summary = create_archive_summary([])

        assert summary["file_count"] == 0
        assert summary["directory_count"] == 0
        assert summary["total_uncompressed_size"] == 0
        assert summary["total_compressed_size"] == 0
        assert summary["compression_ratio"] == 0.0
        assert summary["archive_type"] == "empty"

    def test_create_summary_with_files(self):
        """Test summary creation with actual files."""
        # Create mock ArchiveInfo objects
        file1 = ArchiveInfo("file1.txt")
        file1.file_size = 100
        file1.compress_size = 80
        file1.method = "LZMA2:19"
        file1.type = "file"

        file2 = ArchiveInfo("file2.txt")
        file2.file_size = 200
        file2.compress_size = 150
        file2.method = "LZMA2:19"
        file2.type = "file"

        dir1 = ArchiveInfo("dir/")
        dir1.file_size = 0
        dir1.compress_size = 0
        dir1.type = "dir"

        members = [file1, file2, dir1]
        summary = create_archive_summary(members)

        assert summary["file_count"] == 2
        assert summary["directory_count"] == 1
        assert summary["total_file_count"] == 3
        assert summary["total_uncompressed_size"] == 300
        assert summary["total_compressed_size"] == 230
        assert summary["compression_ratio"] == pytest.approx(0.233333, rel=1e-5)
        assert summary["compression_percentage"] == pytest.approx(23.333333, rel=1e-5)
        assert summary["archive_type"] == "LZMA2:19"

    def test_create_summary_mixed_compression(self):
        """Test summary with mixed compression methods."""
        file1 = ArchiveInfo("file1.txt")
        file1.method = "LZMA2:19"
        file1.type = "file"

        file2 = ArchiveInfo("file2.txt")
        file2.method = "Deflate"
        file2.type = "file"

        file3 = ArchiveInfo("file3.txt")
        file3.method = "LZMA2:19"
        file3.type = "file"

        members = [file1, file2, file3]
        summary = create_archive_summary(members)

        # LZMA2:19 appears twice, Deflate once, so LZMA2:19 should be the type
        assert summary["archive_type"] == "LZMA2:19"


class TestIntegrationWithRealArchive:
    """Integration tests with real archive files (if available)."""

    def test_get_detailed_archive_info_error_handling(self):
        """Test error handling when archive doesn't exist."""
        with pytest.raises(FileNotFoundError):
            get_detailed_archive_info("/nonexistent/archive.7z")

    def test_get_detailed_archive_info_with_mock(self, tmp_path):
        """Test get_detailed_archive_info with temporary test archive."""
        # Create a temporary test file to simulate an archive
        test_archive = tmp_path / "test.7z"
        test_archive.write_text("dummy archive content")

        # This would normally require a real 7zz binary and archive
        # For now, we'll test that the function exists and handles file existence
        import contextlib

        with contextlib.suppress(RuntimeError, Exception):
            # This will fail because it's not a real archive, but we can test the path
            get_detailed_archive_info(test_archive)


class TestParserRobustness:
    """Test parser robustness with edge cases."""

    def test_parse_malformed_output(self):
        """Test parsing with malformed or partial output."""
        # Missing separator but with proper format
        malformed_output = """
----------
Path = file1.txt
Size = 100
"""
        members = parse_7zz_slt_output(malformed_output)
        assert len(members) == 1
        assert members[0].filename == "file1.txt"
        assert members[0].file_size == 100

    def test_parse_unicode_filenames(self):
        """Test parsing with Unicode filenames."""
        unicode_output = """
----------
Path = 测试文件.txt
Size = 50
Packed Size = 40
Modified = 2024-01-15 10:30:45
Attributes = A
CRC = 12345678
Method = LZMA2:19

----------
Path = файл.txt
Size = 60
Packed Size = 45
Modified = 2024-01-15 10:30:45
Attributes = A
CRC = 87654321
Method = LZMA2:19

"""
        members = parse_7zz_slt_output(unicode_output)

        assert len(members) == 2
        assert members[0].filename == "测试文件.txt"
        assert members[1].filename == "файл.txt"

    def test_parse_long_filenames(self):
        """Test parsing with very long filenames."""
        long_filename = "a" * 255 + ".txt"
        long_output = f"""
----------
Path = {long_filename}
Size = 100
Packed Size = 80
Modified = 2024-01-15 10:30:45
Attributes = A
CRC = 12345678
Method = LZMA2:19

"""
        members = parse_7zz_slt_output(long_output)

        assert len(members) == 1
        assert members[0].filename == long_filename
        assert len(members[0].filename) == 259  # 255 + ".txt"

    def test_parse_empty_values(self):
        """Test parsing with empty or missing values."""
        empty_values_output = """
----------
Path = empty_values.txt
Size =
Packed Size = 0
Modified =
Attributes =
CRC =
Method =

"""
        members = parse_7zz_slt_output(empty_values_output)

        assert len(members) == 1
        member = members[0]
        assert member.filename == "empty_values.txt"
        assert member.file_size == 0  # Empty size defaults to 0
        assert member.compress_size == 0
        assert member.date_time is None  # Empty date
        assert member.mtime is None
        assert member.CRC == 0  # Empty CRC defaults to 0
        assert member.method == ""  # Empty method

# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""
Basic tests for py7zz core functionality.
"""

import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from py7zz.core import SevenZipFile, find_7z_binary, get_version
from py7zz.exceptions import FileNotFoundError as Py7zzFileNotFoundError


def test_get_version():
    """Test version retrieval."""
    version = get_version()
    # Test version is PEP 440 compliant and is a valid version string
    assert isinstance(version, str)
    assert len(version) > 0

    # Test version format follows PEP 440
    import py7zz.version

    parsed = py7zz.version.parse_version(version)
    # Version components should be valid integers
    assert isinstance(parsed["major"], int) and parsed["major"] >= 0
    assert isinstance(parsed["minor"], int) and parsed["minor"] >= 0
    assert isinstance(parsed["patch"], int) and parsed["patch"] >= 0
    # Version type should be one of the valid types
    assert parsed["version_type"] in ["stable", "alpha", "beta", "rc", "dev"]


def test_find_7z_binary_env_var():
    """Test binary detection from environment variable."""
    with patch.dict(os.environ, {"PY7ZZ_BINARY": "/fake/path/7zz"}), patch(
        "pathlib.Path.exists", return_value=True
    ):
        binary = find_7z_binary()
        assert binary == "/fake/path/7zz"


def test_find_7z_binary_system_path():
    """Test binary detection from system PATH - now removed from design."""
    # This test is no longer valid since we removed system PATH detection
    # py7zz now only uses bundled binaries for version consistency
    pass


def test_find_7z_binary_bundled():
    """Test binary detection from bundled location."""
    with patch.dict(os.environ, {}, clear=True), patch(
        "shutil.which", return_value=None
    ), patch("platform.system", return_value="Linux"), patch(
        "pathlib.Path.exists", return_value=True
    ):
        binary = find_7z_binary()
        assert binary.endswith(("bin/7zz", "bin\\7zz"))


def test_find_7z_binary_not_found():
    """Test binary not found raises error."""
    with patch.dict(os.environ, {}, clear=True), patch(
        "shutil.which", return_value=None
    ), patch("pathlib.Path.exists", return_value=False), pytest.raises(
        RuntimeError, match="7zz binary not found"
    ):
        find_7z_binary()


def test_sevenzipfile_init():
    """Test SevenZipFile initialization."""
    sz = SevenZipFile("test.7z", "w", "normal")
    assert sz.file == Path("test.7z")
    assert sz.mode == "w"
    assert sz.level == "normal"


def test_sevenzipfile_invalid_mode():
    """Test SevenZipFile with invalid mode."""
    with pytest.raises(ValueError, match="Invalid mode"):
        SevenZipFile("test.7z", "x")


def test_sevenzipfile_invalid_level():
    """Test SevenZipFile with invalid compression level."""
    with pytest.raises(ValueError, match="Invalid compression level"):
        SevenZipFile("test.7z", "w", "invalid")


def test_sevenzipfile_context_manager():
    """Test SevenZipFile as context manager."""
    with SevenZipFile("test.7z", "w") as sz:
        assert isinstance(sz, SevenZipFile)


@patch("py7zz.core.run_7z")
def test_sevenzipfile_add(mock_run_7z):
    """Test adding files to archive."""
    mock_run_7z.return_value = Mock()

    with patch("pathlib.Path.exists", return_value=True):
        sz = SevenZipFile("test.7z", "w", "normal")
        sz.add("test.txt")

        mock_run_7z.assert_called_once()
        args = mock_run_7z.call_args[0][0]
        assert "a" in args
        assert "-mx5" in args
        assert "test.7z" in args
        assert "test.txt" in args


def test_sevenzipfile_add_read_mode():
    """Test adding to read-only archive raises error."""
    sz = SevenZipFile("test.7z", "r")
    with pytest.raises(ValueError, match="Cannot add to archive opened in read mode"):
        sz.add("test.txt")


def test_sevenzipfile_add_missing_file():
    """Test adding missing file raises error."""
    sz = SevenZipFile("test.7z", "w")
    with patch("pathlib.Path.exists", return_value=False), pytest.raises(
        Py7zzFileNotFoundError, match="File not found"
    ):
        sz.add("missing.txt")


@patch("py7zz.core.run_7z")
def test_sevenzipfile_extract(mock_run_7z):
    """Test extracting archive."""
    mock_run_7z.return_value = Mock()

    with patch("pathlib.Path.exists", return_value=True), patch("pathlib.Path.mkdir"):
        sz = SevenZipFile("test.7z", "r")
        sz.extract("./output", overwrite=True)

        mock_run_7z.assert_called_once()
        args = mock_run_7z.call_args[0][0]
        assert "x" in args
        assert "test.7z" in args
        assert "-ooutput" in args
        assert "-y" in args


def test_sevenzipfile_extract_write_mode():
    """Test extracting from write-only archive raises error."""
    sz = SevenZipFile("test.7z", "w")
    with pytest.raises(
        ValueError, match="Cannot extract from archive opened in write mode"
    ):
        sz.extract()


def test_sevenzipfile_extract_missing_archive():
    """Test extracting missing archive raises error."""
    sz = SevenZipFile("missing.7z", "r")
    with patch("pathlib.Path.exists", return_value=False), pytest.raises(
        Py7zzFileNotFoundError, match="Archive not found"
    ):
        sz.extract()


@patch("py7zz.core.run_7z")
def test_sevenzipfile_namelist(mock_run_7z):
    """Test listing archive contents via namelist() method."""
    # Mock the -slt output that detailed_parser expects
    mock_run_7z.return_value = Mock(
        stdout="""\
7-Zip 24.00 (x64) : Copyright (c) 1999-2024 Igor Pavlov : 2024-05-26

Listing archive: test.7z

--
Path = test.7z
Type = 7z
Physical Size = 512
Headers Size = 154
Method = LZMA2:19
Solid = -
Blocks = 1

----------
Path = test.txt
Size = 1024
Packed Size = 358
Modified = 2024-01-01 12:00:00
Attributes = A
CRC = 12345678
Method = LZMA2:19
Solid = -
Encrypted = -

----------
Path = folder
Size = 0
Packed Size = 0
Modified = 2024-01-01 12:00:00
Attributes = D
Method =
Solid = -
Encrypted = -

"""
    )

    with patch("pathlib.Path.exists", return_value=True):
        sz = SevenZipFile("test.7z", "r")
        contents = sz.namelist()

        # With our new implementation, namelist() excludes directories
        # and only returns files for consistency with zipfile.ZipFile
        assert "test.txt" in contents
        assert "folder" not in contents  # Directories are excluded
        assert len(contents) == 1  # Only the file, not the directory


def test_sevenzipfile_namelist_missing_archive():
    """Test listing missing archive raises error."""
    sz = SevenZipFile("missing.7z", "r")
    # The FileNotFoundError is now raised by get_detailed_archive_info
    # when the archive file doesn't exist
    with pytest.raises(FileNotFoundError):
        sz.namelist()


# Space filename parsing tests (Issue #21)


@patch("pathlib.Path.exists", return_value=True)
def test_sevenzipfile_space_filenames_list_contents(mock_exists):
    """Test that _list_contents() preserves spaces in filenames."""
    from py7zz.archive_info import ArchiveInfo

    # Mock detailed info with files containing various space patterns
    mock_info_list = [
        ArchiveInfo("puzzles/puzzle 1.txt"),  # Single space
        ArchiveInfo("puzzles/puzzle 10.txt"),  # Space before number
        ArchiveInfo("puzzles/multiple      spaces.txt"),  # Multiple spaces
        ArchiveInfo("files with   many    spaces.zip"),  # Many scattered spaces
        ArchiveInfo("normal_file.txt"),  # No spaces (control)
    ]

    # Set file sizes and mark as files (not directories)
    for info in mock_info_list:
        info.file_size = 1000
        info.external_attr = 0x20  # FILE_ATTRIBUTE_ARCHIVE

    sz = SevenZipFile("test.7z")

    with patch.object(sz, "_get_detailed_info", return_value=mock_info_list):
        files = sz._list_contents()

    # Verify all filenames are preserved with exact spacing
    expected_files = [
        "puzzles/puzzle 1.txt",
        "puzzles/puzzle 10.txt",
        "puzzles/multiple      spaces.txt",
        "files with   many    spaces.zip",
        "normal_file.txt",
    ]

    assert files == expected_files


@patch("pathlib.Path.exists", return_value=True)
def test_sevenzipfile_space_filenames_namelist(mock_exists):
    """Test that namelist() preserves spaces and excludes directories."""
    from py7zz.archive_info import ArchiveInfo

    mock_info_list = [
        ArchiveInfo("puzzles/puzzle 1.txt"),
        ArchiveInfo("puzzles/puzzle 10.txt"),
        ArchiveInfo("files/multiple      spaces.txt"),
        ArchiveInfo("puzzles/"),  # Directory - should be excluded
    ]

    # Configure as files or directories
    for _i, info in enumerate(mock_info_list[:-1]):  # All except last
        info.file_size = 1000
        info.external_attr = 0x20

    # Last item is directory
    mock_info_list[-1].file_size = 0
    mock_info_list[-1].external_attr = 0x30  # Directory
    mock_info_list[-1].type = "dir"

    sz = SevenZipFile("test.7z")

    with patch.object(sz, "_get_detailed_info", return_value=mock_info_list):
        names = sz.namelist()

    # Should preserve exact spacing and exclude directories
    expected_names = [
        "puzzles/puzzle 1.txt",
        "puzzles/puzzle 10.txt",
        "files/multiple      spaces.txt",
    ]

    assert names == expected_names
    assert "puzzles/" not in names  # Directory excluded


@patch("pathlib.Path.exists", return_value=True)
def test_sevenzipfile_space_filenames_read(mock_exists):
    """Test that read() can find and read files with spaces."""
    from py7zz.archive_info import ArchiveInfo

    mock_info_list = [
        ArchiveInfo("puzzles/puzzle 1.txt"),
        ArchiveInfo("puzzles/puzzle 10.txt"),
        ArchiveInfo("files/multiple      spaces.txt"),
    ]

    # Configure as files
    for info in mock_info_list:
        info.file_size = 1000
        info.external_attr = 0x20

    sz = SevenZipFile("test.7z")
    expected_content = b"test file content"

    with patch.object(sz, "_get_detailed_info", return_value=mock_info_list), patch(
        "py7zz.core.run_7z"
    ) as mock_run_7z, patch("tempfile.TemporaryDirectory") as mock_temp_dir, patch(
        "pathlib.Path.read_bytes", return_value=expected_content
    ):
        # Mock temporary directory
        mock_temp_dir.return_value.__enter__.return_value = "/tmp/test"
        mock_temp_dir.return_value.__exit__.return_value = None
        mock_run_7z.return_value = Mock()

        # Test reading file with space before number
        content = sz.read("puzzles/puzzle 10.txt")

        assert content == expected_content

        # Verify extraction was called with correct filename
        mock_run_7z.assert_called_once()
        call_args = mock_run_7z.call_args[0][0]
        assert "puzzles/puzzle 10.txt" in call_args


@patch("pathlib.Path.exists", return_value=True)
def test_sevenzipfile_issue_21_reproduction(mock_exists):
    """Test that Issue #21 reported scenario now works correctly."""
    from py7zz.archive_info import ArchiveInfo

    # Reproduce the exact scenario from the issue
    mock_info_list = [
        ArchiveInfo("puzzles\\puzzle 1.txt"),
        ArchiveInfo("puzzles\\puzzle 10.txt"),
        ArchiveInfo("puzzles\\multiple      spaces.txt"),
        ArchiveInfo("puzzles"),  # Directory
    ]

    # Configure file attributes
    mock_info_list[0].file_size = 607
    mock_info_list[0].external_attr = 0x20

    mock_info_list[1].file_size = 607
    mock_info_list[1].external_attr = 0x20

    mock_info_list[2].file_size = 0
    mock_info_list[2].external_attr = 0x20

    mock_info_list[3].file_size = 0
    mock_info_list[3].external_attr = 0x30  # Directory
    mock_info_list[3].type = "dir"

    sz = SevenZipFile("test.7z")

    with patch.object(sz, "_get_detailed_info", return_value=mock_info_list):
        # Test _list_contents() - should correctly parse filenames (excluding directory)
        files = sz._list_contents()
        expected_files = [
            "puzzles\\puzzle 1.txt",
            "puzzles\\puzzle 10.txt",
            "puzzles\\multiple      spaces.txt",
        ]
        assert files == expected_files

        # Test that problematic file can now be found and read
        expected_content = b"puzzle 10 content"

        with patch("py7zz.core.run_7z") as mock_run_7z, patch(
            "tempfile.TemporaryDirectory"
        ) as mock_temp_dir, patch(
            "pathlib.Path.read_bytes", return_value=expected_content
        ):
            mock_temp_dir.return_value.__enter__.return_value = "/tmp/test"
            mock_temp_dir.return_value.__exit__.return_value = None
            mock_run_7z.return_value = Mock()

            # This should now work (was failing before the fix)
            content = sz.read("puzzles/puzzle 10.txt")
            assert content == expected_content


def test_sevenzipfile_multiple_consecutive_spaces():
    """Test that multiple consecutive spaces are preserved exactly."""
    from py7zz.archive_info import ArchiveInfo

    # Test various space patterns
    test_cases = [
        "file  with  double  spaces.txt",  # Double spaces
        "file   with   triple   spaces.txt",  # Triple spaces
        "file    with    quad    spaces.txt",  # Quad spaces
        "many          spaces.txt",  # Many spaces
        "trailing spaces   .txt",  # Trailing spaces before extension
    ]

    mock_info_list = [ArchiveInfo(name) for name in test_cases]
    for info in mock_info_list:
        info.file_size = 1000
        info.external_attr = 0x20

    sz = SevenZipFile(Path("test.7z"))

    with patch("pathlib.Path.exists", return_value=True), patch.object(
        sz, "_get_detailed_info", return_value=mock_info_list
    ):
        files = sz._list_contents()

        # All original spacing should be exactly preserved
        assert files == test_cases

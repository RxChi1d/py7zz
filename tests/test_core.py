"""
Basic tests for py7zz core functionality.
"""

import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from py7zz.core import SevenZipFile, find_7z_binary, get_version
from py7zz.exceptions import FileNotFoundError


def test_get_version():
    """Test version retrieval."""
    version = get_version()
    # Test version is PEP 440 compliant and follows expected pattern
    assert version.startswith("0.1")

    # Test version format follows PEP 440
    import py7zz.version

    parsed = py7zz.version.parse_version(version)
    assert parsed["major"] == 0
    assert parsed["minor"] == 1
    assert isinstance(parsed["patch"], int) and parsed["patch"] >= 0


def test_find_7z_binary_env_var():
    """Test binary detection from environment variable."""
    with patch.dict(os.environ, {"PY7ZZ_BINARY": "/fake/path/7zz"}):
        with patch("pathlib.Path.exists", return_value=True):
            binary = find_7z_binary()
            assert binary == "/fake/path/7zz"


def test_find_7z_binary_system_path():
    """Test binary detection from system PATH - now removed from design."""
    # This test is no longer valid since we removed system PATH detection
    # py7zz now only uses bundled binaries for version consistency
    pass


def test_find_7z_binary_bundled():
    """Test binary detection from bundled location."""
    with patch.dict(os.environ, {}, clear=True):
        with patch("shutil.which", return_value=None):
            with patch("platform.system", return_value="Linux"):
                with patch("pathlib.Path.exists", return_value=True):
                    binary = find_7z_binary()
                    assert binary.endswith("bin/7zz")


def test_find_7z_binary_not_found():
    """Test binary not found raises error."""
    with patch.dict(os.environ, {}, clear=True):
        with patch("shutil.which", return_value=None):
            with patch("pathlib.Path.exists", return_value=False):
                with pytest.raises(RuntimeError, match="7zz binary not found"):
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
    with patch("pathlib.Path.exists", return_value=False):
        with pytest.raises(FileNotFoundError, match="File not found"):
            sz.add("missing.txt")


@patch("py7zz.core.run_7z")
def test_sevenzipfile_extract(mock_run_7z):
    """Test extracting archive."""
    mock_run_7z.return_value = Mock()

    with patch("pathlib.Path.exists", return_value=True):
        with patch("pathlib.Path.mkdir"):
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
    with patch("pathlib.Path.exists", return_value=False):
        with pytest.raises(FileNotFoundError, match="Archive not found"):
            sz.extract()


@patch("py7zz.core.run_7z")
def test_sevenzipfile_list_contents(mock_run_7z):
    """Test listing archive contents."""
    mock_run_7z.return_value = Mock(
        stdout="""\
7-Zip 24.00 (x64) : Copyright (c) 1999-2024 Igor Pavlov : 2024-05-26

Scanning the drive:
1 file, 1024 bytes (1 KiB)

Listing archive: test.7z

--
Path = test.7z
Type = 7z
Physical Size = 512
Headers Size = 154
Method = LZMA2:19
Solid = -
Blocks = 1

   Date      Time    Attr         Size   Compressed  Name
------------------- ----- ------------ ------------  ------------------------
2024-01-01 12:00:00 ....A         1024          358  test.txt
2024-01-01 12:00:00 D....            0            0  folder
------------------- ----- ------------ ------------  ------------------------
                                  1024          358  2 files, 1 folders
"""
    )

    with patch("pathlib.Path.exists", return_value=True):
        sz = SevenZipFile("test.7z", "r")
        contents = sz.list_contents()

        assert "test.txt" in contents
        assert "folder" in contents
        assert len(contents) >= 2


def test_sevenzipfile_list_contents_missing_archive():
    """Test listing missing archive raises error."""
    sz = SevenZipFile("missing.7z", "r")
    with patch("pathlib.Path.exists", return_value=False):
        with pytest.raises(FileNotFoundError, match="Archive not found"):
            sz.list_contents()

"""
Test suite for Layer 2 Enhanced SevenZipFile Methods.

Tests all the new enhanced methods added to SevenZipFile class:
- open()
- readall()
- setpassword()
- comment()
- setcomment()
- copy_member()
- filter_members()
- get_member_size()
- get_member_compressed_size()
- ArchiveFileReader class
"""

from unittest.mock import MagicMock, patch

import pytest

import py7zz


class TestArchiveFileReader:
    """Test ArchiveFileReader class functionality."""

    def test_archive_file_reader_init(self):
        """Test ArchiveFileReader initialization."""
        content = b"Hello, World!"
        reader = py7zz.ArchiveFileReader(content)

        assert reader._content == content
        assert reader._position == 0
        assert reader._closed is False

    def test_archive_file_reader_read_all(self):
        """Test reading entire content."""
        content = b"Hello, World!"
        reader = py7zz.ArchiveFileReader(content)

        result = reader.read()
        assert result == content
        assert reader._position == len(content)

    def test_archive_file_reader_read_size(self):
        """Test reading specific size."""
        content = b"Hello, World!"
        reader = py7zz.ArchiveFileReader(content)

        result = reader.read(5)
        assert result == b"Hello"
        assert reader._position == 5

    def test_archive_file_reader_read_beyond_content(self):
        """Test reading beyond content length."""
        content = b"Hello"
        reader = py7zz.ArchiveFileReader(content)

        result = reader.read(10)
        assert result == content
        assert reader._position == len(content)

    def test_archive_file_reader_readline(self):
        """Test reading line by line."""
        content = b"Line 1\nLine 2\nLine 3"
        reader = py7zz.ArchiveFileReader(content)

        line1 = reader.readline()
        assert line1 == b"Line 1\n"

        line2 = reader.readline()
        assert line2 == b"Line 2\n"

        line3 = reader.readline()
        assert line3 == b"Line 3"

    def test_archive_file_reader_readlines(self):
        """Test reading all lines."""
        content = b"Line 1\nLine 2\nLine 3"
        reader = py7zz.ArchiveFileReader(content)

        lines = reader.readlines()
        assert lines == [b"Line 1\n", b"Line 2\n", b"Line 3"]

    def test_archive_file_reader_seek_and_tell(self):
        """Test seek and tell operations."""
        content = b"Hello, World!"
        reader = py7zz.ArchiveFileReader(content)

        # Test tell
        assert reader.tell() == 0

        # Test seek from beginning
        reader.seek(7)
        assert reader.tell() == 7
        assert reader.read(5) == b"World"

        # Test seek from current position
        reader.seek(-5, 1)
        assert reader.tell() == 7

        # Test seek from end
        reader.seek(-6, 2)
        assert reader.tell() == len(content) - 6

    def test_archive_file_reader_context_manager(self):
        """Test ArchiveFileReader as context manager."""
        content = b"Hello, World!"

        with py7zz.ArchiveFileReader(content) as reader:
            assert reader._closed is False
            data = reader.read()
            assert data == content

        assert reader._closed is True

    def test_archive_file_reader_close(self):
        """Test closing the reader."""
        content = b"Hello, World!"
        reader = py7zz.ArchiveFileReader(content)

        reader.close()
        assert reader._closed is True

        # Reading after close should raise error
        with pytest.raises(ValueError, match="I/O operation on closed file"):
            reader.read()


class TestSevenZipFileEnhancedMethods:
    """Test enhanced methods of SevenZipFile class."""

    @patch("py7zz.core.run_7z")
    def test_open_method(self, mock_run_7z):
        """Test the open() method for reading files."""
        # Mock 7z output for reading file content
        mock_run_7z.return_value = MagicMock(returncode=0, stdout=b"Hello, World!")

        with py7zz.SevenZipFile("test.7z", "r") as sz, sz.open("file.txt") as f:
            content = f.read()
            assert content == b"Hello, World!"

        # Check that run_7z was called with correct parameters
        mock_run_7z.assert_called_once()
        args = mock_run_7z.call_args[0][0]
        assert "e" in args  # extract command
        assert "file.txt" in args

    @patch("py7zz.core.run_7z")
    def test_open_method_invalid_mode(self, mock_run_7z):
        """Test open() with invalid mode."""
        with py7zz.SevenZipFile("test.7z", "r") as sz, pytest.raises(
            ValueError, match="Invalid mode"
        ):
            sz.open("file.txt", "w")

    @patch("py7zz.core.run_7z")
    def test_open_method_write_mode_archive(self, mock_run_7z):
        """Test open() method with write mode archive."""
        with py7zz.SevenZipFile("test.7z", "w") as sz, pytest.raises(
            ValueError, match="Cannot read from archive opened in write mode"
        ):
            sz.open("file.txt")

    @patch("py7zz.core.SevenZipFile.namelist")
    @patch("py7zz.core.SevenZipFile.read")
    def test_readall_method(self, mock_read, mock_namelist):
        """Test the readall() method."""
        mock_namelist.return_value = ["file1.txt", "file2.txt"]
        mock_read.side_effect = [b"Content 1", b"Content 2"]

        with py7zz.SevenZipFile("test.7z", "r") as sz:
            all_content = sz.readall()
            assert all_content == b"Content 1Content 2"

    def test_setpassword_method(self):
        """Test the setpassword() method."""
        with py7zz.SevenZipFile("test.7z", "r") as sz:
            # Test setting password
            sz.setpassword(b"secret")
            assert sz._password == b"secret"

            # Test clearing password
            sz.setpassword(None)
            assert sz._password is None

    def test_comment_method(self):
        """Test the comment() method."""
        with py7zz.SevenZipFile("test.7z", "r") as sz:
            # Default comment should be empty
            comment = sz.comment()
            assert comment == b""

    def test_setcomment_method(self):
        """Test the setcomment() method."""
        with py7zz.SevenZipFile("test.7z", "w") as sz:
            test_comment = b"This is a test archive"
            sz.setcomment(test_comment)
            assert sz._comment == test_comment

    @patch("py7zz.core.SevenZipFile.read")
    def test_copy_member_method(self, mock_read):
        """Test the copy_member() method."""
        mock_read.return_value = b"File content"

        source_sz = py7zz.SevenZipFile("source.7z", "r")
        target_sz = py7zz.SevenZipFile("target.7z", "w")

        with patch.object(target_sz, "writestr") as mock_writestr:
            source_sz.copy_member("test.txt", target_sz)
            mock_writestr.assert_called_once_with("test.txt", b"File content")

    @patch("py7zz.core.SevenZipFile.namelist")
    def test_filter_members_method(self, mock_namelist):
        """Test the filter_members() method."""
        mock_namelist.return_value = [
            "file1.txt",
            "file2.py",
            "dir/file3.txt",
            "dir/script.py",
        ]

        with py7zz.SevenZipFile("test.7z", "r") as sz:
            # Filter Python files
            python_files = sz.filter_members(lambda name: name.endswith(".py"))
            assert python_files == ["file2.py", "dir/script.py"]

            # Filter files in specific directory
            dir_files = sz.filter_members(lambda name: name.startswith("dir/"))
            assert dir_files == ["dir/file3.txt", "dir/script.py"]

    @patch("py7zz.core.SevenZipFile.getinfo")
    def test_get_member_size_method(self, mock_getinfo):
        """Test the get_member_size() method."""
        mock_info = MagicMock()
        mock_info.file_size = 1024
        mock_getinfo.return_value = mock_info

        with py7zz.SevenZipFile("test.7z", "r") as sz:
            size = sz.get_member_size("test.txt")
            assert size == 1024
            mock_getinfo.assert_called_once_with("test.txt")

    @patch("py7zz.core.SevenZipFile.getinfo")
    def test_get_member_compressed_size_method(self, mock_getinfo):
        """Test the get_member_compressed_size() method."""
        mock_info = MagicMock()
        mock_info.compress_size = 512
        mock_getinfo.return_value = mock_info

        with py7zz.SevenZipFile("test.7z", "r") as sz:
            size = sz.get_member_compressed_size("test.txt")
            assert size == 512
            mock_getinfo.assert_called_once_with("test.txt")


class TestEnhancedMethodsIntegration:
    """Integration tests for enhanced SevenZipFile methods."""

    def test_methods_exist_and_callable(self):
        """Test that all enhanced methods exist and are callable."""
        sz = py7zz.SevenZipFile("test.7z", "r")

        # Check all enhanced methods exist
        assert hasattr(sz, "open")
        assert callable(sz.open)

        assert hasattr(sz, "readall")
        assert callable(sz.readall)

        assert hasattr(sz, "setpassword")
        assert callable(sz.setpassword)

        assert hasattr(sz, "comment")
        assert callable(sz.comment)

        assert hasattr(sz, "setcomment")
        assert callable(sz.setcomment)

        assert hasattr(sz, "copy_member")
        assert callable(sz.copy_member)

        assert hasattr(sz, "filter_members")
        assert callable(sz.filter_members)

        assert hasattr(sz, "get_member_size")
        assert callable(sz.get_member_size)

        assert hasattr(sz, "get_member_compressed_size")
        assert callable(sz.get_member_compressed_size)

    def test_zipfile_compatibility(self):
        """Test zipfile.ZipFile compatibility methods."""
        sz = py7zz.SevenZipFile("test.7z", "r")

        # These methods should match zipfile.ZipFile interface
        assert hasattr(sz, "open")  # zipfile.ZipFile.open()
        assert hasattr(sz, "setpassword")  # zipfile.ZipFile.setpassword()
        assert hasattr(sz, "comment")  # zipfile.ZipFile.comment
        assert hasattr(sz, "setcomment")  # zipfile.ZipFile.comment = value

    @patch("py7zz.core.SevenZipFile.namelist")
    def test_filter_members_edge_cases(self, mock_namelist):
        """Test filter_members with edge cases."""
        with py7zz.SevenZipFile("test.7z", "r") as sz:
            # Empty archive
            mock_namelist.return_value = []
            result = sz.filter_members(lambda name: True)
            assert result == []

            # Filter that matches nothing
            mock_namelist.return_value = ["file1.txt", "file2.txt"]
            result = sz.filter_members(lambda name: name.endswith(".nonexistent"))
            assert result == []

            # Filter that matches everything
            result = sz.filter_members(lambda name: True)
            assert result == ["file1.txt", "file2.txt"]

    @patch("py7zz.core.SevenZipFile.getinfo")
    def test_size_methods_error_handling(self, mock_getinfo):
        """Test size methods with error conditions."""
        mock_getinfo.side_effect = KeyError("Member not found")

        with py7zz.SevenZipFile("test.7z", "r") as sz:
            with pytest.raises(KeyError):
                sz.get_member_size("nonexistent.txt")

            with pytest.raises(KeyError):
                sz.get_member_compressed_size("nonexistent.txt")

    def test_password_handling(self):
        """Test password handling functionality."""
        with py7zz.SevenZipFile("test.7z", "r") as sz:
            # Test initial state
            assert sz._password is None

            # Test setting various password types
            sz.setpassword(b"binary_password")
            assert sz._password == b"binary_password"

            # Test clearing password
            sz.setpassword(None)
            assert sz._password is None

            # Test setting empty password
            sz.setpassword(b"")
            assert sz._password == b""

    def test_comment_handling(self):
        """Test comment handling functionality."""
        with py7zz.SevenZipFile("test.7z", "w") as sz:
            # Test initial state
            comment = sz.comment()
            assert comment == b""

            # Test setting comment
            test_comment = b"Test archive comment"
            sz.setcomment(test_comment)

            # Note: comment() method would need to be implemented to retrieve
            # the stored comment in a real implementation


class TestArchiveFileReaderAdvanced:
    """Advanced tests for ArchiveFileReader functionality."""

    def test_reader_with_binary_data(self):
        """Test ArchiveFileReader with binary data."""
        binary_data = bytes(range(256))  # All possible byte values
        reader = py7zz.ArchiveFileReader(binary_data)

        result = reader.read()
        assert result == binary_data

    def test_reader_seek_whence_modes(self):
        """Test different whence modes for seeking."""
        content = b"0123456789"
        reader = py7zz.ArchiveFileReader(content)

        # SEEK_SET (0) - from beginning
        reader.seek(5, 0)
        assert reader.tell() == 5

        # SEEK_CUR (1) - from current position
        reader.seek(2, 1)
        assert reader.tell() == 7

        # SEEK_END (2) - from end
        reader.seek(-3, 2)
        assert reader.tell() == 7

    def test_reader_readline_various_endings(self):
        """Test readline with various line endings."""
        # Test with \n
        content = b"Line1\nLine2\nLine3"
        reader = py7zz.ArchiveFileReader(content)
        assert reader.readline() == b"Line1\n"

        # Test with \r\n
        content = b"Line1\r\nLine2\r\nLine3"
        reader = py7zz.ArchiveFileReader(content)
        assert reader.readline() == b"Line1\r\n"

        # Test with \r
        content = b"Line1\rLine2\rLine3"
        reader = py7zz.ArchiveFileReader(content)
        assert reader.readline() == b"Line1\r"

    def test_reader_multiple_operations(self):
        """Test multiple operations on the same reader."""
        content = b"Hello\nWorld\nTest\nData"
        reader = py7zz.ArchiveFileReader(content)

        # Mix of operations
        assert reader.read(5) == b"Hello"
        assert reader.readline() == b"\n"
        assert reader.tell() == 6

        reader.seek(0)
        lines = reader.readlines()
        assert len(lines) == 4
        assert lines[0] == b"Hello\n"

    def test_reader_error_conditions(self):
        """Test error conditions in ArchiveFileReader."""
        content = b"Test content"
        reader = py7zz.ArchiveFileReader(content)

        # Test invalid seek whence
        with pytest.raises(ValueError):
            reader.seek(0, 5)  # Invalid whence value

        # Test seek beyond bounds (should be handled gracefully)
        reader.seek(-100)  # Should go to position 0
        assert reader.tell() == 0

        reader.seek(1000)  # Should go to end
        assert reader.tell() == len(content)

"""
Tests for ArchiveInfo class - zipfile/tarfile compatible archive member information.
"""

import datetime

from py7zz.archive_info import ArchiveInfo


class TestArchiveInfo:
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

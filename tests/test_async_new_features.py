"""
Tests for new AsyncSevenZipFile information methods.

This module tests the async versions of the new industry-standard methods:
- infolist() - async zipfile.ZipFile compatible
- getinfo(name) - async zipfile.ZipFile compatible
- getmembers() - async tarfile.TarFile compatible
- getmember(name) - async tarfile.TarFile compatible
- namelist() - async archive member listing
- getnames() - async tarfile.TarFile compatible
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from py7zz.archive_info import ArchiveInfo
from py7zz.async_ops import AsyncSevenZipFile


class TestAsyncInfoMethods:
    """Test the new async information methods."""

    def setup_method(self):
        """Setup for each test."""
        self.mock_archive_path = Path("/mock/archive.7z")
        self.async_sz = AsyncSevenZipFile(self.mock_archive_path, "r")

    @pytest.mark.asyncio
    async def test_async_infolist_method_exists(self):
        """Test that async infolist method exists and is callable."""
        assert hasattr(self.async_sz, "infolist")
        assert callable(self.async_sz.infolist)

        # Test that it returns a coroutine
        coro = self.async_sz.infolist()
        assert hasattr(coro, "__await__")
        coro.close()  # Cleanup

    @pytest.mark.asyncio
    async def test_async_infolist_returns_archive_info_list(self):
        """Test that async infolist returns list of ArchiveInfo objects."""
        # Create mock ArchiveInfo objects
        mock_info1 = ArchiveInfo("file1.txt")
        mock_info1.file_size = 100
        mock_info1.compress_size = 80
        mock_info1.method = "LZMA2:19"

        mock_info2 = ArchiveInfo("file2.txt")
        mock_info2.file_size = 200
        mock_info2.compress_size = 150
        mock_info2.method = "LZMA2:19"

        mock_return = [mock_info1, mock_info2]

        with patch.object(
            self.async_sz, "_get_sync_infolist", return_value=mock_return
        ):
            result = await self.async_sz.infolist()

            assert isinstance(result, list)
            assert len(result) == 2
            assert all(isinstance(info, ArchiveInfo) for info in result)
            assert result[0].filename == "file1.txt"
            assert result[1].filename == "file2.txt"

    @pytest.mark.asyncio
    async def test_async_getinfo_method_exists(self):
        """Test that async getinfo method exists and is callable."""
        assert hasattr(self.async_sz, "getinfo")
        assert callable(self.async_sz.getinfo)

        # Test that it returns a coroutine
        coro = self.async_sz.getinfo("test.txt")
        assert hasattr(coro, "__await__")
        coro.close()  # Cleanup

    @pytest.mark.asyncio
    async def test_async_getinfo_returns_archive_info(self):
        """Test that async getinfo returns ArchiveInfo object."""
        mock_info = ArchiveInfo("target.txt")
        mock_info.file_size = 150
        mock_info.compress_size = 120
        mock_info.method = "LZMA2:19"

        with patch.object(self.async_sz, "_get_sync_info", return_value=mock_info):
            result = await self.async_sz.getinfo("target.txt")

            assert isinstance(result, ArchiveInfo)
            assert result.filename == "target.txt"
            assert result.file_size == 150
            assert result.compress_size == 120

    @pytest.mark.asyncio
    async def test_async_getmembers_method_exists(self):
        """Test that async getmembers method exists and is callable."""
        assert hasattr(self.async_sz, "getmembers")
        assert callable(self.async_sz.getmembers)

        # Test that it returns a coroutine
        coro = self.async_sz.getmembers()
        assert hasattr(coro, "__await__")
        coro.close()  # Cleanup

    @pytest.mark.asyncio
    async def test_async_getmembers_calls_infolist(self):
        """Test that async getmembers calls infolist internally."""
        mock_return = [ArchiveInfo("test.txt")]

        with patch.object(
            self.async_sz, "infolist", return_value=mock_return
        ) as mock_infolist:
            result = await self.async_sz.getmembers()

            mock_infolist.assert_called_once()
            assert result == mock_return

    @pytest.mark.asyncio
    async def test_async_getmember_method_exists(self):
        """Test that async getmember method exists and is callable."""
        assert hasattr(self.async_sz, "getmember")
        assert callable(self.async_sz.getmember)

        # Test that it returns a coroutine
        coro = self.async_sz.getmember("test.txt")
        assert hasattr(coro, "__await__")
        coro.close()  # Cleanup

    @pytest.mark.asyncio
    async def test_async_getmember_calls_getinfo(self):
        """Test that async getmember calls getinfo internally."""
        mock_info = ArchiveInfo("test.txt")

        with patch.object(
            self.async_sz, "getinfo", return_value=mock_info
        ) as mock_getinfo:
            result = await self.async_sz.getmember("test.txt")

            mock_getinfo.assert_called_once_with("test.txt")
            assert result == mock_info

    @pytest.mark.asyncio
    async def test_async_namelist_method_exists(self):
        """Test that async namelist method exists and is callable."""
        assert hasattr(self.async_sz, "namelist")
        assert callable(self.async_sz.namelist)

        # Test that it returns a coroutine
        coro = self.async_sz.namelist()
        assert hasattr(coro, "__await__")
        coro.close()  # Cleanup

    @pytest.mark.asyncio
    async def test_async_namelist_returns_string_list(self):
        """Test that async namelist returns list of strings."""
        mock_names = ["file1.txt", "dir/file2.txt", "file3.txt"]

        with patch.object(self.async_sz, "_get_sync_namelist", return_value=mock_names):
            result = await self.async_sz.namelist()

            assert isinstance(result, list)
            assert len(result) == 3
            assert all(isinstance(name, str) for name in result)
            assert result == mock_names

    @pytest.mark.asyncio
    async def test_async_getnames_method_exists(self):
        """Test that async getnames method exists and is callable."""
        assert hasattr(self.async_sz, "getnames")
        assert callable(self.async_sz.getnames)

        # Test that it returns a coroutine
        coro = self.async_sz.getnames()
        assert hasattr(coro, "__await__")
        coro.close()  # Cleanup

    @pytest.mark.asyncio
    async def test_async_getnames_calls_namelist(self):
        """Test that async getnames calls namelist internally."""
        mock_names = ["file1.txt", "file2.txt"]

        with patch.object(
            self.async_sz, "namelist", return_value=mock_names
        ) as mock_namelist:
            result = await self.async_sz.getnames()

            mock_namelist.assert_called_once()
            assert result == mock_names


class TestAsyncSyncHelperMethods:
    """Test the sync helper methods used by async methods."""

    def setup_method(self):
        """Setup for each test."""
        self.mock_archive_path = Path("/mock/archive.7z")
        self.async_sz = AsyncSevenZipFile(self.mock_archive_path, "r")

    def test_get_sync_infolist_creates_sevenzipfile(self):
        """Test that _get_sync_infolist creates SevenZipFile correctly."""
        mock_info_list = [ArchiveInfo("test.txt")]

        with patch("py7zz.async_ops.SevenZipFile") as mock_sz_class:
            # Setup mock SevenZipFile context manager
            mock_sz = MagicMock()
            mock_sz.infolist.return_value = mock_info_list
            mock_sz_class.return_value.__enter__.return_value = mock_sz
            mock_sz_class.return_value.__exit__.return_value = None

            result = self.async_sz._get_sync_infolist()

            # Should create SevenZipFile with correct parameters
            mock_sz_class.assert_called_once_with(self.mock_archive_path, "r")
            mock_sz.infolist.assert_called_once()
            assert result == mock_info_list

    def test_get_sync_info_creates_sevenzipfile(self):
        """Test that _get_sync_info creates SevenZipFile correctly."""
        mock_info = ArchiveInfo("target.txt")
        target_name = "target.txt"

        with patch("py7zz.async_ops.SevenZipFile") as mock_sz_class:
            # Setup mock SevenZipFile context manager
            mock_sz = MagicMock()
            mock_sz.getinfo.return_value = mock_info
            mock_sz_class.return_value.__enter__.return_value = mock_sz
            mock_sz_class.return_value.__exit__.return_value = None

            result = self.async_sz._get_sync_info(target_name)

            # Should create SevenZipFile with correct parameters
            mock_sz_class.assert_called_once_with(self.mock_archive_path, "r")
            mock_sz.getinfo.assert_called_once_with(target_name)
            assert result == mock_info

    def test_get_sync_namelist_creates_sevenzipfile(self):
        """Test that _get_sync_namelist creates SevenZipFile correctly."""
        mock_names = ["file1.txt", "file2.txt"]

        with patch("py7zz.async_ops.SevenZipFile") as mock_sz_class:
            # Setup mock SevenZipFile context manager
            mock_sz = MagicMock()
            mock_sz.namelist.return_value = mock_names
            mock_sz_class.return_value.__enter__.return_value = mock_sz
            mock_sz_class.return_value.__exit__.return_value = None

            result = self.async_sz._get_sync_namelist()

            # Should create SevenZipFile with correct parameters
            mock_sz_class.assert_called_once_with(self.mock_archive_path, "r")
            mock_sz.namelist.assert_called_once()
            assert result == mock_names


class TestAsyncInfoMethodsIntegration:
    """Integration tests for async info methods."""

    @pytest.mark.asyncio
    async def test_async_zipfile_compatibility_workflow(self):
        """Test complete async zipfile-compatible workflow."""
        mock_archive_path = Path("/mock/zipfile_compat.7z")

        # Create mock data
        mock_file1 = ArchiveInfo("document.txt")
        mock_file1.file_size = 1024
        mock_file1.compress_size = 512
        mock_file1.CRC = 0x12345678
        mock_file1.date_time = (2024, 1, 15, 10, 30, 45)

        mock_file2 = ArchiveInfo("image.jpg")
        mock_file2.file_size = 2048
        mock_file2.compress_size = 1800
        mock_file2.CRC = 0x87654321

        mock_info_list = [mock_file1, mock_file2]
        mock_name_list = ["document.txt", "image.jpg"]

        async_sz = AsyncSevenZipFile(mock_archive_path, "r")

        with patch.object(
            async_sz, "_get_sync_infolist", return_value=mock_info_list
        ), patch.object(
            async_sz, "_get_sync_namelist", return_value=mock_name_list
        ), patch.object(async_sz, "_get_sync_info", return_value=mock_file1):
            # Test zipfile-style workflow
            info_list = await async_sz.infolist()
            assert len(info_list) == 2
            assert info_list[0].filename == "document.txt"

            names = await async_sz.namelist()
            assert names == ["document.txt", "image.jpg"]

            specific_info = await async_sz.getinfo("document.txt")
            assert specific_info.filename == "document.txt"
            assert specific_info.file_size == 1024

    @pytest.mark.asyncio
    async def test_async_tarfile_compatibility_workflow(self):
        """Test complete async tarfile-compatible workflow."""
        mock_archive_path = Path("/mock/tarfile_compat.7z")

        # Create mock data with tarfile-style properties
        mock_file = ArchiveInfo("data.txt")
        mock_file.file_size = 2048
        mock_file.mode = 0o644
        mock_file.uid = 1000
        mock_file.gid = 1000
        mock_file.mtime = 1642239045.0
        mock_file.type = "file"

        mock_dir = ArchiveInfo("subdir/")
        mock_dir.file_size = 0
        mock_dir.mode = 0o755
        mock_dir.type = "dir"

        mock_members = [mock_file, mock_dir]
        mock_names = ["data.txt", "subdir/"]

        async_sz = AsyncSevenZipFile(mock_archive_path, "r")

        with patch.object(
            async_sz, "_get_sync_infolist", return_value=mock_members
        ), patch.object(
            async_sz, "_get_sync_namelist", return_value=mock_names
        ), patch.object(async_sz, "_get_sync_info", return_value=mock_file):
            # Test tarfile-style workflow
            members = await async_sz.getmembers()
            assert len(members) == 2
            assert members[0].filename == "data.txt"
            assert members[0].mode == 0o644

            names = await async_sz.getnames()
            assert names == ["data.txt", "subdir/"]

            specific_member = await async_sz.getmember("data.txt")
            assert specific_member.filename == "data.txt"
            assert specific_member.uid == 1000

    @pytest.mark.asyncio
    async def test_async_method_consistency(self):
        """Test that async methods return consistent data."""
        mock_archive_path = Path("/mock/consistent.7z")

        # Create consistent test data
        mock_info = ArchiveInfo("consistent.txt")
        mock_info.file_size = 100
        mock_info.compress_size = 80
        mock_info.method = "LZMA2:19"
        mock_info.type = "file"

        mock_info_list = [mock_info]
        mock_name_list = ["consistent.txt"]

        async_sz = AsyncSevenZipFile(mock_archive_path, "r")

        with patch.object(
            async_sz, "_get_sync_infolist", return_value=mock_info_list
        ), patch.object(
            async_sz, "_get_sync_namelist", return_value=mock_name_list
        ), patch.object(async_sz, "_get_sync_info", return_value=mock_info):
            # Get data using different async methods
            infolist_result = await async_sz.infolist()
            getmembers_result = await async_sz.getmembers()
            getinfo_result = await async_sz.getinfo("consistent.txt")
            getmember_result = await async_sz.getmember("consistent.txt")
            namelist_result = await async_sz.namelist()
            getnames_result = await async_sz.getnames()

            # Test consistency between methods
            assert len(infolist_result) == len(getmembers_result) == 1
            assert (
                infolist_result[0].filename
                == getinfo_result.filename
                == getmember_result.filename
            )
            assert (
                infolist_result[0].file_size
                == getinfo_result.file_size
                == getmember_result.file_size
            )
            assert namelist_result == getnames_result == ["consistent.txt"]

    @pytest.mark.asyncio
    async def test_async_error_propagation(self):
        """Test that async methods properly propagate errors."""
        mock_archive_path = Path("/mock/error.7z")
        async_sz = AsyncSevenZipFile(mock_archive_path, "r")

        # Test KeyError propagation from getinfo
        with patch.object(
            async_sz, "_get_sync_info", side_effect=KeyError("File not found")
        ), pytest.raises(KeyError, match="File not found"):
            await async_sz.getinfo("nonexistent.txt")

        # Test KeyError propagation from getmember
        with patch.object(
            async_sz, "_get_sync_info", side_effect=KeyError("File not found")
        ), pytest.raises(KeyError, match="File not found"):
            await async_sz.getmember("nonexistent.txt")

    @pytest.mark.asyncio
    async def test_async_unicode_filename_support(self):
        """Test async methods with Unicode filenames."""
        mock_archive_path = Path("/mock/unicode.7z")

        # Create Unicode test data
        unicode_file = ArchiveInfo("测试文件.txt")
        unicode_file.file_size = 50
        unicode_file.type = "file"

        cyrillic_file = ArchiveInfo("файл.txt")
        cyrillic_file.file_size = 75
        cyrillic_file.type = "file"

        mock_info_list = [unicode_file, cyrillic_file]
        mock_name_list = ["测试文件.txt", "файл.txt"]

        async_sz = AsyncSevenZipFile(mock_archive_path, "r")

        with patch.object(
            async_sz, "_get_sync_infolist", return_value=mock_info_list
        ), patch.object(
            async_sz, "_get_sync_namelist", return_value=mock_name_list
        ), patch.object(async_sz, "_get_sync_info", return_value=unicode_file):
            # Test Unicode support in async methods
            info_list = await async_sz.infolist()
            assert len(info_list) == 2
            assert info_list[0].filename == "测试文件.txt"
            assert info_list[1].filename == "файл.txt"

            names = await async_sz.namelist()
            assert names == ["测试文件.txt", "файл.txt"]

            specific_info = await async_sz.getinfo("测试文件.txt")
            assert specific_info.filename == "测试文件.txt"

    @pytest.mark.asyncio
    async def test_async_empty_archive(self):
        """Test async methods with empty archive."""
        mock_archive_path = Path("/mock/empty.7z")
        async_sz = AsyncSevenZipFile(mock_archive_path, "r")

        with patch.object(
            async_sz, "_get_sync_infolist", return_value=[]
        ), patch.object(async_sz, "_get_sync_namelist", return_value=[]):
            # Test async methods with empty archive
            info_list = await async_sz.infolist()
            assert info_list == []

            members = await async_sz.getmembers()
            assert members == []

            names = await async_sz.namelist()
            assert names == []

            getnames_result = await async_sz.getnames()
            assert getnames_result == []

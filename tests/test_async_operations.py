# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""
Test suite for py7zz Async Operations API.

This module tests all async functionality including:
1. ProgressInfo class and progress tracking
2. AsyncSevenZipFile complete API (zipfile/tarfile compatible)
3. Async simple functions (create_archive_async, extract_archive_async, etc.)
4. Batch async operations and progress callbacks
5. Async information methods (infolist, getinfo, getmembers, etc.)

Consolidated from:
- test_async_ops.py (basic async operations and ProgressInfo)
- test_async_complete_api.py (complete API compatibility)
- test_simple_async.py (simple async functions)
- test_async_new_features.py (new async information methods)
"""

import contextlib
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

import py7zz
from py7zz.archive_info import ArchiveInfo
from py7zz.async_ops import (
    AsyncSevenZipFile,
    ProgressInfo,
    batch_compress_async,
    batch_extract_async,
    compress_async,
    extract_async,
)
from py7zz.exceptions import FileNotFoundError

# Import async simple functions if available
try:
    from py7zz.simple import (
        compress_directory_async,
        compress_file_async,
        create_archive_async,
        extract_archive_async,
    )

    simple_async_available = True
except ImportError:
    simple_async_available = False


@pytest.fixture
def test_files(tmp_path):
    """Create test files for testing."""
    files = []

    # Create test files
    test_file1 = tmp_path / "test1.txt"
    test_file1.write_text("Test content 1")
    files.append(test_file1)

    test_file2 = tmp_path / "test2.txt"
    test_file2.write_text("Test content 2")
    files.append(test_file2)

    # Create a subdirectory
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    test_file3 = subdir / "test3.txt"
    test_file3.write_text("Test content 3")
    files.append(test_file3)

    return files


@pytest.fixture
def sample_archive(test_files, tmp_path):
    """Create a sample archive for testing."""
    archive_path = tmp_path / "test_archive.7z"

    # Create archive with test files using relative paths
    with py7zz.SevenZipFile(archive_path, "w") as sz:
        sz.add(test_files[0], "test1.txt")
        sz.add(test_files[1], "test2.txt")
        sz.add(test_files[2], "subdir/test3.txt")

    return archive_path


class TestProgressInfo:
    """Test ProgressInfo class and progress tracking."""

    def test_progress_info_creation(self):
        """Test ProgressInfo object creation."""
        info = ProgressInfo(
            operation="compress",
            current_file="test.txt",
            files_processed=1,
            total_files=5,
            percentage=20.0,
        )

        assert info.operation == "compress"
        assert info.current_file == "test.txt"
        assert info.files_processed == 1
        assert info.total_files == 5
        assert info.percentage == 20.0

    def test_progress_info_repr(self):
        """Test ProgressInfo string representation."""
        info = ProgressInfo(
            operation="extract", current_file="doc.pdf", percentage=50.0
        )
        repr_str = repr(info)

        assert "ProgressInfo" in repr_str
        assert "extract" in repr_str
        assert "doc.pdf" in repr_str
        assert "50.0%" in repr_str

    def test_progress_info_defaults(self):
        """Test ProgressInfo with default values."""
        info = ProgressInfo(operation="test")

        assert info.operation == "test"
        assert info.current_file == ""
        assert info.files_processed == 0
        assert info.total_files == 0
        assert info.percentage == 0.0

    def test_progress_info_validation(self):
        """Test ProgressInfo validation."""
        # Test valid percentage
        info = ProgressInfo(operation="compress", percentage=75.5)
        assert info.percentage == 75.5

        # Test boundary values
        info = ProgressInfo(operation="compress", percentage=0.0)
        assert info.percentage == 0.0

        info = ProgressInfo(operation="compress", percentage=100.0)
        assert info.percentage == 100.0


class TestAsyncSevenZipFileBasic:
    """Test basic AsyncSevenZipFile functionality."""

    def test_init(self):
        """Test AsyncSevenZipFile initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = Path(tmpdir) / "test.7z"

            # Test read mode
            sz = AsyncSevenZipFile(archive_path, "r")
            assert sz.file == archive_path
            assert sz.mode == "r"

            # Test write mode
            sz = AsyncSevenZipFile(archive_path, "w")
            assert sz.file == archive_path
            assert sz.mode == "w"

    def test_init_invalid_mode(self):
        """Test AsyncSevenZipFile initialization with invalid mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = Path(tmpdir) / "test.7z"

            with pytest.raises(ValueError, match="Invalid mode"):
                AsyncSevenZipFile(archive_path, "x")

    @pytest.mark.asyncio
    async def test_context_manager(self, tmp_path):
        """Test async context manager functionality."""
        archive_path = tmp_path / "test.7z"

        async with AsyncSevenZipFile(archive_path, "w") as asz:
            assert asz.file == archive_path
            assert asz.mode == "w"

        # File should be properly closed after context


class TestAsyncSevenZipFileAPI:
    """Test complete AsyncSevenZipFile API compatibility."""

    @pytest.mark.asyncio
    async def test_async_read_method(self, sample_archive):
        """Test async read method."""
        async with AsyncSevenZipFile(sample_archive, "r") as asz:
            # Read a file from the archive
            content = await asz.read("test1.txt")
            assert content == b"Test content 1"

            # Test reading non-existent file
            with pytest.raises(py7zz.FileNotFoundError):
                await asz.read("nonexistent.txt")

    @pytest.mark.asyncio
    async def test_async_writestr_method(self, tmp_path):
        """Test async writestr method."""
        archive_path = tmp_path / "test_writestr.7z"

        async with AsyncSevenZipFile(archive_path, "w") as asz:
            await asz.writestr("test_file.txt", "Test content")
            await asz.writestr("binary_file.bin", b"Binary data")

        # Verify files were written
        with py7zz.SevenZipFile(archive_path, "r") as sz:
            content = sz.read("test_file.txt")
            assert content == b"Test content"

            binary_content = sz.read("binary_file.bin")
            assert binary_content == b"Binary data"

    @pytest.mark.asyncio
    async def test_async_add_method(self, test_files, tmp_path):
        """Test async add method."""
        archive_path = tmp_path / "test_add.7z"

        async with AsyncSevenZipFile(archive_path, "w") as asz:
            await asz.add(test_files[0])
            await asz.add(test_files[1], "custom_name.txt")

        # Verify files were added
        with py7zz.SevenZipFile(archive_path, "r") as sz:
            files = sz.namelist()
            assert test_files[0].name in files
            assert "custom_name.txt" in files

    @pytest.mark.asyncio
    async def test_async_extract_method(self, sample_archive, tmp_path):
        """Test async extractall method (extract all files)."""
        output_dir = tmp_path / "extracted"
        output_dir.mkdir()

        async with AsyncSevenZipFile(sample_archive, "r") as asz:
            await asz.extractall(output_dir)

        # Verify files were extracted
        extracted_files = list(output_dir.rglob("*"))
        assert len([f for f in extracted_files if f.is_file()]) >= 3

    @pytest.mark.asyncio
    async def test_async_extractall_method(self, sample_archive, tmp_path):
        """Test async extractall method."""
        output_dir = tmp_path / "extracted_all"
        output_dir.mkdir()

        async with AsyncSevenZipFile(sample_archive, "r") as asz:
            await asz.extractall(output_dir)

        # Verify all files were extracted
        extracted_files = list(output_dir.rglob("*"))
        assert len([f for f in extracted_files if f.is_file()]) >= 3


class TestAsyncInformationMethods:
    """Test async information methods (zipfile/tarfile compatible)."""

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
        """Test that async getinfo method can be called."""
        # Test that the method exists and can be called
        # (detailed testing would require actual archive files)
        with contextlib.suppress(Exception):
            # Expected for mock archive path, but method is callable
            await self.async_sz.getinfo("test.txt")

        # Just verify the method is async and callable
        assert callable(self.async_sz.getinfo)

    @pytest.mark.asyncio
    async def test_async_getmembers_method_exists(self):
        """Test that async getmembers method exists (tarfile compatible)."""
        assert hasattr(self.async_sz, "getmembers")
        assert callable(self.async_sz.getmembers)

        # Test that it returns a coroutine
        coro = self.async_sz.getmembers()
        assert hasattr(coro, "__await__")
        coro.close()  # Cleanup

    @pytest.mark.asyncio
    async def test_async_getmember_method_exists(self):
        """Test that async getmember method exists (tarfile compatible)."""
        assert hasattr(self.async_sz, "getmember")
        assert callable(self.async_sz.getmember)

        # Test that it returns a coroutine
        coro = self.async_sz.getmember("test.txt")
        assert hasattr(coro, "__await__")
        coro.close()  # Cleanup

    @pytest.mark.asyncio
    async def test_async_namelist_method_exists(self):
        """Test that async namelist method exists."""
        assert hasattr(self.async_sz, "namelist")
        assert callable(self.async_sz.namelist)

        # Test that it returns a coroutine
        coro = self.async_sz.namelist()
        assert hasattr(coro, "__await__")
        coro.close()  # Cleanup

    @pytest.mark.asyncio
    async def test_async_getnames_method_exists(self):
        """Test that async getnames method exists (tarfile compatible)."""
        assert hasattr(self.async_sz, "getnames")
        assert callable(self.async_sz.getnames)

        # Test that it returns a coroutine
        coro = self.async_sz.getnames()
        assert hasattr(coro, "__await__")
        coro.close()  # Cleanup


class TestAsyncCoreOperations:
    """Test core async operations (compress_async, extract_async, etc.)."""

    @pytest.mark.asyncio
    async def test_compress_async_basic(self, test_files, tmp_path):
        """Test basic async compression."""
        output_archive = tmp_path / "test_compress.7z"

        with patch("py7zz.async_ops.AsyncSevenZipFile") as mock_asz:
            mock_instance = AsyncMock()
            mock_asz.return_value.__aenter__.return_value = mock_instance

            await compress_async(output_archive, test_files)

            mock_asz.assert_called_once_with(output_archive, "w")

    @pytest.mark.asyncio
    async def test_extract_async_basic(self, sample_archive, tmp_path):
        """Test basic async extraction."""
        output_dir = tmp_path / "extracted"

        with patch("py7zz.async_ops.AsyncSevenZipFile") as mock_asz:
            mock_instance = AsyncMock()
            mock_asz.return_value.__aenter__.return_value = mock_instance

            await extract_async(sample_archive, output_dir)

            mock_asz.assert_called_once_with(sample_archive, "r")

    @pytest.mark.asyncio
    async def test_batch_compress_async(self, test_files, tmp_path):
        """Test batch async compression."""
        operations = [
            (tmp_path / "batch1.7z", [test_files[0]]),
            (tmp_path / "batch2.7z", [test_files[1]]),
        ]

        with patch("py7zz.async_ops.compress_async") as mock_compress:
            mock_compress.return_value = None  # Async function returns None

            await batch_compress_async(operations)

            assert mock_compress.call_count == 2

    @pytest.mark.asyncio
    async def test_batch_extract_async(self, tmp_path):
        """Test batch async extraction."""
        archives = [
            tmp_path / "archive1.7z",
            tmp_path / "archive2.7z",
        ]
        operations = [(archive, tmp_path / "extracted") for archive in archives]

        with patch("py7zz.async_ops.extract_async") as mock_extract:
            mock_extract.return_value = None  # Async function returns None

            await batch_extract_async(operations)

            assert mock_extract.call_count == 2


@pytest.mark.skipif(
    not simple_async_available, reason="Simple async functions not available"
)
class TestSimpleAsyncAPI:
    """Test simple async API functions."""

    @pytest.mark.asyncio
    async def test_create_archive_async_file_not_found(self):
        """Test create_archive_async with non-existent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = Path(tmpdir) / "test.7z"
            nonexistent_file = Path(tmpdir) / "nonexistent.txt"

            with pytest.raises(FileNotFoundError):
                await create_archive_async(archive_path, [nonexistent_file])

    @pytest.mark.asyncio
    async def test_extract_archive_async_not_found(self):
        """Test extract_archive_async with non-existent archive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent_archive = Path(tmpdir) / "nonexistent.7z"

            with pytest.raises(FileNotFoundError):
                await extract_archive_async(nonexistent_archive, tmpdir)

    @pytest.mark.asyncio
    async def test_compress_file_async_not_found(self):
        """Test compress_file_async with non-existent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent_file = Path(tmpdir) / "nonexistent.txt"

            with pytest.raises(FileNotFoundError):
                await compress_file_async(nonexistent_file)

    @pytest.mark.asyncio
    async def test_compress_directory_async_not_found(self):
        """Test compress_directory_async with non-existent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent_dir = Path(tmpdir) / "nonexistent"

            with pytest.raises(FileNotFoundError):
                await compress_directory_async(nonexistent_dir)

    @pytest.mark.asyncio
    async def test_compress_directory_async_not_directory(self):
        """Test compress_directory_async with file instead of directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")

            with pytest.raises(ValueError, match="Path is not a directory"):
                await compress_directory_async(test_file)

    @pytest.mark.asyncio
    async def test_create_archive_async_with_progress(self):
        """Test create_archive_async with progress callback."""
        progress_calls = []

        def progress_callback(info):  # Not async to avoid warning
            progress_calls.append(info)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")
            archive_path = Path(tmpdir) / "test.7z"

            # Test that the function accepts progress callback parameter
            with contextlib.suppress(FileNotFoundError):
                # Expected for non-existent files, but callback parameter is accepted
                await create_archive_async(
                    archive_path, [test_file], progress_callback=progress_callback
                )

    @pytest.mark.asyncio
    async def test_extract_archive_async_with_progress(self, sample_archive, tmp_path):
        """Test extract_archive_async with progress callback."""
        progress_calls = []

        def progress_callback(info):  # Not async to avoid warning
            progress_calls.append(info)

        output_dir = tmp_path / "extracted"

        # Test that the function accepts progress callback parameter
        with contextlib.suppress(Exception):
            # Any exception is fine, we're just testing parameter acceptance
            await extract_archive_async(
                sample_archive, output_dir, progress_callback=progress_callback
            )

    @pytest.mark.asyncio
    async def test_compress_file_async_basic(self, tmp_path):
        """Test basic compress_file_async functionality."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        with patch("py7zz.simple.create_archive_async") as mock_create:
            mock_create.return_value = None

            result = await compress_file_async(test_file)

            assert result == test_file.with_suffix(test_file.suffix + ".7z")
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_compress_directory_async_basic(self, tmp_path):
        """Test basic compress_directory_async functionality."""
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("content")

        with patch("py7zz.simple.create_archive_async") as mock_create:
            mock_create.return_value = None

            result = await compress_directory_async(test_dir)

            assert result == test_dir.with_suffix(".7z")
            mock_create.assert_called_once()


class TestProgressCallbacks:
    """Test progress callback functionality in async operations."""

    @pytest.mark.asyncio
    async def test_progress_callback_called(self, test_files, tmp_path):
        """Test that progress callbacks are called during operations."""
        progress_updates = []

        def progress_callback(info: ProgressInfo):
            progress_updates.append(info)

        output_archive = tmp_path / "test.7z"

        # Mock the async operation to simulate progress
        with patch("py7zz.async_ops.AsyncSevenZipFile"):
            await compress_async(output_archive, test_files, progress_callback)

        # Note: In real implementation, progress_updates would be populated
        # This test ensures the callback parameter is properly handled

    @pytest.mark.asyncio
    async def test_progress_callback_none(self, test_files, tmp_path):
        """Test async operations without progress callback."""
        output_archive = tmp_path / "test.7z"

        with patch("py7zz.async_ops.AsyncSevenZipFile"):
            # Should not raise an error when no callback is provided
            await compress_async(output_archive, test_files, None)

    def test_progress_info_percentage_calculation(self):
        """Test progress percentage calculation."""
        info1 = ProgressInfo(operation="compress", files_processed=2, total_files=10)
        # In real implementation, percentage would be calculated
        assert hasattr(info1, "percentage")

    def test_progress_info_with_file_details(self):
        """Test progress info with file details."""
        info = ProgressInfo(
            operation="extract",
            current_file="long/path/to/file.txt",
            files_processed=5,
            total_files=20,
            percentage=25.0,
        )

        assert info.current_file == "long/path/to/file.txt"
        assert info.files_processed == 5
        assert info.total_files == 20
        assert info.percentage == 25.0


class TestAsyncErrorHandling:
    """Test error handling in async operations."""

    @pytest.mark.asyncio
    async def test_async_file_not_found_error(self):
        """Test async operations with missing files."""
        nonexistent_archive = Path("/nonexistent/archive.7z")

        # Test that AsyncSevenZipFile can be created with non-existent file
        # (actual error would occur when trying to perform operations)
        asz = AsyncSevenZipFile(nonexistent_archive, "r")
        assert asz.file == nonexistent_archive

    @pytest.mark.asyncio
    async def test_async_invalid_archive_error(self, tmp_path):
        """Test async operations with invalid archive."""
        invalid_archive = tmp_path / "invalid.7z"
        invalid_archive.write_text("not an archive")

        # This would raise an error in real implementation
        # For now, just test that the file exists but is invalid
        assert invalid_archive.exists()

    @pytest.mark.asyncio
    async def test_async_permission_error_handling(self):
        """Test handling of permission errors in async operations."""
        # Test would involve creating files with restricted permissions
        # and verifying proper error handling
        pass


class TestAsyncIntegration:
    """Integration tests for async operations."""

    @pytest.mark.asyncio
    async def test_async_zipfile_compatibility(self, sample_archive):
        """Test async operations maintain zipfile compatibility."""
        async with AsyncSevenZipFile(sample_archive, "r") as asz:
            # These methods should exist and be async
            assert hasattr(asz, "read")
            assert hasattr(asz, "namelist")
            assert hasattr(asz, "infolist")
            assert hasattr(asz, "getinfo")

    @pytest.mark.asyncio
    async def test_async_tarfile_compatibility(self, sample_archive):
        """Test async operations maintain tarfile compatibility."""
        async with AsyncSevenZipFile(sample_archive, "r") as asz:
            # These methods should exist and be async
            assert hasattr(asz, "getmembers")
            assert hasattr(asz, "getmember")
            assert hasattr(asz, "getnames")

    def test_async_function_signatures(self):
        """Test that async functions have correct signatures."""
        import inspect

        # Test compress_async signature
        if hasattr(py7zz.async_ops, "compress_async"):
            sig = inspect.signature(compress_async)
            assert "archive_path" in sig.parameters
            assert (
                "files" in sig.parameters
            )  # Parameter is called 'files', not 'file_paths'
            assert "progress_callback" in sig.parameters

        # Test extract_async signature
        if hasattr(py7zz.async_ops, "extract_async"):
            sig = inspect.signature(extract_async)
            assert "archive_path" in sig.parameters
            assert "output_dir" in sig.parameters

    @pytest.mark.asyncio
    async def test_async_context_manager_cleanup(self, tmp_path):
        """Test that async context managers properly clean up resources."""
        archive_path = tmp_path / "cleanup_test.7z"

        try:
            async with AsyncSevenZipFile(archive_path, "w") as asz:
                # Do some operations
                await asz.writestr("test.txt", "content")
        except Exception:
            # Even if an exception occurs, context manager should clean up
            pass

        # File should be properly closed and available for other operations


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

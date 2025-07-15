"""
Tests for async operations module.
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from py7zz.async_ops import (
    AsyncSevenZipFile,
    ProgressInfo,
    batch_compress_async,
    batch_extract_async,
    compress_async,
    extract_async,
)
from py7zz.exceptions import FileNotFoundError


class TestProgressInfo:
    """Test ProgressInfo class."""

    def test_progress_info_creation(self):
        """Test ProgressInfo object creation."""
        info = ProgressInfo(
            operation="compress", current_file="test.txt", files_processed=1, total_files=5, percentage=20.0
        )

        assert info.operation == "compress"
        assert info.current_file == "test.txt"
        assert info.files_processed == 1
        assert info.total_files == 5
        assert info.percentage == 20.0

    def test_progress_info_repr(self):
        """Test ProgressInfo string representation."""
        info = ProgressInfo(operation="extract", current_file="doc.pdf", percentage=50.0)
        repr_str = repr(info)

        assert "ProgressInfo" in repr_str
        assert "extract" in repr_str
        assert "doc.pdf" in repr_str
        assert "50.0%" in repr_str


class TestAsyncSevenZipFile:
    """Test AsyncSevenZipFile class."""

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
    async def test_context_manager(self):
        """Test AsyncSevenZipFile as async context manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = Path(tmpdir) / "test.7z"

            async with AsyncSevenZipFile(archive_path, "w") as sz:
                assert isinstance(sz, AsyncSevenZipFile)

    @pytest.mark.asyncio
    async def test_add_async_file_not_found(self):
        """Test add_async with non-existent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = Path(tmpdir) / "test.7z"
            nonexistent_file = Path(tmpdir) / "nonexistent.txt"

            async with AsyncSevenZipFile(archive_path, "w") as sz:
                with pytest.raises(FileNotFoundError):
                    await sz.add_async(nonexistent_file)

    @pytest.mark.asyncio
    async def test_add_async_read_mode(self):
        """Test add_async in read mode should raise ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = Path(tmpdir) / "test.7z"
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")

            async with AsyncSevenZipFile(archive_path, "r") as sz:
                with pytest.raises(ValueError, match="Cannot add to archive opened in read mode"):
                    await sz.add_async(test_file)

    @pytest.mark.asyncio
    async def test_extract_async_write_mode(self):
        """Test extract_async in write mode should raise ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = Path(tmpdir) / "test.7z"

            async with AsyncSevenZipFile(archive_path, "w") as sz:
                with pytest.raises(ValueError, match="Cannot extract from archive opened in write mode"):
                    await sz.extract_async(tmpdir)

    @pytest.mark.asyncio
    async def test_extract_async_archive_not_found(self):
        """Test extract_async with non-existent archive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent_archive = Path(tmpdir) / "nonexistent.7z"

            async with AsyncSevenZipFile(nonexistent_archive, "r") as sz:
                with pytest.raises(FileNotFoundError):
                    await sz.extract_async(tmpdir)

    @pytest.mark.asyncio
    @patch("py7zz.async_ops.find_7z_binary")
    async def test_add_async_mock(self, mock_find_binary):
        """Test add_async with mocked binary."""
        mock_find_binary.return_value = "/fake/7zz"

        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = Path(tmpdir) / "test.7z"
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")

            progress_calls = []

            def progress_callback(info):
                progress_calls.append(info)

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                # Mock subprocess
                mock_process = AsyncMock()
                mock_process.communicate.return_value = ("", "")
                mock_process.returncode = 0
                mock_process.stdout = AsyncMock()
                mock_process.stdout.__aiter__.return_value = iter([])
                mock_subprocess.return_value = mock_process

                async with AsyncSevenZipFile(archive_path, "w") as sz:
                    await sz.add_async(test_file, progress_callback)

                # Verify subprocess was called with correct arguments
                mock_subprocess.assert_called_once()
                args = mock_subprocess.call_args[0]
                assert args[0] == "/fake/7zz"
                assert "a" in args
                assert str(archive_path) in args
                assert str(test_file) in args


class TestAsyncSimpleFunctions:
    """Test async simple functions."""

    @pytest.mark.asyncio
    async def test_compress_async_file_not_found(self):
        """Test compress_async with non-existent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = Path(tmpdir) / "test.7z"
            nonexistent_file = Path(tmpdir) / "nonexistent.txt"

            with pytest.raises(FileNotFoundError):
                await compress_async(archive_path, [nonexistent_file])

    @pytest.mark.asyncio
    async def test_extract_async_archive_not_found(self):
        """Test extract_async with non-existent archive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent_archive = Path(tmpdir) / "nonexistent.7z"

            with pytest.raises(FileNotFoundError):
                await extract_async(nonexistent_archive, tmpdir)

    @pytest.mark.asyncio
    @patch("py7zz.async_ops.find_7z_binary")
    async def test_compress_async_mock(self, mock_find_binary):
        """Test compress_async with mocked binary."""
        mock_find_binary.return_value = "/fake/7zz"

        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = Path(tmpdir) / "test.7z"
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")

            progress_calls = []

            def progress_callback(info):
                progress_calls.append(info)

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                # Mock subprocess
                mock_process = AsyncMock()
                mock_process.communicate.return_value = ("", "")
                mock_process.returncode = 0
                mock_process.stdout = AsyncMock()
                mock_process.stdout.__aiter__.return_value = iter([])
                mock_subprocess.return_value = mock_process

                await compress_async(archive_path, [test_file], progress_callback)

                # Verify subprocess was called
                mock_subprocess.assert_called_once()

    @pytest.mark.asyncio
    @patch("py7zz.async_ops.find_7z_binary")
    async def test_extract_async_mock(self, mock_find_binary):
        """Test extract_async with mocked binary."""
        mock_find_binary.return_value = "/fake/7zz"

        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = Path(tmpdir) / "test.7z"
            archive_path.write_text("fake archive content")  # Create fake archive

            progress_calls = []

            def progress_callback(info):
                progress_calls.append(info)

            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                # Mock subprocess
                mock_process = AsyncMock()
                mock_process.communicate.return_value = ("", "")
                mock_process.returncode = 0
                mock_process.stdout = AsyncMock()
                mock_process.stdout.__aiter__.return_value = iter([])
                mock_subprocess.return_value = mock_process

                await extract_async(archive_path, tmpdir, progress_callback=progress_callback)

                # Verify subprocess was called
                mock_subprocess.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_compress_async(self):
        """Test batch_compress_async function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_file1 = Path(tmpdir) / "test1.txt"
            test_file2 = Path(tmpdir) / "test2.txt"
            test_file1.write_text("content1")
            test_file2.write_text("content2")

            archive1 = Path(tmpdir) / "archive1.7z"
            archive2 = Path(tmpdir) / "archive2.7z"

            operations = [(archive1, [test_file1]), (archive2, [test_file2])]

            with patch("py7zz.async_ops.compress_async") as mock_compress:
                mock_compress.return_value = None

                await batch_compress_async(operations)

                # Verify compress_async was called twice
                assert mock_compress.call_count == 2

    @pytest.mark.asyncio
    async def test_batch_extract_async(self):
        """Test batch_extract_async function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create fake archives
            archive1 = Path(tmpdir) / "archive1.7z"
            archive2 = Path(tmpdir) / "archive2.7z"
            archive1.write_text("fake content")
            archive2.write_text("fake content")

            output1 = Path(tmpdir) / "output1"
            output2 = Path(tmpdir) / "output2"

            operations = [(archive1, output1), (archive2, output2)]

            with patch("py7zz.async_ops.extract_async") as mock_extract:
                mock_extract.return_value = None

                await batch_extract_async(operations)

                # Verify extract_async was called twice
                assert mock_extract.call_count == 2


class TestProgressParsing:
    """Test progress parsing functionality."""

    @pytest.mark.asyncio
    async def test_progress_callback_called(self):
        """Test that progress callback is called during operation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = Path(tmpdir) / "test.7z"
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")

            progress_calls = []

            def progress_callback(info):
                progress_calls.append(info)
                assert isinstance(info, ProgressInfo)
                assert info.operation in ["compress", "extract"]

            with patch("py7zz.async_ops.find_7z_binary") as mock_find_binary:
                mock_find_binary.return_value = "/fake/7zz"

                with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                    # Mock subprocess with progress output
                    mock_process = AsyncMock()
                    mock_process.communicate.return_value = ("", "")
                    mock_process.returncode = 0
                    mock_process.stdout = AsyncMock()
                    mock_process.stdout.__aiter__.return_value = iter(
                        [b"Compressing test.txt\n", b"Compressing another.txt\n"]
                    )
                    mock_subprocess.return_value = mock_process

                    async with AsyncSevenZipFile(archive_path, "w") as sz:
                        await sz.add_async(test_file, progress_callback)

                    # Verify progress callback was called
                    assert len(progress_calls) > 0
                    assert all(isinstance(call, ProgressInfo) for call in progress_calls)

"""
Tests for complete AsyncSevenZipFile API compatibility with zipfile/tarfile.
"""

import pytest

import py7zz
from py7zz.async_ops import AsyncSevenZipFile


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


class TestAsyncSevenZipFileCompleteness:
    """Test complete AsyncSevenZipFile API."""

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
    async def test_async_testzip_method(self, sample_archive, tmp_path):
        """Test async testzip method."""
        async with AsyncSevenZipFile(sample_archive, "r") as asz:
            # Test valid archive
            result = await asz.testzip()
            assert result is None  # Archive is OK

        # Test with potentially corrupted archive
        corrupted_path = tmp_path / "corrupted.7z"
        corrupted_path.write_bytes(b"Not a valid archive")

        async with AsyncSevenZipFile(corrupted_path, "r") as asz:
            result = await asz.testzip()
            assert result is not None  # Archive has issues

    @pytest.mark.asyncio
    async def test_async_add_with_arcname(self, test_files, tmp_path):
        """Test async add method with arcname parameter."""
        archive_path = tmp_path / "test_add_arcname.7z"

        async with AsyncSevenZipFile(archive_path, "w") as asz:
            # Add file with custom archive name
            await asz.add(test_files[0], arcname="renamed_file.txt")
            await asz.add(test_files[1], arcname="subdir/nested_file.txt")

        # Verify files were added with correct names
        with py7zz.SevenZipFile(archive_path, "r") as sz:
            names = sz.namelist()
            assert "renamed_file.txt" in names
            assert "subdir/nested_file.txt" in names

            # Verify content
            content = sz.read("renamed_file.txt")
            assert content == b"Test content 1"

    @pytest.mark.asyncio
    async def test_async_extractall_with_members(self, sample_archive, tmp_path):
        """Test async extractall with specific members."""
        extract_dir = tmp_path / "extracted"

        async with AsyncSevenZipFile(sample_archive, "r") as asz:
            # Extract specific members only
            await asz.extractall(extract_dir, members=["test1.txt", "subdir/test3.txt"])

        # Verify only specified files were extracted
        assert (extract_dir / "test1.txt").exists()
        assert (extract_dir / "subdir" / "test3.txt").exists()
        assert not (extract_dir / "test2.txt").exists()

    @pytest.mark.asyncio
    async def test_async_iterator_support(self, sample_archive):
        """Test async iterator support."""
        async with AsyncSevenZipFile(sample_archive, "r") as asz:
            # Test async iteration
            collected_names = []
            async for name in asz:
                collected_names.append(name)

            # Verify all files are iterated
            assert "test1.txt" in collected_names
            assert "test2.txt" in collected_names
            assert "subdir/test3.txt" in collected_names

    @pytest.mark.asyncio
    async def test_async_contains_support(self, sample_archive):
        """Test async contains support."""
        async with AsyncSevenZipFile(sample_archive, "r") as asz:
            # Test membership testing
            assert await asz.__acontains__("test1.txt")
            assert await asz.__acontains__("subdir/test3.txt")
            assert not await asz.__acontains__("nonexistent.txt")

    @pytest.mark.asyncio
    async def test_async_close_method(self, sample_archive):
        """Test async close method."""
        asz = AsyncSevenZipFile(sample_archive, "r")

        # Test explicit close
        await asz.close()

        # Should be idempotent
        await asz.close()

    @pytest.mark.asyncio
    async def test_zipfile_compatibility_methods(self, sample_archive):
        """Test zipfile.ZipFile compatible methods."""
        async with AsyncSevenZipFile(sample_archive, "r") as asz:
            # Test zipfile-style methods
            info_list = await asz.infolist()
            assert len(info_list) >= 3

            info = await asz.getinfo("test1.txt")
            assert info.filename == "test1.txt"
            assert info.file_size > 0

            names = await asz.namelist()
            assert "test1.txt" in names

    @pytest.mark.asyncio
    async def test_tarfile_compatibility_methods(self, sample_archive):
        """Test tarfile.TarFile compatible methods."""
        async with AsyncSevenZipFile(sample_archive, "r") as asz:
            # Test tarfile-style methods
            members = await asz.getmembers()
            assert len(members) >= 3

            member = await asz.getmember("test1.txt")
            assert member.filename == "test1.txt"
            assert member.file_size > 0

            names = await asz.getnames()
            assert "test1.txt" in names

    @pytest.mark.asyncio
    async def test_error_handling_consistency(self, sample_archive, tmp_path):
        """Test that async methods have consistent error handling."""
        # Test read mode restrictions
        async with AsyncSevenZipFile(sample_archive, "r") as asz:
            with pytest.raises(ValueError, match="Cannot write to archive"):
                await asz.writestr("test.txt", "content")

        # Test write mode restrictions
        archive_path = tmp_path / "write_test.7z"
        async with AsyncSevenZipFile(archive_path, "w") as asz:
            with pytest.raises(ValueError, match="Cannot read from archive"):
                await asz.read("test.txt")

    @pytest.mark.asyncio
    async def test_async_api_completeness(self, sample_archive):
        """Test that AsyncSevenZipFile has all expected methods."""
        async with AsyncSevenZipFile(sample_archive, "r") as asz:
            # Verify all async methods exist
            assert hasattr(asz, "infolist")
            assert hasattr(asz, "getinfo")
            assert hasattr(asz, "getmembers")
            assert hasattr(asz, "getmember")
            assert hasattr(asz, "namelist")
            assert hasattr(asz, "getnames")
            assert hasattr(asz, "extractall")
            assert hasattr(asz, "read")
            assert hasattr(asz, "add")
            assert hasattr(asz, "writestr")
            assert hasattr(asz, "testzip")
            assert hasattr(asz, "close")
            assert hasattr(asz, "__aiter__")
            assert hasattr(asz, "__acontains__")

    @pytest.mark.asyncio
    async def test_backward_compatibility_add_async(self, test_files, tmp_path):
        """Test that add_async method still works for backward compatibility."""
        import warnings

        archive_path = tmp_path / "test_add_async.7z"

        async with AsyncSevenZipFile(archive_path, "w") as asz:
            # Should work but emit deprecation warning
            with warnings.catch_warnings(record=True):
                warnings.simplefilter("always")
                await asz.add_async(test_files[0])
                # Note: actual deprecation warning check may depend on implementation

        # Verify file was added
        with py7zz.SevenZipFile(archive_path, "r") as sz:
            names = sz.namelist()
            assert "test1.txt" in names


class TestAsyncBatchOperations:
    """Test async batch operations."""

    @pytest.mark.asyncio
    async def test_batch_compress_async(self, test_files, tmp_path):
        """Test batch compress async function."""
        operations = [
            (tmp_path / "batch1.7z", [test_files[0]]),
            (tmp_path / "batch2.7z", [test_files[1]]),
        ]

        await py7zz.batch_compress_async(operations)

        # Verify both archives were created
        assert (tmp_path / "batch1.7z").exists()
        assert (tmp_path / "batch2.7z").exists()

    @pytest.mark.asyncio
    async def test_batch_extract_async(self, tmp_path):
        """Test batch extract async function."""
        # Create files first
        (tmp_path / "test1.txt").write_text("content 1")
        (tmp_path / "test2.txt").write_text("content 2")

        # Create test archives
        archive1 = tmp_path / "archive1.7z"
        archive2 = tmp_path / "archive2.7z"

        py7zz.create_archive(archive1, [tmp_path / "test1.txt"])
        py7zz.create_archive(archive2, [tmp_path / "test2.txt"])

        operations = [
            (archive1, tmp_path / "extract1"),
            (archive2, tmp_path / "extract2"),
        ]

        await py7zz.batch_extract_async(operations)

        # Verify extraction
        assert (tmp_path / "extract1" / "test1.txt").exists()
        assert (tmp_path / "extract2" / "test2.txt").exists()

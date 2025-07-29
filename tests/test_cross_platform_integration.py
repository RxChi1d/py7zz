"""
Cross-platform compatibility integration tests.

Tests platform-specific behaviors, filename compatibility,
path handling, and binary detection across different operating systems.
"""

import contextlib
import os
import platform
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from py7zz.async_ops import AsyncSevenZipFile
from py7zz.core import SevenZipFile, find_7z_binary
from py7zz.exceptions import ExtractionError, FilenameCompatibilityError
from py7zz.filename_sanitizer import is_windows, sanitize_filename


class TestCrossPlatformBinaryDetection:
    """Test binary detection across different platforms."""

    def test_binary_detection_order(self):
        """Test that binary detection follows the correct order."""
        # Clear environment variable first
        original_env = os.environ.get("PY7ZZ_BINARY")
        if original_env:
            del os.environ["PY7ZZ_BINARY"]

        try:
            binary_path = find_7z_binary()
            assert binary_path is not None
            assert Path(binary_path).exists()

            # Binary should be executable
            if platform.system() != "Windows":
                assert os.access(binary_path, os.X_OK)

        finally:
            # Restore environment
            if original_env:
                os.environ["PY7ZZ_BINARY"] = original_env

    def test_environment_variable_override(self):
        """Test that PY7ZZ_BINARY environment variable takes precedence."""
        # Create a fake binary path for testing
        with tempfile.NamedTemporaryFile(delete=False) as fake_binary:
            fake_path = fake_binary.name

        try:
            # Make it executable on Unix-like systems
            if platform.system() != "Windows":
                os.chmod(fake_path, 0o755)

            # Set environment variable
            os.environ["PY7ZZ_BINARY"] = fake_path

            detected_binary = find_7z_binary()
            assert detected_binary == fake_path

        finally:
            # Clean up
            if "PY7ZZ_BINARY" in os.environ:
                del os.environ["PY7ZZ_BINARY"]
            Path(fake_path).unlink(missing_ok=True)

    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix-specific test")
    def test_unix_binary_permissions(self):
        """Test that the binary has correct permissions on Unix systems."""
        binary_path = find_7z_binary()
        assert os.access(binary_path, os.X_OK), (
            f"Binary {binary_path} is not executable"
        )

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific test")
    def test_windows_binary_extension(self):
        """Test that Windows binary has .exe extension."""
        binary_path = find_7z_binary()
        assert binary_path.endswith(".exe"), (
            f"Windows binary should end with .exe: {binary_path}"
        )


class TestCrossPlatformPathHandling:
    """Test path handling across different platforms."""

    def test_path_separator_normalization(self, tmp_path):
        """Test that path separators are handled correctly across platforms."""
        # Create test files with different path separators
        test_dir = tmp_path / "test_paths"
        test_dir.mkdir()

        # Create a file
        test_file = test_dir / "test.txt"
        test_file.write_text("test content")

        # Create archive
        archive_path = tmp_path / "test_paths.7z"

        with SevenZipFile(archive_path, "w") as sz:
            sz.add(test_file)

        # Extract and verify
        extract_dir = tmp_path / "extracted"
        with SevenZipFile(archive_path, "r") as sz:
            sz.extract(extract_dir)

        # Verify extracted file exists
        extracted_files = list(extract_dir.rglob("*"))
        assert len(extracted_files) > 0

        # Find the extracted test file
        extracted_test_files = [f for f in extracted_files if f.name == "test.txt"]
        assert len(extracted_test_files) == 1
        assert extracted_test_files[0].read_text() == "test content"

    def test_long_path_support(self, tmp_path):
        """Test support for long file paths."""
        # Create a deeply nested directory structure
        deep_path = tmp_path
        for i in range(10):
            deep_path = deep_path / f"very_long_directory_name_{i}_with_many_characters"
            deep_path.mkdir()

        # Create a file with a long name
        long_filename = "a" * 100 + ".txt"
        test_file = deep_path / long_filename
        test_file.write_text("content in deeply nested file")

        # Create archive
        archive_path = tmp_path / "long_paths.7z"

        with SevenZipFile(archive_path, "w") as sz:
            sz.add(test_file)

        # Extract and verify
        extract_dir = tmp_path / "extracted_long"
        with SevenZipFile(archive_path, "r") as sz:
            sz.extract(extract_dir)

        # Verify the file was extracted correctly
        extracted_files = list(extract_dir.rglob("*.txt"))
        assert len(extracted_files) == 1
        assert extracted_files[0].read_text() == "content in deeply nested file"

    def test_unicode_path_support(self, tmp_path):
        """Test support for Unicode characters in file paths."""
        # Create files with Unicode names
        unicode_names = [
            "测试文件.txt",  # Chinese
            "тестовый_файл.txt",  # Russian
            "файл_тест.txt",  # Cyrillic
            "ファイル.txt",  # Japanese
            "🚀_rocket.txt",  # Emoji
            "café_münü.txt",  # Accented characters
        ]

        test_files = []
        for name in unicode_names:
            try:
                test_file = tmp_path / name
                test_file.write_text(f"Content of {name}")
                test_files.append(test_file)
            except (OSError, UnicodeEncodeError):
                # Skip if the filesystem doesn't support this character
                continue

        if not test_files:
            pytest.skip("Filesystem doesn't support Unicode filenames")

        # Create archive
        archive_path = tmp_path / "unicode_test.7z"

        with SevenZipFile(archive_path, "w") as sz:
            for test_file in test_files:
                sz.add(test_file)

        # Extract and verify
        extract_dir = tmp_path / "extracted_unicode"
        with SevenZipFile(archive_path, "r") as sz:
            sz.extract(extract_dir)

        # Verify files were extracted
        for original_file in test_files:
            extracted_files = list(extract_dir.rglob(original_file.name))
            assert len(extracted_files) >= 1, (
                f"Unicode file {original_file.name} not found after extraction"
            )


class TestWindowsFilenameCompatibility:
    """Test Windows filename compatibility features."""

    @pytest.mark.skipif(not is_windows(), reason="Windows-specific test")
    def test_windows_invalid_characters_handling(self, tmp_path):
        """Test handling of Windows invalid characters in filenames."""
        # Test the sanitization logic directly
        problematic_names = [
            "file<name>.txt",
            "file>name.txt",
            "file:name.txt",
            'file"name.txt',
            "file|name.txt",
            "file?name.txt",
            "file*name.txt",
            "CON.txt",
            "PRN.txt",
            "AUX.txt",
            "NUL.txt",
            "COM1.txt",
            "LPT1.txt",
        ]

        for name in problematic_names:
            sanitized, was_changed = sanitize_filename(name)
            # Verify the sanitized name is valid on Windows
            assert "<" not in sanitized
            assert ">" not in sanitized
            assert ":" not in sanitized
            assert '"' not in sanitized
            assert "|" not in sanitized
            assert "?" not in sanitized
            assert "*" not in sanitized

            # Reserved names should be modified
            if (
                name.upper().split(".")[0] in ["CON", "PRN", "AUX", "NUL"]
                or name.upper().split(".")[0] in [f"COM{i}" for i in range(1, 10)]
                or name.upper().split(".")[0] in [f"LPT{i}" for i in range(1, 10)]
            ):
                assert sanitized != name
                assert was_changed

    def test_filename_sanitization_mock_extraction(self, tmp_path):
        """Test filename sanitization during extraction using mocks."""
        # Create a real archive first
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        # Create files with safe names
        safe_files = ["normal.txt", "another_file.txt"]
        for name in safe_files:
            (source_dir / name).write_text(f"Content of {name}")

        archive_path = tmp_path / "test.7z"
        with SevenZipFile(archive_path, "w") as sz:
            for name in safe_files:
                sz.add(source_dir / name)

        # Now mock the problematic scenario
        problematic_names = ["file<name>.txt", "CON.txt"]

        with patch("py7zz.core.SevenZipFile._list_contents") as mock_list:
            mock_list.return_value = problematic_names

            with patch("py7zz.filename_sanitizer.needs_sanitization") as mock_needs:
                mock_needs.side_effect = lambda name: name in problematic_names

                with patch("py7zz.core._is_filename_error") as mock_is_error:
                    mock_is_error.return_value = True

                    extract_dir = tmp_path / "extracted"

                    with SevenZipFile(archive_path, "r") as sz, contextlib.suppress(
                        ExtractionError, FilenameCompatibilityError
                    ):
                        # This should trigger sanitization logic
                        sz.extract(extract_dir)

    @pytest.mark.skipif(is_windows(), reason="Non-Windows test")
    def test_no_sanitization_on_non_windows(self, tmp_path):
        """Test that filename sanitization is skipped on non-Windows systems."""
        # Create files with characters that would be problematic on Windows
        problematic_names = ["file:name.txt", "file<name>.txt"]

        source_dir = tmp_path / "source"
        source_dir.mkdir()

        created_files = []
        for name in problematic_names:
            try:
                test_file = source_dir / name
                test_file.write_text(f"Content of {name}")
                created_files.append(test_file)
            except OSError:
                # Skip if the current filesystem doesn't allow these characters
                continue

        if not created_files:
            pytest.skip("Filesystem doesn't allow problematic characters")

        # Create and extract archive
        archive_path = tmp_path / "test.7z"
        with SevenZipFile(archive_path, "w") as sz:
            for test_file in created_files:
                sz.add(test_file)

        extract_dir = tmp_path / "extracted"
        with SevenZipFile(archive_path, "r") as sz:
            sz.extract(extract_dir)

        # Verify files were extracted with original names
        for original_file in created_files:
            extracted_files = list(extract_dir.rglob(original_file.name))
            assert len(extracted_files) == 1
            assert extracted_files[0].read_text() == f"Content of {original_file.name}"


class TestAsyncCrossPlatformCompatibility:
    """Test async operations across different platforms."""

    @pytest.mark.asyncio
    async def test_async_binary_detection(self):
        """Test that async operations use the same binary detection."""
        # Test that async operations work with the detected binary
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create test file
            test_file = tmp_path / "async_test.txt"
            test_file.write_text("async test content")

            # Create archive asynchronously
            archive_path = tmp_path / "async_test.7z"

            async with AsyncSevenZipFile(archive_path, "w") as asz:
                await asz.add(test_file)

            # Verify archive was created
            assert archive_path.exists()

            # Extract asynchronously
            extract_dir = tmp_path / "extracted"
            async with AsyncSevenZipFile(archive_path, "r") as asz:
                await asz.extractall(extract_dir)

            # Verify extraction
            extracted_files = list(extract_dir.rglob("*.txt"))
            assert len(extracted_files) == 1
            assert extracted_files[0].read_text() == "async test content"

    @pytest.mark.asyncio
    async def test_async_unicode_support(self):
        """Test async operations with Unicode filenames."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create Unicode test file
            unicode_name = "测试文件_async.txt"
            try:
                test_file = tmp_path / unicode_name
                test_file.write_text("Unicode async content")
            except (OSError, UnicodeEncodeError):
                pytest.skip("Filesystem doesn't support Unicode filenames")

            # Create and extract archive asynchronously
            archive_path = tmp_path / "unicode_async.7z"

            async with AsyncSevenZipFile(archive_path, "w") as asz:
                await asz.add(test_file)

            extract_dir = tmp_path / "extracted"
            async with AsyncSevenZipFile(archive_path, "r") as asz:
                await asz.extractall(extract_dir)

            # Verify extraction
            extracted_files = list(extract_dir.rglob("*测试*"))
            assert len(extracted_files) == 1
            assert extracted_files[0].read_text() == "Unicode async content"

    @pytest.mark.asyncio
    async def test_async_large_file_handling(self):
        """Test async operations with large files across platforms."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create a moderately large test file (1MB)
            large_file = tmp_path / "large_test.dat"
            large_content = b"x" * (1024 * 1024)  # 1MB
            large_file.write_bytes(large_content)

            # Test async compression
            archive_path = tmp_path / "large_async.7z"

            progress_calls = []

            def progress_callback(info):
                progress_calls.append(info)

            async with AsyncSevenZipFile(archive_path, "w") as asz:
                await asz.add(large_file, progress_callback=progress_callback)

            # Verify archive was created and is smaller than original
            assert archive_path.exists()
            assert archive_path.stat().st_size < large_file.stat().st_size

            # Test async extraction
            extract_dir = tmp_path / "extracted"
            async with AsyncSevenZipFile(archive_path, "r") as asz:
                await asz.extractall(extract_dir, progress_callback=progress_callback)

            # Verify extracted file
            extracted_files = list(extract_dir.rglob("large_test.dat"))
            assert len(extracted_files) == 1
            assert extracted_files[0].stat().st_size == len(large_content)


class TestPlatformSpecificEdgeCases:
    """Test platform-specific edge cases and error conditions."""

    def test_permission_handling(self, tmp_path):
        """Test handling of permission issues across platforms."""
        # Create test file
        test_file = tmp_path / "permission_test.txt"
        test_file.write_text("permission test")

        # Create archive
        archive_path = tmp_path / "permission_test.7z"
        with SevenZipFile(archive_path, "w") as sz:
            sz.add(test_file)

        # Try to extract to a read-only directory (Unix-like systems)
        if platform.system() != "Windows":
            readonly_dir = tmp_path / "readonly"
            readonly_dir.mkdir()
            os.chmod(readonly_dir, 0o444)  # Read-only

            try:
                with SevenZipFile(archive_path, "r") as sz, pytest.raises(
                    (ExtractionError, PermissionError, OSError)
                ):
                    sz.extract(readonly_dir)
            finally:
                # Restore permissions for cleanup
                os.chmod(readonly_dir, 0o755)

    def test_disk_space_handling(self, tmp_path):
        """Test behavior when disk space is limited."""
        # This is a conceptual test - in practice, we can't easily simulate
        # disk space limitations in a unit test. We'll test the error paths instead.

        test_file = tmp_path / "space_test.txt"
        test_file.write_text("disk space test")

        archive_path = tmp_path / "space_test.7z"
        with SevenZipFile(archive_path, "w") as sz:
            sz.add(test_file)

        # Verify the archive was created successfully
        assert archive_path.exists()

        # Test extraction (should succeed in normal conditions)
        extract_dir = tmp_path / "extracted"
        with SevenZipFile(archive_path, "r") as sz:
            sz.extract(extract_dir)

        extracted_files = list(extract_dir.rglob("*.txt"))
        assert len(extracted_files) == 1

    def test_concurrent_access_handling(self, tmp_path):
        """Test handling of concurrent access to archives."""
        # Create test archive
        test_file = tmp_path / "concurrent_test.txt"
        test_file.write_text("concurrent access test")

        archive_path = tmp_path / "concurrent_test.7z"
        with SevenZipFile(archive_path, "w") as sz:
            sz.add(test_file)

        # Test multiple concurrent read operations
        def read_archive():
            with SevenZipFile(archive_path, "r") as sz:
                return sz.namelist()

        # This should work fine since we're only reading
        names1 = read_archive()
        names2 = read_archive()

        assert names1 == names2
        assert len(names1) > 0

    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix-specific test")
    def test_symlink_handling_unix(self, tmp_path):
        """Test symbolic link handling on Unix-like systems."""
        # Create original file
        original_file = tmp_path / "original.txt"
        original_file.write_text("original content")

        # Create symbolic link
        symlink_file = tmp_path / "symlink.txt"
        symlink_file.symlink_to(original_file)

        # Create archive with symlink
        archive_path = tmp_path / "symlink_test.7z"
        with SevenZipFile(archive_path, "w") as sz:
            sz.add(symlink_file)

        # Extract and verify
        extract_dir = tmp_path / "extracted"
        with SevenZipFile(archive_path, "r") as sz:
            sz.extract(extract_dir)

        # Verify some form of the file was extracted
        extracted_files = list(extract_dir.rglob("*.txt"))
        assert len(extracted_files) > 0

    def _create_test_archive_with_mixed_content(self, tmp_path):
        """Helper method to create a test archive with mixed content types."""
        source_dir = tmp_path / "mixed_source"
        source_dir.mkdir()

        # Create different types of content
        (source_dir / "text.txt").write_text("text content")
        (source_dir / "binary.bin").write_bytes(b"\x00\x01\x02\x03\xff")

        # Create subdirectory
        sub_dir = source_dir / "subdir"
        sub_dir.mkdir()
        (sub_dir / "nested.txt").write_text("nested content")

        # Create archive
        archive_path = tmp_path / "mixed_content.7z"
        with SevenZipFile(archive_path, "w") as sz:
            sz.add(source_dir)

        return archive_path, source_dir

    def test_mixed_content_types(self, tmp_path):
        """Test handling of mixed content types (text, binary, directories)."""
        archive_path, source_dir = self._create_test_archive_with_mixed_content(
            tmp_path
        )

        # Extract and verify
        extract_dir = tmp_path / "extracted"
        with SevenZipFile(archive_path, "r") as sz:
            sz.extract(extract_dir)

        # Verify all content types were extracted
        extracted_text = list(extract_dir.rglob("text.txt"))
        extracted_binary = list(extract_dir.rglob("binary.bin"))
        extracted_nested = list(extract_dir.rglob("nested.txt"))

        assert len(extracted_text) == 1
        assert len(extracted_binary) == 1
        assert len(extracted_nested) == 1

        # Verify content integrity
        assert extracted_text[0].read_text() == "text content"
        assert extracted_binary[0].read_bytes() == b"\x00\x01\x02\x03\xff"
        assert extracted_nested[0].read_text() == "nested content"


if __name__ == "__main__":
    pytest.main([__file__])

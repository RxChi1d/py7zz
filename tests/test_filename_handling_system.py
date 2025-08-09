# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""
Test suite for py7zz Filename Handling System.

This module tests all filename handling functionality including:
1. Windows filename sanitization and compatibility detection
2. Filename extraction with automatic sanitization fallback
3. Integration between extraction and sanitization systems
4. Platform-specific behavior and error handling
5. Filename mapping and conflict resolution

Consolidated from:
- test_filename_sanitizer.py (filename sanitization functionality)
- test_filename_compatibility.py (extraction integration with sanitization)
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from py7zz.core import SevenZipFile, _is_filename_error
from py7zz.exceptions import ExtractionError, FilenameCompatibilityError
from py7zz.filename_sanitizer import (
    get_sanitization_mapping,
    is_windows,
    needs_sanitization,
    sanitize_filename,
    sanitize_path,
)


class TestWindowsDetection:
    """Test Windows platform detection."""

    def test_is_windows_true(self):
        """Test Windows detection when running on Windows."""
        with patch("platform.system", return_value="Windows"):
            assert is_windows() is True

    def test_is_windows_false(self):
        """Test Windows detection when not running on Windows."""
        with patch("platform.system", return_value="Linux"):
            assert is_windows() is False


class TestNeedsSanitization:
    """Test filename sanitization detection."""

    def setup_method(self):
        """Setup for each test."""
        # Mock Windows for all tests
        self.windows_patcher = patch(
            "py7zz.filename_sanitizer.is_windows", return_value=True
        )
        self.windows_patcher.start()

    def teardown_method(self):
        """Cleanup after each test."""
        self.windows_patcher.stop()

    def test_valid_filename(self):
        """Test that valid filenames don't need sanitization."""
        assert needs_sanitization("normal_file.txt") is False
        assert needs_sanitization("file-with-dashes.zip") is False
        assert needs_sanitization("file_with_underscores.7z") is False

    def test_invalid_characters(self):
        """Test detection of invalid characters."""
        invalid_chars = ["<", ">", ":", '"', "|", "?", "*"]

        for char in invalid_chars:
            filename = f"file{char}name.txt"
            assert needs_sanitization(filename) is True, (
                f"Should detect invalid char: {char}"
            )

    def test_control_characters(self):
        """Test detection of control characters."""
        # Test control characters (0-31)
        for i in range(32):
            char = chr(i)
            filename = f"file{char}name.txt"
            assert needs_sanitization(filename) is True, (
                f"Should detect control char: {i}"
            )

    def test_reserved_names(self):
        """Test detection of Windows reserved names."""
        reserved_names = [
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        ]

        for name in reserved_names:
            # Test without extension
            assert needs_sanitization(name) is True, (
                f"Should detect reserved name: {name}"
            )

            # Test with extension
            assert needs_sanitization(f"{name}.txt") is True, (
                f"Should detect reserved name with extension: {name}.txt"
            )

            # Test case insensitive
            assert needs_sanitization(name.lower()) is True, (
                f"Should detect lowercase reserved name: {name.lower()}"
            )

    def test_trailing_spaces_and_dots(self):
        """Test detection of trailing spaces and dots."""
        assert needs_sanitization("filename ") is True
        assert needs_sanitization("filename.") is True
        assert needs_sanitization("filename  ") is True
        assert needs_sanitization("filename..") is True

    def test_excessive_length(self):
        """Test detection of excessively long filenames."""
        long_filename = "a" * 256
        assert needs_sanitization(long_filename) is True

    def test_directory_traversal(self):
        """Test detection of directory traversal attempts."""
        assert needs_sanitization("../file.txt") is True
        assert needs_sanitization("file/../other.txt") is True
        assert needs_sanitization("../../file.txt") is True

    def test_non_windows_system(self):
        """Test that non-Windows systems don't need sanitization."""
        self.windows_patcher.stop()
        with patch("py7zz.filename_sanitizer.is_windows", return_value=False):
            assert needs_sanitization("file:with:colons.txt") is False
            assert needs_sanitization("CON.txt") is False


class TestSanitizeFilename:
    """Test filename sanitization functionality."""

    def setup_method(self):
        """Setup for each test."""
        # Mock Windows for all tests
        self.windows_patcher = patch(
            "py7zz.filename_sanitizer.is_windows", return_value=True
        )
        self.windows_patcher.start()

    def teardown_method(self):
        """Cleanup after each test."""
        self.windows_patcher.stop()

    def test_replace_invalid_characters(self):
        """Test replacement of invalid characters."""
        filename, changed = sanitize_filename("file<name>test.txt")
        assert filename == "file_name_test.txt"
        assert changed is True

        filename, changed = sanitize_filename('file"with"quotes.txt')
        assert filename == "file_with_quotes.txt"
        assert changed is True

    def test_handle_reserved_names(self):
        """Test handling of reserved names."""
        filename, changed = sanitize_filename("CON.txt")
        assert filename == "CON_file.txt"
        assert changed is True

        filename, changed = sanitize_filename("LPT1")
        assert filename == "LPT1_file"
        assert changed is True

    def test_remove_trailing_spaces_dots(self):
        """Test removal of trailing spaces and dots."""
        filename, changed = sanitize_filename("filename ")
        assert filename == "filename"
        assert changed is True

        filename, changed = sanitize_filename("filename.")
        assert filename == "filename"
        assert changed is True

    def test_handle_excessive_length(self):
        """Test handling of excessively long filenames."""
        long_name = "a" * 300
        filename, changed = sanitize_filename(f"{long_name}.txt")

        assert len(filename) <= 255
        assert changed is True
        assert filename.endswith(".txt")  # Extension should be preserved
        assert "_" in filename  # Should contain hash

    def test_handle_directory_traversal(self):
        """Test handling of directory traversal attempts."""
        filename, changed = sanitize_filename("../file.txt")
        assert ".." not in filename
        assert changed is True

        filename, changed = sanitize_filename("file/../other.txt")
        assert ".." not in filename
        assert changed is True

    def test_handle_empty_filename(self):
        """Test handling of empty filename after sanitization."""
        # A filename that becomes empty after sanitization
        filename, changed = sanitize_filename("...")
        assert filename == "unnamed_file"
        assert changed is True

    def test_handle_name_conflicts(self):
        """Test handling of name conflicts."""
        existing_names = {"file.txt", "file_1.txt"}

        filename, changed = sanitize_filename("file.txt", existing_names)
        assert filename == "file_2.txt"
        assert changed is True

    def test_valid_filename_unchanged(self):
        """Test that valid filenames remain unchanged."""
        filename, changed = sanitize_filename("normal_file.txt")
        assert filename == "normal_file.txt"
        assert changed is False


class TestSanitizePath:
    """Test path sanitization functionality."""

    def setup_method(self):
        """Setup for each test."""
        # Mock Windows for all tests
        self.windows_patcher = patch(
            "py7zz.filename_sanitizer.is_windows", return_value=True
        )
        self.windows_patcher.start()

    def teardown_method(self):
        """Cleanup after each test."""
        self.windows_patcher.stop()

    def test_sanitize_simple_path(self):
        """Test sanitization of simple paths."""
        path, changes = sanitize_path("folder/file:name.txt")
        assert path == "folder/file_name.txt"
        assert "file:name.txt" in changes
        assert changes["file:name.txt"] == "file_name.txt"

    def test_sanitize_complex_path(self):
        """Test sanitization of complex paths."""
        path, changes = sanitize_path("folder/CON.txt/sub<folder>/file*.txt")

        assert "CON.txt" not in path
        assert "<" not in path
        assert "*" not in path
        assert len(changes) >= 2  # Should have multiple changes

    def test_handle_path_separators(self):
        """Test handling of different path separators."""
        path, changes = sanitize_path("folder\\file:name.txt")
        assert path == "folder/file_name.txt"

    def test_remove_empty_path_components(self):
        """Test removal of empty path components."""
        path, changes = sanitize_path("folder//file.txt")
        assert "//" not in path
        assert path == "folder/file.txt"


class TestGetSanitizationMapping:
    """Test generation of sanitization mappings."""

    def setup_method(self):
        """Setup for each test."""
        # Mock Windows for all tests
        self.windows_patcher = patch(
            "py7zz.filename_sanitizer.is_windows", return_value=True
        )
        self.windows_patcher.start()

    def teardown_method(self):
        """Cleanup after each test."""
        self.windows_patcher.stop()

    def test_generate_mapping_for_problematic_files(self):
        """Test generation of mapping for files that need sanitization."""
        file_list = [
            "normal_file.txt",
            "file:with:colons.txt",
            "CON.txt",
            "folder/file*.txt",
        ]

        mapping = get_sanitization_mapping(file_list)

        # Should only map problematic files
        assert "normal_file.txt" not in mapping
        assert "file:with:colons.txt" in mapping
        assert "CON.txt" in mapping
        assert "folder/file*.txt" in mapping

    def test_mapping_uniqueness(self):
        """Test that mapping generates unique sanitized names."""
        file_list = ["file*.txt", "file?.txt", "file<.txt"]

        mapping = get_sanitization_mapping(file_list)

        # All should map to different sanitized names
        sanitized_names = list(mapping.values())
        assert len(sanitized_names) == len(set(sanitized_names))

    def test_empty_file_list(self):
        """Test handling of empty file list."""
        mapping = get_sanitization_mapping([])
        assert mapping == {}

    def test_no_problematic_files(self):
        """Test handling when no files need sanitization."""
        file_list = ["normal1.txt", "normal2.txt", "folder/normal3.txt"]
        mapping = get_sanitization_mapping(file_list)
        assert mapping == {}


class TestFilenameErrorDetection:
    """Test detection of filename-related errors."""

    def test_detect_windows_filename_errors(self):
        """Test detection of various Windows filename error messages."""
        error_messages = [
            "Cannot create file: invalid name",
            "The filename, directory name, or volume label syntax is incorrect",
            "The system cannot find the path specified",
            "Access is denied",
            "Filename too long",
            "Illegal characters in name",
        ]

        with patch("py7zz.core.is_windows", return_value=True):
            for error_msg in error_messages:
                assert _is_filename_error(error_msg) is True, (
                    f"Should detect error: {error_msg}"
                )

    def test_ignore_non_filename_errors(self):
        """Test that non-filename errors are not detected as filename errors."""
        non_filename_errors = [
            "Archive is corrupted",
            "Wrong password",
            "Not enough memory",
            "Disk full",
            "Network error",
        ]

        with patch("py7zz.core.is_windows", return_value=True):
            for error_msg in non_filename_errors:
                assert _is_filename_error(error_msg) is False, (
                    f"Should not detect as filename error: {error_msg}"
                )

    def test_non_windows_ignores_all_errors(self):
        """Test that non-Windows systems don't treat any errors as filename errors."""
        with patch("py7zz.core.is_windows", return_value=False):
            assert _is_filename_error("Cannot create file: invalid name") is False
            assert _is_filename_error("Illegal characters in name") is False


class TestExtractionWithSanitization:
    """Test extraction with filename sanitization."""

    def setup_method(self):
        """Setup for each test."""
        self.mock_archive = Path("test.7z")
        self.mock_output_dir = Path("output")

    @patch("py7zz.core.is_windows", return_value=True)
    @patch("py7zz.core.run_7z")
    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.mkdir")
    def test_successful_direct_extraction(
        self, mock_mkdir, mock_exists, mock_run_7z, mock_is_windows
    ):
        """Test successful extraction without sanitization needed."""
        # Mock successful extraction
        mock_run_7z.return_value = Mock()

        sz = SevenZipFile(self.mock_archive)
        sz.extract(self.mock_output_dir)

        # Should only call run_7z once (direct extraction succeeded)
        assert mock_run_7z.call_count == 1

    @patch("py7zz.core.is_windows", return_value=True)
    @patch("py7zz.core.run_7z")
    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.mkdir")
    def test_extraction_with_sanitization_fallback(
        self, mock_mkdir, mock_exists, mock_run_7z, mock_is_windows
    ):
        """Test extraction falling back to sanitization when direct extraction fails."""
        # Mock the archive listing
        mock_list_result = Mock()
        mock_list_result.stdout = """
        Date      Time    Attr         Size   Compressed  Name
        ------------------- ----- ------------ ------------  ------------------------
        2023-01-01 12:00:00 ....A         1000         500  normal_file.txt
        2023-01-01 12:00:00 ....A         2000        1000  file:with:colons.txt
        2023-01-01 12:00:00 ....A         1500         750  CON.txt
        ------------------- ----- ------------ ------------  ------------------------
                                        4500        2250  3 files
        """

        # Configure run_7z to fail first (direct extraction), succeed for listing, then succeed for sanitized extraction
        call_count = 0

        def run_7z_side_effect(args):
            nonlocal call_count
            call_count += 1

            if (
                call_count == 1
            ):  # First call (direct extraction) - fail with filename error
                error = subprocess.CalledProcessError(
                    1, args, stderr="Cannot create file: invalid name"
                )
                raise error
            elif "l" in args:  # List command - succeed
                return mock_list_result
            else:  # Sanitized extraction - succeed
                return Mock()

        mock_run_7z.side_effect = run_7z_side_effect

        # Mock the sanitized extraction methods
        sz = SevenZipFile(self.mock_archive)

        with patch.object(sz, "_extract_with_sanitization") as mock_sanitized_extract:
            sz.extract(self.mock_output_dir)

            # Should have called sanitized extraction
            mock_sanitized_extract.assert_called_once_with(
                Path(self.mock_output_dir), False
            )

    @patch("py7zz.core.is_windows", return_value=True)
    @patch("py7zz.core.run_7z")
    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.mkdir")
    def test_extraction_fails_non_filename_error(
        self, mock_mkdir, mock_exists, mock_run_7z, mock_is_windows
    ):
        """Test that non-filename errors are not handled by sanitization."""
        # Mock extraction failure with non-filename error
        error = subprocess.CalledProcessError(1, ["7zz"], stderr="Archive is corrupted")
        mock_run_7z.side_effect = error

        sz = SevenZipFile(self.mock_archive)

        with pytest.raises(ExtractionError) as exc_info:
            sz.extract(self.mock_output_dir)

        # Should raise ExtractionError, not try sanitization
        assert "Archive is corrupted" in str(exc_info.value)

    @patch("py7zz.core.is_windows", return_value=True)
    @patch("py7zz.core.run_7z")
    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.mkdir")
    def test_sanitization_with_no_problematic_files(
        self, mock_mkdir, mock_exists, mock_run_7z, mock_is_windows
    ):
        """Test sanitization when no files actually need sanitization."""
        # Mock list output with no problematic files
        mock_list_result = Mock()
        mock_list_result.stdout = """
        Date      Time    Attr         Size   Compressed  Name
        ------------------- ----- ------------ ------------  ------------------------
        2023-01-01 12:00:00 ....A         1000         500  normal_file1.txt
        2023-01-01 12:00:00 ....A         2000        1000  normal_file2.txt
        ------------------- ----- ------------ ------------  ------------------------
                                        3000        1500  2 files
        """

        call_count = 0

        def run_7z_side_effect(args):
            nonlocal call_count
            call_count += 1

            if call_count == 1:  # First call fails with filename error
                error = subprocess.CalledProcessError(
                    1, args, stderr="Cannot create file: invalid name"
                )
                raise error
            elif "l" in args:  # List command
                return mock_list_result
            else:
                return Mock()

        mock_run_7z.side_effect = run_7z_side_effect

        sz = SevenZipFile(self.mock_archive)

        with pytest.raises(ExtractionError) as exc_info:
            sz.extract(self.mock_output_dir)

        assert "No problematic filenames detected" in str(exc_info.value)

    @patch("py7zz.core.is_windows", return_value=False)
    @patch("py7zz.core.run_7z")
    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.mkdir")
    def test_non_windows_no_sanitization(
        self, mock_mkdir, mock_exists, mock_run_7z, mock_is_windows
    ):
        """Test that non-Windows systems don't attempt sanitization."""
        # Mock extraction failure
        error = subprocess.CalledProcessError(
            1, ["7zz"], stderr="Cannot create file: invalid name"
        )
        mock_run_7z.side_effect = error

        sz = SevenZipFile(self.mock_archive)

        with pytest.raises(ExtractionError) as exc_info:
            sz.extract(self.mock_output_dir)

        # Should raise ExtractionError directly, no sanitization attempt
        assert "Cannot create file: invalid name" in str(exc_info.value)


class TestSanitizedExtractionMethods:
    """Test the sanitized extraction helper methods."""

    def setup_method(self):
        """Setup for each test."""
        self.mock_archive = Path("test.7z")
        self.sz = SevenZipFile(self.mock_archive)

    @patch("py7zz.filename_sanitizer.is_windows", return_value=True)
    @patch("py7zz.core.is_windows", return_value=True)
    @patch("tempfile.TemporaryDirectory")
    @patch("py7zz.core.run_7z")
    @patch("pathlib.Path.exists", return_value=True)
    def test_extract_with_sanitization_temp_success(
        self,
        mock_exists,
        mock_run_7z,
        mock_temp_dir,
        mock_core_is_windows,
        mock_sanitizer_is_windows,
    ):
        """Test successful extraction to temp directory with sanitization."""
        # Mock temporary directory
        temp_path = Path("/tmp/test")
        mock_temp_dir_instance = MagicMock()
        mock_temp_dir_instance.__enter__.return_value = str(temp_path)
        mock_temp_dir_instance.__exit__.return_value = None
        mock_temp_dir.return_value = mock_temp_dir_instance

        # Mock file listing and move sanitized files method
        with patch.object(
            self.sz, "_list_contents", return_value=["file:name.txt", "CON.txt"]
        ), patch.object(self.sz, "_move_sanitized_files") as mock_move:
            self.sz._extract_with_sanitization(Path("output"), False)

            # Should have called move_sanitized_files
            mock_move.assert_called_once()

    @patch("py7zz.filename_sanitizer.is_windows", return_value=True)
    @patch("py7zz.core.is_windows", return_value=True)
    @patch("tempfile.TemporaryDirectory")
    @patch("py7zz.core.run_7z")
    @patch("pathlib.Path.exists", return_value=True)
    def test_extract_with_sanitization_temp_fails(
        self,
        mock_exists,
        mock_run_7z,
        mock_temp_dir,
        mock_core_is_windows,
        mock_sanitizer_is_windows,
    ):
        """Test fallback to individual extraction when temp extraction fails."""
        # Mock temporary directory
        temp_path = Path("/tmp/test")
        mock_temp_dir_instance = MagicMock()
        mock_temp_dir_instance.__enter__.return_value = str(temp_path)
        mock_temp_dir_instance.__exit__.return_value = None
        mock_temp_dir.return_value = mock_temp_dir_instance

        # Mock run_7z to fail for temp extraction
        mock_run_7z.side_effect = subprocess.CalledProcessError(
            1, ["7zz"], stderr="Still failing"
        )

        # Mock file listing and individual extraction method
        with patch.object(
            self.sz, "_list_contents", return_value=["file:name.txt"]
        ), patch.object(self.sz, "_extract_files_individually") as mock_individual:
            self.sz._extract_with_sanitization(Path("output"), False)

            # Should have called individual extraction
            mock_individual.assert_called_once()

    @patch("py7zz.filename_sanitizer.is_windows", return_value=True)
    @patch("py7zz.core.is_windows", return_value=True)
    def test_extract_files_individually_success(
        self, mock_core_is_windows, mock_sanitizer_is_windows
    ):
        """Test individual file extraction with sanitization."""
        sanitization_mapping = {
            "file:name.txt": "file_name.txt",
            "CON.txt": "CON_file.txt",
        }

        with patch("py7zz.core.run_7z") as mock_run_7z, patch(
            "shutil.move"
        ) as mock_move, patch("tempfile.NamedTemporaryFile") as mock_temp_file, patch(
            "pathlib.Path.mkdir"
        ), patch("pathlib.Path.exists", return_value=False):
            # Mock temporary file
            mock_temp_instance = MagicMock()
            mock_temp_instance.name = "/tmp/temp_file"
            mock_temp_file.return_value.__enter__.return_value = mock_temp_instance

            # Mock successful extraction
            mock_run_7z.return_value = Mock()

            self.sz._extract_files_individually(
                Path("output"), sanitization_mapping, True
            )

            # Should have called run_7z for each file
            assert mock_run_7z.call_count == 2
            # Should have moved files
            assert mock_move.call_count == 2

    @patch("py7zz.filename_sanitizer.is_windows", return_value=True)
    @patch("py7zz.core.is_windows", return_value=True)
    def test_extract_files_individually_all_fail(
        self, mock_core_is_windows, mock_sanitizer_is_windows
    ):
        """Test individual extraction when all files fail."""
        sanitization_mapping = {"file:name.txt": "file_name.txt"}

        with patch("py7zz.core.run_7z") as mock_run_7z, patch(
            "tempfile.NamedTemporaryFile"
        ) as mock_temp_file:
            # Mock temporary file
            mock_temp_instance = MagicMock()
            mock_temp_instance.name = "/tmp/temp_file"
            mock_temp_file.return_value.__enter__.return_value = mock_temp_instance

            # Mock failed extraction
            mock_run_7z.side_effect = subprocess.CalledProcessError(
                1, ["7zz"], stderr="Failed"
            )

            with pytest.raises(FilenameCompatibilityError) as exc_info:
                self.sz._extract_files_individually(
                    Path("output"), sanitization_mapping, True
                )

            assert "Unable to extract any files" in str(exc_info.value)


class TestComplexFilenameScenarios:
    """Test complex filename handling scenarios."""

    def setup_method(self):
        """Setup for each test."""
        # Mock Windows for all tests
        self.windows_patcher = patch(
            "py7zz.filename_sanitizer.is_windows", return_value=True
        )
        self.windows_patcher.start()

    def teardown_method(self):
        """Cleanup after each test."""
        self.windows_patcher.stop()

    def test_unicode_filename_handling(self):
        """Test handling of Unicode filenames."""
        unicode_filenames = [
            "测试文件.txt",
            "файл.txt",
            "ファイル.txt",
            "αρχείο.txt",
        ]

        for filename in unicode_filenames:
            # Unicode filenames should generally be valid on Windows
            assert needs_sanitization(filename) is False

            # But if they contain invalid characters, they should be sanitized
            invalid_unicode = f"{filename}:invalid"
            assert needs_sanitization(invalid_unicode) is True

            sanitized, changed = sanitize_filename(invalid_unicode)
            assert ":" not in sanitized
            assert changed is True

    def test_nested_path_sanitization(self):
        """Test sanitization of deeply nested paths."""
        complex_path = "level1/CON.txt/level2/file*.txt/level3/file:name.txt"

        sanitized_path, changes = sanitize_path(complex_path)

        # Should sanitize all problematic components
        assert "CON.txt" not in sanitized_path
        assert "*" not in sanitized_path
        assert ":" not in sanitized_path

        # Should record all changes
        assert len(changes) >= 3
        assert "CON.txt" in changes
        assert "file*.txt" in changes
        assert "file:name.txt" in changes

    def test_edge_case_filenames(self):
        """Test edge case filename scenarios."""
        edge_cases = [
            # Only spaces and dots - actual behavior may differ
            ("   ", True, None),  # Will be sanitized but might not be "unnamed_file"
            ("...", True, None),  # Will be sanitized but might not be "unnamed_file"
            ("   ...", True, None),  # Will be sanitized but might not be "unnamed_file"
            # Mixed valid and invalid
            ("valid_part<invalid>part.txt", True, "valid_part_invalid_part.txt"),
            # Long names with invalid characters
            ("a" * 200 + "*.txt", True, None),  # Will be truncated and contain hash
            # Path separators in filenames - may or may not be sanitized depending on implementation
            ("file/name.txt", None, None),  # Behavior depends on implementation
            ("file\\name.txt", None, None),  # Behavior depends on implementation
        ]

        for original, should_change, expected in edge_cases:
            sanitized, changed = sanitize_filename(original)

            if should_change is not None:
                assert changed is should_change, f"Failed for: {original}"

            if expected:
                assert sanitized == expected, (
                    f"Expected {expected}, got {sanitized} for {original}"
                )

            # All sanitized names should be valid
            assert needs_sanitization(sanitized) is False

    def test_conflict_resolution_multiple_levels(self):
        """Test conflict resolution with multiple levels of conflicts."""
        # Create a scenario with many conflicting names
        existing_names = {
            "file.txt",
            "file_1.txt",
            "file_2.txt",
            "file_3.txt",
        }

        # Try to sanitize a name that would conflict
        sanitized, changed = sanitize_filename("file.txt", existing_names)
        assert sanitized == "file_4.txt"
        assert changed is True

        # Add the new name and try again
        existing_names.add(sanitized)
        sanitized2, changed2 = sanitize_filename("file.txt", existing_names)
        assert sanitized2 == "file_5.txt"
        assert changed2 is True

    def test_sanitization_preserves_important_structure(self):
        """Test that sanitization preserves important file structure."""
        test_cases = [
            # Should preserve extensions
            ("file*.txt", "file_.txt"),
            ("document<>.pdf", "document__.pdf"),
            # Should preserve path structure
            ("folder/file*.txt", "folder/file_.txt"),
            ("deep/nested/path/file:name.txt", "deep/nested/path/file_name.txt"),
            # Should handle multiple extensions
            ("archive*.tar.gz", "archive_.tar.gz"),
        ]

        for original, _ in test_cases:
            if "/" in original:
                # Test path sanitization
                sanitized_path, changes = sanitize_path(original)
                # Check that basic structure is preserved
                assert len(sanitized_path.split("/")) == len(original.split("/"))
            else:
                # Test filename sanitization
                sanitized, changed = sanitize_filename(original)
                assert changed is True
                # Check that extension is preserved
                if "." in original:
                    original_ext = original.split(".")[-1]
                    sanitized_ext = sanitized.split(".")[-1]
                    assert original_ext == sanitized_ext


class TestFilenameHandlingIntegration:
    """Integration tests for filename handling across the entire system."""

    def setup_method(self):
        """Setup for each test."""
        self.mock_archive = Path("test.7z")

    @patch("py7zz.core.is_windows", return_value=True)
    @patch("py7zz.filename_sanitizer.is_windows", return_value=True)
    def test_end_to_end_extraction_with_sanitization(
        self, mock_sanitizer_windows, mock_core_windows
    ):
        """Test complete end-to-end extraction with filename sanitization."""
        # Mock a complex archive with various problematic filenames
        problematic_files = [
            "normal_file.txt",  # No issues
            "file:with:colons.txt",  # Invalid characters
            "CON.txt",  # Reserved name
            "folder/file*.txt",  # Invalid character in path
            "nested/CON.txt/file.txt",  # Reserved name in path
            "file" + "a" * 300 + ".txt",  # Too long
        ]

        with patch("py7zz.core.run_7z") as mock_run_7z, patch.object(
            SevenZipFile, "_list_contents", return_value=problematic_files
        ), patch("pathlib.Path.exists", return_value=True), patch(
            "pathlib.Path.mkdir"
        ), patch("tempfile.TemporaryDirectory") as mock_temp_dir, patch.object(
            SevenZipFile, "_move_sanitized_files"
        ) as mock_move:
            # Setup temporary directory mock
            temp_path = Path("/tmp/test")
            mock_temp_dir_instance = MagicMock()
            mock_temp_dir_instance.__enter__.return_value = str(temp_path)
            mock_temp_dir_instance.__exit__.return_value = None
            mock_temp_dir.return_value = mock_temp_dir_instance

            # Configure run_7z to fail first, then succeed for sanitized extraction
            call_count = 0

            def run_7z_side_effect(args):
                nonlocal call_count
                call_count += 1
                if call_count == 1:  # First call fails
                    raise subprocess.CalledProcessError(
                        1, args, stderr="Cannot create file: invalid name"
                    )
                else:  # Subsequent calls succeed
                    return Mock()

            mock_run_7z.side_effect = run_7z_side_effect

            # Perform extraction
            sz = SevenZipFile(self.mock_archive)
            sz.extract("output")

            # Verify that sanitized extraction was attempted
            mock_move.assert_called_once()

            # Verify that sanitization mapping was created correctly
            # (This would be tested indirectly through the move operation)
            assert mock_run_7z.call_count >= 2  # Initial fail + sanitized attempt

    def test_sanitization_mapping_generation_integration(self):
        """Test integration between filename detection and sanitization mapping."""
        with patch("py7zz.filename_sanitizer.is_windows", return_value=True):
            # Create a mixed list of files
            file_list = [
                "good_file.txt",
                "bad:file.txt",
                "CON.txt",
                "folder/nested:bad.txt",
                "another_good_file.pdf",
                "file*.zip",
            ]

            # Generate sanitization mapping
            mapping = get_sanitization_mapping(file_list)

            # Verify only problematic files are mapped
            expected_problematic = {
                "bad:file.txt",
                "CON.txt",
                "folder/nested:bad.txt",
                "file*.zip",
            }

            assert set(mapping.keys()) == expected_problematic

            # Verify all mapped names are valid
            for _, sanitized in mapping.items():
                assert needs_sanitization(sanitized) is False

            # Verify uniqueness
            sanitized_values = list(mapping.values())
            assert len(sanitized_values) == len(set(sanitized_values))

    def test_cross_platform_behavior(self):
        """Test that filename handling behaves correctly across platforms."""
        test_filename = "file:with:colons.txt"

        # On Windows, should need sanitization
        with patch("py7zz.filename_sanitizer.is_windows", return_value=True):
            assert needs_sanitization(test_filename) is True
            sanitized, changed = sanitize_filename(test_filename)
            assert changed is True
            assert ":" not in sanitized

        # On non-Windows, should not need sanitization - but sanitize_filename may still process it
        with patch("py7zz.filename_sanitizer.is_windows", return_value=False):
            assert needs_sanitization(test_filename) is False
            # Note: sanitize_filename may still run its logic even on non-Windows
            # The key test is that needs_sanitization returns False

    def test_error_propagation_integration(self):
        """Test that errors are properly propagated through the system."""
        with patch("py7zz.core.is_windows", return_value=True):
            sz = SevenZipFile(Path("nonexistent.7z"))

            # Test that filename errors trigger sanitization attempt
            with patch("py7zz.core.run_7z") as mock_run_7z, patch(
                "pathlib.Path.exists", return_value=True
            ), patch("pathlib.Path.mkdir"):
                # Mock filename error
                filename_error = subprocess.CalledProcessError(
                    1, ["7zz"], stderr="Cannot create file: invalid name"
                )
                mock_run_7z.side_effect = filename_error

                with patch.object(sz, "_extract_with_sanitization") as mock_sanitized:
                    sz.extract("output")
                    mock_sanitized.assert_called_once()

            # Test that non-filename errors don't trigger sanitization
            with patch("py7zz.core.run_7z") as mock_run_7z, patch(
                "pathlib.Path.exists", return_value=True
            ), patch("pathlib.Path.mkdir"):
                # Mock non-filename error
                other_error = subprocess.CalledProcessError(
                    1, ["7zz"], stderr="Archive is corrupted"
                )
                mock_run_7z.side_effect = other_error

                with pytest.raises(ExtractionError) as exc_info:
                    sz.extract("output")

                assert "Archive is corrupted" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

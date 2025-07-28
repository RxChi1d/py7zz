"""
Tests for Windows filename compatibility sanitizer.
"""

from unittest.mock import patch

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

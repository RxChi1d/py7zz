"""
Integration tests for Windows filename compatibility during extraction.
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from py7zz.core import SevenZipFile, _is_filename_error
from py7zz.exceptions import ExtractionError, FilenameCompatibilityError


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
            self.sz, "list_contents", return_value=["file:name.txt", "CON.txt"]
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
            self.sz, "list_contents", return_value=["file:name.txt"]
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

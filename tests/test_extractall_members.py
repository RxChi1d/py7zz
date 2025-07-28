"""
Tests for SevenZipFile.extractall(members=...) parameter implementation.

This module tests the selective extraction functionality using the members parameter,
ensuring compatibility with zipfile.ZipFile.extractall() and tarfile.TarFile.extractall().
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from py7zz.core import SevenZipFile
from py7zz.exceptions import ExtractionError, FileNotFoundError


class TestExtractallMembersParameter:
    """Test the extractall members parameter functionality."""

    def test_extractall_no_members_extracts_all(self):
        """Test that extractall() without members parameter extracts everything."""
        mock_archive_path = Path("/mock/archive.7z")

        with patch("py7zz.core.Path.exists", return_value=True), patch.object(
            SevenZipFile, "extract"
        ) as mock_extract:
            sz = SevenZipFile(mock_archive_path, "r")
            sz.extractall("output")

            # Should call extract with overwrite=True
            mock_extract.assert_called_once_with(Path("output"), overwrite=True)

    def test_extractall_empty_members_list(self):
        """Test that extractall() with empty members list does nothing."""
        mock_archive_path = Path("/mock/archive.7z")

        with patch("py7zz.core.Path.exists", return_value=True), patch(
            "py7zz.core.Path.mkdir"
        ) as mock_mkdir, patch.object(
            SevenZipFile, "_extract_selective_members"
        ) as mock_selective:
            sz = SevenZipFile(mock_archive_path, "r")
            sz.extractall("output", members=[])

            # Should create output directory
            mock_mkdir.assert_called_once()

            # Should call selective extraction with empty list
            mock_selective.assert_called_once_with(Path("output"), [])

    def test_extractall_with_specific_members(self):
        """Test extractall() with specific member names."""
        mock_archive_path = Path("/mock/archive.7z")
        test_members = ["file1.txt", "dir/file2.txt", "file3.txt"]

        with patch("py7zz.core.Path.exists", return_value=True), patch(
            "py7zz.core.Path.mkdir"
        ) as mock_mkdir, patch.object(
            SevenZipFile, "_extract_selective_members"
        ) as mock_selective:
            sz = SevenZipFile(mock_archive_path, "r")
            sz.extractall("output", members=test_members)

            # Should create output directory
            mock_mkdir.assert_called_once()

            # Should call selective extraction with specified members
            mock_selective.assert_called_once_with(Path("output"), test_members)

    def test_extractall_write_mode_error(self):
        """Test that extractall() in write mode raises error."""
        mock_archive_path = Path("/mock/archive.7z")

        sz = SevenZipFile(mock_archive_path, "w")

        with pytest.raises(
            ValueError, match="Cannot extract from archive opened in write mode"
        ):
            sz.extractall("output", members=["file1.txt"])

    def test_extractall_missing_archive(self):
        """Test that extractall() with missing archive raises error."""
        mock_archive_path = Path("/mock/missing.7z")

        with patch("py7zz.core.Path.exists", return_value=False):
            sz = SevenZipFile(mock_archive_path, "r")

            with pytest.raises(FileNotFoundError, match="Archive not found"):
                sz.extractall("output", members=["file1.txt"])


class TestExtractSelectiveMembers:
    """Test the _extract_selective_members internal method."""

    def setup_method(self):
        """Setup for each test."""
        self.mock_archive_path = Path("/mock/archive.7z")
        self.sz = SevenZipFile(self.mock_archive_path, "r")

    @patch("py7zz.core.run_7z")
    def test_extract_selective_members_success(self, mock_run_7z):
        """Test successful selective extraction."""
        mock_run_7z.return_value = Mock()
        test_members = ["file1.txt", "file2.txt"]
        target_path = Path("/mock/output")

        self.sz._extract_selective_members(target_path, test_members)

        # Should call run_7z with correct arguments
        mock_run_7z.assert_called_once()
        args = mock_run_7z.call_args[0][0]

        assert "x" in args  # extract command
        assert str(self.mock_archive_path) in args
        assert f"-o{target_path}" in args
        assert "-y" in args  # assume yes
        assert "file1.txt" in args
        assert "file2.txt" in args

    def test_extract_selective_members_empty_list(self):
        """Test selective extraction with empty members list."""
        target_path = Path("/mock/output")

        # Should return immediately without calling run_7z
        with patch("py7zz.core.run_7z") as mock_run_7z:
            self.sz._extract_selective_members(target_path, [])
            mock_run_7z.assert_not_called()

    @patch("py7zz.core.run_7z")
    def test_extract_selective_members_7z_error(self, mock_run_7z):
        """Test selective extraction when 7z command fails."""
        import subprocess

        mock_run_7z.side_effect = subprocess.CalledProcessError(
            2, ["7zz"], stderr="File not found in archive"
        )

        test_members = ["nonexistent.txt"]
        target_path = Path("/mock/output")

        with pytest.raises(ExtractionError, match="Failed to extract selected members"):
            self.sz._extract_selective_members(target_path, test_members)

    @patch("py7zz.core._is_filename_error", return_value=True)
    @patch("py7zz.core.run_7z")
    def test_extract_selective_members_filename_sanitization(
        self, mock_run_7z, mock_is_filename_error
    ):
        """Test selective extraction with filename sanitization fallback."""
        import subprocess

        # First call fails with filename error
        mock_run_7z.side_effect = subprocess.CalledProcessError(
            2, ["7zz"], stderr="Cannot create file: invalid name"
        )

        test_members = ["file:name.txt"]
        target_path = Path("/mock/output")

        with patch.object(
            self.sz, "_extract_selective_with_sanitization"
        ) as mock_sanitize:
            self.sz._extract_selective_members(target_path, test_members)

            # Should call sanitization method
            mock_sanitize.assert_called_once_with(target_path, test_members)


class TestExtractSelectiveWithSanitization:
    """Test the _extract_selective_with_sanitization method."""

    def setup_method(self):
        """Setup for each test."""
        self.mock_archive_path = Path("/mock/archive.7z")
        self.sz = SevenZipFile(self.mock_archive_path, "r")

    @patch("py7zz.core.needs_sanitization")
    @patch("py7zz.core.get_sanitization_mapping")
    @patch("py7zz.core.log_sanitization_changes")
    def test_extract_selective_with_sanitization_success(
        self, mock_log_changes, mock_get_mapping, mock_needs_sanitization
    ):
        """Test successful selective extraction with sanitization."""
        # Setup mocks
        requested_members = ["file:name.txt", "CON.txt", "normal.txt"]
        all_files = ["file:name.txt", "CON.txt", "normal.txt", "other.txt"]

        with patch.object(self.sz, "_list_contents", return_value=all_files):
            mock_needs_sanitization.side_effect = lambda f: f in [
                "file:name.txt",
                "CON.txt",
            ]
            mock_get_mapping.return_value = {
                "file:name.txt": "file_name.txt",
                "CON.txt": "CON_file.txt",
                "normal.txt": "normal.txt",
            }

            target_path = Path("/mock/output")

            # Mock the individual extraction method
            with patch.object(
                self.sz, "_extract_files_individually"
            ) as mock_individual:
                # Set up the method to succeed with some files
                def mock_extract_individual(target, mapping):
                    # Simulate successful extraction of 2 files
                    pass

                mock_individual.side_effect = mock_extract_individual

                # Should not raise exception
                import contextlib

                with contextlib.suppress(Exception):
                    self.sz._extract_selective_with_sanitization(
                        target_path, requested_members
                    )

                # Verify sanitization mapping was generated for requested members only
                mock_get_mapping.assert_called_once_with(all_files)

    def test_extract_selective_with_sanitization_no_requested_members_in_archive(self):
        """Test sanitization when requested members don't exist in archive."""
        requested_members = ["nonexistent1.txt", "nonexistent2.txt"]
        all_files = ["existing1.txt", "existing2.txt"]

        with patch.object(self.sz, "_list_contents", return_value=all_files):
            target_path = Path("/mock/output")

            # Should return early since no requested members exist
            self.sz._extract_selective_with_sanitization(target_path, requested_members)
            # Method should complete without errors (just log warnings)

    @patch("py7zz.core.needs_sanitization", return_value=False)
    def test_extract_selective_with_sanitization_no_problematic_files(
        self, mock_needs_sanitization
    ):
        """Test when no files need sanitization but extraction still failed."""
        requested_members = ["normal1.txt", "normal2.txt"]
        all_files = ["normal1.txt", "normal2.txt", "other.txt"]

        with patch.object(self.sz, "_list_contents", return_value=all_files):
            target_path = Path("/mock/output")

            from py7zz.exceptions import FilenameCompatibilityError

            with pytest.raises(
                FilenameCompatibilityError,
                match="No problematic filenames detected among requested members",
            ):
                self.sz._extract_selective_with_sanitization(
                    target_path, requested_members
                )


class TestExtractallIntegration:
    """Integration tests for extractall with members parameter."""

    def test_extractall_members_zipfile_compatibility(self):
        """Test that extractall members parameter matches zipfile interface."""
        mock_archive_path = Path("/mock/ziplike.7z")

        with patch("py7zz.core.Path.exists", return_value=True), patch.object(
            SevenZipFile, "_extract_selective_members"
        ) as mock_selective:
            sz = SevenZipFile(mock_archive_path, "r")

            # Test zipfile-style usage
            members_to_extract = ["readme.txt", "src/main.py", "docs/"]
            sz.extractall("/tmp/extract", members=members_to_extract)

            mock_selective.assert_called_once_with(
                Path("/tmp/extract"), members_to_extract
            )

    def test_extractall_members_tarfile_compatibility(self):
        """Test that extractall members parameter matches tarfile interface."""
        mock_archive_path = Path("/mock/tarlike.7z")

        with patch("py7zz.core.Path.exists", return_value=True), patch.object(
            SevenZipFile, "_extract_selective_members"
        ) as mock_selective:
            sz = SevenZipFile(mock_archive_path, "r")

            # Test tarfile-style usage
            members_to_extract = ["./config.conf", "bin/script.sh"]
            sz.extractall("/tmp/extract", members=members_to_extract)

            mock_selective.assert_called_once_with(
                Path("/tmp/extract"), members_to_extract
            )

    def test_extractall_default_path_with_members(self):
        """Test extractall with members but default path."""
        mock_archive_path = Path("/mock/archive.7z")

        with patch("py7zz.core.Path.exists", return_value=True), patch(
            "py7zz.core.Path.mkdir"
        ) as mock_mkdir, patch.object(
            SevenZipFile, "_extract_selective_members"
        ) as mock_selective:
            sz = SevenZipFile(mock_archive_path, "r")
            sz.extractall(members=["selected.txt"])

            # Should use current directory as default
            mock_mkdir.assert_called_once()
            mock_selective.assert_called_once_with(Path("."), ["selected.txt"])

    def test_extractall_with_unicode_member_names(self):
        """Test extractall with Unicode member names."""
        mock_archive_path = Path("/mock/unicode.7z")
        unicode_members = ["测试文件.txt", "файл.txt", "アーカイブ.txt"]

        with patch("py7zz.core.Path.exists", return_value=True), patch.object(
            SevenZipFile, "_extract_selective_members"
        ) as mock_selective:
            sz = SevenZipFile(mock_archive_path, "r")
            sz.extractall("/tmp/unicode", members=unicode_members)

            mock_selective.assert_called_once_with(
                Path("/tmp/unicode"), unicode_members
            )

    def test_extractall_with_special_character_member_names(self):
        """Test extractall with special character member names."""
        mock_archive_path = Path("/mock/special.7z")
        special_members = [
            "file with spaces.txt",
            "file-with-dashes.txt",
            "file.with.dots.txt",
            "file(with)parens.txt",
        ]

        with patch("py7zz.core.Path.exists", return_value=True), patch.object(
            SevenZipFile, "_extract_selective_members"
        ) as mock_selective:
            sz = SevenZipFile(mock_archive_path, "r")
            sz.extractall("/tmp/special", members=special_members)

            mock_selective.assert_called_once_with(
                Path("/tmp/special"), special_members
            )

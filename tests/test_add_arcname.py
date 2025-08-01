"""
Tests for SevenZipFile.add(arcname=...) parameter implementation.

This module tests the custom archive naming functionality using the arcname parameter,
ensuring compatibility with zipfile.ZipFile.add() behavior.
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from py7zz.core import SevenZipFile
from py7zz.exceptions import FileNotFoundError


class TestAddArcnameParameter:
    """Test the add arcname parameter functionality."""

    def test_add_without_arcname_uses_original_name(self):
        """Test that add() without arcname uses original file name."""
        mock_archive_path = Path("/mock/archive.7z")
        mock_file_path = Path("/mock/test.txt")

        with patch("py7zz.core.Path.exists", return_value=True), patch.object(
            SevenZipFile, "_add_simple"
        ) as mock_add_simple:
            sz = SevenZipFile(mock_archive_path, "w")
            sz.add(mock_file_path)

            # Should call _add_simple with the file path
            mock_add_simple.assert_called_once_with(mock_file_path)

    def test_add_with_arcname_uses_custom_name(self):
        """Test that add() with arcname uses custom archive name."""
        mock_archive_path = Path("/mock/archive.7z")
        mock_file_path = Path("/mock/test.txt")
        custom_arcname = "custom_name.txt"

        with patch("py7zz.core.Path.exists", return_value=True), patch.object(
            SevenZipFile, "_add_with_arcname"
        ) as mock_add_arcname:
            sz = SevenZipFile(mock_archive_path, "w")
            sz.add(mock_file_path, arcname=custom_arcname)

            # Should call _add_with_arcname with file path and custom name
            mock_add_arcname.assert_called_once_with(mock_file_path, custom_arcname)

    def test_add_read_mode_error(self):
        """Test that add() in read mode raises error."""
        mock_archive_path = Path("/mock/archive.7z")
        mock_file_path = Path("/mock/test.txt")

        sz = SevenZipFile(mock_archive_path, "r")

        with pytest.raises(
            ValueError, match="Cannot add to archive opened in read mode"
        ):
            sz.add(mock_file_path, arcname="custom.txt")

    def test_add_missing_file_error(self):
        """Test that add() with missing file raises error."""
        mock_archive_path = Path("/mock/archive.7z")
        mock_file_path = Path("/mock/missing.txt")

        with patch("py7zz.core.Path.exists", return_value=False):
            sz = SevenZipFile(mock_archive_path, "w")

            with pytest.raises(FileNotFoundError, match="File not found"):
                sz.add(mock_file_path, arcname="custom.txt")


class TestAddSimpleMethod:
    """Test the _add_simple internal method."""

    def setup_method(self):
        """Setup for each test."""
        self.mock_archive_path = Path("/mock/archive.7z")
        self.sz = SevenZipFile(self.mock_archive_path, "w")

    @patch("py7zz.core.run_7z")
    def test_add_simple_success(self, mock_run_7z):
        """Test successful simple file addition."""
        mock_run_7z.return_value = Mock()
        mock_file_path = Path("/mock/test.txt")

        self.sz._add_simple(mock_file_path)

        # Should call run_7z with correct arguments
        mock_run_7z.assert_called_once()
        args = mock_run_7z.call_args[0][0]

        assert "a" in args  # add command
        assert str(self.mock_archive_path) in args
        assert str(mock_file_path) in args
        # Should include compression configuration
        assert any("-mx" in arg for arg in args)

    @patch("py7zz.core.run_7z")
    def test_add_simple_7z_error(self, mock_run_7z):
        """Test simple addition when 7z command fails."""
        import subprocess

        mock_run_7z.side_effect = subprocess.CalledProcessError(
            2, ["7zz"], stderr="Cannot add file"
        )

        mock_file_path = Path("/mock/test.txt")

        with pytest.raises(RuntimeError, match="Failed to add .* to archive"):
            self.sz._add_simple(mock_file_path)


class TestAddWithArcnameMethod:
    """Test the _add_with_arcname internal method."""

    def setup_method(self):
        """Setup for each test."""
        self.mock_archive_path = Path("/mock/archive.7z")
        self.sz = SevenZipFile(self.mock_archive_path, "w")

    @patch("tempfile.TemporaryDirectory")
    @patch("shutil.copy2")
    @patch("subprocess.run")
    @patch("py7zz.core.find_7z_binary")
    def test_add_with_arcname_file_success(
        self, mock_find_binary, mock_subprocess, mock_copy, mock_temp_dir
    ):
        """Test successful file addition with custom arcname."""
        # Setup mocks
        mock_find_binary.return_value = "/usr/bin/7zz"
        mock_temp_dir_path = Path("/tmp/mock_temp")
        mock_temp_dir_instance = MagicMock()
        mock_temp_dir_instance.__enter__.return_value = str(mock_temp_dir_path)
        mock_temp_dir_instance.__exit__.return_value = None
        mock_temp_dir.return_value = mock_temp_dir_instance

        mock_subprocess.return_value = Mock(returncode=0)

        # Setup file mocks
        mock_file_path = Path("/mock/source.txt")
        custom_arcname = "custom/path/renamed.txt"

        with patch("pathlib.Path.is_file", return_value=True), patch(
            "pathlib.Path.mkdir"
        ) as mock_mkdir:
            self.sz._add_with_arcname(mock_file_path, custom_arcname)

            # Should create necessary directories
            mock_mkdir.assert_called()

            # Should copy file to temporary location
            mock_copy.assert_called_once()

            # Should run 7z with correct arguments in temp directory
            mock_subprocess.assert_called_once()
            args = mock_subprocess.call_args[0][0]
            kwargs = mock_subprocess.call_args[1]

            assert "/usr/bin/7zz" in args
            assert "a" in args
            assert str(self.mock_archive_path) in args
            assert kwargs.get("cwd") == str(mock_temp_dir_path)

    @patch("tempfile.TemporaryDirectory")
    @patch("shutil.copytree")
    @patch("subprocess.run")
    @patch("py7zz.core.find_7z_binary")
    def test_add_with_arcname_directory_success(
        self, mock_find_binary, mock_subprocess, mock_copytree, mock_temp_dir
    ):
        """Test successful directory addition with custom arcname."""
        # Setup mocks
        mock_find_binary.return_value = "/usr/bin/7zz"
        mock_temp_dir_path = Path("/tmp/mock_temp")
        mock_temp_dir_instance = MagicMock()
        mock_temp_dir_instance.__enter__.return_value = str(mock_temp_dir_path)
        mock_temp_dir_instance.__exit__.return_value = None
        mock_temp_dir.return_value = mock_temp_dir_instance

        mock_subprocess.return_value = Mock(returncode=0)

        # Setup directory mocks
        mock_dir_path = Path("/mock/source_dir")
        custom_arcname = "custom_dir"

        with patch("pathlib.Path.is_file", return_value=False), patch(
            "pathlib.Path.mkdir"
        ) as mock_mkdir, patch(
            "os.symlink", side_effect=OSError("Symlink not supported")
        ):
            self.sz._add_with_arcname(mock_dir_path, custom_arcname)

            # Should create necessary directories
            mock_mkdir.assert_called()

            # Should copy directory to temporary location (fallback from symlink)
            mock_copytree.assert_called_once()

            # Should run 7z command
            mock_subprocess.assert_called_once()

    @patch("tempfile.TemporaryDirectory")
    @patch("os.symlink")
    @patch("subprocess.run")
    @patch("py7zz.core.find_7z_binary")
    def test_add_with_arcname_directory_with_symlink(
        self, mock_find_binary, mock_subprocess, mock_symlink, mock_temp_dir
    ):
        """Test directory addition using symlink (faster method)."""
        # Setup mocks
        mock_find_binary.return_value = "/usr/bin/7zz"
        mock_temp_dir_path = Path("/tmp/mock_temp")
        mock_temp_dir_instance = MagicMock()
        mock_temp_dir_instance.__enter__.return_value = str(mock_temp_dir_path)
        mock_temp_dir_instance.__exit__.return_value = None
        mock_temp_dir.return_value = mock_temp_dir_instance

        mock_subprocess.return_value = Mock(returncode=0)
        mock_symlink.return_value = None  # Symlink succeeds

        # Setup directory mocks
        mock_dir_path = Path("/mock/source_dir")
        custom_arcname = "custom_dir"

        with patch("pathlib.Path.is_file", return_value=False), patch(
            "pathlib.Path.mkdir"
        ):
            self.sz._add_with_arcname(mock_dir_path, custom_arcname)

            # Should create symlink instead of copying
            mock_symlink.assert_called_once()

            # Should run 7z command
            mock_subprocess.assert_called_once()

    @patch("tempfile.TemporaryDirectory")
    @patch("shutil.copy2")
    @patch("subprocess.run")
    @patch("py7zz.core.find_7z_binary")
    def test_add_with_arcname_7z_error(
        self, mock_find_binary, mock_subprocess, mock_copy, mock_temp_dir
    ):
        """Test arcname addition when 7z command fails."""
        # Setup mocks
        mock_find_binary.return_value = "/usr/bin/7zz"
        mock_temp_dir_path = Path("/tmp/mock_temp")
        mock_temp_dir_instance = MagicMock()
        mock_temp_dir_instance.__enter__.return_value = str(mock_temp_dir_path)
        mock_temp_dir_instance.__exit__.return_value = None
        mock_temp_dir.return_value = mock_temp_dir_instance

        import subprocess

        mock_subprocess.side_effect = subprocess.CalledProcessError(
            2, ["7zz"], stderr="Cannot add file with custom name"
        )

        mock_file_path = Path("/mock/source.txt")
        custom_arcname = "custom.txt"

        with patch("pathlib.Path.is_file", return_value=True), patch(
            "pathlib.Path.mkdir"
        ), pytest.raises(RuntimeError, match="Failed to add .* as .* to archive"):
            self.sz._add_with_arcname(mock_file_path, custom_arcname)

    def test_add_with_arcname_nested_path(self):
        """Test arcname with nested directory structure."""
        mock_file_path = Path("/mock/source.txt")
        nested_arcname = "deep/nested/structure/file.txt"

        with patch("tempfile.TemporaryDirectory") as mock_temp_dir, patch(
            "shutil.copy2"
        ), patch("subprocess.run") as mock_subprocess, patch(
            "py7zz.core.find_7z_binary", return_value="/usr/bin/7zz"
        ):
            # Setup temp directory mock
            mock_temp_dir_path = Path("/tmp/mock_temp")
            mock_temp_dir_instance = MagicMock()
            mock_temp_dir_instance.__enter__.return_value = str(mock_temp_dir_path)
            mock_temp_dir_instance.__exit__.return_value = None
            mock_temp_dir.return_value = mock_temp_dir_instance

            mock_subprocess.return_value = Mock(returncode=0)

            with patch("pathlib.Path.is_file", return_value=True), patch(
                "pathlib.Path.mkdir"
            ) as mock_mkdir:
                self.sz._add_with_arcname(mock_file_path, nested_arcname)

                # Should create nested directory structure
                assert mock_mkdir.called
                # Check that parents=True was used for nested structure
                call_args = mock_mkdir.call_args
                assert call_args[1]["parents"] is True


class TestAddArcnameIntegration:
    """Integration tests for add with arcname parameter."""

    def test_add_arcname_zipfile_compatibility(self):
        """Test that add arcname parameter matches zipfile interface."""
        mock_archive_path = Path("/mock/ziplike.7z")
        mock_file_path = Path("/mock/source.txt")

        with patch("py7zz.core.Path.exists", return_value=True), patch.object(
            SevenZipFile, "_add_with_arcname"
        ) as mock_add_arcname:
            sz = SevenZipFile(mock_archive_path, "w")

            # Test zipfile-style usage
            sz.add(mock_file_path, arcname="data/processed.txt")

            mock_add_arcname.assert_called_once_with(
                mock_file_path, "data/processed.txt"
            )

    def test_add_multiple_files_with_arcnames(self):
        """Test adding multiple files with different arcnames."""
        mock_archive_path = Path("/mock/archive.7z")

        test_files = [
            ("/mock/file1.txt", "renamed1.txt"),
            ("/mock/file2.txt", "subdir/renamed2.txt"),
            ("/mock/file3.txt", "deep/nested/renamed3.txt"),
        ]

        with patch("py7zz.core.Path.exists", return_value=True), patch.object(
            SevenZipFile, "_add_with_arcname"
        ) as mock_add_arcname:
            sz = SevenZipFile(mock_archive_path, "w")

            for file_path, arcname in test_files:
                sz.add(Path(file_path), arcname=arcname)

            # Should call _add_with_arcname for each file
            assert mock_add_arcname.call_count == 3

            # Verify call arguments
            call_args_list = mock_add_arcname.call_args_list
            for i, (file_path, arcname) in enumerate(test_files):
                assert call_args_list[i][0] == (Path(file_path), arcname)

    def test_add_with_unicode_arcname(self):
        """Test add with Unicode arcname."""
        mock_archive_path = Path("/mock/unicode.7z")
        mock_file_path = Path("/mock/source.txt")
        unicode_arcname = "测试文件/файл/アーカイブ.txt"

        with patch("py7zz.core.Path.exists", return_value=True), patch.object(
            SevenZipFile, "_add_with_arcname"
        ) as mock_add_arcname:
            sz = SevenZipFile(mock_archive_path, "w")
            sz.add(mock_file_path, arcname=unicode_arcname)

            mock_add_arcname.assert_called_once_with(mock_file_path, unicode_arcname)

    def test_add_with_special_character_arcname(self):
        """Test add with special character arcname."""
        mock_archive_path = Path("/mock/special.7z")
        mock_file_path = Path("/mock/source.txt")
        special_arcname = "file with spaces & symbols!@#.txt"

        with patch("py7zz.core.Path.exists", return_value=True), patch.object(
            SevenZipFile, "_add_with_arcname"
        ) as mock_add_arcname:
            sz = SevenZipFile(mock_archive_path, "w")
            sz.add(mock_file_path, arcname=special_arcname)

            mock_add_arcname.assert_called_once_with(mock_file_path, special_arcname)

    def test_add_directory_with_arcname(self):
        """Test adding directory with custom arcname."""
        mock_archive_path = Path("/mock/archive.7z")
        mock_dir_path = Path("/mock/source_directory")

        with patch("py7zz.core.Path.exists", return_value=True), patch.object(
            SevenZipFile, "_add_with_arcname"
        ) as mock_add_arcname:
            sz = SevenZipFile(mock_archive_path, "w")
            sz.add(mock_dir_path, arcname="custom_directory_name")

            mock_add_arcname.assert_called_once_with(
                mock_dir_path, "custom_directory_name"
            )

    def test_add_preserves_compression_settings_with_arcname(self):
        """Test that compression settings are preserved when using arcname."""
        mock_archive_path = Path("/mock/archive.7z")
        mock_file_path = Path("/mock/source.txt")

        # Create SevenZipFile with specific compression settings
        sz = SevenZipFile(mock_archive_path, "w", level="maximum")

        with patch("py7zz.core.Path.exists", return_value=True), patch(
            "tempfile.TemporaryDirectory"
        ) as mock_temp_dir, patch("subprocess.run") as mock_subprocess, patch(
            "py7zz.core.find_7z_binary", return_value="/usr/bin/7zz"
        ):
            # Setup temp directory mock
            mock_temp_dir_path = Path("/tmp/mock_temp")
            mock_temp_dir_instance = MagicMock()
            mock_temp_dir_instance.__enter__.return_value = str(mock_temp_dir_path)
            mock_temp_dir_instance.__exit__.return_value = None
            mock_temp_dir.return_value = mock_temp_dir_instance

            mock_subprocess.return_value = Mock(returncode=0)

            with patch("pathlib.Path.is_file", return_value=True), patch(
                "pathlib.Path.mkdir"
            ), patch("shutil.copy2"):
                sz.add(mock_file_path, arcname="custom.txt")

                # Verify compression settings are included in the command
                mock_subprocess.assert_called_once()
                args = mock_subprocess.call_args[0][0]

                # Should include maximum compression settings
                assert any("-mx7" in arg for arg in args)  # Level 7 for maximum

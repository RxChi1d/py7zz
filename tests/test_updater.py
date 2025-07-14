"""Tests for the updater module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

from py7zz.updater import (
    UpdateError,
    check_for_updates,
    get_asset_name,
    get_cached_binary,
    get_latest_release,
    get_platform_info,
    get_version_from_binary,
)


class TestPlatformInfo:
    """Test platform detection functions."""

    @patch("platform.system")
    @patch("platform.machine")
    def test_get_platform_info_mac_arm64(self, mock_machine: Mock, mock_system: Mock) -> None:
        """Test macOS ARM64 platform detection."""
        mock_system.return_value = "Darwin"
        mock_machine.return_value = "arm64"
        
        platform, arch = get_platform_info()
        assert platform == "mac"
        assert arch == "arm64"

    @patch("platform.system")
    @patch("platform.machine")
    def test_get_platform_info_linux_x64(self, mock_machine: Mock, mock_system: Mock) -> None:
        """Test Linux x64 platform detection."""
        mock_system.return_value = "Linux"
        mock_machine.return_value = "x86_64"
        
        platform, arch = get_platform_info()
        assert platform == "linux"
        assert arch == "x64"

    @patch("platform.system")
    @patch("platform.machine")
    def test_get_platform_info_windows_x64(self, mock_machine: Mock, mock_system: Mock) -> None:
        """Test Windows x64 platform detection."""
        mock_system.return_value = "Windows"
        mock_machine.return_value = "AMD64"
        
        platform, arch = get_platform_info()
        assert platform == "windows"
        assert arch == "x64"

    @patch("platform.system")
    def test_get_platform_info_unsupported_system(self, mock_system: Mock) -> None:
        """Test unsupported system raises error."""
        mock_system.return_value = "FreeBSD"
        
        with pytest.raises(UpdateError, match="Unsupported platform"):
            get_platform_info()

    @patch("platform.system")
    @patch("platform.machine")
    def test_get_platform_info_unsupported_arch(self, mock_machine: Mock, mock_system: Mock) -> None:
        """Test unsupported architecture raises error."""
        mock_system.return_value = "Linux"
        mock_machine.return_value = "i386"
        
        with pytest.raises(UpdateError, match="Unsupported architecture"):
            get_platform_info()


class TestAssetName:
    """Test asset name generation."""

    def test_get_asset_name_windows(self) -> None:
        """Test Windows asset name generation."""
        assert get_asset_name("2408", "windows", "x64") == "7z2408-x64.exe"

    def test_get_asset_name_mac(self) -> None:
        """Test macOS asset name generation."""
        assert get_asset_name("2408", "mac", "arm64") == "7z2408-mac.tar.xz"

    def test_get_asset_name_linux(self) -> None:
        """Test Linux asset name generation."""
        assert get_asset_name("2408", "linux", "x64") == "7z2408-linux-x64.tar.xz"

    def test_get_asset_name_unsupported(self) -> None:
        """Test unsupported platform raises error."""
        with pytest.raises(UpdateError, match="Unsupported platform"):
            get_asset_name("2408", "freebsd", "x64")


class TestLatestRelease:
    """Test GitHub API release fetching."""

    @patch("requests.get")
    def test_get_latest_release_success(self, mock_get: Mock) -> None:
        """Test successful release fetching."""
        mock_response = Mock()
        mock_response.json.return_value = {"tag_name": "2408", "name": "7-Zip 24.08"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("py7zz.updater.CACHE_DIR", Path(tmpdir)):
                result = get_latest_release(use_cache=False)
                assert result["tag_name"] == "2408"
                assert result["name"] == "7-Zip 24.08"

    @patch("requests.get")
    def test_get_latest_release_network_error(self, mock_get: Mock) -> None:
        """Test network error handling."""
        mock_get.side_effect = requests.RequestException("Network error")
        
        with pytest.raises(UpdateError, match="Failed to fetch release information"):
            get_latest_release(use_cache=False)

    def test_get_latest_release_cache_hit(self) -> None:
        """Test cache hit scenario."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            cache_file = cache_dir / "latest_release.json"
            
            # Create cache file
            cache_data = {"tag_name": "2408", "name": "7-Zip 24.08"}
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
            
            with patch("py7zz.updater.CACHE_DIR", cache_dir):
                result = get_latest_release(use_cache=True)
                assert result["tag_name"] == "2408"


class TestVersionChecking:
    """Test version checking and comparison."""

    @patch("py7zz.updater.get_latest_release")
    def test_check_for_updates_newer_available(self, mock_get_release: Mock) -> None:
        """Test when newer version is available."""
        mock_get_release.return_value = {"tag_name": "2409"}
        
        result = check_for_updates("2408")
        assert result == "2409"

    @patch("py7zz.updater.get_latest_release")
    def test_check_for_updates_no_update_needed(self, mock_get_release: Mock) -> None:
        """Test when no update is needed."""
        mock_get_release.return_value = {"tag_name": "2408"}
        
        result = check_for_updates("2408")
        assert result is None

    @patch("py7zz.updater.get_latest_release")
    def test_check_for_updates_current_none(self, mock_get_release: Mock) -> None:
        """Test when current version is None."""
        mock_get_release.return_value = {"tag_name": "2408"}
        
        result = check_for_updates(None)
        assert result == "2408"

    @patch("py7zz.updater.get_latest_release")
    def test_check_for_updates_error(self, mock_get_release: Mock) -> None:
        """Test error handling in version checking."""
        mock_get_release.side_effect = UpdateError("API error")
        
        result = check_for_updates("2408")
        assert result is None


class TestCachedBinary:
    """Test cached binary management."""

    @patch("py7zz.updater.get_platform_info")
    def test_get_cached_binary_exists(self, mock_platform: Mock) -> None:
        """Test when cached binary exists."""
        mock_platform.return_value = ("linux", "x64")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            version_dir = cache_dir / "2408"
            version_dir.mkdir(parents=True)
            binary_path = version_dir / "7zz"
            binary_path.touch()
            
            with patch("py7zz.updater.CACHE_DIR", cache_dir):
                result = get_cached_binary("2408", auto_update=False)
                assert result == binary_path

    @patch("py7zz.updater.get_platform_info")
    def test_get_cached_binary_not_exists_no_update(self, mock_platform: Mock) -> None:
        """Test when cached binary doesn't exist and auto_update is False."""
        mock_platform.return_value = ("linux", "x64")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("py7zz.updater.CACHE_DIR", Path(tmpdir)):
                result = get_cached_binary("2408", auto_update=False)
                assert result is None


class TestVersionFromBinary:
    """Test version extraction from binary."""

    @patch("subprocess.run")
    def test_get_version_from_binary_success(self, mock_run: Mock) -> None:
        """Test successful version extraction."""
        mock_result = Mock()
        mock_result.stdout = "7-Zip 24.08 (x64) : Copyright (c) 1999-2024 Igor Pavlov"
        mock_run.return_value = mock_result
        
        result = get_version_from_binary(Path("/fake/path/7zz"))
        assert result == "2408"

    @patch("subprocess.run")
    def test_get_version_from_binary_error(self, mock_run: Mock) -> None:
        """Test error handling in version extraction."""
        mock_run.side_effect = OSError("Binary not found")
        
        result = get_version_from_binary(Path("/fake/path/7zz"))
        assert result is None

    @patch("subprocess.run")
    def test_get_version_from_binary_no_version(self, mock_run: Mock) -> None:
        """Test when version cannot be parsed."""
        mock_result = Mock()
        mock_result.stdout = "Invalid output"
        mock_run.return_value = mock_result
        
        result = get_version_from_binary(Path("/fake/path/7zz"))
        assert result is None
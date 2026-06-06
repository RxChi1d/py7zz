# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""Tests for the updater module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

import py7zz._download as dl
from py7zz.updater import (
    UpdateError,
    _is_cache_complete,
    check_for_updates,
    cleanup_old_versions,
    ensure_7zz_available,
    get_asset_name,
    get_cached_binary,
    get_latest_release,
    get_pinned_7zz_version,
    get_platform_info,
    get_version_from_binary,
)


class TestPlatformInfo:
    """Test platform detection functions."""

    @patch("platform.system")
    @patch("platform.machine")
    def test_get_platform_info_mac_arm64(
        self, mock_machine: Mock, mock_system: Mock
    ) -> None:
        """Test macOS ARM64 platform detection."""
        mock_system.return_value = "Darwin"
        mock_machine.return_value = "arm64"

        platform, arch = get_platform_info()
        assert platform == "mac"
        assert arch == "arm64"

    @patch("platform.system")
    @patch("platform.machine")
    def test_get_platform_info_linux_x64(
        self, mock_machine: Mock, mock_system: Mock
    ) -> None:
        """Test Linux x64 platform detection."""
        mock_system.return_value = "Linux"
        mock_machine.return_value = "x86_64"

        platform, arch = get_platform_info()
        assert platform == "linux"
        assert arch == "x64"

    @patch("platform.system")
    @patch("platform.machine")
    def test_get_platform_info_windows_x64(
        self, mock_machine: Mock, mock_system: Mock
    ) -> None:
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
    def test_get_platform_info_unsupported_arch(
        self, mock_machine: Mock, mock_system: Mock
    ) -> None:
        """Test unsupported architecture raises error."""
        mock_system.return_value = "Linux"
        mock_machine.return_value = "i386"

        with pytest.raises(UpdateError, match="Unsupported architecture"):
            get_platform_info()

    @patch("platform.system")
    @patch("platform.machine")
    def test_get_platform_info_linux_aarch64(
        self, mock_machine: Mock, mock_system: Mock
    ) -> None:
        """Test Linux aarch64 platform detection maps to arm64."""
        mock_system.return_value = "Linux"
        mock_machine.return_value = "aarch64"

        platform, arch = get_platform_info()
        assert platform == "linux"
        assert arch == "arm64"

    @patch("platform.system")
    @patch("platform.machine")
    def test_get_platform_info_windows_arm64(
        self, mock_machine: Mock, mock_system: Mock
    ) -> None:
        """Test Windows ARM64 platform detection."""
        mock_system.return_value = "Windows"
        mock_machine.return_value = "ARM64"

        platform, arch = get_platform_info()
        assert platform == "windows"
        assert arch == "arm64"


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

    def test_get_asset_name_windows_arm64(self) -> None:
        """Test Windows arm64 asset name generation."""
        assert get_asset_name("2408", "windows", "arm64") == "7z2408-arm64.exe"

    def test_get_asset_name_linux_arm64(self) -> None:
        """Test Linux arm64 asset name generation."""
        assert get_asset_name("2408", "linux", "arm64") == "7z2408-linux-arm64.tar.xz"

    def test_get_asset_name_unsupported(self) -> None:
        """Test unsupported platform raises error."""
        with pytest.raises(UpdateError, match="Unsupported platform"):
            get_asset_name("2408", "freebsd", "x64")

    def test_get_asset_name_linux_unsupported_arch(self) -> None:
        """Test unsupported Linux architecture raises error with matching message."""
        with pytest.raises(UpdateError, match="Unsupported Linux architecture: i386"):
            get_asset_name("2408", "linux", "i386")

    def test_get_asset_name_windows_unsupported_arch(self) -> None:
        """Test unsupported Windows architecture raises error with matching message."""
        with pytest.raises(UpdateError, match="Unsupported Windows architecture: arm"):
            get_asset_name("2408", "windows", "arm")


class TestLatestRelease:
    """Test GitHub API release fetching."""

    @patch("requests.get")
    def test_get_latest_release_success(self, mock_get: Mock) -> None:
        """Test successful release fetching."""
        mock_response = Mock()
        mock_response.json.return_value = {"tag_name": "2408", "name": "7-Zip 24.08"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir, patch(
            "py7zz.updater.CACHE_DIR", Path(tmpdir)
        ):
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
            with open(cache_file, "w") as f:
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
        """Test when cached binary exists in the nested per-arch layout."""
        mock_platform.return_value = ("linux", "x64")

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            # New layout: CACHE_DIR/{version}/{platform}-{arch}/{binary}
            arch_dir = cache_dir / "2408" / "linux-x64"
            arch_dir.mkdir(parents=True)
            binary_path = arch_dir / "7zz"
            binary_path.touch()

            with patch("py7zz.updater.CACHE_DIR", cache_dir):
                result = get_cached_binary("2408", auto_update=False)
                assert result == binary_path

    @patch("py7zz.updater.get_platform_info")
    def test_get_cached_binary_exists_mac_universal(self, mock_platform: Mock) -> None:
        """Test that macOS resolves to the literal 'mac-universal' arch dir."""
        mock_platform.return_value = ("mac", "arm64")

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            # Reason: mac asset is a universal binary, so arch dir is fixed.
            arch_dir = cache_dir / "2601" / "mac-universal"
            arch_dir.mkdir(parents=True)
            binary_path = arch_dir / "7zz"
            binary_path.touch()

            with patch("py7zz.updater.CACHE_DIR", cache_dir):
                result = get_cached_binary("2601", auto_update=False)
                assert result == binary_path

    @patch("py7zz.updater.get_platform_info")
    def test_get_cached_binary_exists_windows(self, mock_platform: Mock) -> None:
        """Test Windows resolves to '7zz.exe' inside the windows-x64 arch dir."""
        mock_platform.return_value = ("windows", "x64")

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            arch_dir = cache_dir / "2601" / "windows-x64"
            arch_dir.mkdir(parents=True)
            binary_path = arch_dir / "7zz.exe"
            binary_path.touch()
            # Reason: a complete Windows cache entry requires the sibling dll.
            (arch_dir / "7z.dll").touch()

            with patch("py7zz.updater.CACHE_DIR", cache_dir):
                result = get_cached_binary("2601", auto_update=False)
                assert result == binary_path

    @patch("py7zz.updater.get_platform_info")
    def test_get_cached_binary_not_exists_no_update(self, mock_platform: Mock) -> None:
        """Test when cached binary doesn't exist and auto_update is False."""
        mock_platform.return_value = ("linux", "x64")

        with tempfile.TemporaryDirectory() as tmpdir, patch(
            "py7zz.updater.CACHE_DIR", Path(tmpdir)
        ):
            result = get_cached_binary("2408", auto_update=False)
            assert result is None

    @patch("py7zz.updater.cleanup_old_versions")
    @patch("py7zz.updater.download_and_extract_binary")
    @patch("py7zz.updater.get_platform_info")
    def test_get_cached_binary_download_success(
        self,
        mock_platform: Mock,
        mock_download: Mock,
        mock_cleanup: Mock,
    ) -> None:
        """Test a cache miss triggers download and post-download cleanup."""
        mock_platform.return_value = ("linux", "x64")

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            arch_dir = cache_dir / "2601" / "linux-x64"
            downloaded = arch_dir / "7zz"

            def fake_download(version, platform, arch, target_dir):
                # Simulate the download materializing the binary on a cache miss.
                target_dir.mkdir(parents=True, exist_ok=True)
                downloaded.touch()
                return downloaded

            mock_download.side_effect = fake_download

            with patch("py7zz.updater.CACHE_DIR", cache_dir):
                result = get_cached_binary("26.01", auto_update=True)

            assert result == downloaded
            # download_and_extract_binary receives the dotted release tag (for the
            # URL) + the leaf dir (whose name is the dotless cache tag).
            mock_download.assert_called_once_with("26.01", "linux", "x64", arch_dir)
            # Reason: cleanup only runs after a successful download.
            mock_cleanup.assert_called_once_with(keep_count=3)

    @patch("py7zz.updater.cleanup_old_versions")
    @patch("py7zz.updater.download_and_extract_binary")
    @patch("py7zz.updater.get_platform_info")
    def test_get_cached_binary_dotless_input_normalized_to_dotted_tag(
        self,
        mock_platform: Mock,
        mock_download: Mock,
        mock_cleanup: Mock,
    ) -> None:
        """Test a dotless version input is converted back to the dotted tag."""
        mock_platform.return_value = ("linux", "x64")

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            arch_dir = cache_dir / "2601" / "linux-x64"
            downloaded = arch_dir / "7zz"

            def fake_download(version, platform, arch, target_dir):
                target_dir.mkdir(parents=True, exist_ok=True)
                downloaded.touch()
                return downloaded

            mock_download.side_effect = fake_download

            with patch("py7zz.updater.CACHE_DIR", cache_dir):
                result = get_cached_binary("2601", auto_update=True)

            assert result == downloaded
            # Reason: a dotless input must still yield the dotted release tag,
            # otherwise the download URL would 404.
            mock_download.assert_called_once_with("26.01", "linux", "x64", arch_dir)

    @patch("py7zz.updater.get_platform_info")
    def test_get_cached_binary_rejects_unrecognized_version_format(
        self, mock_platform: Mock
    ) -> None:
        """Test an unparseable version string raises UpdateError early."""
        mock_platform.return_value = ("linux", "x64")

        for bad_version in ("26011", "abc", ""):
            with pytest.raises(UpdateError, match="Unrecognized 7zz version"):
                get_cached_binary(bad_version)

    @patch("py7zz.updater.cleanup_old_versions")
    @patch("py7zz.updater.download_and_extract_binary")
    @patch("py7zz.updater.get_platform_info")
    def test_get_cached_binary_download_failure_returns_none(
        self,
        mock_platform: Mock,
        mock_download: Mock,
        mock_cleanup: Mock,
    ) -> None:
        """Test a failed download returns None and skips cleanup."""
        mock_platform.return_value = ("linux", "x64")
        mock_download.side_effect = UpdateError("network down")

        with tempfile.TemporaryDirectory() as tmpdir, patch(
            "py7zz.updater.CACHE_DIR", Path(tmpdir)
        ):
            result = get_cached_binary("2601", auto_update=True)

        assert result is None
        # Reason: a transient failure must never delete usable cached binaries.
        mock_cleanup.assert_not_called()


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


class TestPinnedVersion:
    """Test reading the pinned 7zz version file (auto-download source of truth)."""

    def test_get_pinned_7zz_version_reads_packaged_file(self) -> None:
        """Test the real packaged 7zz_version.txt is read and dotted."""
        version = get_pinned_7zz_version()
        # The shipped file currently pins 26.01; assert the dotted shape.
        assert isinstance(version, str)
        assert "." in version
        # Sanity: it should normalize to a digit-only tag form.
        assert version.replace(".", "").isdigit()

    def test_get_pinned_7zz_version_missing_file(self) -> None:
        """Test a missing version file raises UpdateError."""
        fake = Path("/nonexistent/py7zz/7zz_version.txt")
        with patch("py7zz.updater.PINNED_VERSION_FILE", fake), pytest.raises(
            UpdateError, match="not found"
        ):
            get_pinned_7zz_version()

    def test_get_pinned_7zz_version_empty_file(self) -> None:
        """Test an empty version file raises UpdateError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            empty = Path(tmpdir) / "7zz_version.txt"
            empty.write_text("   \n", encoding="utf-8")
            with patch("py7zz.updater.PINNED_VERSION_FILE", empty), pytest.raises(
                UpdateError, match="empty"
            ):
                get_pinned_7zz_version()


class TestEnsureAvailable:
    """Test the auto-download entry point used by source installs."""

    @patch("py7zz.updater.get_cached_binary")
    @patch("py7zz.updater.get_pinned_7zz_version")
    def test_ensure_passes_dotted_version(
        self, mock_pinned: Mock, mock_cached: Mock
    ) -> None:
        """Test the dotted release tag is threaded through to get_cached_binary."""
        mock_pinned.return_value = "26.01"

        with tempfile.TemporaryDirectory() as tmpdir:
            binary = Path(tmpdir) / "7zz"
            binary.touch()
            mock_cached.return_value = binary

            result = ensure_7zz_available()

        assert result == binary
        # Reason: the dotted form is the GitHub release tag for download URLs;
        # normalization to the dotless cache tag happens inside get_cached_binary.
        mock_cached.assert_called_once_with("26.01", auto_update=True)

    @patch("py7zz.updater.get_cached_binary")
    @patch("py7zz.updater.get_pinned_7zz_version")
    def test_ensure_none_result_raises(
        self, mock_pinned: Mock, mock_cached: Mock
    ) -> None:
        """Test a None cache result is converted to a UpdateError."""
        mock_pinned.return_value = "26.01"
        mock_cached.return_value = None

        with pytest.raises(UpdateError, match="auto-download"):
            ensure_7zz_available()

    @patch("py7zz.updater.get_cached_binary")
    @patch("py7zz.updater.get_pinned_7zz_version")
    def test_ensure_missing_file_result_raises(
        self, mock_pinned: Mock, mock_cached: Mock
    ) -> None:
        """Test a returned path that does not exist raises UpdateError."""
        mock_pinned.return_value = "26.01"
        mock_cached.return_value = Path("/nonexistent/7zz")

        with pytest.raises(UpdateError, match="auto-download"):
            ensure_7zz_available()

    @patch(
        "py7zz.updater.get_pinned_7zz_version",
        side_effect=UpdateError("missing version file"),
    )
    def test_ensure_propagates_pinned_error(self, mock_pinned: Mock) -> None:
        """Test a pinned-version read failure propagates as UpdateError."""
        with pytest.raises(UpdateError, match="missing version file"):
            ensure_7zz_available()


class TestCacheCompleteness:
    """Test _is_cache_complete platform-specific torn-cache detection."""

    def test_missing_binary_is_incomplete(self) -> None:
        """Test a non-existent binary is reported incomplete."""
        with tempfile.TemporaryDirectory() as tmpdir:
            binary = Path(tmpdir) / "7zz"
            assert _is_cache_complete(binary, "linux") is False

    def test_unix_binary_present_is_complete(self) -> None:
        """Test a present unix binary needs no sibling files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            binary = Path(tmpdir) / "7zz"
            binary.touch()
            assert _is_cache_complete(binary, "linux") is True

    def test_windows_exe_without_dll_is_incomplete(self) -> None:
        """Test a lone 7zz.exe (torn/legacy state) is treated as a miss."""
        with tempfile.TemporaryDirectory() as tmpdir:
            binary = Path(tmpdir) / "7zz.exe"
            binary.touch()
            # No sibling 7z.dll -> incomplete.
            assert _is_cache_complete(binary, "windows") is False

    def test_windows_exe_with_dll_is_complete(self) -> None:
        """Test 7zz.exe plus sibling 7z.dll is a complete cache entry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            binary = Path(tmpdir) / "7zz.exe"
            binary.touch()
            (Path(tmpdir) / "7z.dll").touch()
            assert _is_cache_complete(binary, "windows") is True

    @patch("py7zz.updater.get_platform_info")
    def test_get_cached_binary_windows_exe_without_dll_is_miss(
        self, mock_platform: Mock
    ) -> None:
        """Test get_cached_binary treats exe-without-dll as a cache miss."""
        mock_platform.return_value = ("windows", "x64")

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            arch_dir = cache_dir / "2601" / "windows-x64"
            arch_dir.mkdir(parents=True)
            (arch_dir / "7zz.exe").touch()  # exe present, dll missing

            with patch("py7zz.updater.CACHE_DIR", cache_dir):
                # auto_update=False so the incomplete cache is reported as miss.
                result = get_cached_binary("2601", auto_update=False)
            assert result is None


class TestDownloadUrls:
    """Test full download URLs use the dotted release tag and dotless assets.

    Reason: the official ip7z/7zip release TAG is dotted ("26.01"); only that
    form 302-redirects, while the dotless form 404s. Asset names are dotless.
    These assert the EXACT full URLs to guard against a regression.
    """

    def test_unix_download_url_is_exact(self) -> None:
        """Test the linux asset URL keeps the dotted tag, dotless asset name."""
        captured: dict = {}

        def fake_download(url: str, dest: Path) -> None:
            captured["url"] = url
            raise UpdateError("stop after capturing url")

        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)
            with patch.object(dl, "download_to_file", side_effect=fake_download):
                with pytest.raises(UpdateError):
                    dl.extract_unix_binary(
                        "26.01", "linux", "x64", target_dir, target_dir / "7zz"
                    )

        assert (
            captured["url"]
            == "https://github.com/ip7z/7zip/releases/download/26.01/7z2601-linux-x64.tar.xz"
        )

    def test_windows_urls_are_exact(self) -> None:
        """Test the Windows bootstrap + SFX URLs keep the dotted tag."""
        urls: list = []

        def fake_download(url: str, dest: Path) -> None:
            urls.append(url)
            if "7zr.exe" in url:
                dest.write_bytes(b"BOOT")
                return
            # Stop before subprocess once both URLs are captured.
            raise UpdateError("stop after capturing urls")

        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir)
            with patch.object(dl, "download_to_file", side_effect=fake_download):
                with pytest.raises(UpdateError):
                    dl.extract_windows_binary(
                        "26.01", "x64", target_dir, target_dir / "7zz.exe"
                    )

        assert "https://github.com/ip7z/7zip/releases/download/26.01/7zr.exe" in urls
        assert (
            "https://github.com/ip7z/7zip/releases/download/26.01/7z2601-x64.exe"
            in urls
        )


class TestCleanupNestedLayout:
    """Test cleanup_old_versions with the nested per-arch cache layout."""

    def test_cleanup_keeps_recent_nested_versions(self) -> None:
        """Test old digit-named version dirs are pruned, recent ones kept."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            # Build a nested layout for several versions.
            for ver in ("2200", "2300", "2400", "2601"):
                leaf = cache_dir / ver / "linux-x64"
                leaf.mkdir(parents=True)
                (leaf / "7zz").touch()

            with patch("py7zz.updater.CACHE_DIR", cache_dir):
                cleanup_old_versions(keep_count=2)

            remaining = sorted(d.name for d in cache_dir.iterdir() if d.is_dir())
            # Keeps the two highest versions, removes the rest.
            assert remaining == ["2400", "2601"]

    def test_cleanup_ignores_non_digit_dirs(self) -> None:
        """Test non-version directories (e.g. cache metadata) are untouched."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            (cache_dir / "2601" / "linux-x64").mkdir(parents=True)
            (cache_dir / "not_a_version").mkdir()

            with patch("py7zz.updater.CACHE_DIR", cache_dir):
                cleanup_old_versions(keep_count=1)

            assert (cache_dir / "not_a_version").exists()
            assert (cache_dir / "2601").exists()

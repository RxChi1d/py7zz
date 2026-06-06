# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""Tests for the source-install auto-download tier (issue #31).

These tests exercise the reconnected auto-download path end to end without any
network access: ``requests`` and ``subprocess`` are mocked throughout. They
cover the Windows SFX extraction flow, atomic binary placement, the
``core.find_7z_binary`` tier-3 behavior, and the recursion regression guard.
"""

import hashlib
import io
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

import py7zz._download as dl
from py7zz.updater import UpdateError, download_and_extract_binary


@pytest.fixture(autouse=True)
def _reset_tier3_memo():
    """Reset core's memoized tier-3 binary path between tests.

    Reason: find_7z_binary memoizes the auto-downloaded path at module level;
    leaked state would let one test's temp path satisfy another test's lookup.
    """
    import py7zz.core as core

    core._cached_downloaded_binary = None
    yield
    core._cached_downloaded_binary = None


def _checksums_for(named_bytes: dict) -> dict:
    """Build a pinned-checksums mapping for canned asset bytes.

    Args:
        named_bytes: Mapping of asset name -> bytes the fake download writes.

    Returns:
        Mapping of asset name -> SHA-256 hex digest, suitable for patching
        ``read_pinned_checksums`` so live verification passes in tests.
    """
    return {
        name: hashlib.sha256(data).hexdigest() for name, data in named_bytes.items()
    }


def _fake_download_factory(file_contents: dict):
    """Build a download_to_file stand-in that writes canned bytes per URL.

    Args:
        file_contents: Mapping of URL substring -> bytes to write at dest.

    Returns:
        A function with the same signature as ``download_to_file``.
    """

    def _fake_download(url: str, dest: Path) -> None:
        for needle, data in file_contents.items():
            if needle in url:
                dest.write_bytes(data)
                return
        # Reason: mirror real behavior where an unknown asset 404s.
        raise UpdateError(f"Failed to download {url}: not found")

    return _fake_download


class TestWindowsExtraction:
    """Test the Windows SFX (7zr.exe) extraction branch."""

    def _run(self, tmpdir: str, run_side_effect=None, run_return=None, drop_dll=False):
        """Drive extract_windows_binary with mocked downloads + subprocess.

        Args:
            tmpdir: Temporary cache directory.
            run_side_effect: Optional exception to raise from subprocess.run.
            run_return: Optional Mock to return from subprocess.run.
            drop_dll: If True, the simulated extraction omits 7z.dll.

        Returns:
            The (result_or_exc, mock_run) tuple for assertions.
        """
        target_dir = Path(tmpdir) / "2601" / "windows-x64"
        target_dir.mkdir(parents=True)
        binary_path = target_dir / "7zz.exe"

        canned = {"7zr.exe": b"BOOTSTRAP", "7z2601-x64.exe": b"SFX"}
        fake_download = _fake_download_factory(canned)
        # Reason: pass the dotted release tag ("26.01"); the dotless asset name
        # ("7z2601-x64.exe") is derived internally by get_asset_name.
        release_tag = "26.01"

        def fake_run(cmd, *args, **kwargs):
            # Simulate 7zr.exe writing 7z.exe (+ 7z.dll) into the -o dir.
            out_arg = next(a for a in cmd if a.startswith("-o"))
            out_dir = Path(out_arg[2:])
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "7z.exe").write_bytes(b"REAL7ZEXE")
            if not drop_dll:
                (out_dir / "7z.dll").write_bytes(b"REAL7ZDLL")
            return run_return if run_return is not None else Mock(returncode=0)

        # Reason: checksum verification stays LIVE in these tests; the pinned
        # digests are simply swapped for the canned bytes' real digests.
        with patch.object(dl, "download_to_file", side_effect=fake_download), patch(
            "py7zz._download.read_pinned_checksums",
            return_value=_checksums_for(canned),
        ), patch(
            "subprocess.run",
            side_effect=run_side_effect if run_side_effect else fake_run,
        ) as mock_run:
            return (
                dl.extract_windows_binary(release_tag, "x64", target_dir, binary_path),
                mock_run,
                binary_path,
                target_dir,
            )

    def test_windows_extraction_success(self) -> None:
        """Test a successful run places both 7zz.exe and 7z.dll."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result, mock_run, binary_path, target_dir = self._run(tmpdir)

            assert result == binary_path
            assert binary_path.exists()
            assert binary_path.read_bytes() == b"REAL7ZEXE"
            assert (target_dir / "7z.dll").exists()
            assert (target_dir / "7z.dll").read_bytes() == b"REAL7ZDLL"

            # 7zr.exe invoked with the documented extraction arguments. The
            # bootstrap path is a per-process unique temp file in target_dir.
            cmd = mock_run.call_args[0][0]
            assert cmd[0].endswith(".tmp")
            assert str(target_dir) in cmd[0]
            assert cmd[1] == "x"
            assert "-y" in cmd
            assert any(a.startswith("-o") for a in cmd)

    def test_windows_extraction_cleans_temp_files(self) -> None:
        """Test temp downloads and extraction dir are removed on success.

        Unique per-process staging files use random mkstemp names, so assert
        that only the published binaries (7zz.exe + 7z.dll) remain.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            _, _, _, target_dir = self._run(tmpdir)

            remaining = sorted(p.name for p in target_dir.iterdir())
            assert remaining == ["7z.dll", "7zz.exe"]

    def test_windows_extraction_subprocess_nonzero(self) -> None:
        """Test a non-zero 7zr.exe exit raises an actionable UpdateError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bad = Mock(returncode=2, stderr=b"boom")
            with pytest.raises(UpdateError, match="pip install py7zz"):
                self._run(tmpdir, run_return=bad)

    def test_windows_extraction_subprocess_timeout(self) -> None:
        """Test a subprocess timeout raises UpdateError with guidance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            timeout = subprocess.TimeoutExpired(cmd="7zr", timeout=120)
            with pytest.raises(UpdateError, match="PY7ZZ_BINARY"):
                self._run(tmpdir, run_side_effect=timeout)

    def test_windows_extraction_missing_dll(self) -> None:
        """Test a missing 7z.dll after extraction is a hard failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(UpdateError, match="7z.dll not found"):
                self._run(tmpdir, drop_dll=True)


class TestAtomicPlacement:
    """Test atomic binary placement helpers."""

    def test_atomic_place_uses_os_replace(self) -> None:
        """Test final placement goes through os.replace (atomic swap)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "source"
            src.write_bytes(b"DATA")
            target = Path(tmpdir) / "dest" / "7zz"

            with patch("py7zz._download.os.replace") as mock_replace:
                dl.atomic_place(src, target)
                assert mock_replace.called
                # Final arg of os.replace is the authoritative target path.
                assert mock_replace.call_args[0][1] == str(target)

    def test_atomic_place_sets_mode(self) -> None:
        """Test the executable mode is applied on placement."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "source"
            src.write_bytes(b"DATA")
            target = Path(tmpdir) / "7zz"

            dl.atomic_place(src, target, mode=0o755)

            assert target.exists()
            # Reason: Windows has no POSIX permission bits; chmod is a no-op
            # there, so only assert the executable mode on POSIX platforms.
            if sys.platform != "win32":
                assert (target.stat().st_mode & 0o777) == 0o755

    def test_unix_extraction_happy_path_places_executable(self) -> None:
        """Test a real tar.xz containing 7zz lands at target with mode 0o755."""
        # Build an in-memory tar.xz fixture with a single '7zz' member.
        buf = io.BytesIO()
        payload = b"REAL7ZZBINARY"
        with tarfile.open(fileobj=buf, mode="w:xz") as tar:
            info = tarfile.TarInfo(name="7zz")
            info.size = len(payload)
            tar.addfile(info, io.BytesIO(payload))
        fixture_bytes = buf.getvalue()

        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir) / "2601" / "linux-x64"
            target_dir.mkdir(parents=True)
            binary_path = target_dir / "7zz"

            def fake_download(url: str, dest: Path) -> None:
                # Copy the in-memory fixture to the requested download dest.
                dest.write_bytes(fixture_bytes)

            with patch.object(dl, "download_to_file", side_effect=fake_download), patch(
                "py7zz._download.read_pinned_checksums",
                return_value=_checksums_for({"7z2601-linux-x64.tar.xz": fixture_bytes}),
            ):
                result = dl.extract_unix_binary(
                    "26.01", "linux", "x64", target_dir, binary_path
                )

            assert result == binary_path
            assert binary_path.exists()
            assert binary_path.read_bytes() == payload
            # Reason: Windows has no POSIX permission bits; chmod is a no-op
            # there, so only assert the executable mode on POSIX platforms.
            if sys.platform != "win32":
                assert (binary_path.stat().st_mode & 0o777) == 0o755
            # Only the published binary remains; temp staging is cleaned up.
            assert sorted(p.name for p in target_dir.iterdir()) == ["7zz"]

    def test_unix_extraction_no_partial_on_failure(self) -> None:
        """Test a failed unix extraction leaves no binary at the final path."""
        target_dir = None
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir) / "2601" / "linux-x64"
            target_dir.mkdir(parents=True)
            binary_path = target_dir / "7zz"

            # Simulate a download that writes an invalid (non-tar) archive.
            # Reason: its checksum is pinned to match so the failure exercised
            # here is the tar-extraction error path, not checksum rejection.
            bad_bytes = b"not a tar archive"

            def fake_download(url: str, dest: Path) -> None:
                dest.write_bytes(bad_bytes)

            with patch.object(dl, "download_to_file", side_effect=fake_download), patch(
                "py7zz._download.read_pinned_checksums",
                return_value=_checksums_for({"7z2601-linux-x64.tar.xz": bad_bytes}),
            ):
                with pytest.raises(UpdateError):
                    dl.extract_unix_binary(
                        "2601", "linux", "x64", target_dir, binary_path
                    )

            # No partial/temp artifacts and no final binary remain.
            assert not binary_path.exists()
            assert list(target_dir.iterdir()) == []


class TestDownloadDispatch:
    """Test download_and_extract_binary routing and early-return."""

    def test_early_return_when_present(self) -> None:
        """Test an existing binary short-circuits without downloading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir) / "2601" / "linux-x64"
            target_dir.mkdir(parents=True)
            existing = target_dir / "7zz"
            existing.touch()

            # If download were attempted it would raise; absence proves skip.
            with patch.object(
                dl, "download_to_file", side_effect=AssertionError("no download")
            ):
                result = download_and_extract_binary("2601", "linux", "x64", target_dir)
            assert result == existing

    def test_routes_to_windows_branch(self) -> None:
        """Test the windows platform dispatches to extract_windows_binary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir) / "2601" / "windows-x64"
            sentinel = target_dir / "7zz.exe"

            with patch(
                "py7zz._download.extract_windows_binary", return_value=sentinel
            ) as mock_win, patch("py7zz._download.extract_unix_binary") as mock_unix:
                result = download_and_extract_binary(
                    "2601", "windows", "x64", target_dir
                )

            assert result == sentinel
            mock_win.assert_called_once()
            mock_unix.assert_not_called()


class TestCoreTier3:
    """Test core.find_7z_binary tier-3 auto-download integration."""

    def test_auto_download_success_returns_cached(self) -> None:
        """Test a missing bundled binary triggers auto-download success."""
        import py7zz.core as core

        with tempfile.TemporaryDirectory() as tmpdir:
            cached = Path(tmpdir) / "7zz"
            cached.touch()  # the cached download is a real, existing file

            real_exists = Path.exists

            def selective_exists(self):
                # Only the auto-downloaded cached binary exists; the bundled
                # path (and any env binary) is reported missing.
                if str(self) == str(cached):
                    return real_exists(self)
                return False

            with patch.dict("os.environ", {}, clear=False) as _env, patch.object(
                core.Path, "exists", selective_exists
            ):
                _env.pop("PY7ZZ_NO_AUTODOWNLOAD", None)
                _env.pop("PY7ZZ_BINARY", None)
                with patch("py7zz.updater.ensure_7zz_available", return_value=cached):
                    result = core.find_7z_binary()

            assert result == str(cached)

    def test_auto_download_failure_raises_runtime_error(self) -> None:
        """Test auto-download failure falls through to RuntimeError."""
        import py7zz.core as core

        with patch.dict("os.environ", {}, clear=False) as _env:
            _env.pop("PY7ZZ_NO_AUTODOWNLOAD", None)
            _env.pop("PY7ZZ_BINARY", None)
            with patch.object(core.Path, "exists", return_value=False), patch(
                "py7zz.updater.ensure_7zz_available",
                side_effect=UpdateError("no network"),
            ):
                with pytest.raises(RuntimeError, match="pip install py7zz"):
                    core.find_7z_binary()

    def test_auto_download_result_is_memoized(self) -> None:
        """Test the tier-3 resolution runs once per process on a warm cache."""
        import py7zz.core as core

        with tempfile.TemporaryDirectory() as tmpdir:
            cached = Path(tmpdir) / "7zz"
            cached.touch()

            real_exists = Path.exists

            def selective_exists(self):
                if str(self) == str(cached):
                    return real_exists(self)
                return False

            with patch.dict("os.environ", {}, clear=False) as _env, patch.object(
                core.Path, "exists", selective_exists
            ):
                _env.pop("PY7ZZ_NO_AUTODOWNLOAD", None)
                _env.pop("PY7ZZ_BINARY", None)
                with patch(
                    "py7zz.updater.ensure_7zz_available", return_value=cached
                ) as mock_ensure:
                    first = core.find_7z_binary()
                    second = core.find_7z_binary()

            assert first == second == str(cached)
            # Reason: the second call must hit the memo, not re-resolve.
            mock_ensure.assert_called_once()

    def test_memoized_path_revalidated_when_deleted(self) -> None:
        """Test a stale memoized path (file deleted) triggers re-resolution."""
        import py7zz.core as core

        with tempfile.TemporaryDirectory() as tmpdir:
            cached = Path(tmpdir) / "7zz"
            cached.touch()
            core._cached_downloaded_binary = str(cached)
            cached.unlink()  # the memoized file vanishes

            with patch.dict("os.environ", {}, clear=False) as _env:
                _env.pop("PY7ZZ_NO_AUTODOWNLOAD", None)
                _env.pop("PY7ZZ_BINARY", None)
                with patch.object(core.Path, "exists", return_value=False), patch(
                    "py7zz.updater.ensure_7zz_available",
                    side_effect=UpdateError("no network"),
                ) as mock_ensure:
                    with pytest.raises(RuntimeError):
                        core.find_7z_binary()
            # Reason: a dead memo must fall through to a fresh resolution.
            mock_ensure.assert_called_once()

    def test_opt_out_skips_auto_download(self) -> None:
        """Test PY7ZZ_NO_AUTODOWNLOAD skips ensure_7zz_available entirely."""
        import py7zz.core as core

        with patch.dict(
            "os.environ", {"PY7ZZ_NO_AUTODOWNLOAD": "1"}, clear=False
        ) as _env:
            _env.pop("PY7ZZ_BINARY", None)
            with patch.object(core.Path, "exists", return_value=False), patch(
                "py7zz.updater.ensure_7zz_available"
            ) as mock_ensure:
                with pytest.raises(RuntimeError):
                    core.find_7z_binary()
            # Reason: air-gapped/CI opt-out must not attempt any network call.
            mock_ensure.assert_not_called()


class TestAutoDownloadOptOutParsing:
    """Test PY7ZZ_NO_AUTODOWNLOAD truthy/falsey parsing semantics (FIX E)."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("1", True),
            ("true", True),
            ("TRUE", True),
            ("yes", True),
            ("on", True),
            ("  1  ", True),
            ("0", False),
            ("false", False),
            ("no", False),
            ("", False),
            ("random", False),
        ],
    )
    def test_disabled_only_on_explicit_truthy(self, value: str, expected: bool) -> None:
        """Test only explicit truthy values disable auto-download."""
        import py7zz.core as core

        with patch.dict("os.environ", {"PY7ZZ_NO_AUTODOWNLOAD": value}, clear=False):
            assert core._autodownload_disabled() is expected

    def test_unset_leaves_enabled(self) -> None:
        """Test an unset variable leaves auto-download enabled."""
        import py7zz.core as core

        with patch.dict("os.environ", {}, clear=False) as _env:
            _env.pop("PY7ZZ_NO_AUTODOWNLOAD", None)
            assert core._autodownload_disabled() is False

    def test_falsey_value_still_attempts_autodownload(self) -> None:
        """Test PY7ZZ_NO_AUTODOWNLOAD=0 does NOT skip ensure_7zz_available."""
        import py7zz.core as core

        with patch.dict(
            "os.environ", {"PY7ZZ_NO_AUTODOWNLOAD": "0"}, clear=False
        ) as _env:
            _env.pop("PY7ZZ_BINARY", None)
            with patch.object(core.Path, "exists", return_value=False), patch(
                "py7zz.updater.ensure_7zz_available",
                side_effect=UpdateError("no network"),
            ) as mock_ensure:
                with pytest.raises(RuntimeError):
                    core.find_7z_binary()
            # Reason: "0" is falsey, so auto-download must still be attempted.
            mock_ensure.assert_called_once()


class TestRecursionRegression:
    """Guard against the 0fef8b6 recursion loop in source installs."""

    def test_find_7z_binary_no_recursion_error(self) -> None:
        """Test a source install with no binary fails promptly, not recursively.

        Simulates: no PY7ZZ_BINARY, no bundled binary, network mocked to fail.
        The previous bug recursed find_7z_binary -> get_bundled_7zz_version ->
        get_version_info -> detect_7zz_version -> find_7z_binary. This asserts a
        clean RuntimeError rather than a RecursionError.
        """
        import py7zz.core as core

        with patch.dict("os.environ", {}, clear=False) as _env:
            _env.pop("PY7ZZ_NO_AUTODOWNLOAD", None)
            _env.pop("PY7ZZ_BINARY", None)
            # No bundled binary anywhere.
            with patch.object(core.Path, "exists", return_value=False), patch(
                # Network failure at the lowest level keeps the real call chain
                # intact (get_pinned_7zz_version -> get_cached_binary -> ...).
                "py7zz._download.download_to_file",
                side_effect=UpdateError("network unreachable"),
            ), patch("py7zz.updater.cleanup_old_versions"):
                try:
                    core.find_7z_binary()
                except RecursionError:  # pragma: no cover - regression guard
                    pytest.fail("find_7z_binary recursed (issue #31 regression)")
                except RuntimeError as e:
                    assert "pip install py7zz" in str(e)

    def test_get_version_info_uses_pinned_file_no_recursion(self) -> None:
        """Test bundled_info fallback reads the pinned file without recursing."""
        from py7zz import bundled_info

        # Force the registry-miss fallback branch.
        with patch.object(bundled_info, "get_version", return_value="9.9.9"), patch(
            "py7zz.bundled_info.read_pinned_7zz_version", return_value="26.01"
        ) as mock_pinned, patch(
            "py7zz.core.find_7z_binary",
            side_effect=AssertionError("must not call find_7z_binary"),
        ):
            info = bundled_info.get_version_info()

        assert info["bundled_7zz_version"] == "26.01"
        mock_pinned.assert_called_once()

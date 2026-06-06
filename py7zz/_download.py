# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""Low-level download and extraction helpers for the auto-update tier.

This module holds the platform-specific download/extract routines used by
``py7zz.updater``. It is kept separate to keep ``updater.py`` under the
500-line module limit. The functions here perform atomic, crash-safe binary
placement into the per-user cache.
"""

import hashlib
import os
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Optional

import requests

from ._pinned import read_pinned_checksums

# Reason: import from .updater at module load is safe because updater imports
# this module only inside function bodies, avoiding a circular import at import
# time.
from .updater import GITHUB_RELEASES_URL, UpdateError, get_asset_name


def download_to_file(url: str, dest: Path) -> None:
    """Stream-download a URL to a destination file.

    Args:
        url: Direct download URL.
        dest: Destination path (parent must exist).

    Raises:
        UpdateError: If the download fails.
    """
    try:
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    except requests.RequestException as e:
        raise UpdateError(f"Failed to download {url}: {e}") from e


def verify_checksum(path: Path, asset_name: str) -> None:
    """Verify a downloaded file against the pinned SHA-256 checksum.

    Args:
        path: Downloaded file to verify.
        asset_name: Release asset filename used to look up the pinned digest
            in ``py7zz/7zz_checksums.txt``.

    Raises:
        UpdateError: If no checksum is pinned for the asset (fail closed), or
            if the computed digest does not match the pinned one.

    Note:
        Verification happens after download and BEFORE any extraction or
        execution of the file. # Reason: a compromised upstream asset must be
        rejected before tarfile/7zr.exe ever touch it.
    """
    expected = read_pinned_checksums().get(asset_name)
    if expected is None:
        raise UpdateError(
            f"No pinned SHA-256 checksum for {asset_name}; refusing to use the "
            "downloaded file. The py7zz installation may be corrupt or the "
            "checksum file out of sync with 7zz_version.txt."
        )

    sha256 = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                sha256.update(chunk)
    except OSError as e:
        raise UpdateError(
            f"Failed to read {path} for checksum verification: {e}"
        ) from e

    actual = sha256.hexdigest()
    if actual != expected:
        raise UpdateError(
            f"SHA-256 mismatch for {asset_name}: expected {expected}, got "
            f"{actual}. The download may be corrupted or tampered with; "
            "refusing to use it."
        )


def _find_extracted_member(extract_dir: Path, name: str) -> Optional[Path]:
    """Locate an extracted installer member deterministically.

    Prefers the exact top-level path (the layout official installers ship),
    falling back to a sorted recursive search so the choice stays
    deterministic even if a future installer layout nests or duplicates
    files.

    Args:
        extract_dir: Directory the installer was extracted into.
        name: Member filename to locate (e.g. ``"7z.exe"``).

    Returns:
        Path to the member, or ``None`` if not found.
    """
    direct = extract_dir / name
    if direct.is_file():
        return direct
    # Reason: sorted() pins the selection order; bare next(rglob()) depends on
    # filesystem iteration order and could silently pick a different copy.
    matches = sorted(p for p in extract_dir.rglob(name) if p.is_file())
    return matches[0] if matches else None


def atomic_place(source: Path, target: Path, mode: Optional[int] = None) -> None:
    """Atomically place a file at its final cache location.

    The file is staged via a temporary file in the SAME directory as the
    target and then moved with ``os.replace``, which is atomic on both POSIX
    and Windows.

    Args:
        source: Existing file to move into place.
        target: Final destination path.
        mode: Optional permission bits to apply (e.g. ``0o755``).

    Raises:
        UpdateError: If the atomic placement fails.
    """
    tmp_path: Optional[Path] = None
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        # Reason: tempfile in the same directory guarantees os.replace stays on
        # one filesystem, keeping the swap atomic and crash-safe.
        fd, tmp_name = tempfile.mkstemp(dir=str(target.parent))
        os.close(fd)
        tmp_path = Path(tmp_name)
        shutil.move(str(source), str(tmp_path))
        if mode is not None:
            tmp_path.chmod(mode)
        os.replace(str(tmp_path), str(target))
        tmp_path = None  # Published; nothing left to clean up.
    except OSError as e:
        raise UpdateError(f"Failed to place binary at {target}: {e}") from e
    finally:
        # Reason: a failure between mkstemp and os.replace must not leave a
        # stray staging file behind in the cache directory.
        if tmp_path is not None and tmp_path.exists():
            tmp_path.unlink()


def extract_unix_binary(
    release_tag: str, platform: str, arch: str, target_dir: Path, binary_path: Path
) -> Path:
    """Download and extract the 7zz binary from a Unix tar.xz asset.

    Args:
        release_tag: GitHub release tag in dotted form (e.g. ``"26.01"``) used
            as the URL path segment. Asset names are normalized to the dotless
            form (``7z2601-...``) by ``get_asset_name``.
        platform: Platform name (``"mac"`` or ``"linux"``).
        arch: Architecture string.
        target_dir: Per-arch cache directory.
        binary_path: Final path for the extracted ``7zz`` binary.

    Returns:
        Path to the extracted, executable 7zz binary.

    Raises:
        UpdateError: If download or extraction fails.
    """
    asset_name = get_asset_name(release_tag, platform, arch)
    download_url = f"{GITHUB_RELEASES_URL}/{release_tag}/{asset_name}"

    # Reason: per-process unique temp names let two concurrent first-use
    # processes share the cache dir without corrupting each other's staging.
    fd_archive, archive_name = tempfile.mkstemp(dir=str(target_dir), suffix=".tmp")
    os.close(fd_archive)
    fd_extract, extract_name = tempfile.mkstemp(dir=str(target_dir), suffix=".tmp")
    os.close(fd_extract)
    tmp_archive = Path(archive_name)
    extracted_tmp = Path(extract_name)
    try:
        download_to_file(download_url, tmp_archive)
        verify_checksum(tmp_archive, asset_name)
        with tarfile.open(str(tmp_archive), "r:xz") as tar:
            for member in tar.getmembers():
                if member.name.endswith("/7zz") or member.name == "7zz":
                    src = tar.extractfile(member)
                    if src is None:
                        raise UpdateError(
                            f"Could not read 7zz binary from {asset_name}"
                        )
                    with src, open(extracted_tmp, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    break
            else:
                raise UpdateError(f"Could not find 7zz binary in {asset_name}")

        # Atomic placement with executable permissions.
        atomic_place(extracted_tmp, binary_path, mode=0o755)
        return binary_path
    except (tarfile.TarError, OSError) as e:
        raise UpdateError(f"Failed to extract {asset_name}: {e}") from e
    finally:
        tmp_archive.unlink(missing_ok=True)
        extracted_tmp.unlink(missing_ok=True)


def extract_windows_binary(
    release_tag: str, arch: str, target_dir: Path, binary_path: Path
) -> Path:
    """Download and extract the 7zz binary from a Windows SFX installer.

    The official Windows asset ``7z{ver}-{arch}.exe`` is a 7-Zip SFX
    installer. This function uses the version-pinned bootstrap extractor
    ``7zr.exe`` (also a release asset) to unpack ``7z.exe`` and ``7z.dll``,
    which are then placed as ``7zz.exe`` and ``7z.dll`` in the cache.

    Args:
        release_tag: GitHub release tag in dotted form (e.g. ``"26.01"``) used
            as the URL path segment. The SFX asset name is normalized to the
            dotless form (``7z2601-x64.exe``) by ``get_asset_name``.
        arch: Architecture string (``"x64"`` or ``"arm64"``).
        target_dir: Per-arch cache directory.
        binary_path: Final path for ``7zz.exe``.

    Returns:
        Path to the placed ``7zz.exe`` binary.

    Raises:
        UpdateError: If download, extraction, or placement fails.

    Note:
        ``7zr.exe`` runs only on Windows, so this branch executes only at
        runtime on Windows; there is no cross-platform concern.
    """
    asset_name = get_asset_name(release_tag, "windows", arch)
    sfx_url = f"{GITHUB_RELEASES_URL}/{release_tag}/{asset_name}"
    bootstrap_url = f"{GITHUB_RELEASES_URL}/{release_tag}/7zr.exe"

    dll_final = target_dir / "7z.dll"

    # Reason: per-process unique staging names + a unique extraction dir let two
    # concurrent first-use processes share the cache dir without clobbering each
    # other. The extraction dir lives on the same filesystem as the target, so
    # os.replace during atomic_place stays atomic.
    fd_boot, boot_name = tempfile.mkstemp(dir=str(target_dir), suffix=".tmp")
    os.close(fd_boot)
    fd_sfx, sfx_name = tempfile.mkstemp(dir=str(target_dir), suffix=".tmp")
    os.close(fd_sfx)
    bootstrap_path = Path(boot_name)
    sfx_path = Path(sfx_name)
    extract_tmpdir = tempfile.TemporaryDirectory(dir=str(target_dir))
    extract_dir = Path(extract_tmpdir.name)
    try:
        # a. Download and verify the version-pinned bootstrap extractor.
        # Reason: 7zr.exe is EXECUTED below, so its checksum must be verified
        # before it ever runs.
        download_to_file(bootstrap_url, bootstrap_path)
        verify_checksum(bootstrap_path, "7zr.exe")
        # b. Download and verify the SFX installer.
        download_to_file(sfx_url, sfx_path)
        verify_checksum(sfx_path, asset_name)

        # c. Let 7zr.exe unpack the SFX installer natively.
        try:
            result = subprocess.run(
                [
                    str(bootstrap_path),
                    "x",
                    str(sfx_path),
                    "-o" + str(extract_dir),
                    "-y",
                ],
                capture_output=True,
                timeout=120,
            )
        except (subprocess.SubprocessError, OSError) as e:
            raise UpdateError(
                f"Failed to run 7zr.exe to extract {asset_name}: {e}. "
                "Install a bundled wheel with 'pip install py7zz', or set "
                "PY7ZZ_BINARY to point at a working 7zz binary."
            ) from e

        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace")
            raise UpdateError(
                f"7zr.exe failed to extract {asset_name} (exit "
                f"{result.returncode}): {stderr}. Install a bundled wheel with "
                "'pip install py7zz', or set PY7ZZ_BINARY to a working 7zz binary."
            )

        # d. Locate 7z.exe and 7z.dll; both are required to run.
        exe_src = _find_extracted_member(extract_dir, "7z.exe")
        dll_src = _find_extracted_member(extract_dir, "7z.dll")
        if exe_src is None:
            raise UpdateError(
                f"7z.exe not found in extracted {asset_name}. Install a bundled "
                "wheel with 'pip install py7zz', or set PY7ZZ_BINARY."
            )
        if dll_src is None:
            # Reason: 7z.exe cannot run without 7z.dll, so a missing DLL is a
            # hard failure rather than a partial success.
            raise UpdateError(
                f"7z.dll not found in extracted {asset_name}. Install a bundled "
                "wheel with 'pip install py7zz', or set PY7ZZ_BINARY."
            )

        # Atomic placement: dll first, then 7z.exe -> 7zz.exe last.
        # Reason: the exe is the publication marker, so placing the dll first
        # guarantees a complete cache entry the moment the exe appears.
        atomic_place(dll_src, dll_final)
        atomic_place(exe_src, binary_path)
        return binary_path
    finally:
        # e. Clean up temporary downloads and extraction directory.
        bootstrap_path.unlink(missing_ok=True)
        sfx_path.unlink(missing_ok=True)
        extract_tmpdir.cleanup()

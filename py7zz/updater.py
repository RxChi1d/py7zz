# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""Auto-download module for py7zz.

This module resolves the pinned 7zz binary for source installs, downloading
and caching it from the official GitHub releases on first use. Downloads are
verified against the SHA-256 checksums pinned in ``py7zz/7zz_checksums.txt``.
"""

import platform
import shutil
from pathlib import Path
from typing import Optional, Tuple

from ._pinned import read_pinned_7zz_version
from ._platform_spec import MACHINE_TO_ARCH, PLATFORM_SPECS, SYSTEM_TO_PLATFORM
from .logging_config import get_logger

# GitHub release download configuration
GITHUB_RELEASES_URL = "https://github.com/ip7z/7zip/releases/download"
CACHE_DIR = Path.home() / ".cache" / "py7zz"

logger = get_logger(__name__)


class UpdateError(Exception):
    """Raised when update operations fail."""

    pass


def get_pinned_7zz_version() -> str:
    """Read the 7zz version pinned for this py7zz build.

    The version is read from ``py7zz/7zz_version.txt`` (e.g. ``"26.01"``), a
    git-tracked file shipped in both wheel and sdist distributions. This is the
    single source of truth for the auto-download tier.

    Returns:
        Pinned 7zz version string in dotted form (e.g. ``"26.01"``).

    Raises:
        UpdateError: If the version file is missing or empty.

    Note:
        This function intentionally avoids importing ``bundled_info`` or any
        binary-version detection. # Reason: the auto-download path must not
        re-enter find_7z_binary, which previously caused a recursion loop
        (find_7z_binary -> get_bundled_7zz_version -> get_version_info ->
        detect_7zz_version -> find_7z_binary).
    """
    version = read_pinned_7zz_version()
    if version is None:
        raise UpdateError(
            f"Pinned 7zz version file at {Path(__file__).parent / '7zz_version.txt'} "
            "is missing or empty; cannot determine which 7zz version to download."
        )
    return version


def ensure_7zz_available() -> Path:
    """Ensure a runnable 7zz binary is available, downloading it if needed.

    This is the entry point for the auto-download tier used by source installs.
    It reads the pinned 7zz version (dotted form, e.g. ``"26.01"``) and resolves
    a cached binary, downloading and extracting it on a cache miss.

    Returns:
        Path to a ready-to-run 7zz binary in the per-user cache.

    Raises:
        UpdateError: If the pinned version cannot be read, or the binary cannot
            be downloaded/extracted.

    Note:
        The pinned version is threaded through downstream helpers in its dotted
        form. # Reason: the official ip7z/7zip release TAG used in download URLs
        is dotted ("26.01"); asset names are dotless ("7z2601-...") and are
        normalized only where filenames are built (get_asset_name).
    """
    pinned_version = get_pinned_7zz_version()

    binary_path = get_cached_binary(pinned_version, auto_update=True)
    if binary_path is None or not binary_path.exists():
        raise UpdateError(
            f"Failed to obtain 7zz {pinned_version} via auto-download. "
            "Install a bundled wheel with 'pip install py7zz', or set "
            "PY7ZZ_BINARY to point at a working 7zz binary."
        )

    return binary_path


def get_platform_info() -> Tuple[str, str]:
    """Get platform and architecture information for binary selection.

    Returns:
        Tuple of (platform, architecture) strings compatible with 7zz release naming.
    """
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system not in SYSTEM_TO_PLATFORM:
        raise UpdateError(f"Unsupported platform: {system}")

    if machine not in MACHINE_TO_ARCH:
        raise UpdateError(f"Unsupported architecture: {machine}")

    return SYSTEM_TO_PLATFORM[system], MACHINE_TO_ARCH[machine]


def get_asset_name(version: str, platform: str, arch: str) -> str:
    """Generate the correct asset name for a given version, platform, and architecture.

    Args:
        version: 7zz version string (e.g., "24.07" or "2408").
        platform: Platform name ("mac", "linux", "windows").
        arch: Architecture ("x64", "arm64").

    Returns:
        Asset filename for downloading from GitHub releases.

    Raises:
        UpdateError: If the platform is unsupported, or if the architecture is
            unsupported for the given platform.
    """
    # Convert version format if needed (24.07 -> 2407)
    if "." in version:
        version = version.replace(".", "")

    if platform == "windows":
        if arch == "x64":
            return f"7z{version}-x64.exe"
        elif arch == "arm64":
            return f"7z{version}-arm64.exe"
        else:
            raise UpdateError(f"Unsupported Windows architecture: {arch}")
    elif platform == "mac":
        # Reason: the official macOS archive is a universal binary covering both x64 and arm64.
        return f"7z{version}-mac.tar.xz"
    elif platform == "linux":
        if arch == "x64":
            return f"7z{version}-linux-x64.tar.xz"
        elif arch == "arm64":
            return f"7z{version}-linux-arm64.tar.xz"
        else:
            raise UpdateError(f"Unsupported Linux architecture: {arch}")
    else:
        raise UpdateError(f"Unsupported platform: {platform}")


def _is_cache_complete(binary_path: Path, platform: str) -> bool:
    """Check whether a cached binary entry is complete and runnable.

    Args:
        binary_path: Final path of the cached 7zz binary (``7zz`` or
            ``7zz.exe``).
        platform: Platform name (``"mac"``, ``"linux"``, ``"windows"``).

    Returns:
        ``True`` if the cache entry is complete for the platform, else
        ``False``.

    Note:
        On Windows the binary cannot run without its sibling ``7z.dll``, so a
        lone ``7zz.exe`` (a torn or legacy cache entry) must be treated as a
        miss. # Reason: the exe is published last and acts as the publication
        marker, so requiring the extra files guards against torn states.
    """
    if not binary_path.exists():
        return False
    spec = PLATFORM_SPECS.get(platform)
    if spec is None:
        return False
    return all((binary_path.parent / extra).exists() for extra in spec.extra_files)


def download_and_extract_binary(
    release_tag: str, platform: str, arch: str, target_dir: Path
) -> Path:
    """Download and extract the 7zz binary for a version and platform.

    Args:
        release_tag: GitHub release tag in dotted form (e.g. ``"26.01"``).
            This is the URL path segment; asset names are normalized to the
            dotless form internally.
        platform: Platform name (``"mac"``, ``"linux"``, ``"windows"``).
        arch: Architecture (``"x64"``, ``"arm64"``).
        target_dir: Per-arch cache directory to place the binary in.

    Returns:
        Path to the ready-to-run 7zz binary.

    Raises:
        UpdateError: If the binary cannot be downloaded or extracted.
    """
    # Reason: local import avoids a circular import, since _download imports
    # names from this module at its top level.
    from ._download import extract_unix_binary, extract_windows_binary

    if platform not in PLATFORM_SPECS:
        raise UpdateError(f"Unsupported platform: {platform}")
    target_path = target_dir / PLATFORM_SPECS[platform].binary_name

    # Skip if the cache entry is complete (Windows also needs the sibling dll).
    if _is_cache_complete(target_path, platform):
        return target_path

    target_dir.mkdir(parents=True, exist_ok=True)

    if platform == "windows":
        return extract_windows_binary(release_tag, arch, target_dir, target_path)
    return extract_unix_binary(release_tag, platform, arch, target_dir, target_path)


def get_cached_binary(version: str, auto_update: bool = True) -> Optional[Path]:
    """Get the cached 7zz binary for a version, downloading if necessary.

    The cache layout is ``CACHE_DIR/{tag}/{platform}-{arch}/{binary_name}``,
    where ``{tag}`` is the dotless, digit-only form (e.g. ``2601``) so the
    pruning logic in ``cleanup_old_versions`` can sort versions numerically.
    For macOS the official asset is a universal binary, so the literal arch
    directory ``universal`` is used (``.../mac-universal/``).

    Args:
        version: 7zz version string, dotted (``"26.01"``) or dotless
            (``"2601"``). The dotted form is used as the GitHub release tag for
            download URLs; the dotless form names the cache directory.
        auto_update: Whether to download the binary on a cache miss.

    Returns:
        Path to the cached binary, or ``None`` if not available and
        ``auto_update`` is ``False``, or if the download/cache is incomplete.
    """
    platform, arch = get_platform_info()
    spec = PLATFORM_SPECS[platform]

    # Reason: the GitHub release tag is dotted ("26.01") for URLs, but the cache
    # dir must be digit-only ("2601") so cleanup_old_versions can sort it. A
    # dotless input is converted back to the dotted tag (the 7-Zip version
    # format is always MAJOR.MINOR with two digits each); anything else would
    # build a 404 download URL, so reject it early.
    if "." in version:
        release_tag = version
    elif len(version) == 4 and version.isdigit():
        release_tag = f"{version[:2]}.{version[2:]}"
    else:
        raise UpdateError(
            f"Unrecognized 7zz version format: {version!r} "
            '(expected dotted "26.01" or dotless "2601")'
        )
    cache_tag = release_tag.replace(".", "")

    # Reason: the mac asset is a single universal binary covering x64 and arm64,
    # so a fixed 'universal' arch dir avoids duplicate per-arch downloads.
    arch_dir_name = spec.arch_dir or arch
    arch_dir = CACHE_DIR / cache_tag / f"{platform}-{arch_dir_name}"
    binary_path = arch_dir / spec.binary_name

    # Return cached binary only if the entry is complete for this platform.
    if _is_cache_complete(binary_path, platform):
        return binary_path

    if auto_update:
        try:
            result = download_and_extract_binary(release_tag, platform, arch, arch_dir)
            # Reason: prune stale versions only after a successful download so a
            # transient network failure never deletes a usable cached binary.
            cleanup_old_versions(keep_count=3)
            return result
        except UpdateError as e:
            logger.warning(f"Auto-download of 7zz {version} failed: {e}")
            return None

    return None


def cleanup_old_versions(keep_count: int = 3) -> None:
    """Clean up old cached versions, keeping only the most recent ones.

    Also removes leftovers from the pre-nested cache layout, which placed the
    binary directly at ``CACHE_DIR/{ver}/7zz`` instead of inside a
    ``{platform}-{arch}`` subdirectory. Those flat files are unreachable by
    the current resolution logic but would otherwise occupy keep slots
    forever.

    Args:
        keep_count: Number of versions to keep
    """
    if not CACHE_DIR.exists():
        return

    # Get all version directories
    version_dirs = [d for d in CACHE_DIR.iterdir() if d.is_dir() and d.name.isdigit()]

    # Sort by version number (descending)
    version_dirs.sort(key=lambda d: int(d.name), reverse=True)

    # Remove old versions
    for old_dir in version_dirs[keep_count:]:
        shutil.rmtree(old_dir, ignore_errors=True)

    # Purge flat-layout orphans from kept versions. Only the known binary
    # filenames are removed, never subdirectories, so the nested entries and
    # any in-flight staging directories are untouched.
    flat_orphan_names = {"7zz", "7zz.exe", "7z.dll"}
    for version_dir in version_dirs[:keep_count]:
        for orphan_name in flat_orphan_names:
            orphan = version_dir / orphan_name
            try:
                if orphan.is_file():
                    orphan.unlink()
            except OSError:
                # Reason: cache hygiene is best-effort; a locked or
                # permission-protected file must not break binary resolution.
                pass

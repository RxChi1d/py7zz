# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""Auto-update module for py7zz.

This module handles automatic downloading and caching of the latest 7zz binaries
from GitHub releases, with 24-hour caching and platform-specific binary resolution.
"""

import json
import os
import platform
import shutil
import tarfile
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests
from packaging.version import Version

# GitHub API configuration
GITHUB_API_URL = "https://api.github.com/repos/ip7z/7zip/releases"
GITHUB_RELEASES_URL = "https://github.com/ip7z/7zip/releases/download"
CACHE_DIR = Path.home() / ".cache" / "py7zz"
CACHE_TIMEOUT = 24 * 60 * 60  # 24 hours in seconds


class UpdateError(Exception):
    """Raised when update operations fail."""

    pass


def get_platform_info() -> Tuple[str, str]:
    """Get platform and architecture information for binary selection.

    Returns:
        Tuple of (platform, architecture) strings compatible with 7zz release naming.
    """
    system = platform.system().lower()
    machine = platform.machine().lower()

    # Map Python platform names to 7zz release naming
    platform_map = {"darwin": "mac", "linux": "linux", "windows": "windows"}

    # Map architecture names
    arch_map = {"x86_64": "x64", "amd64": "x64", "arm64": "arm64", "aarch64": "arm64"}

    if system not in platform_map:
        raise UpdateError(f"Unsupported platform: {system}")

    if machine not in arch_map:
        raise UpdateError(f"Unsupported architecture: {machine}")

    return platform_map[system], arch_map[machine]


def get_asset_name(version: str, platform: str, arch: str) -> str:
    """Generate the correct asset name for a given version and platform.

    Args:
        version: 7zz version string (e.g., "24.07" or "2408")
        platform: Platform name ("mac", "linux", "windows")
        arch: Architecture ("x64", "arm64")

    Returns:
        Asset filename for downloading from GitHub releases.
    """
    # Convert version format if needed (24.07 -> 2407)
    if "." in version:
        version = version.replace(".", "")

    if platform == "windows":
        return f"7z{version}-x64.exe"
    elif platform == "mac":
        return f"7z{version}-mac.tar.xz"
    elif platform == "linux":
        return f"7z{version}-linux-x64.tar.xz"
    else:
        raise UpdateError(f"Unsupported platform: {platform}")


def get_latest_release(use_cache: bool = True) -> Dict[str, Any]:
    """Get the latest 7zz release information from GitHub API.

    Args:
        use_cache: Whether to use cached release information if available.

    Returns:
        Dictionary containing release information.
    """
    cache_file = CACHE_DIR / "latest_release.json"

    # Check cache first
    if use_cache and cache_file.exists():
        cache_age = cache_file.stat().st_mtime
        if (cache_age + CACHE_TIMEOUT) > os.path.getmtime(__file__):
            try:
                with open(cache_file) as f:
                    return json.load(f)  # type: ignore[no-any-return]
            except (json.JSONDecodeError, OSError):
                pass  # Fall through to fetch from API

    # Fetch from GitHub API
    try:
        response = requests.get(f"{GITHUB_API_URL}/latest", timeout=10)
        response.raise_for_status()
        release_data = response.json()

        # Cache the response
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w") as f:
            json.dump(release_data, f, indent=2)

        return release_data  # type: ignore[no-any-return]

    except requests.RequestException as e:
        raise UpdateError(f"Failed to fetch release information: {e}") from e


def download_and_extract_binary(
    version: str, platform: str, arch: str, target_dir: Path
) -> Path:
    """Download and extract 7zz binary for specified version and platform.

    Args:
        version: 7zz version string
        platform: Platform name
        arch: Architecture
        target_dir: Directory to extract binary to

    Returns:
        Path to the extracted binary.
    """
    asset_name = get_asset_name(version, platform, arch)
    download_url = f"{GITHUB_RELEASES_URL}/{version}/{asset_name}"

    binary_name = "7zz.exe" if platform == "windows" else "7zz"
    target_path = target_dir / binary_name

    # Skip if already exists
    if target_path.exists():
        return target_path

    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Download asset
        response = requests.get(download_url, timeout=30, stream=True)
        response.raise_for_status()

        if platform == "windows":
            # Windows .exe file - direct download
            with open(target_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        else:
            # Unix tar.xz file - extract binary
            with tempfile.NamedTemporaryFile(
                suffix=".tar.xz", delete=False
            ) as tmp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp_file.write(chunk)
                tmp_file.flush()

                # Extract 7zz binary from tar.xz
                with tarfile.open(tmp_file.name, "r:xz") as tar:
                    # Find the 7zz binary in the archive
                    for member in tar.getmembers():
                        if member.name.endswith("/7zz") or member.name == "7zz":
                            src = tar.extractfile(member)
                            if src is not None:
                                with src, open(target_path, "wb") as dst:
                                    shutil.copyfileobj(src, dst)
                            break
                    else:
                        raise UpdateError(f"Could not find 7zz binary in {asset_name}")

                # Clean up temporary file
                os.unlink(tmp_file.name)

        # Make binary executable
        target_path.chmod(0o755)

        return target_path

    except requests.RequestException as e:
        raise UpdateError(f"Failed to download {asset_name}: {e}") from e
    except (tarfile.TarError, OSError) as e:
        raise UpdateError(f"Failed to extract {asset_name}: {e}") from e


def get_cached_binary(version: str, auto_update: bool = True) -> Optional[Path]:
    """Get cached binary for specified version, downloading if necessary.

    Args:
        version: 7zz version string
        auto_update: Whether to automatically download if not cached

    Returns:
        Path to cached binary, or None if not available and auto_update is False.
    """
    platform, arch = get_platform_info()
    binary_name = "7zz.exe" if platform == "windows" else "7zz"

    version_dir = CACHE_DIR / version
    binary_path = version_dir / binary_name

    # Return cached binary if it exists
    if binary_path.exists():
        return binary_path

    # Download if auto_update is enabled
    if auto_update:
        try:
            return download_and_extract_binary(version, platform, arch, version_dir)
        except UpdateError:
            return None

    return None


def check_for_updates(current_version: Optional[str] = None) -> Optional[str]:
    """Check if a newer version of 7zz is available.

    Args:
        current_version: Current version string, or None to always return latest

    Returns:
        Latest version string if newer than current, otherwise None.
    """
    try:
        release_data = get_latest_release()
        latest_version: str = release_data["tag_name"]

        if current_version is None:
            return latest_version

        # Compare versions
        if Version(latest_version) > Version(current_version):
            return latest_version

        return None

    except (UpdateError, ValueError):
        return None


def cleanup_old_versions(keep_count: int = 3) -> None:
    """Clean up old cached versions, keeping only the most recent ones.

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


def get_version_from_binary(binary_path: Path) -> Optional[str]:
    """Extract version string from 7zz binary output.

    Args:
        binary_path: Path to 7zz binary

    Returns:
        Version string if extractable, otherwise None.
    """
    try:
        import subprocess

        result = subprocess.run(
            [str(binary_path), "--help"], capture_output=True, text=True, timeout=5
        )

        # Parse version from help output
        for line in result.stdout.splitlines():
            if "7-Zip" in line and "Igor Pavlov" in line:
                # Extract version from line like "7-Zip 24.08 (x64) : Copyright (c) 1999-2024 Igor Pavlov"
                parts = line.split()
                if len(parts) >= 2:
                    version_str = parts[1]
                    # Convert "24.08" to "2408" format
                    try:
                        major, minor = version_str.split(".")
                        return f"{major}{minor.zfill(2)}"
                    except ValueError:
                        pass

        return None

    except (subprocess.SubprocessError, OSError):
        return None

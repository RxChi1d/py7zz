# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""
Bundled version information for py7zz package.

This module provides version registry and bundled information for the py7zz package,
supporting the new PEP 440 compliant version system.
"""

import re
import subprocess
from typing import Dict, Union

from .version import get_version, get_version_type

# Version registry containing all version information
VERSION_REGISTRY: Dict[str, Dict[str, Union[str, None]]] = {
    "0.1.0": {
        "7zz_version": "25.00",
        "release_date": "2024-12-15",
        "release_type": "stable",
        "github_tag": "v0.1.0",
        "changelog_url": "https://github.com/rxchi1d/py7zz/releases/tag/v0.1.0",
    },
    # Auto versions will be dynamically added by CI/CD
    # Example: "0.1.0a1": {"7zz_version": "24.08", ...}
    # Dev versions will be manually added
    # Example: "0.2.0.dev1": {"7zz_version": "24.08", ...}
}


def detect_7zz_version(binary_path: str) -> str:
    """
    Automatically detect the version of bundled 7zz binary.

    Args:
        binary_path: Path to the 7zz binary

    Returns:
        Detected 7zz version string or "unknown" if detection fails

    Example:
        >>> detect_7zz_version("/path/to/7zz")
        '25.00'
    """
    try:
        # Run 7zz without arguments to get help output with version info
        result = subprocess.run(
            [binary_path], capture_output=True, text=True, timeout=10
        )

        # Combine stdout and stderr as version info might be in either
        output = (result.stdout or "") + (result.stderr or "")

        # Parse version from output using regex patterns
        # Common patterns: "7-Zip 25.00", "7-zip 24.08", "7zip (z) 23.01"
        version_patterns = [
            r"7-?[Zz]ip\s*(?:\([^)]*\))?\s*(\d+\.\d+)",
            r"(\d+\.\d+)\s*\(.*7-?[Zz]ip",
            r"Version\s*:?\s*(\d+\.\d+)",
            r"v(\d+\.\d+)",
        ]

        for pattern in version_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return match.group(1)

        # If no pattern matches, return unknown
        return "unknown"

    except Exception:
        # If any error occurs during detection, return unknown
        return "unknown"


def get_version_info() -> Dict[str, Union[str, None]]:
    """
    Get detailed version information for the current py7zz version.

    Returns:
        Dictionary containing version information including:
        - py7zz_version: Current py7zz version
        - bundled_7zz_version: Bundled 7zz version
        - release_type: Type of release (stable, auto, dev)
        - release_date: Release date
        - github_tag: GitHub tag
        - changelog_url: URL to changelog

    Example:
        >>> get_version_info()
        {
            'py7zz_version': '0.1.0',
            'bundled_7zz_version': '24.07',
            'release_type': 'stable',
            'release_date': '2024-12-15',
            'github_tag': 'v0.1.0',
            'changelog_url': 'https://github.com/rxchi1d/py7zz/releases/tag/v0.1.0'
        }
    """
    current_version = get_version()
    info = VERSION_REGISTRY.get(current_version, {})

    # Use hybrid approach: registry first, then auto-detection
    bundled_7zz_version = info.get("7zz_version")
    if bundled_7zz_version is None:
        # Not in registry, try auto-detection
        try:
            from .core import find_7z_binary

            binary_path = find_7z_binary()
            bundled_7zz_version = detect_7zz_version(binary_path)
        except Exception:
            bundled_7zz_version = "unknown"

    # Determine release type: prefer registry, otherwise derive from version string
    release_type = info.get("release_type")
    if not isinstance(release_type, str) or release_type == "unknown":
        try:
            derived = get_version_type(current_version)
            release_type = derived
        except Exception:
            release_type = "unknown"

    return {
        "py7zz_version": current_version,
        "bundled_7zz_version": bundled_7zz_version,
        "release_type": release_type,
        "release_date": info.get("release_date", "unknown"),
        "github_tag": info.get("github_tag", f"v{current_version}"),
        "changelog_url": info.get(
            "changelog_url",
            f"https://github.com/rxchi1d/py7zz/releases/tag/v{current_version}",
        ),
    }


def get_bundled_7zz_version() -> str:
    """
    Get the bundled 7zz version for the current py7zz version.

    Returns:
        Bundled 7zz version string

    Example:
        >>> get_bundled_7zz_version()
        '24.07'
    """
    version = get_version_info()["bundled_7zz_version"]
    return version if isinstance(version, str) else "unknown"


def get_release_type() -> str:
    """
    Get the release type for the current py7zz version.

    Returns:
        Release type: 'stable', 'auto', or 'dev'

    Example:
        >>> get_release_type()
        'stable'
    """
    release_type = get_version_info()["release_type"]
    return release_type if isinstance(release_type, str) else "unknown"


def is_stable_release() -> bool:
    """
    Check if the current version is a stable release.

    Returns:
        True if current version is stable
    """
    return get_release_type() == "stable"


def is_auto_release() -> bool:
    """
    Check if the current version is an auto release.

    Returns:
        True if current version is auto
    """
    return get_release_type() == "auto"


def is_dev_release() -> bool:
    """
    Check if the current version is a dev release.

    Returns:
        True if current version is dev
    """
    return get_release_type() == "dev"

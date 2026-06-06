# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""Readers for the pinned 7zz metadata files shipped with the package.

This module is the single source of truth for reading the git-tracked
``7zz_version.txt`` and ``7zz_checksums.txt`` files. It has no third-party
dependencies and performs no network or subprocess work, so it is safe to
import from any other py7zz module without circular-import or startup-cost
concerns.
"""

from pathlib import Path
from typing import Dict, Optional

# Pinned metadata files shipped alongside this module (git-tracked, included
# in both wheel and sdist distributions).
PINNED_VERSION_FILE = Path(__file__).parent / "7zz_version.txt"
PINNED_CHECKSUM_FILE = Path(__file__).parent / "7zz_checksums.txt"


def read_pinned_7zz_version() -> Optional[str]:
    """Read the 7zz version pinned for this py7zz build.

    Returns:
        The dotted 7zz version string (e.g. ``"26.01"``), or ``None`` if the
        file is missing, empty, or unreadable.
    """
    try:
        version = PINNED_VERSION_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return version or None


def read_pinned_checksums() -> Dict[str, str]:
    """Read the pinned SHA-256 checksums for downloadable 7zz release assets.

    The file uses the standard ``sha256sum`` line format
    (``<hex-digest>  <asset-name>``); blank lines and ``#`` comments are
    ignored.

    Returns:
        Mapping of asset filename to lowercase hex SHA-256 digest. Empty if
        the file is missing or unreadable; consumers that require checksums
        must treat a missing entry as a hard failure (fail closed).
    """
    try:
        content = PINNED_CHECKSUM_FILE.read_text(encoding="utf-8")
    except OSError:
        return {}

    checksums: Dict[str, str] = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != 2:
            continue
        digest, asset_name = parts
        checksums[asset_name] = digest.lower()
    return checksums

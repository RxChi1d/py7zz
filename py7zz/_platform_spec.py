# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""Per-platform packaging facts for the 7zz binary.

This module collects in one table everything that varies per platform about
how the 7zz binary is named, cached, and validated, so the rules are not
duplicated across ``core``, ``updater``, and ``_download``. It has no
third-party dependencies and is safe to import from any other py7zz module.
"""

from typing import Dict, NamedTuple, Optional, Tuple


class PlatformSpec(NamedTuple):
    """Static facts about the 7zz binary on one platform.

    Attributes:
        binary_name: Filename of the main 7zz executable.
        extra_files: Sibling files required next to the binary for it to run
            (e.g. ``7z.dll`` on Windows). A cache entry missing any of these
            is incomplete.
        arch_dir: Fixed cache arch-directory override, or ``None`` to use the
            actual architecture. macOS ships a single universal binary, so it
            uses a fixed ``"universal"`` directory to avoid duplicate
            per-arch downloads.
    """

    binary_name: str
    extra_files: Tuple[str, ...]
    arch_dir: Optional[str]


# Keyed by 7zz release platform names (see SYSTEM_TO_PLATFORM).
PLATFORM_SPECS: Dict[str, PlatformSpec] = {
    "linux": PlatformSpec(binary_name="7zz", extra_files=(), arch_dir=None),
    "mac": PlatformSpec(binary_name="7zz", extra_files=(), arch_dir="universal"),
    "windows": PlatformSpec(
        binary_name="7zz.exe", extra_files=("7z.dll",), arch_dir=None
    ),
}

# Map ``platform.system().lower()`` values to 7zz release platform names.
SYSTEM_TO_PLATFORM: Dict[str, str] = {
    "darwin": "mac",
    "linux": "linux",
    "windows": "windows",
}

# Map ``platform.machine().lower()`` values to 7zz release arch names.
MACHINE_TO_ARCH: Dict[str, str] = {
    "x86_64": "x64",
    "amd64": "x64",
    "arm64": "arm64",
    "aarch64": "arm64",
}


def binary_name_for_system(system: str) -> str:
    """Return the 7zz binary filename for a ``platform.system()`` value.

    Args:
        system: Lowercased ``platform.system()`` value (e.g. ``"darwin"``).

    Returns:
        ``"7zz.exe"`` on Windows, ``"7zz"`` everywhere else (including
        unknown systems, which keep the historical POSIX default).
    """
    platform_name = SYSTEM_TO_PLATFORM.get(system)
    if platform_name is None:
        return "7zz"
    return PLATFORM_SPECS[platform_name].binary_name

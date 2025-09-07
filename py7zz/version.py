# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""
Version information for py7zz package.

This module manages the PEP 440 compliant version system for py7zz with
automatic version detection from git tags and package metadata:
- Release (stable): {major}.{minor}.{patch}
- Alpha (pre-release): {major}.{minor}.{patch}a{N}
- Beta (pre-release): {major}.{minor}.{patch}b{N}
- RC (pre-release): {major}.{minor}.{patch}rc{N}
- Dev (unstable): {major}.{minor}.{patch}.dev{N}

The version is automatically determined from:
1. Package metadata (for installed packages)
2. Git tags and commits (for development environments)
3. No hardcoded versions - single source of truth from git tags
"""

import re
import subprocess
from typing import Dict, Optional, Union

# Dynamic version following PEP 440 specification
# This is determined at runtime from git tags or package metadata


def get_version() -> str:
    """
    Get the current py7zz version.

    Returns:
        Current version string in PEP 440 format

    Example:
        >>> get_version()
        '0.1.2.dev23'
    """
    # Primary: Try to get version from package metadata (for wheel installations)
    try:
        from importlib.metadata import version as get_pkg_version

        return get_pkg_version("py7zz")
    except Exception:
        pass

    # Fallback: Try to get version from git describe (for development/editable installs)
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--match=v*", "--always"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        git_version = result.stdout.strip()

        # Convert git describe output to PEP 440 format
        if git_version.startswith("v"):
            # Remove 'v' prefix
            git_version = git_version[1:]

        # Handle format like "0.1.1-23-gbc38e6d" -> "0.1.2.dev23"
        if "-" in git_version and "-g" in git_version:
            parts = git_version.split("-")
            if len(parts) >= 3:
                base_version = parts[0]
                commits_ahead = parts[1]

                # Parse base version to increment patch for dev versions
                base_parts = base_version.split(".")
                if len(base_parts) >= 3:
                    major, minor, patch = base_parts[0], base_parts[1], base_parts[2]
                    # Increment patch version for dev versions
                    next_patch = int(patch) + 1
                    return f"{major}.{minor}.{next_patch}.dev{commits_ahead}"

        return git_version
    except Exception:
        pass

    # Last resort: Return a reasonable default version for development
    return "1.1.1"


def parse_version(version_string: str) -> Dict[str, Union[str, int, None]]:
    """
    Parse a PEP 440 version string into components.

    Args:
        version_string: Version string in PEP 440 format

    Returns:
        Dictionary containing parsed version components

    Raises:
        ValueError: If version string format is invalid

    Example:
        >>> parse_version('1.0.0')
        {'major': 1, 'minor': 0, 'patch': 0, 'version_type': 'stable', 'build_number': None}
        >>> parse_version('1.0.0a1')
        {'major': 1, 'minor': 0, 'patch': 0, 'version_type': 'alpha', 'build_number': 1}
        >>> parse_version('1.1.0.dev1')
        {'major': 1, 'minor': 1, 'patch': 0, 'version_type': 'dev', 'build_number': 1}
    """
    # Use a comprehensive PEP 440 regex pattern
    # Pattern: [N!]N(.N)*[{a|b|rc}N][.postN][.devN]
    pep440_pattern = (
        r"^(\d+)\.(\d+)\.(\d+)(?:(a|b|rc)(\d+))?(?:\.post(\d+))?(?:\.dev(\d+))?$"
    )

    match = re.match(pep440_pattern, version_string)
    if match:
        groups = match.groups()
        major = int(groups[0])
        minor = int(groups[1])
        patch = int(groups[2])

        pre_type = groups[3]  # 'a', 'b', 'rc', or None
        pre_num = int(groups[4]) if groups[4] else None
        post_num = int(groups[5]) if groups[5] else None
        dev_num = int(groups[6]) if groups[6] else None

        # Determine version type based on presence of suffixes
        if dev_num is not None:
            version_type = "dev"
            build_number: Optional[int] = dev_num
        elif pre_type == "a":
            version_type = "alpha"
            build_number = pre_num
            assert (
                build_number is not None
            )  # pre_num is guaranteed to be int when pre_type is "a"
        elif pre_type == "b":
            version_type = "beta"
            build_number = pre_num
            assert (
                build_number is not None
            )  # pre_num is guaranteed to be int when pre_type is "b"
        elif pre_type == "rc":
            version_type = "rc"
            build_number = pre_num
            assert (
                build_number is not None
            )  # pre_num is guaranteed to be int when pre_type is "rc"
        elif post_num is not None:
            version_type = "post"
            build_number = post_num
        else:
            version_type = "stable"
            build_number = None

        return {
            "major": major,
            "minor": minor,
            "patch": patch,
            "version_type": version_type,
            "build_number": build_number,
            "base_version": f"{major}.{minor}.{patch}",
        }

    # Fallback for older dev formats like 0.1.dev21
    dev_pattern = r"^(\d+)\.(\d+)\.dev(\d+)$"
    match = re.match(dev_pattern, version_string)
    if match:
        major = int(match.group(1))
        minor = int(match.group(2))
        dev_num = int(match.group(3))

        return {
            "major": major,
            "minor": minor,
            "patch": 0,
            "version_type": "dev",
            "build_number": dev_num,
            "base_version": f"{major}.{minor}.0",
        }

    raise ValueError(f"Invalid version format: {version_string}")


def get_version_type(version_string: Optional[str] = None) -> str:
    """
    Get the version type from a version string.

    Args:
        version_string: Version string to check (defaults to current version)

    Returns:
        Version type: 'stable', 'alpha', 'beta', 'rc', or 'dev'

    Example:
        >>> get_version_type('1.0.0')
        'stable'
        >>> get_version_type('1.0.0a1')
        'alpha'
        >>> get_version_type('1.1.0.dev1')
        'dev'
    """
    if version_string is None:
        version_string = get_version()

    parsed = parse_version(version_string)
    return str(parsed["version_type"])


def is_stable_version(version_string: Optional[str] = None) -> bool:
    """Check if a version string is a stable release version."""
    return get_version_type(version_string) == "stable"


def is_alpha_version(version_string: Optional[str] = None) -> bool:
    """Check if a version string is an alpha release version."""
    return get_version_type(version_string) == "alpha"


def is_beta_version(version_string: Optional[str] = None) -> bool:
    """Check if a version string is a beta release version."""
    return get_version_type(version_string) == "beta"


def is_rc_version(version_string: Optional[str] = None) -> bool:
    """Check if a version string is a release candidate version."""
    return get_version_type(version_string) == "rc"


def is_dev_version(version_string: Optional[str] = None) -> bool:
    """Check if a version string is a dev release version."""
    return get_version_type(version_string) == "dev"


def generate_alpha_version(base_version: str, build_number: int = 1) -> str:
    """
    Generate an alpha version string for pre-releases.

    Args:
        base_version: Base version (e.g., "1.0.0")
        build_number: Alpha build number (e.g., 1)

    Returns:
        Alpha version string in format: {base_version}a{build_number}

    Example:
        >>> generate_alpha_version("1.0.0", 1)
        '1.0.0a1'
    """
    return f"{base_version}a{build_number}"


def generate_dev_version(base_version: str, build_number: int = 1) -> str:
    """
    Generate a dev version string for development builds.

    Args:
        base_version: Base version (e.g., "1.1.0")
        build_number: Dev build number (e.g., 1)

    Returns:
        Dev version string in format: {base_version}.dev{build_number}

    Example:
        >>> generate_dev_version("1.1.0", 1)
        '1.1.0.dev1'
    """
    return f"{base_version}.dev{build_number}"


def get_base_version(version_string: Optional[str] = None) -> str:
    """
    Get the base version (major.minor.patch) from a version string.

    Args:
        version_string: Version string to parse (defaults to current version)

    Returns:
        Base version string

    Example:
        >>> get_base_version('1.0.0a1')
        '1.0.0'
        >>> get_base_version('1.1.0.dev1')
        '1.1.0'
    """
    if version_string is None:
        version_string = get_version()

    parsed = parse_version(version_string)
    return str(parsed["base_version"])


def get_build_number(version_string: Optional[str] = None) -> int:
    """
    Get the build number from a version string.

    Args:
        version_string: Version string to parse (defaults to current version)

    Returns:
        Build number or 0 for stable versions

    Example:
        >>> get_build_number('1.0.0a1')
        1
        >>> get_build_number('1.0.0')
        0
    """
    if version_string is None:
        version_string = get_version()

    parsed = parse_version(version_string)
    build_number = parsed["build_number"]
    return build_number if isinstance(build_number, int) else 0


# Legacy compatibility functions for backward compatibility
def get_py7zz_version() -> str:
    """Get the current py7zz version (legacy compatibility)."""
    return __version__


def get_version_info() -> Dict[str, Union[str, int, None]]:
    """
    Get detailed version information (legacy compatibility).

    Returns:
        Dictionary containing version information

    Example:
        >>> get_version_info()
        {
            'py7zz_version': '0.1.0',
            'version_type': 'stable',
            'build_number': None,
            'base_version': '0.1.0'
        }
    """
    current_version = get_version()
    parsed = parse_version(current_version)
    return {
        "py7zz_version": current_version,
        "version_type": parsed["version_type"],
        "build_number": parsed["build_number"],
        "base_version": parsed["base_version"],
    }


def compare_versions(version1: str, version2: str) -> int:
    """
    Compare two version strings.

    Args:
        version1: First version string
        version2: Second version string

    Returns:
        -1 if version1 < version2, 0 if equal, 1 if version1 > version2

    Example:
        >>> compare_versions('1.0.0', '1.0.1')
        -1
        >>> compare_versions('1.0.0', '1.0.0')
        0
        >>> compare_versions('1.0.1', '1.0.0')
        1
    """
    v1 = parse_version(version1)
    v2 = parse_version(version2)

    # Compare major.minor.patch
    v1_tuple = (v1["major"], v1["minor"], v1["patch"])
    v2_tuple = (v2["major"], v2["minor"], v2["patch"])

    if v1_tuple < v2_tuple:
        return -1
    elif v1_tuple > v2_tuple:
        return 1

    # Same base version, compare version types
    # PEP 440 precedence: dev < alpha < beta < rc < stable
    type_order = {"dev": 0, "alpha": 1, "beta": 2, "rc": 3, "stable": 4}
    v1_type = v1["version_type"]
    v2_type = v2["version_type"]
    v1_type_priority = type_order.get(str(v1_type) if v1_type else "stable", 4)
    v2_type_priority = type_order.get(str(v2_type) if v2_type else "stable", 4)

    if v1_type_priority < v2_type_priority:
        return -1
    elif v1_type_priority > v2_type_priority:
        return 1

    # Same version type, compare build numbers
    v1_build_raw = v1["build_number"]
    v2_build_raw = v2["build_number"]

    # Convert to int, handle None and str cases
    v1_build = int(v1_build_raw) if v1_build_raw is not None else 0
    v2_build = int(v2_build_raw) if v2_build_raw is not None else 0

    if v1_build < v2_build:
        return -1
    elif v1_build > v2_build:
        return 1

    return 0


def is_newer_version(version1: str, version2: str) -> bool:
    """
    Check if version1 is newer than version2.

    Args:
        version1: First version string
        version2: Second version string

    Returns:
        True if version1 is newer than version2

    Example:
        >>> is_newer_version('1.0.1', '1.0.0')
        True
        >>> is_newer_version('1.0.0', '1.0.1')
        False
    """
    return compare_versions(version1, version2) > 0


def get_version_components() -> Dict[str, Union[str, int, None]]:
    """
    Get comprehensive version component information.

    Returns:
        Dictionary with all version components and metadata

    Example:
        >>> get_version_components()
        {
            'py7zz_version': '0.1.0',
            'major': 0,
            'minor': 1,
            'patch': 0,
            'version_type': 'stable',
            'build_number': None,
            'base_version': '0.1.0',
            'is_stable': True,
            'is_development': False
        }
    """
    current_version = get_version()
    parsed = parse_version(current_version)
    version_type = parsed["version_type"]

    return {
        "py7zz_version": current_version,
        "major": parsed["major"],
        "minor": parsed["minor"],
        "patch": parsed["patch"],
        "version_type": version_type,
        "build_number": parsed["build_number"],
        "base_version": parsed["base_version"],
        "is_stable": version_type == "stable",
        "is_development": version_type == "dev",
        "is_alpha": version_type == "alpha",
    }


def format_version_for_display(
    version_string: Optional[str] = None, include_type: bool = True
) -> str:
    """
    Format version string for user display.

    Args:
        version_string: Version to format (defaults to current version)
        include_type: Whether to include version type information

    Returns:
        Formatted version string

    Example:
        >>> format_version_for_display('1.0.0')
        'py7zz 1.0.0 (stable)'
        >>> format_version_for_display('1.0.0a1')
        'py7zz 1.0.0a1 (alpha)'
        >>> format_version_for_display('1.0.0', include_type=False)
        'py7zz 1.0.0'
    """
    if version_string is None:
        version_string = get_version()

    if not include_type:
        return f"py7zz {version_string}"

    version_type = get_version_type(version_string)
    type_labels = {
        "stable": "stable",
        "alpha": "alpha",
        "beta": "beta",
        "rc": "release-candidate",
        "dev": "development",
    }

    type_label = type_labels.get(version_type, version_type)
    return f"py7zz {version_string} ({type_label})"


# Legacy compatibility aliases for backward compatibility
def is_auto_version(version_string: Optional[str] = None) -> bool:
    """Check if a version string is an alpha release version (legacy alias)."""
    return is_alpha_version(version_string)


def generate_auto_version(base_version: str, build_number: int = 1) -> str:
    """Generate an alpha version string (legacy alias)."""
    return generate_alpha_version(base_version, build_number)


# Simple default version to avoid circular import issues
# Real version will be set dynamically in __init__.py
__version__ = "1.1.1"

"""
Version information for py7zz package.

This module manages the PEP 440 compliant version system for py7zz:
- Release (stable): {major}.{minor}.{patch}
- Auto (basic stable): {major}.{minor}.{patch}a{N}
- Dev (unstable): {major}.{minor}.{patch}.dev{N}

The version is unified with GitHub releases and PyPI to avoid version conflicts.
"""

import re
from typing import Dict, Optional, Union

# py7zz version following PEP 440 specification
__version__ = "0.1.0"


def get_version() -> str:
    """
    Get the current py7zz version.

    Returns:
        Current version string in PEP 440 format

    Example:
        >>> get_version()
        '0.1.0'
    """
    # Try to get version from package metadata (for wheel installations)
    try:
        from importlib.metadata import version

        return version("py7zz")
    except ImportError:
        # Python < 3.8 fallback
        try:
            from importlib_metadata import version

            return version("py7zz")
        except ImportError:
            pass
    except Exception:
        pass

    # Fallback to hardcoded version (for development/editable installs)
    return __version__


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
        {'major': 1, 'minor': 0, 'patch': 0, 'version_type': 'auto', 'build_number': 1}
        >>> parse_version('1.1.0.dev1')
        {'major': 1, 'minor': 1, 'patch': 0, 'version_type': 'dev', 'build_number': 1}
    """
    # Pattern for PEP 440 version formats
    patterns = [
        # Dev version: 1.1.0.dev1 or 0.1.dev21
        (r"^(\d+)\.(\d+)\.(\d+)\.dev(\d+)$", "dev"),
        (r"^(\d+)\.(\d+)\.dev(\d+)$", "dev"),
        # Alpha version (auto): 1.0.0a1
        (r"^(\d+)\.(\d+)\.(\d+)a(\d+)$", "auto"),
        # Release version: 1.0.0
        (r"^(\d+)\.(\d+)\.(\d+)$", "stable"),
    ]

    for pattern, version_type in patterns:
        match = re.match(pattern, version_string)
        if match:
            groups = match.groups()
            major, minor = int(groups[0]), int(groups[1])

            # Handle different pattern lengths
            if len(groups) == 3:
                # Format: 0.1.dev21
                patch = 0
                build_number: Optional[int] = int(groups[2])
            elif len(groups) == 4:
                # Format: 1.1.0.dev1 or 1.0.0a1
                patch = int(groups[2])
                build_number = int(groups[3]) if groups[3] is not None else None
            else:
                # Format: 1.0.0
                patch = int(groups[2])
                build_number = None

            return {
                "major": major,
                "minor": minor,
                "patch": patch,
                "version_type": version_type,
                "build_number": build_number,
                "base_version": f"{major}.{minor}.{patch}",
            }

    raise ValueError(f"Invalid version format: {version_string}")


def get_version_type(version_string: Optional[str] = None) -> str:
    """
    Get the version type from a version string.

    Args:
        version_string: Version string to check (defaults to current version)

    Returns:
        Version type: 'stable', 'auto', or 'dev'

    Example:
        >>> get_version_type('1.0.0')
        'stable'
        >>> get_version_type('1.0.0a1')
        'auto'
        >>> get_version_type('1.1.0.dev1')
        'dev'
    """
    if version_string is None:
        version_string = __version__

    parsed = parse_version(version_string)
    return str(parsed["version_type"])


def is_stable_version(version_string: Optional[str] = None) -> bool:
    """Check if a version string is a stable release version."""
    return get_version_type(version_string) == "stable"


def is_auto_version(version_string: Optional[str] = None) -> bool:
    """Check if a version string is an auto release version."""
    return get_version_type(version_string) == "auto"


def is_dev_version(version_string: Optional[str] = None) -> bool:
    """Check if a version string is a dev release version."""
    return get_version_type(version_string) == "dev"


def generate_auto_version(base_version: str, build_number: int = 1) -> str:
    """
    Generate an auto version string for 7zz updates.

    Args:
        base_version: Base version (e.g., "1.0.0")
        build_number: Auto build number (e.g., 1)

    Returns:
        Auto version string in format: {base_version}a{build_number}

    Example:
        >>> generate_auto_version("1.0.0", 1)
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
        version_string = __version__

    parsed = parse_version(version_string)
    return str(parsed["base_version"])


def get_build_number(version_string: Optional[str] = None) -> Optional[int]:
    """
    Get the build number from a version string.

    Args:
        version_string: Version string to parse (defaults to current version)

    Returns:
        Build number or None for stable versions

    Example:
        >>> get_build_number('1.0.0a1')
        1
        >>> get_build_number('1.0.0')
        None
    """
    if version_string is None:
        version_string = __version__

    parsed = parse_version(version_string)
    build_number = parsed["build_number"]
    return build_number if isinstance(build_number, int) else None


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
    parsed = parse_version(__version__)
    return {
        "py7zz_version": __version__,
        "version_type": parsed["version_type"],
        "build_number": parsed["build_number"],
        "base_version": parsed["base_version"],
    }

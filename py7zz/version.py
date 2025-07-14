"""
Version information for py7zz package.

This module manages the three-tier version system for py7zz:
- Release (stable): {major}.{minor}.{patch}+7zz{7zz_version}
- Auto (basic stable): {major}.{minor}.{patch}.auto+7zz{7zz_version}  
- Dev (unstable): {major}.{minor}.{patch}-dev.{build}+7zz{7zz_version}
"""

from typing import Dict, Literal, Tuple, Union
from enum import Enum

# py7zz semantic version
PY7ZZ_VERSION = "1.0.0"

# 7zz binary version (follows upstream)
SEVEN_ZZ_VERSION = "24.07"

# Version type
class VersionType(Enum):
    """Version type enumeration."""
    RELEASE = "release"
    AUTO = "auto"
    DEV = "dev"

# Current version type (default to release)
VERSION_TYPE = VersionType.RELEASE

# Build number for dev versions
DEV_BUILD_NUMBER = 1

# Full version combining both
FULL_VERSION = f"{PY7ZZ_VERSION}+7zz{SEVEN_ZZ_VERSION}"


def get_version() -> str:
    """
    Get the full version string based on current version type.
    
    Returns:
        Full version string in appropriate format
        
    Example:
        >>> get_version()  # Release version
        '1.0.0+7zz24.07'
        >>> get_version()  # Auto version
        '1.0.0.auto+7zz24.08'
        >>> get_version()  # Dev version
        '1.1.0-dev.1+7zz24.07'
    """
    return build_version(PY7ZZ_VERSION, SEVEN_ZZ_VERSION, VERSION_TYPE, DEV_BUILD_NUMBER)


def build_version(
    py7zz_version: str,
    seven_zz_version: str,
    version_type: VersionType,
    build_number: int = 1
) -> str:
    """
    Build a version string based on type.
    
    Args:
        py7zz_version: py7zz semantic version
        seven_zz_version: 7zz version
        version_type: Version type (release, auto, dev)
        build_number: Build number for dev versions
        
    Returns:
        Formatted version string
        
    Example:
        >>> build_version("1.0.0", "24.07", VersionType.RELEASE)
        '1.0.0+7zz24.07'
        >>> build_version("1.0.0", "24.08", VersionType.AUTO)
        '1.0.0.auto+7zz24.08'
        >>> build_version("1.1.0", "24.07", VersionType.DEV, 2)
        '1.1.0-dev.2+7zz24.07'
    """
    if version_type == VersionType.RELEASE:
        return f"{py7zz_version}+7zz{seven_zz_version}"
    elif version_type == VersionType.AUTO:
        return f"{py7zz_version}.auto+7zz{seven_zz_version}"
    elif version_type == VersionType.DEV:
        return f"{py7zz_version}-dev.{build_number}+7zz{seven_zz_version}"
    else:
        raise ValueError(f"Unknown version type: {version_type}")


def get_py7zz_version() -> str:
    """
    Get only the py7zz version.
    
    Returns:
        py7zz semantic version string
        
    Example:
        >>> get_py7zz_version()
        '1.0.0'
    """
    return PY7ZZ_VERSION


def get_7zz_version() -> str:
    """
    Get only the 7zz version.
    
    Returns:
        7zz version string
        
    Example:
        >>> get_7zz_version()
        '24.07'
    """
    return SEVEN_ZZ_VERSION


def get_version_info() -> Dict[str, Union[str, int]]:
    """
    Get detailed version information.
    
    Returns:
        Dictionary containing version information
        
    Example:
        >>> get_version_info()
        {
            'py7zz_version': '1.0.0',
            '7zz_version': '24.07',
            'version_type': 'release',
            'build_number': None,
            'full_version': '1.0.0+7zz24.07'
        }
    """
    return {
        "py7zz_version": PY7ZZ_VERSION,
        "7zz_version": SEVEN_ZZ_VERSION,
        "version_type": VERSION_TYPE.value,
        "build_number": DEV_BUILD_NUMBER if VERSION_TYPE == VersionType.DEV else None,
        "full_version": get_version()
    }


def parse_version(version_string: str) -> Dict[str, Union[str, int, None]]:
    """
    Parse a full version string into components.
    
    Args:
        version_string: Full version string in any supported format
        
    Returns:
        Dictionary containing parsed version components
        
    Raises:
        ValueError: If version string format is invalid
        
    Example:
        >>> parse_version('1.0.0+7zz24.07')
        {'py7zz_version': '1.0.0', '7zz_version': '24.07', 'version_type': 'release', 'build_number': None}
        >>> parse_version('1.0.0.auto+7zz24.08')
        {'py7zz_version': '1.0.0', '7zz_version': '24.08', 'version_type': 'auto', 'build_number': None}
        >>> parse_version('1.1.0-dev.2+7zz24.07')
        {'py7zz_version': '1.1.0', '7zz_version': '24.07', 'version_type': 'dev', 'build_number': 2}
    """
    if "+7zz" not in version_string:
        raise ValueError(f"Invalid version format: {version_string}")
    
    parts = version_string.split("+7zz")
    if len(parts) != 2:
        raise ValueError(f"Invalid version format: {version_string}")
    
    py7zz_part, seven_zz_version = parts
    
    # Determine version type and extract components
    if "-dev." in py7zz_part:
        # Dev version: 1.1.0-dev.2
        version_type = "dev"
        base_version, dev_part = py7zz_part.split("-dev.")
        build_number = int(dev_part)
        py7zz_version = base_version
    elif ".auto" in py7zz_part:
        # Auto version: 1.0.0.auto
        version_type = "auto"
        py7zz_version = py7zz_part.replace(".auto", "")
        build_number = None
    else:
        # Release version: 1.0.0
        version_type = "release"
        py7zz_version = py7zz_part
        build_number = None
    
    return {
        "py7zz_version": py7zz_version,
        "7zz_version": seven_zz_version,
        "version_type": version_type,
        "build_number": build_number
    }


def generate_auto_version(base_version: str, new_7zz_version: str) -> str:
    """
    Generate an auto version string for 7zz updates.
    
    Args:
        base_version: Base py7zz version (e.g., "1.0.0")
        new_7zz_version: New 7zz version (e.g., "24.08")
        
    Returns:
        Auto version string in format: {base_version}.auto+7zz{new_7zz_version}
        
    Example:
        >>> generate_auto_version("1.0.0", "24.08")
        '1.0.0.auto+7zz24.08'
    """
    return build_version(base_version, new_7zz_version, VersionType.AUTO)


def generate_dev_version(base_version: str, seven_zz_version: str, build_number: int) -> str:
    """
    Generate a dev version string for development builds.
    
    Args:
        base_version: Base py7zz version (e.g., "1.1.0")
        seven_zz_version: 7zz version (e.g., "24.07")
        build_number: Build number (e.g., 2)
        
    Returns:
        Dev version string in format: {base_version}-dev.{build_number}+7zz{seven_zz_version}
        
    Example:
        >>> generate_dev_version("1.1.0", "24.07", 2)
        '1.1.0-dev.2+7zz24.07'
    """
    return build_version(base_version, seven_zz_version, VersionType.DEV, build_number)


def get_version_type(version_string: str) -> str:
    """
    Get the version type from a version string.
    
    Args:
        version_string: Version string to check
        
    Returns:
        Version type: 'release', 'auto', or 'dev'
        
    Example:
        >>> get_version_type('1.0.0+7zz24.07')
        'release'
        >>> get_version_type('1.0.0.auto+7zz24.08')
        'auto'
        >>> get_version_type('1.1.0-dev.2+7zz24.07')
        'dev'
    """
    parsed = parse_version(version_string)
    return parsed["version_type"]


def is_release_version(version_string: str) -> bool:
    """Check if a version string is a release version."""
    return get_version_type(version_string) == "release"


def is_auto_version(version_string: str) -> bool:
    """Check if a version string is an auto version."""
    return get_version_type(version_string) == "auto"


def is_dev_version(version_string: str) -> bool:
    """Check if a version string is a dev version."""
    return get_version_type(version_string) == "dev"
"""
py7zz - Python wrapper for 7zz CLI tool

Provides a consistent OOP interface across platforms (macOS, Linux, Windows)
with automatic update mechanisms.
"""

from .core import SevenZipFile, get_version

__version__ = "0.1.0"
__all__ = ["SevenZipFile", "get_version"]
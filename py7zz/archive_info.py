# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""
Archive member information classes for py7zz package.

Provides zipfile.ZipInfo and tarfile.TarInfo compatible interfaces
for 7zz archive members with detailed metadata support.
"""

import os
from datetime import datetime
from typing import Any, Optional, Union


class ArchiveInfo:
    """
    Archive member information, similar to zipfile.ZipInfo and tarfile.TarInfo.

    This class provides detailed information about files within an archive,
    compatible with both zipfile and tarfile interfaces for easy migration.
    """

    def __init__(self, filename: str = "") -> None:
        """
        Initialize ArchiveInfo object.

        Args:
            filename: Name of the file in the archive
        """
        # Basic file information
        self.filename = filename
        self.orig_filename = filename  # Keep original for reference

        # File sizes (compatible with zipfile.ZipInfo)
        self.file_size: int = 0  # Uncompressed size
        self.compress_size: int = 0  # Compressed size

        # Time information (compatible with both zipfile and tarfile)
        self.date_time: Optional[tuple] = (
            None  # (year, month, day, hour, minute, second)
        )
        self.mtime: Optional[float] = None  # tarfile-compatible modification time

        # Compression information
        self.compress_type: Optional[str] = None  # Compression method used
        self.CRC: int = 0  # CRC32 checksum (zipfile compatible)

        # File attributes (zipfile compatible)
        self.create_system: int = 0  # System that created the file
        self.create_version: int = 0  # Version that created the file
        self.extract_version: int = 0  # Version needed to extract
        self.reserved: int = 0  # Reserved field
        self.flag_bits: int = 0  # General purpose bit flags
        self.volume: int = 0  # Volume number
        self.internal_attr: int = 0  # Internal file attributes
        self.external_attr: int = 0  # External file attributes
        self.header_offset: int = 0  # Offset to file header

        # Additional metadata and comments
        self.comment: str = ""  # File comment
        self.extra: bytes = b""  # Extra field data

        # File type information (tarfile compatible)
        self.mode: int = 0  # File mode (permissions)
        self.uid: int = 0  # User ID
        self.gid: int = 0  # Group ID
        self.uname: str = ""  # User name
        self.gname: str = ""  # Group name
        self.type: str = "file"  # File type ("file", "dir", "link", etc.)

        # 7zz specific information
        self.method: Optional[str] = None  # Compression method name
        self.solid: Optional[bool] = None  # Whether file is in solid block
        self.encrypted: bool = False  # Whether file is encrypted

    def __repr__(self) -> str:
        """String representation of ArchiveInfo."""
        return (
            f"<ArchiveInfo filename='{self.filename}' "
            f"compress_type='{self.compress_type}' "
            f"file_size={self.file_size} "
            f"compress_size={self.compress_size}>"
        )

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.filename} ({self.file_size} bytes)"

    # zipfile.ZipInfo compatibility methods

    def is_dir(self) -> bool:
        """
        Return True if this archive member is a directory.
        Compatible with zipfile.ZipInfo.is_dir().
        """
        return self.type == "dir" or self.filename.endswith("/")

    @property
    def is_directory(self) -> bool:
        """Alias for is_dir() for additional compatibility."""
        return self.is_dir()

    # tarfile.TarInfo compatibility methods

    def isfile(self) -> bool:
        """
        Return True if this archive member is a regular file.
        Compatible with tarfile.TarInfo.isfile().
        """
        return self.type == "file" and not self.is_dir()

    def isdir(self) -> bool:
        """
        Return True if this archive member is a directory.
        Compatible with tarfile.TarInfo.isdir().
        """
        return self.is_dir()

    def islink(self) -> bool:
        """
        Return True if this archive member is a symbolic link.
        Compatible with tarfile.TarInfo.islink().
        """
        return self.type == "link"

    def issym(self) -> bool:
        """
        Return True if this archive member is a symbolic link.
        Alias for islink() for tarfile compatibility.
        """
        return self.islink()

    def isreg(self) -> bool:
        """
        Return True if this archive member is a regular file.
        Alias for isfile() for tarfile compatibility.
        """
        return self.isfile()

    # Utility methods for time handling

    def get_mtime(self) -> Optional[float]:
        """
        Get modification time as Unix timestamp.

        Returns:
            Unix timestamp or None if no time information available
        """
        if self.mtime is not None:
            return self.mtime

        if self.date_time is not None:
            try:
                dt = datetime(*self.date_time)
                return dt.timestamp()
            except (ValueError, TypeError):
                pass

        return None

    def set_mtime(self, timestamp: Union[float, datetime]) -> None:
        """
        Set modification time from Unix timestamp or datetime object.

        Args:
            timestamp: Unix timestamp (float) or datetime object
        """
        if isinstance(timestamp, datetime):
            self.mtime = timestamp.timestamp()
            self.date_time = (
                timestamp.year,
                timestamp.month,
                timestamp.day,
                timestamp.hour,
                timestamp.minute,
                timestamp.second,
            )
        else:
            self.mtime = float(timestamp)
            dt = datetime.fromtimestamp(timestamp)
            self.date_time = (
                dt.year,
                dt.month,
                dt.day,
                dt.hour,
                dt.minute,
                dt.second,
            )

    def get_datetime(self) -> Optional[datetime]:
        """
        Get modification time as datetime object.

        Returns:
            datetime object or None if no time information available
        """
        if self.date_time is not None:
            try:
                return datetime(*self.date_time)
            except (ValueError, TypeError):
                pass

        if self.mtime is not None:
            try:
                return datetime.fromtimestamp(self.mtime)
            except (ValueError, OSError):
                pass

        return None

    # Compression ratio calculation

    def get_compression_ratio(self) -> float:
        """
        Calculate compression ratio.

        Returns:
            Compression ratio as a float (0.0 to 1.0)
            0.0 means no compression, 1.0 means 100% compression
        """
        if self.file_size == 0:
            return 0.0

        if self.compress_size == 0:
            return 1.0

        return 1.0 - (self.compress_size / self.file_size)

    def get_compression_percentage(self) -> float:
        """
        Calculate compression percentage.

        Returns:
            Compression percentage (0.0 to 100.0)
        """
        return self.get_compression_ratio() * 100.0

    # File path utilities

    @property
    def basename(self) -> str:
        """Get the base name of the file (filename without directory path)."""
        return os.path.basename(self.filename)

    @property
    def dirname(self) -> str:
        """Get the directory name of the file."""
        return os.path.dirname(self.filename)

    # Validation methods

    def validate(self) -> bool:
        """
        Validate the ArchiveInfo object for consistency.

        Returns:
            True if the object is valid, False otherwise
        """
        # Basic validation checks
        if not self.filename:
            return False

        if self.file_size < 0 or self.compress_size < 0:
            return False

        if self.date_time is not None:
            if len(self.date_time) != 6:
                return False

            year, month, day, hour, minute, second = self.date_time
            if not (1980 <= year <= 2107):  # ZIP date range
                return False
            if not (1 <= month <= 12):
                return False
            if not (1 <= day <= 31):
                return False
            if not (0 <= hour <= 23):
                return False
            if not (0 <= minute <= 59):
                return False
            if not (0 <= second <= 59):
                return False

        return True

    # Factory methods for different archive types

    @classmethod
    def from_zipinfo(cls, zipinfo: Any) -> "ArchiveInfo":
        """
        Create ArchiveInfo from zipfile.ZipInfo object.

        Args:
            zipinfo: zipfile.ZipInfo object

        Returns:
            ArchiveInfo object with equivalent data
        """
        info = cls(zipinfo.filename)
        info.file_size = zipinfo.file_size
        info.compress_size = zipinfo.compress_size
        info.date_time = zipinfo.date_time
        info.CRC = zipinfo.CRC
        info.compress_type = str(zipinfo.compress_type)
        info.comment = zipinfo.comment.decode() if zipinfo.comment else ""
        info.extra = zipinfo.extra
        info.create_system = zipinfo.create_system
        info.create_version = zipinfo.create_version
        info.extract_version = zipinfo.extract_version
        info.reserved = zipinfo.reserved
        info.flag_bits = zipinfo.flag_bits
        info.volume = zipinfo.volume
        info.internal_attr = zipinfo.internal_attr
        info.external_attr = zipinfo.external_attr
        info.header_offset = zipinfo.header_offset

        # Set file type based on directory indicator
        if info.is_dir():
            info.type = "dir"
        else:
            info.type = "file"

        return info

    @classmethod
    def from_tarinfo(cls, tarinfo: Any) -> "ArchiveInfo":
        """
        Create ArchiveInfo from tarfile.TarInfo object.

        Args:
            tarinfo: tarfile.TarInfo object

        Returns:
            ArchiveInfo object with equivalent data
        """
        info = cls(tarinfo.name)
        info.file_size = tarinfo.size
        info.compress_size = tarinfo.size  # TAR doesn't compress individual files
        info.mtime = tarinfo.mtime
        info.mode = tarinfo.mode
        info.uid = tarinfo.uid
        info.gid = tarinfo.gid
        info.uname = tarinfo.uname
        info.gname = tarinfo.gname

        # Map tarfile types to our type system
        if tarinfo.isfile():
            info.type = "file"
        elif tarinfo.isdir():
            info.type = "dir"
        elif tarinfo.islink() or tarinfo.issym():
            info.type = "link"
        else:
            info.type = "other"

        # Set date_time from mtime
        if info.mtime:
            dt = datetime.fromtimestamp(info.mtime)
            info.date_time = (
                dt.year,
                dt.month,
                dt.day,
                dt.hour,
                dt.minute,
                dt.second,
            )

        return info

# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""
Detailed information parser for py7zz package.

Parses 7zz -slt (show technical information) output to extract
comprehensive metadata about archive members.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from .archive_info import ArchiveInfo
from .logging_config import get_logger

logger = get_logger(__name__)


def parse_7zz_slt_output(output: str) -> List[ArchiveInfo]:
    """
    Parse 7zz -slt output to extract detailed archive member information.

    The -slt flag provides technical information in the format:

    ----------
    Path = filename.txt
    Size = 1234
    Packed Size = 567
    Modified = 2024-01-15 10:30:45
    Attributes = A
    CRC = 12345678
    Method = LZMA2:19
    Solid = +
    Encrypted = -

    Args:
        output: Raw output from 7zz -slt command

    Returns:
        List of ArchiveInfo objects with parsed metadata
    """
    members: List[ArchiveInfo] = []
    current_member: Optional[ArchiveInfo] = None
    member_has_props = False  # Track if current member has any file-level properties
    in_archive_header = True  # Track if we're still in archive header section

    lines = output.split("\n")

    for line in lines:
        line = line.strip()

        # Skip empty lines and separators; the long dashes indicate file entries start
        if not line or line.startswith("=="):
            continue

        # Long dashes (----------) indicate start of individual file entries
        if line.startswith("----------"):
            in_archive_header = False
            continue

        # Short dashes (--) indicate archive metadata section
        if line.startswith("--") and in_archive_header:
            continue

        # Skip header information until we reach file entries
        if any(
            line.startswith(prefix)
            for prefix in [
                "Listing archive:",
                "7-Zip",
            ]
        ):
            continue

        # Parse property lines (format: "Property = Value")
        if "=" in line:
            prop, value = line.split("=", 1)
            prop = prop.strip()
            value = value.strip()

            # Skip known archive-level properties when in header section,
            # but allow "Path" to start a member for minimal outputs where
            # the separator lines (----------) are omitted.
            if in_archive_header and prop in [
                "Type",
                "Physical Size",
                "Headers Size",
                "Method",
                "Solid",
                "Blocks",
            ]:
                continue

            # Start of new file entry
            if prop == "Path":
                # Save previous member if it had any file-level properties
                if current_member is not None and member_has_props:
                    members.append(current_member)

                # Start new member
                current_member = ArchiveInfo(value)
                member_has_props = False
                continue

            # Skip if no current member
            if current_member is None:
                continue

            # Parse different properties
            if prop == "Size":
                current_member.file_size = _parse_int(value, 0)
                member_has_props = True

            elif prop == "Packed Size":
                current_member.compress_size = _parse_int(value, 0)
                member_has_props = True

            elif prop == "Modified":
                current_member.date_time, current_member.mtime = _parse_datetime(value)
                member_has_props = True

            elif prop == "Attributes":
                current_member.external_attr = _parse_attributes(value)
                current_member.type = _determine_file_type(
                    value, current_member.filename
                )
                member_has_props = True

            elif prop == "CRC":
                current_member.CRC = _parse_int(value, 0, base=16) if value != "" else 0
                member_has_props = True

            elif prop == "Method":
                current_member.compress_type = value if value else ""
                current_member.method = value if value else ""
                # Method may appear for both archive and file entries; do not
                # mark as file-level property by itself when still in header.
                if not in_archive_header:
                    member_has_props = True

            elif prop == "Solid":
                current_member.solid = value == "+"
                if not in_archive_header:
                    member_has_props = True

            elif prop == "Encrypted":
                current_member.encrypted = value == "+"
                member_has_props = True

            elif prop == "Comment":
                current_member.comment = value
                member_has_props = True

    # Add the last member if it had any file-level properties
    if current_member is not None and member_has_props:
        members.append(current_member)

    logger.debug(f"Parsed {len(members)} archive members from 7zz -slt output")
    return members


def _parse_int(value: str, default: int = 0, base: int = 10) -> int:
    """
    Parse integer value with error handling.

    Args:
        value: String value to parse
        default: Default value if parsing fails
        base: Number base (10 for decimal, 16 for hex)

    Returns:
        Parsed integer or default value
    """
    try:
        if not value or value == "":
            return default
        return int(value, base)
    except (ValueError, TypeError):
        logger.warning(f"Failed to parse integer value: {value}")
        return default


def _parse_datetime(value: str) -> Tuple[Optional[Tuple], Optional[float]]:
    """
    Parse datetime string from 7zz output.

    7zz outputs datetime in format: "YYYY-MM-DD HH:MM:SS"

    Args:
        value: DateTime string from 7zz

    Returns:
        Tuple of (date_time tuple, unix timestamp) or (None, None)
    """
    if not value or value == "":
        return None, None

    # Common 7zz datetime formats
    formats = [
        "%Y-%m-%d %H:%M:%S",  # "2024-01-15 10:30:45"
        "%Y-%m-%d %H:%M:%S.%f",  # "2024-01-15 10:30:45.123"
        "%Y-%m-%d",  # "2024-01-15" (date only)
        "%Y/%m/%d %H:%M:%S",  # Alternative format
        "%d/%m/%Y %H:%M:%S",  # DD/MM/YYYY format
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(value, fmt)
            date_tuple = (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
            timestamp = dt.timestamp()
            return date_tuple, timestamp
        except ValueError:
            continue

    # Try to parse partial matches
    try:
        # Extract year, month, day from various formats
        match = re.match(
            r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})(?:\s+(\d{1,2}):(\d{1,2}):(\d{1,2}))?",
            value,
        )
        if match:
            year, month, day = (
                int(match.group(1)),
                int(match.group(2)),
                int(match.group(3)),
            )
            hour = int(match.group(4)) if match.group(4) else 0
            minute = int(match.group(5)) if match.group(5) else 0
            second = int(match.group(6)) if match.group(6) else 0

            dt = datetime(year, month, day, hour, minute, second)
            date_tuple = (year, month, day, hour, minute, second)
            timestamp = dt.timestamp()
            return date_tuple, timestamp
    except (ValueError, TypeError):
        # Date parsing failed, fall back to warning and return None
        pass

    logger.warning(f"Failed to parse datetime value: {value}")
    return None, None


def _parse_attributes(attributes: str) -> int:
    """
    Parse file attributes string to integer.

    7zz attributes format uses letters:
    - D: Directory
    - A: Archive bit
    - R: Read-only
    - H: Hidden
    - S: System

    Args:
        attributes: Attributes string from 7zz

    Returns:
        Integer representation of attributes
    """
    if not attributes:
        return 0

    attr_value = 0

    # Map 7zz attribute letters to Windows file attribute bits
    attr_map = {
        "D": 0x10,  # FILE_ATTRIBUTE_DIRECTORY
        "A": 0x20,  # FILE_ATTRIBUTE_ARCHIVE
        "R": 0x01,  # FILE_ATTRIBUTE_READONLY
        "H": 0x02,  # FILE_ATTRIBUTE_HIDDEN
        "S": 0x04,  # FILE_ATTRIBUTE_SYSTEM
    }

    for char in attributes.upper():
        if char in attr_map:
            attr_value |= attr_map[char]

    return attr_value


def _determine_file_type(attributes: str, filename: str) -> str:
    """
    Determine file type from attributes and filename.

    Args:
        attributes: Attributes string from 7zz
        filename: Filename to check

    Returns:
        File type string ("file", "dir", "link", etc.)
    """
    # Check if it's a directory
    if "D" in attributes.upper() or filename.endswith("/"):
        return "dir"

    # Check for symbolic links (7zz may indicate this differently)
    if filename.startswith("->") or " -> " in filename:
        return "link"

    # Default to regular file
    return "file"


def get_detailed_archive_info(
    archive_path: Union[str, Path], password: Optional[Union[str, bytes]] = None
) -> List[ArchiveInfo]:
    """
    Get detailed information about all members in an archive.

    This function executes '7zz l -slt' command to get comprehensive
    metadata about each file in the archive.

    Args:
        archive_path: Path to the archive file
        password: Password for encrypted archives (optional)

    Returns:
        List of ArchiveInfo objects with detailed metadata

    Raises:
        subprocess.CalledProcessError: If 7zz command fails
        RuntimeError: If binary not found or parsing fails
    """
    from .core import run_7z

    archive_path = Path(archive_path)

    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    # Execute 7zz list command with technical information
    args = ["l", "-slt", str(archive_path)]

    # Add password if provided
    if password is not None:
        # Convert bytes password to string for 7zz command
        password_str = (
            password.decode("utf-8") if isinstance(password, bytes) else str(password)
        )
        args.append(f"-p{password_str}")

    try:
        result = run_7z(args)
        members = parse_7zz_slt_output(result.stdout)

        logger.info(
            f"Retrieved detailed information for {len(members)} archive members"
        )
        return members

    except Exception as e:
        logger.error(f"Failed to get detailed archive info: {e}")
        raise RuntimeError(f"Failed to get detailed archive information: {e}") from e


def create_archive_summary(
    members: List[ArchiveInfo],
) -> Dict[str, Union[int, float, str]]:
    """
    Create summary statistics from list of archive members.

    Args:
        members: List of ArchiveInfo objects

    Returns:
        Dictionary with summary statistics
    """
    if not members:
        return {
            "file_count": 0,
            "directory_count": 0,
            "total_file_count": 0,
            "total_uncompressed_size": 0,
            "total_compressed_size": 0,
            "compression_ratio": 0.0,
            "compression_percentage": 0.0,
            "archive_type": "empty",
        }

    file_count = 0
    directory_count = 0
    total_uncompressed = 0
    total_compressed = 0

    for member in members:
        if member.is_dir():
            directory_count += 1
        else:
            file_count += 1

        total_uncompressed += member.file_size
        total_compressed += member.compress_size

    # Calculate compression ratio
    if total_uncompressed > 0:
        compression_ratio = 1.0 - (total_compressed / total_uncompressed)
    else:
        compression_ratio = 0.0

    # Determine predominant archive type
    methods = [m.method for m in members if m.method]
    archive_type = "mixed"
    if methods:
        # Find most common compression method
        method_counts: Dict[str, int] = {}
        for method in methods:
            method_counts[method] = method_counts.get(method, 0) + 1
        archive_type = max(method_counts, key=lambda k: method_counts[k])

    return {
        "file_count": file_count,
        "directory_count": directory_count,
        "total_file_count": file_count + directory_count,
        "total_uncompressed_size": total_uncompressed,
        "total_compressed_size": total_compressed,
        "compression_ratio": compression_ratio,
        "compression_percentage": compression_ratio * 100.0,
        "archive_type": archive_type,
    }

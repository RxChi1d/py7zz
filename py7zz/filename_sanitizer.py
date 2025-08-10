# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""
Windows filename compatibility sanitizer.

Handles Windows filename restrictions and provides safe alternatives
for archives containing files with invalid Windows names.
"""

import hashlib
import platform
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .logging_config import get_logger

# Get logger for this module
logger = get_logger(__name__)

# Windows invalid characters: < > : " | ? * and control characters (0-31)
INVALID_CHARS = set('<>:"|?*') | {chr(i) for i in range(32)}

# Windows reserved names (case-insensitive)
RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}

# Maximum filename length (Windows NTFS limit is 255)
MAX_FILENAME_LENGTH = 255
MAX_PATH_LENGTH = 260


def is_windows() -> bool:
    """Check if running on Windows system."""
    return platform.system().lower() == "windows"


def needs_sanitization(filename: str) -> bool:
    """
    Check if a filename needs sanitization for Windows compatibility.

    Args:
        filename: The filename to check

    Returns:
        True if sanitization is needed, False otherwise
    """
    if not is_windows():
        return False

    # Check for invalid characters
    if any(char in INVALID_CHARS for char in filename):
        return True

    # Check for reserved names (case-insensitive)
    name_without_ext = Path(filename).stem.upper()
    if name_without_ext in RESERVED_NAMES:
        return True

    # Check for names that are reserved with any extension
    if "." in filename:
        base_name = filename.split(".")[0].upper()
        if base_name in RESERVED_NAMES:
            return True

    # Check for trailing spaces or dots
    if filename.rstrip() != filename or filename.rstrip(".") != filename:
        return True

    # Check for excessive length
    if len(filename) > MAX_FILENAME_LENGTH:
        return True

    # Check for directory traversal attempts
    return ".." in filename or filename.startswith("/") or filename.startswith("\\")


def sanitize_filename(
    filename: str, existing_names: Optional[Set[str]] = None
) -> Tuple[str, bool]:
    """
    Sanitize a filename for Windows compatibility.

    Args:
        filename: The original filename
        existing_names: Set of already used names to avoid conflicts

    Returns:
        Tuple of (sanitized_filename, was_changed)
    """
    if existing_names is None:
        existing_names = set()

    original_filename = filename
    changed = False

    # Remove directory traversal attempts
    while ".." in filename:
        filename = filename.replace("..", "_")
        changed = True

    # Remove leading path separators
    filename = filename.lstrip("/\\")
    if filename != original_filename:
        changed = True

    # Replace invalid characters with underscores
    for char in INVALID_CHARS:
        if char in filename:
            filename = filename.replace(char, "_")
            changed = True

    # Handle reserved names
    path_obj = Path(filename)
    stem = path_obj.stem.upper()
    suffix = path_obj.suffix

    # Check if stem is a reserved name
    if stem in RESERVED_NAMES:
        filename = f"{path_obj.stem}_file{suffix}"
        changed = True

    # Check if the entire name (before first dot) is reserved
    elif "." in filename:
        base_name = filename.split(".")[0].upper()
        if base_name in RESERVED_NAMES:
            parts = filename.split(".")
            parts[0] = f"{parts[0]}_file"
            filename = ".".join(parts)
            changed = True

    # Remove trailing spaces and dots
    original_len = len(filename)
    filename = filename.rstrip(" .")
    if len(filename) != original_len:
        changed = True

    # Handle empty filename after sanitization
    if not filename or filename in ("", ".", "_"):
        filename = "unnamed_file"
        changed = True

    # Handle excessive length
    if len(filename) > MAX_FILENAME_LENGTH:
        # Create hash of original filename for uniqueness
        hash_suffix = hashlib.md5(original_filename.encode("utf-8")).hexdigest()[:8]

        # Keep extension if possible
        path_obj = Path(filename)
        extension = path_obj.suffix
        available_length = MAX_FILENAME_LENGTH - len(extension) - len(hash_suffix) - 1

        if available_length > 0:
            base_name = path_obj.stem[:available_length]
            filename = f"{base_name}_{hash_suffix}{extension}"
        else:
            # Extension too long, truncate everything
            filename = f"truncated_{hash_suffix}"

        changed = True

    # Handle name conflicts
    original_base = filename
    counter = 1
    while filename in existing_names:
        path_obj = Path(original_base)
        stem = path_obj.stem
        suffix = path_obj.suffix
        filename = f"{stem}_{counter}{suffix}"
        counter += 1
        changed = True

    return filename, changed


def sanitize_path(
    filepath: str, existing_paths: Optional[Set[str]] = None
) -> Tuple[str, Dict[str, str]]:
    """
    Sanitize a full file path for Windows compatibility.

    Args:
        filepath: The original file path
        existing_paths: Set of already used paths to avoid conflicts

    Returns:
        Tuple of (sanitized_path, changes_dict)
        changes_dict maps original components to sanitized versions
    """
    if existing_paths is None:
        _ = set()  # Parameter reserved for future conflict resolution

    # Normalize path separators
    filepath = filepath.replace("\\", "/")

    # Split path into components
    parts = filepath.split("/")
    sanitized_parts = []
    changes = {}
    existing_names_at_level: Set[str] = set()

    for part in parts:
        if not part:  # Skip empty parts (double slashes, etc.)
            continue

        sanitized_part, was_changed = sanitize_filename(part, existing_names_at_level)

        if was_changed:
            changes[part] = sanitized_part

        sanitized_parts.append(sanitized_part)
        existing_names_at_level.add(sanitized_part)

    sanitized_path = "/".join(sanitized_parts)

    # Handle path length limits (Windows has a 260 character limit)
    if len(sanitized_path) > MAX_PATH_LENGTH:
        # This is a complex case - for now, just warn
        logger.warning(
            f"Path too long after sanitization: {len(sanitized_path)} > {MAX_PATH_LENGTH}"
        )

    return sanitized_path, changes


def get_sanitization_mapping(file_list: List[str]) -> Dict[str, str]:
    """
    Generate a mapping of original filenames to sanitized versions.

    Args:
        file_list: List of original filenames from archive

    Returns:
        Dictionary mapping original names to sanitized names
    """
    mapping = {}
    used_names = set()

    # First pass: add all files that don't need sanitization to used_names
    for filename in file_list:
        if not needs_sanitization(filename):
            used_names.add(filename)

    # Second pass: sanitize problematic files ensuring uniqueness
    for filename in file_list:
        if needs_sanitization(filename):
            sanitized_path, changes = sanitize_path(filename, used_names)

            # Ensure the sanitized path is unique
            counter = 1
            while sanitized_path in used_names:
                # Extract directory and filename parts
                path_parts = sanitized_path.split("/")
                if len(path_parts) > 1:
                    # Has directory components
                    dirs = "/".join(path_parts[:-1])
                    filename_part = path_parts[-1]

                    # Add counter to filename part
                    path_obj = Path(filename_part)
                    stem = path_obj.stem
                    suffix = path_obj.suffix
                    new_filename = f"{stem}_{counter}{suffix}"
                    sanitized_path = f"{dirs}/{new_filename}"
                else:
                    # Just a filename
                    path_obj = Path(sanitized_path)
                    stem = path_obj.stem
                    suffix = path_obj.suffix
                    sanitized_path = f"{stem}_{counter}{suffix}"

                counter += 1

            mapping[filename] = sanitized_path
            used_names.add(sanitized_path)

    return mapping


def log_sanitization_changes(changes: Dict[str, str]) -> None:
    """
    Log sanitization changes with detailed information.

    Args:
        changes: Dictionary mapping original names to sanitized names
    """
    if not changes:
        return

    logger.warning(f"Windows filename compatibility: {len(changes)} files renamed")

    for original, sanitized in changes.items():
        reason = _get_sanitization_reason(original)
        logger.warning(f"  '{original}' -> '{sanitized}' (reason: {reason})")


# Public API functions for filename sanitization


def is_valid_windows_filename(filename: str) -> bool:
    """
    Check if a filename is valid for Windows.

    Args:
        filename: The filename to check

    Returns:
        True if the filename is valid on Windows, False otherwise
    """
    return not needs_sanitization(filename)


def get_safe_filename(filename: str, existing_names: Optional[Set[str]] = None) -> str:
    """
    Get a safe version of a filename that's compatible with Windows.

    Args:
        filename: The original filename
        existing_names: Set of existing filenames to avoid conflicts (optional)

    Returns:
        A sanitized filename that's safe to use on Windows
    """
    sanitized, _ = sanitize_filename(filename, existing_names)
    return sanitized


def sanitize_filename_simple(filename: str) -> str:
    """
    Simple filename sanitization function for public API.

    Args:
        filename: The filename to sanitize

    Returns:
        Sanitized filename
    """
    return get_safe_filename(filename)


def _get_sanitization_reason(filename: str) -> str:
    """Get human-readable reason for why a filename was sanitized."""
    reasons = []

    # Check for invalid characters
    invalid_found = [char for char in filename if char in INVALID_CHARS]
    if invalid_found:
        # Show printable characters, represent non-printable as hex
        char_display = []
        for char in invalid_found[:5]:  # Limit to first 5 chars
            if char.isprintable():
                char_display.append(f"'{char}'")
            else:
                char_display.append(f"0x{ord(char):02x}")
        reasons.append(f"invalid characters: {', '.join(char_display)}")

    # Check for reserved names
    name_without_ext = Path(filename).stem.upper()
    if name_without_ext in RESERVED_NAMES:
        reasons.append(f"reserved name: {name_without_ext}")

    # Check for trailing spaces or dots
    if filename.rstrip() != filename:
        reasons.append("trailing spaces")
    if filename.rstrip(".") != filename:
        reasons.append("trailing dots")

    # Check for excessive length
    if len(filename) > MAX_FILENAME_LENGTH:
        reasons.append(f"too long: {len(filename)} > {MAX_FILENAME_LENGTH}")

    # Check for directory traversal
    if ".." in filename:
        reasons.append("directory traversal")

    return "; ".join(reasons) if reasons else "unknown"

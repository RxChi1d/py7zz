# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""
Security utilities and checks for py7zz package.

Provides ZIP bomb detection and other security measures to prevent
malicious archive exploitation.
"""

from pathlib import Path, PureWindowsPath
from typing import List, Optional, Sequence, Union

from .exceptions import SecurityError, ZipBombError
from .filename_sanitizer import is_windows
from .logging_config import get_logger

# Get logger for this module
logger = get_logger(__name__)

# Security limits
DEFAULT_MAX_FILE_COUNT = 5000  # Maximum number of files in an archive
DEFAULT_MAX_COMPRESSION_RATIO = (
    100.0  # Maximum compression ratio (uncompressed/compressed)
)
DEFAULT_MAX_TOTAL_SIZE = 10 * 1024 * 1024 * 1024  # 10GB maximum total uncompressed size


class SecurityConfig:
    """Configuration for security checks."""

    def __init__(
        self,
        max_file_count: int = DEFAULT_MAX_FILE_COUNT,
        max_compression_ratio: float = DEFAULT_MAX_COMPRESSION_RATIO,
        max_total_size: int = DEFAULT_MAX_TOTAL_SIZE,
        enable_file_count_check: bool = True,
        enable_compression_ratio_check: bool = True,
        enable_size_check: bool = True,
    ):
        """
        Initialize security configuration.

        Args:
            max_file_count: Maximum number of files allowed in archive
            max_compression_ratio: Maximum compression ratio allowed
            max_total_size: Maximum total uncompressed size allowed (bytes)
            enable_file_count_check: Enable file count checking
            enable_compression_ratio_check: Enable compression ratio checking
            enable_size_check: Enable total size checking
        """
        self.max_file_count = max_file_count
        self.max_compression_ratio = max_compression_ratio
        self.max_total_size = max_total_size
        self.enable_file_count_check = enable_file_count_check
        self.enable_compression_ratio_check = enable_compression_ratio_check
        self.enable_size_check = enable_size_check


# Default security configuration
_default_security_config = SecurityConfig()


def set_default_security_config(config: SecurityConfig) -> None:
    """
    Set the default security configuration.

    Args:
        config: New security configuration
    """
    global _default_security_config
    _default_security_config = config


def get_default_security_config() -> SecurityConfig:
    """
    Get the current default security configuration.

    Returns:
        Current security configuration
    """
    return _default_security_config


def check_file_count_security(
    file_list: List[str], config: Optional[SecurityConfig] = None
) -> None:
    """
    Check if the file count in an archive exceeds security limits.

    Args:
        file_list: List of file names in the archive
        config: Security configuration (uses default if None)

    Raises:
        ZipBombError: If file count exceeds the security limit
    """
    if config is None:
        config = _default_security_config

    if not config.enable_file_count_check:
        return

    file_count = len(file_list)

    if file_count > config.max_file_count:
        logger.warning(
            f"Archive contains {file_count} files, exceeding security limit of {config.max_file_count}"
        )
        raise ZipBombError(
            f"Archive contains too many files ({file_count}), "
            f"which may indicate a ZIP bomb attack. "
            f"Maximum allowed: {config.max_file_count}",
            file_count=file_count,
        )

    logger.debug(
        f"File count check passed: {file_count} files (limit: {config.max_file_count})"
    )


def check_compression_ratio_security(
    compressed_size: int,
    uncompressed_size: int,
    config: Optional[SecurityConfig] = None,
) -> None:
    """
    Check if the compression ratio indicates a potential ZIP bomb.

    Args:
        compressed_size: Size of compressed data (bytes)
        uncompressed_size: Size of uncompressed data (bytes)
        config: Security configuration (uses default if None)

    Raises:
        ZipBombError: If compression ratio exceeds the security limit
    """
    if config is None:
        config = _default_security_config

    if not config.enable_compression_ratio_check:
        return

    if compressed_size <= 0:
        # Cannot calculate ratio, skip check
        return

    compression_ratio = uncompressed_size / compressed_size

    if compression_ratio > config.max_compression_ratio:
        logger.warning(
            f"Archive has compression ratio of {compression_ratio:.2f}, "
            f"exceeding security limit of {config.max_compression_ratio}"
        )
        raise ZipBombError(
            f"Archive has suspiciously high compression ratio ({compression_ratio:.2f}), "
            f"which may indicate a ZIP bomb attack. "
            f"Maximum allowed: {config.max_compression_ratio}",
            compression_ratio=compression_ratio,
        )

    logger.debug(
        f"Compression ratio check passed: {compression_ratio:.2f} "
        f"(limit: {config.max_compression_ratio})"
    )


def check_total_size_security(
    total_uncompressed_size: int, config: Optional[SecurityConfig] = None
) -> None:
    """
    Check if the total uncompressed size exceeds security limits.

    Args:
        total_uncompressed_size: Total uncompressed size (bytes)
        config: Security configuration (uses default if None)

    Raises:
        SecurityError: If total size exceeds the security limit
    """
    if config is None:
        config = _default_security_config

    if not config.enable_size_check:
        return

    if total_uncompressed_size > config.max_total_size:
        size_gb = total_uncompressed_size / (1024 * 1024 * 1024)
        limit_gb = config.max_total_size / (1024 * 1024 * 1024)

        logger.warning(
            f"Archive total uncompressed size is {size_gb:.2f}GB, "
            f"exceeding security limit of {limit_gb:.2f}GB"
        )
        raise SecurityError(
            f"Archive total uncompressed size ({size_gb:.2f}GB) exceeds "
            f"security limit ({limit_gb:.2f}GB)",
            limit_type="total_size",
        )

    logger.debug(
        f"Total size check passed: {total_uncompressed_size / (1024 * 1024):.2f}MB "
        f"(limit: {config.max_total_size / (1024 * 1024 * 1024):.2f}GB)"
    )


def perform_security_checks(
    file_list: List[str],
    compressed_size: Optional[int] = None,
    uncompressed_size: Optional[int] = None,
    config: Optional[SecurityConfig] = None,
) -> None:
    """
    Perform comprehensive security checks on archive data.

    Args:
        file_list: List of file names in the archive
        compressed_size: Total compressed size (bytes, optional)
        uncompressed_size: Total uncompressed size (bytes, optional)
        config: Security configuration (uses default if None)

    Raises:
        ZipBombError: If ZIP bomb patterns are detected
        SecurityError: If security limits are exceeded
    """
    if config is None:
        config = _default_security_config

    logger.debug("Starting security checks for archive")

    # Check file count
    check_file_count_security(file_list, config)

    # Check compression ratio if we have size information
    if compressed_size is not None and uncompressed_size is not None:
        check_compression_ratio_security(compressed_size, uncompressed_size, config)

    # Check total uncompressed size
    if uncompressed_size is not None:
        check_total_size_security(uncompressed_size, config)

    logger.debug("All security checks passed")


def build_7z_args(
    command: str,
    switches: Sequence[str],
    archive: Union[str, Path],
    names: Sequence[Union[str, Path]] = (),
) -> List[str]:
    """
    Assemble a 7zz argument list with switch parsing stopped before positionals.

    Args:
        command: 7zz command such as ``x``, ``e``, ``a``, ``l``, ``t`` or ``rn``
        switches: Switch arguments (``-o<dir>``, ``-y``, ``-p<password>``, ...)
        archive: Path to the archive
        names: Member names or file paths to place after the archive

    Returns:
        Argument list of the form ``[command, *switches, "--", archive, *names]``

    Reason: 7zz treats any argument starting with "-" as a switch and any
    argument starting with "@" as a list file, wherever it appears. An archive
    member named "-spf" would therefore be honoured as the "use fully qualified
    paths" switch and defeat the -o<dir> confinement, so every positional must
    sit behind the "--" stop-switch marker.
    """
    return [
        command,
        *[str(switch) for switch in switches],
        "--",
        str(archive),
        *[str(name) for name in names],
    ]


def validate_member_path(name: str, parameter: str = "arcname") -> None:
    """
    Reject archive member names that would escape their destination directory.

    Args:
        name: Member name to validate
        parameter: Name of the caller's parameter, used in the error message

    Raises:
        SecurityError: If the name is empty, absolute, carries a Windows drive
            or UNC prefix, or contains a ".." component
    """
    if not name or not name.strip():
        raise SecurityError(
            f"Empty {parameter} is not allowed", limit_type="path_traversal"
        )

    normalized = name.replace("\\", "/")

    # Reason: a leading separator covers POSIX absolute paths and UNC prefixes
    # ("//server/share", "\\\\server\\share") on every platform.
    if normalized.startswith("/"):
        raise SecurityError(
            f"Absolute paths are not allowed in {parameter}: {name!r}",
            limit_type="path_traversal",
        )

    # Reason: a drive prefix ("C:/x", "D:x") only escapes on Windows, where the
    # path join honours it. Checking it everywhere would reject legitimate POSIX
    # names such as "a:b.txt", so this one test is platform-dependent while the
    # rest of the validation is not. ensure_within_directory() remains the gate
    # that catches an actual escape on either platform.
    if is_windows() and PureWindowsPath(name).drive:
        raise SecurityError(
            f"Absolute paths are not allowed in {parameter}: {name!r}",
            limit_type="path_traversal",
        )

    if ".." in normalized.split("/"):
        raise SecurityError(
            f"Path traversal is not allowed in {parameter}: {name!r}",
            limit_type="path_traversal",
        )


def is_within_directory(base: Path, target: Path) -> bool:
    """
    Report whether a target path resolves inside a base directory.

    Args:
        base: Directory the target should stay inside
        target: Path to check

    Returns:
        True if the resolved target is the base directory or below it
    """
    resolved_base = base.resolve()
    resolved_target = target.resolve()

    return resolved_target == resolved_base or resolved_base in resolved_target.parents


def ensure_within_directory(
    base: Path, target: Path, parameter: str = "arcname"
) -> Path:
    """
    Confirm that a resolved target path stays inside a base directory.

    Args:
        base: Directory the target must stay inside
        target: Path to check
        parameter: Name of the caller's parameter, used in the error message

    Returns:
        The unchanged target path

    Raises:
        SecurityError: If the target resolves outside the base directory
    """
    if not is_within_directory(base, target):
        raise SecurityError(
            f"{parameter} resolves outside the target directory: {target}",
            limit_type="path_traversal",
        )

    return target


def redact_password_args(args: Sequence[str]) -> List[str]:
    """
    Replace 7zz password switches with a placeholder for safe error reporting.

    Args:
        args: Argument list that may contain a ``-p<password>`` switch

    Returns:
        A copy of the arguments with any password value masked

    Reason: subprocess.CalledProcessError renders its full command list in
    str(), so an unmasked argument list leaks the archive password into logs
    and into exception messages that reach the calling application.
    """
    rendered = [str(arg) for arg in args]

    # Reason: only switches can be passwords. Masking past the terminator would
    # rewrite member names such as "-photo.jpg" and hide the real failing
    # command, so stop at "--" when build_7z_args placed one.
    stop = rendered.index("--") if "--" in rendered else len(rendered)

    return [
        "-p***" if index < stop and arg.startswith("-p") and len(arg) > 2 else arg
        for index, arg in enumerate(rendered)
    ]

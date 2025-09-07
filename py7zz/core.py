# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""
Core functionality for py7zz package.
Provides subprocess wrapper and main SevenZipFile class.
"""

import os
import platform
import shutil
import subprocess
import tempfile
import warnings
from pathlib import Path
from typing import Callable, Iterator, List, Optional, Union

# Python 3.8 compatibility - use string annotation for subprocess.CompletedProcess
from .archive_info import ArchiveInfo
from .config import Config, Presets
from .exceptions import (
    ExtractionError,
    FilenameCompatibilityError,
)
from .exceptions import (
    PyFileNotFoundError as FileNotFoundError,
)
from .filename_sanitizer import (
    get_safe_filename,
    get_sanitization_mapping,
    is_windows,
    log_sanitization_changes,
    needs_sanitization,
)
from .logging_config import get_logger

# Removed updater imports - py7zz now only uses bundled binaries

# Get logger for this module
logger = get_logger(__name__)


def get_version() -> str:
    """Get current package version."""
    from .version import get_version as _get_version

    return _get_version()


def find_7z_binary() -> str:
    """
    Find 7zz binary in order of preference:
    1. Environment variable PY7ZZ_BINARY (development/testing only)
    2. Bundled binary (wheel package)
    3. Auto-downloaded binary (source installs)

    Note: py7zz ensures version consistency by never using system 7zz.
    Each py7zz version is paired with a specific 7zz version for isolation and reliability.
    """
    # Check environment variable first (for development/testing only)
    env_binary = os.environ.get("PY7ZZ_BINARY")
    if env_binary and Path(env_binary).exists():
        return env_binary

    # Use bundled binary (preferred for wheel packages) - unified directory
    current_dir = Path(__file__).parent
    binaries_dir = current_dir / "bin"

    # Platform-specific binary name but unified location
    system = platform.system().lower()
    binary_name = "7zz.exe" if system == "windows" else "7zz"

    binary_path = binaries_dir / binary_name

    if binary_path.exists():
        return str(binary_path)

    # Auto-download binary for source installs
    # Skip auto-download to prevent circular dependency with bundled_info
    # This feature requires manual version specification to avoid loops

    raise RuntimeError(
        "7zz binary not found. Please either:\n"
        "1. Ensure internet connection for auto-download (source installs)\n"
        "2. Set PY7ZZ_BINARY environment variable to point to your 7zz binary\n"
        "3. Check that the binary was properly bundled during build process"
    )


def run_7z(
    args: List[str], cwd: Optional[str] = None
) -> "subprocess.CompletedProcess[str]":
    """
    Execute 7zz command with given arguments.

    Args:
        args: Command arguments to pass to 7zz
        cwd: Working directory for the command

    Returns:
        CompletedProcess object with stdout, stderr, and return code

    Raises:
        subprocess.CalledProcessError: If command fails
        RuntimeError: If 7zz binary not found
    """
    binary = find_7z_binary()
    cmd = [binary] + args

    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, check=True
        )
        return result
    except subprocess.CalledProcessError as e:
        raise subprocess.CalledProcessError(
            e.returncode, cmd, e.output, e.stderr
        ) from e


def _is_filename_error(error_message: str) -> bool:
    """
    Check if the error message indicates a filename compatibility issue.

    Args:
        error_message: The error message from 7zz

    Returns:
        True if this appears to be a filename error
    """
    if not is_windows():
        return False

    error_lower = error_message.lower()

    # Common Windows filename error patterns
    filename_error_patterns = [
        "cannot create",
        "cannot use name",
        "invalid name",
        "the filename, directory name, or volume label syntax is incorrect",
        "the system cannot find the path specified",
        "cannot find the path",
        "access is denied",  # Sometimes occurs with reserved names
        "filename too long",
        "illegal characters in name",
    ]

    return any(pattern in error_lower for pattern in filename_error_patterns)


class SevenZipFile:
    """
    A class for working with 7z archives.
    Similar interface to zipfile.ZipFile.
    """

    def __init__(
        self,
        file: Union[str, Path],
        mode: str = "r",
        level: str = "normal",
        preset: Optional[str] = None,
        config: Optional[Config] = None,
    ):
        """
        Initialize SevenZipFile.

        Args:
            file: Path to the archive file
            mode: File mode ('r' for read, 'w' for write, 'a' for append)
            level: Compression level ('store', 'fastest', 'fast', 'normal', 'maximum', 'ultra')
            preset: Preset name ('fast', 'balanced', 'backup', 'ultra', 'secure', 'compatibility')
            config: Custom configuration object (overrides level and preset)
        """
        self.file = Path(file)
        self.mode = mode

        # Handle configuration priority: config > preset > level
        if config is not None:
            self.config = config
        elif preset is not None:
            self.config = Presets.get_preset(preset)
        else:
            # Convert level to config for backwards compatibility
            level_to_config = {
                "store": Config(level=0),
                "fastest": Config(level=1),
                "fast": Config(level=3),
                "normal": Config(level=5),
                "maximum": Config(level=7),
                "ultra": Config(level=9),
            }
            self.config = level_to_config.get(level, Config(level=5))

        # Keep level for backwards compatibility
        self.level = level

        self._validate_mode()
        self._validate_level()

    def _validate_mode(self) -> None:
        """Validate file mode."""
        if self.mode not in ("r", "w", "a"):
            raise ValueError(f"Invalid mode: {self.mode}")

    def _validate_level(self) -> None:
        """Validate compression level."""
        valid_levels = ["store", "fastest", "fast", "normal", "maximum", "ultra"]
        if self.level not in valid_levels:
            raise ValueError(f"Invalid compression level: {self.level}")

    def __enter__(self) -> "SevenZipFile":
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[object],
    ) -> None:
        """Context manager exit."""
        _ = exc_type, exc_val, exc_tb  # Unused parameters

    def _sanitize_filename(self, filename: str, max_length: int = 255) -> str:
        """
        Sanitize and truncate filename to handle extremely long names.

        Args:
            filename: Original filename
            max_length: Maximum allowed filename length

        Returns:
            Sanitized filename that fits within system limits
        """
        if len(filename) <= max_length:
            return filename

        # Import here to avoid circular imports

        # Preserve directory structure by splitting path
        path_parts = filename.split("/")
        if len(path_parts) > 1:
            # Handle directory structure
            directory_part = "/".join(path_parts[:-1])
            filename_part = path_parts[-1]

            # Recursively sanitize directory part
            sanitized_dir = self._sanitize_filename(directory_part, max_length // 2)
            sanitized_file = self._sanitize_single_filename(
                filename_part, max_length // 2
            )

            return f"{sanitized_dir}/{sanitized_file}"
        else:
            # Single filename
            return self._sanitize_single_filename(filename, max_length)

    def _sanitize_single_filename(self, filename: str, max_length: int = 255) -> str:
        """
        Sanitize a single filename (no directory separators).

        Args:
            filename: Single filename to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized filename
        """
        if len(filename) <= max_length:
            return filename

        import hashlib

        # Warn user about filename truncation
        warnings.warn(
            f"Filename too long, truncating: {filename[:50]}...",
            UserWarning,
            stacklevel=4,
        )

        # Preserve file extension
        name, ext = os.path.splitext(filename)

        # Reserve space for hash and extension
        hash_length = 8
        available_length = max_length - len(ext) - hash_length - 1  # -1 for underscore

        if available_length > 0:
            # Create unique hash to avoid conflicts
            hash_suffix = hashlib.md5(filename.encode("utf-8")).hexdigest()[
                :hash_length
            ]
            truncated_name = name[:available_length] + "_" + hash_suffix
            return truncated_name + ext
        else:
            # Extension is too long, create a completely new name
            hash_name = hashlib.md5(filename.encode("utf-8")).hexdigest()[
                : max_length - 4
            ]
            return hash_name + ".dat"  # Generic extension

    def _normalize_path(self, path: str) -> str:
        """
        Normalize archive path for consistent handling.

        Args:
            path: Raw path from archive listing

        Returns:
            Normalized path string, or empty string if path should be skipped
        """
        if not path or not path.strip():
            return ""

        # Remove leading/trailing whitespace
        path = path.strip()

        # Convert backslashes to forward slashes for consistency
        path = path.replace("\\", "/")

        # Skip directory entries (ending with /) - only return actual files
        # This helps with compatibility where different archive formats
        # may or may not list directory entries separately
        if path.endswith("/"):
            return ""

        # Remove leading slash if present (archives should use relative paths)
        path = path.lstrip("/")

        return path

    def add(self, name: Union[str, Path], arcname: Optional[str] = None) -> None:
        """
        Add file or directory to archive.

        Args:
            name: Path to file or directory to add
            arcname: Name in archive (defaults to name)
        """
        if self.mode == "r":
            raise ValueError("Cannot add to archive opened in read mode")

        name = Path(name)
        if not name.exists():
            raise FileNotFoundError(f"File not found: {name}")

        if arcname is None:
            # Simple case: add file with its original name
            self._add_simple(name)
        else:
            # Complex case: add file with custom archive name
            self._add_with_arcname(name, arcname)

    def _add_simple(self, name: Path) -> None:
        """
        Add file with its original name to the archive.

        Args:
            name: Path to file or directory to add
        """
        args = ["a"]  # add command

        # Add configuration arguments
        args.extend(self.config.to_7z_args())

        # Add file and archive paths
        args.extend([str(self.file), str(name)])

        try:
            run_7z(args)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to add {name} to archive: {e.stderr}") from e

    def _add_with_arcname(self, name: Path, arcname: str) -> None:
        """
        Add file with a custom archive name.

        Args:
            name: Path to file or directory to add
            arcname: Name to use in the archive
        """
        # For 7zz, we need to use a temporary directory structure
        # that matches the desired archive name
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_base = Path(temp_dir)

            # Sanitize filename for Windows compatibility if needed
            # This fixes the issue where Windows invalid characters cause OSError
            if is_windows() and needs_sanitization(arcname):
                sanitized_arcname = get_safe_filename(arcname)
                logger.warning(
                    f"Windows filename compatibility: '{arcname}' -> '{sanitized_arcname}'"
                )
                arcname = sanitized_arcname

            # Handle extremely long filenames by using a short temp name
            # but preserving the original arcname for the archive structure
            original_arcname = Path(arcname)

            # Create a safe temporary filename to avoid filesystem limits
            if len(str(original_arcname)) > 200:  # Conservative limit
                import hashlib
                import warnings

                # Warn about long filename
                warnings.warn(
                    f"Very long archive name, using temporary file approach: {arcname[:50]}...",
                    UserWarning,
                    stacklevel=3,
                )

                # Create short temp name but preserve extension for proper handling
                ext = original_arcname.suffix
                temp_name = (
                    "temp_"
                    + hashlib.md5(arcname.encode("utf-8")).hexdigest()[:16]
                    + ext
                )
                temp_target = temp_base / temp_name

                # We'll need to rename it in the archive later using 7z rename feature
                use_rename_approach = True
            else:
                # Normal case: filename is reasonable length
                temp_target = temp_base / original_arcname
                use_rename_approach = False

            # Create parent directories if needed
            temp_target.parent.mkdir(parents=True, exist_ok=True)

            if name.is_file():
                # For files: copy to temporary location with desired name
                shutil.copy2(name, temp_target)
            else:
                # For directories: create symlink or copy
                if hasattr(os, "symlink"):
                    try:
                        # Try to create a symlink (faster)
                        os.symlink(name, temp_target, target_is_directory=True)
                    except (OSError, NotImplementedError):
                        # Symlink failed, fall back to copying
                        shutil.copytree(name, temp_target)
                else:
                    # Platform doesn't support symlinks, copy the directory
                    shutil.copytree(name, temp_target)

            # Add the temporary file/directory to the archive
            args = ["a"]  # add command

            # Add configuration arguments
            args.extend(self.config.to_7z_args())

            # Add archive path (use absolute path to avoid issues with cwd)
            args.append(str(Path(self.file).resolve()))

            # Change to temp directory and add the file with relative path
            try:
                if use_rename_approach:
                    # First add with temporary name
                    temp_rel_name = temp_target.name
                    cmd = [find_7z_binary()] + args + [temp_rel_name]
                    subprocess.run(
                        cmd,
                        cwd=str(temp_base),
                        capture_output=True,
                        text=True,
                        check=True,
                    )

                    # Then rename to desired name in archive using 7z rename command
                    # Note: 7z rename command format: 7z rn <archive> <old_name> <new_name>
                    try:
                        rename_cmd = [
                            find_7z_binary(),
                            "rn",
                            str(Path(self.file).resolve()),
                            temp_rel_name,
                            arcname,
                        ]
                        subprocess.run(
                            rename_cmd,
                            capture_output=True,
                            text=True,
                            check=True,
                        )
                    except subprocess.CalledProcessError:
                        # If rename fails, the file is still added with temp name
                        # This is better than complete failure
                        warnings.warn(
                            f"Could not rename {temp_rel_name} to {arcname} in archive. "
                            f"File added with temporary name instead.",
                            UserWarning,
                            stacklevel=2,
                        )
                else:
                    # Normal case: add with original name
                    cmd = [find_7z_binary()] + args + [str(original_arcname)]
                    subprocess.run(
                        cmd,
                        cwd=str(temp_base),
                        capture_output=True,
                        text=True,
                        check=True,
                    )

                logger.debug(f"Successfully added {name} as {arcname} to archive")

            except subprocess.CalledProcessError as e:
                raise RuntimeError(
                    f"Failed to add {name} as {arcname} to archive: {e.stderr}"
                ) from e

    def extract(self, path: Union[str, Path] = ".", overwrite: bool = False) -> None:
        """
        Extract archive contents with Windows filename compatibility handling.

        Args:
            path: Directory to extract to
            overwrite: Whether to overwrite existing files
        """
        if self.mode == "w":
            raise ValueError("Cannot extract from archive opened in write mode")

        if not self.file.exists():
            raise FileNotFoundError(f"Archive not found: {self.file}")

        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        args = ["x", str(self.file), f"-o{path}"]

        if overwrite:
            args.append("-y")  # assume yes for all prompts

        # Add password if available
        if hasattr(self, "_password") and self._password is not None:
            # Convert bytes password to string for 7zz command
            password_str = (
                self._password.decode("utf-8")
                if isinstance(self._password, bytes)
                else str(self._password)
            )
            args.append(f"-p{password_str}")

        try:
            # First attempt: direct extraction
            run_7z(args)
            logger.debug("Archive extracted successfully without filename sanitization")

        except subprocess.CalledProcessError as e:
            # Check if this is a filename compatibility error
            error_message = e.stderr or str(e)

            if not _is_filename_error(error_message):
                # Not a filename error, re-raise as extraction error
                raise ExtractionError(
                    f"Failed to extract archive: {error_message}", e.returncode
                ) from e

            logger.info(
                "Extraction failed due to filename compatibility issues, attempting with sanitized names"
            )

            # Second attempt: extraction with filename sanitization
            try:
                self._extract_with_sanitization(path, overwrite)

            except Exception as sanitization_error:
                # If sanitization also fails, raise the original error with context
                raise ExtractionError(
                    f"Failed to extract archive even with filename sanitization. "
                    f"Original error: {error_message}. "
                    f"Sanitization error: {sanitization_error}",
                    e.returncode,
                ) from e

    def _extract_with_sanitization(self, target_path: Path, overwrite: bool) -> None:
        """
        Extract archive with filename sanitization for Windows compatibility.

        Args:
            target_path: Final destination for extracted files
            overwrite: Whether to overwrite existing files
        """
        # Get list of files in archive to determine what needs sanitization
        file_list = self._list_contents()

        # Check if any files need sanitization
        problematic_files = [f for f in file_list if needs_sanitization(f)]

        if not problematic_files:
            # No problematic files found, this might be a different issue
            raise FilenameCompatibilityError(
                "No problematic filenames detected, but extraction failed. "
                "This might be a different type of error.",
                problematic_files=problematic_files,
            )

        # Generate sanitization mapping
        sanitization_mapping = get_sanitization_mapping(file_list)

        if not sanitization_mapping:
            raise FilenameCompatibilityError(
                "Unable to generate filename sanitization mapping",
                problematic_files=problematic_files,
            )

        # Log the changes that will be made
        log_sanitization_changes(sanitization_mapping)

        # Use a temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Extract to temporary directory first
            args = ["x", str(self.file), f"-o{temp_path}"]
            if overwrite:
                args.append("-y")

            try:
                # This might still fail, but we'll handle it
                run_7z(args)

                # If extraction succeeds, move files with sanitized names
                self._move_sanitized_files(
                    temp_path, target_path, sanitization_mapping, overwrite
                )

            except subprocess.CalledProcessError:
                # Even extraction to temp dir failed, try individual file extraction
                logger.warning(
                    "Bulk extraction to temp directory failed, trying individual file extraction"
                )
                self._extract_files_individually(
                    target_path, sanitization_mapping, overwrite
                )

    def _move_sanitized_files(
        self,
        source_path: Path,
        target_path: Path,
        sanitization_mapping: dict,
        overwrite: bool,
    ) -> None:
        """
        Move files from temporary directory to target with sanitized names.

        Args:
            source_path: Source directory (temporary)
            target_path: Target directory (final destination)
            sanitization_mapping: Mapping of original to sanitized names
            overwrite: Whether to overwrite existing files
        """
        for root, _dirs, files in os.walk(source_path):
            root_path = Path(root)

            # Calculate relative path from source
            rel_path = root_path.relative_to(source_path)

            for file in files:
                original_file_path = rel_path / file
                original_file_str = str(original_file_path).replace("\\", "/")

                # Get sanitized name or use original
                sanitized_name = sanitization_mapping.get(
                    original_file_str, original_file_str
                )

                source_file = root_path / file
                target_file = target_path / sanitized_name

                # Create target directory if needed
                target_file.parent.mkdir(parents=True, exist_ok=True)

                # Move file
                if target_file.exists() and not overwrite:
                    logger.warning(f"Skipping existing file: {target_file}")
                    continue

                shutil.move(str(source_file), str(target_file))
                logger.debug(f"Moved {source_file} to {target_file}")

    def _extract_files_individually(
        self, target_path: Path, sanitization_mapping: dict, overwrite: bool
    ) -> None:
        """
        Extract files individually when bulk extraction fails.

        Args:
            target_path: Target directory for extraction
            sanitization_mapping: Mapping of original to sanitized names
            overwrite: Whether to overwrite existing files
        """
        extracted_count = 0
        failed_files = []

        for original_name, sanitized_name in sanitization_mapping.items():
            try:
                # Create a temporary file for this specific extraction
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_path = Path(temp_file.name)

                # Try to extract this specific file
                args = [
                    "e",
                    str(self.file),
                    f"-o{temp_path.parent}",
                    original_name,
                    "-y",
                ]

                try:
                    run_7z(args)

                    # Move to final location with sanitized name
                    final_path = target_path / sanitized_name
                    final_path.parent.mkdir(parents=True, exist_ok=True)

                    if final_path.exists() and not overwrite:
                        logger.warning(f"Skipping existing file: {final_path}")
                        temp_path.unlink(missing_ok=True)
                        continue

                    shutil.move(str(temp_path), str(final_path))
                    extracted_count += 1
                    logger.debug(
                        f"Individually extracted {original_name} as {sanitized_name}"
                    )

                except subprocess.CalledProcessError:
                    failed_files.append(original_name)
                    temp_path.unlink(missing_ok=True)

            except Exception as e:
                failed_files.append(original_name)
                logger.error(f"Failed to extract {original_name}: {e}")

        if failed_files:
            logger.warning(
                f"Failed to extract {len(failed_files)} files: {failed_files[:5]}..."
            )

        if extracted_count == 0:
            raise FilenameCompatibilityError(
                f"Unable to extract any files even with sanitization. Failed files: {failed_files[:10]}",
                problematic_files=list(sanitization_mapping.keys()),
                sanitized=True,
            )

        logger.info(
            f"Successfully extracted {extracted_count} files with sanitized names"
        )

    def _list_contents(self) -> List[str]:
        """
        List archive contents (internal method).

        Returns:
            List of file names in the archive
        """
        if not self.file.exists():
            raise FileNotFoundError(f"Archive not found: {self.file}")

        # Use detailed info parsing for reliable filename extraction
        # This avoids issues with space parsing in standard 7zz list output
        try:
            detailed_info = self._get_detailed_info()

            # Extract filenames, excluding directories
            files = [info.filename for info in detailed_info if not info.is_dir()]

            # Perform security checks on file list
            from .security import check_file_count_security

            try:
                check_file_count_security(files)
            except Exception as security_error:
                logger.warning(f"Security check failed: {security_error}")
                # Re-raise security exceptions to prevent processing dangerous archives
                raise

            logger.debug(
                f"Listed {len(files)} files from archive using detailed parser"
            )
            return files

        except Exception as e:
            # If detailed parsing fails, reraise as runtime error for consistency
            raise RuntimeError(f"Failed to list archive contents: {e}") from e

    def _get_detailed_info(self) -> List[ArchiveInfo]:
        """
        Internal method to get detailed archive information using 7zz -slt.

        Returns:
            List of ArchiveInfo objects with comprehensive metadata
        """
        from .detailed_parser import get_detailed_archive_info

        # Pass password if available
        password = getattr(self, "_password", None)
        return get_detailed_archive_info(self.file, password)

    # zipfile/tarfile compatibility methods

    def namelist(self) -> List[str]:
        """
        Return a list of archive members by name.
        Compatible with zipfile.ZipFile.namelist() and tarfile.TarFile.getnames().

        Only returns files, not directories, for consistency with zipfile behavior.
        """
        if self.mode == "w":
            from .exceptions import OperationError

            raise OperationError(
                "Cannot list contents from archive opened in write mode",
                operation="namelist",
            )

        # Use infolist() and filter out directories for consistency with zipfile behavior
        info_list = self.infolist()
        normalized_files = []
        for info in info_list:
            # Skip directories - zipfile.ZipFile.namelist() only returns files
            if info.is_dir():
                continue
            normalized = self._normalize_path(info.filename)
            if normalized:  # Skip empty or invalid entries
                normalized_files.append(normalized)
        return normalized_files

    def getnames(self) -> List[str]:
        """
        Return a list of archive members by name.
        Compatible with tarfile.TarFile.getnames().

        Returns the same result as namelist() for consistency.
        """
        return self.namelist()

    def infolist(self) -> List[ArchiveInfo]:
        """
        Return a list of ArchiveInfo objects for all members in the archive.
        Compatible with zipfile.ZipFile.infolist().

        Returns:
            List of ArchiveInfo objects with detailed metadata
        """
        return self._get_detailed_info()

    def getinfo(self, name: str) -> ArchiveInfo:
        """
        Return ArchiveInfo object for the specified member.
        Compatible with zipfile.ZipFile.getinfo().

        Args:
            name: Name of the archive member

        Returns:
            ArchiveInfo object for the specified member

        Raises:
            KeyError: If the member is not found in the archive
        """
        members = self._get_detailed_info()

        for member in members:
            if member.filename == name:
                return member

        raise KeyError(f"File '{name}' not found in archive")

    def getmembers(self) -> List[ArchiveInfo]:
        """
        Return a list of ArchiveInfo objects for all members in the archive.
        Compatible with tarfile.TarFile.getmembers().

        Returns:
            List of ArchiveInfo objects with detailed metadata
        """
        return self._get_detailed_info()

    def getmember(self, name: str) -> ArchiveInfo:
        """
        Return ArchiveInfo object for the specified member.
        Compatible with tarfile.TarFile.getmember().

        Args:
            name: Name of the archive member

        Returns:
            ArchiveInfo object for the specified member

        Raises:
            KeyError: If the member is not found in the archive
        """
        return self.getinfo(name)

    def extractall(
        self, path: Union[str, Path] = ".", members: Optional[List[str]] = None
    ) -> None:
        """
        Extract all members from the archive to the current working directory.
        Compatible with zipfile.ZipFile.extractall() and tarfile.TarFile.extractall().

        Args:
            path: Directory to extract to (default: current directory)
            members: List of member names to extract (default: all members)
        """
        if self.mode == "w":
            raise ValueError("Cannot extract from archive opened in write mode")

        if not self.file.exists():
            raise FileNotFoundError(f"Archive not found: {self.file}")

        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        if members is None:
            # Extract all members
            self.extract(path, overwrite=True)
        else:
            # Selective extraction: extract only specified members
            self._extract_selective_members(path, members)

    def _extract_selective_members(self, target_path: Path, members: List[str]) -> None:
        """
        Extract only specified members from the archive.

        Args:
            target_path: Directory to extract to
            members: List of member names to extract
        """
        if not members:
            return  # Nothing to extract

        # Build 7z command for selective extraction
        args = ["x", str(self.file), f"-o{target_path}", "-y"]

        # Add specific file names to extract
        args.extend(members)

        try:
            # First attempt: direct selective extraction
            run_7z(args)
            logger.debug(f"Successfully extracted {len(members)} selected members")

        except subprocess.CalledProcessError as e:
            # Check if this is a filename compatibility error on Windows
            error_message = e.stderr or str(e)

            if not _is_filename_error(error_message):
                # Not a filename error, re-raise as extraction error
                raise ExtractionError(
                    f"Failed to extract selected members: {error_message}", e.returncode
                ) from e

            logger.info(
                "Selective extraction failed due to filename compatibility issues, attempting with sanitization"
            )

            # Second attempt: extraction with filename sanitization
            try:
                self._extract_selective_with_sanitization(target_path, members)
            except Exception as sanitization_error:
                # If sanitization also fails, raise the original error with context
                raise ExtractionError(
                    f"Failed to extract selected members even with filename sanitization. "
                    f"Original error: {error_message}. "
                    f"Sanitization error: {sanitization_error}",
                    e.returncode,
                ) from e

    def _extract_selective_with_sanitization(
        self, target_path: Path, requested_members: List[str]
    ) -> None:
        """
        Extract selected members with filename sanitization for Windows compatibility.

        Args:
            target_path: Final destination for extracted files
            requested_members: List of member names to extract
        """
        # Get full list of files in archive to determine what needs sanitization
        all_files = self._list_contents()

        # Filter to only the requested members that exist in the archive
        existing_members = [f for f in requested_members if f in all_files]
        missing_members = [f for f in requested_members if f not in all_files]

        if missing_members:
            logger.warning(f"Requested members not found in archive: {missing_members}")

        if not existing_members:
            logger.warning("No requested members found in archive")
            return

        # Check if any of the requested files need sanitization
        problematic_files = [f for f in existing_members if needs_sanitization(f)]

        if not problematic_files:
            # No problematic files among requested members, this might be a different issue
            raise FilenameCompatibilityError(
                "No problematic filenames detected among requested members, but extraction failed. "
                "This might be a different type of error.",
                problematic_files=problematic_files,
            )

        # Generate sanitization mapping for all files (needed for context)
        full_file_list = self._list_contents()
        full_sanitization_mapping = get_sanitization_mapping(full_file_list)

        # Filter mapping to only requested members
        selective_mapping = {
            original: sanitized
            for original, sanitized in full_sanitization_mapping.items()
            if original in existing_members
        }

        if not selective_mapping:
            raise FilenameCompatibilityError(
                "Unable to generate filename sanitization mapping for requested members",
                problematic_files=problematic_files,
            )

        # Log the changes that will be made
        log_sanitization_changes(selective_mapping)

        # Extract files individually with sanitized names
        extracted_count = 0
        failed_files = []

        for original_name, sanitized_name in selective_mapping.items():
            try:
                # Create a temporary file for this specific extraction
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_path = Path(temp_file.name)

                # Try to extract this specific file
                args = [
                    "e",
                    str(self.file),
                    f"-o{temp_path.parent}",
                    original_name,
                    "-y",
                ]

                try:
                    run_7z(args)

                    # Move to final location with sanitized name
                    final_path = target_path / sanitized_name
                    final_path.parent.mkdir(parents=True, exist_ok=True)

                    if final_path.exists():
                        logger.warning(f"Overwriting existing file: {final_path}")
                        final_path.unlink()

                    shutil.move(str(temp_path), str(final_path))
                    extracted_count += 1
                    logger.debug(
                        f"Individually extracted {original_name} as {sanitized_name}"
                    )

                except subprocess.CalledProcessError:
                    failed_files.append(original_name)
                    temp_path.unlink(missing_ok=True)

            except Exception as e:
                failed_files.append(original_name)
                logger.error(f"Failed to extract {original_name}: {e}")

        if failed_files:
            logger.warning(
                f"Failed to extract {len(failed_files)} files: {failed_files[:5]}..."
            )

        if extracted_count == 0:
            raise FilenameCompatibilityError(
                f"Unable to extract any requested files even with sanitization. Failed files: {failed_files[:10]}",
                problematic_files=list(selective_mapping.keys()),
                sanitized=True,
            )

        logger.info(
            f"Successfully extracted {extracted_count} selected files with sanitized names"
        )

    def read(self, name: str) -> bytes:
        """
        Read and return the bytes of a file in the archive.
        Compatible with zipfile.ZipFile.read().

        Args:
            name: Name of the file in the archive

        Returns:
            File contents as bytes
        """
        if self.mode == "w":
            from .exceptions import OperationError

            raise OperationError(
                "Cannot read from archive opened in write mode", operation="read"
            )

        if not self.file.exists():
            raise FileNotFoundError(f"Archive not found: {self.file}")

        # Normalize the requested filename
        normalized_name = self._normalize_path(name)

        # Get the actual file list from infolist to ensure accurate matching
        # This uses the same data source as namelist() for consistency
        info_list = self.infolist()
        actual_files = [info.filename for info in info_list]
        actual_file_to_use = None

        # Try to find exact match first
        for actual_file in actual_files:
            if self._normalize_path(actual_file) == normalized_name:
                actual_file_to_use = actual_file
                break

        # If no exact match, try different path variations
        if not actual_file_to_use:
            for actual_file in actual_files:
                normalized_actual = self._normalize_path(actual_file)
                # Try with different separators and cases
                if (
                    normalized_actual.lower() == normalized_name.lower()
                    or normalized_actual.replace("/", "\\")
                    == normalized_name.replace("/", "\\")
                    or normalized_actual.endswith("/" + normalized_name)
                    or actual_file.endswith(normalized_name)
                ):
                    actual_file_to_use = actual_file
                    break

        if not actual_file_to_use:
            # List available files for better error message using normalized names
            available_files = [
                self._normalize_path(info.filename)
                for info in info_list
                if self._normalize_path(info.filename)
            ]
            raise FileNotFoundError(
                f"File '{name}' not found in archive. Available files: {available_files[:5]}..."
            )

        with tempfile.TemporaryDirectory() as tmpdir:
            # Extract specific file to temporary directory with full paths
            args = ["x", str(self.file), f"-o{tmpdir}", actual_file_to_use, "-y"]

            # Add password if available
            if hasattr(self, "_password") and self._password is not None:
                # Convert bytes password to string for 7zz command
                password_str = (
                    self._password.decode("utf-8")
                    if isinstance(self._password, bytes)
                    else str(self._password)
                )
                args.append(f"-p{password_str}")

            try:
                run_7z(args)

                # Try to find the extracted file - it might be in a subdirectory
                tmpdir_path = Path(tmpdir)

                # First try the direct path
                extracted_file = tmpdir_path / actual_file_to_use
                if extracted_file.exists():
                    return extracted_file.read_bytes()

                # If not found, search recursively in the temp directory
                for extracted_file in tmpdir_path.rglob("*"):
                    if extracted_file.is_file():
                        # Check if this matches our target file
                        relative_path = extracted_file.relative_to(tmpdir_path)
                        if (
                            str(relative_path) == actual_file_to_use
                            or str(relative_path).replace("\\", "/")
                            == actual_file_to_use.replace("\\", "/")
                            or extracted_file.name == Path(actual_file_to_use).name
                        ):
                            return extracted_file.read_bytes()

                raise FileNotFoundError(
                    f"File not found in archive after extraction: {actual_file_to_use}"
                )

            except subprocess.CalledProcessError as e:
                raise RuntimeError(
                    f"Failed to extract file {actual_file_to_use}: {e.stderr}"
                ) from e

    def writestr(self, filename: str, data: Union[str, bytes]) -> None:
        """
        Write a string or bytes to a file in the archive.
        Compatible with zipfile.ZipFile.writestr().

        Args:
            filename: Name of the file in the archive
            data: String or bytes data to write
        """
        if self.mode == "r":
            raise ValueError("Cannot write to archive opened in read mode")

        # Convert string to bytes if necessary
        if isinstance(data, str):
            data = data.encode("utf-8")

        with tempfile.TemporaryDirectory() as tmpdir:
            # Write data to temporary file
            temp_file = Path(tmpdir) / filename
            temp_file.parent.mkdir(parents=True, exist_ok=True)
            temp_file.write_bytes(data)

            # Add temporary file to archive
            self.add(temp_file, filename)

    def testzip(self) -> Optional[str]:
        """
        Test the archive for bad CRC or other errors.
        Compatible with zipfile.ZipFile.testzip().

        Returns:
            None if archive is OK, otherwise name of first bad file
        """
        if not self.file.exists():
            raise FileNotFoundError(f"Archive not found: {self.file}")

        args = ["t", str(self.file)]

        # Add password if available
        if hasattr(self, "_password") and self._password is not None:
            # Convert bytes password to string for 7zz command
            password_str = (
                self._password.decode("utf-8")
                if isinstance(self._password, bytes)
                else str(self._password)
            )
            args.append(f"-p{password_str}")

        try:
            run_7z(args)
            # If test passes, return None
            return None
        except subprocess.CalledProcessError as e:
            # Parse error to find first bad file
            if e.stderr:
                # Simple parsing - could be improved
                lines = e.stderr.split("\n")
                for line in lines:
                    if "Error" in line and ":" in line:
                        # Extract filename from error message
                        parts = line.split(":")
                        if len(parts) > 1:
                            return str(parts[0].strip())

            # If we can't parse the error, return a generic error indicator
            return "unknown_file"

    def close(self) -> None:
        """
        Close the archive.
        Compatible with zipfile.ZipFile.close() and tarfile.TarFile.close().
        """
        # py7zz doesn't maintain persistent file handles, so this is a no-op
        pass

    def __iter__(self) -> Iterator[str]:
        """
        Iterate over archive member names.
        Compatible with zipfile.ZipFile iteration.
        """
        return iter(self.namelist())

    def __contains__(self, name: str) -> bool:
        """
        Check if a file exists in the archive.
        Compatible with zipfile.ZipFile membership testing.
        """
        return name in self.namelist()

    # Additional zipfile/tarfile compatibility methods

    def open(self, name: str, mode: str = "r") -> "ArchiveFileReader":
        """
        Open a file from the archive as a file-like object.
        Compatible with zipfile.ZipFile.open().

        Args:
            name: Name of the file in the archive
            mode: File mode (only 'r' is supported for reading)

        Returns:
            File-like object for reading the archive member

        Raises:
            ValueError: If mode is not 'r' or archive is in write mode
            KeyError: If file is not found in archive
        """
        if mode != "r":
            raise ValueError("Only 'r' mode is supported for archive members")

        if self.mode == "w":
            raise ValueError("Cannot read from archive opened in write mode")

        # Check if file exists in archive
        if name not in self.namelist():
            raise KeyError(f"File '{name}' not found in archive")

        # Return file-like object
        return ArchiveFileReader(self, name)

    def readall(self) -> bytes:
        """
        Read all files from the archive and return as concatenated bytes.
        Compatible with some zipfile implementations.

        Returns:
            All file contents concatenated as bytes

        Raises:
            ValueError: If archive is opened in write mode
        """
        if self.mode == "w":
            raise ValueError("Cannot read from archive opened in write mode")

        all_data = b""
        for name in self.namelist():
            try:
                all_data += self.read(name)
            except Exception:
                # Skip files that cannot be read
                continue

        return all_data

    def setpassword(self, pwd: Optional[bytes]) -> None:
        """
        Set password for encrypted archive members.
        Compatible with zipfile.ZipFile.setpassword().

        Args:
            pwd: Password as bytes, or None to clear password

        Note:
            This method sets the password for future operations.
        """
        # Store password for future use
        self._password = pwd

    def comment(self) -> bytes:
        """
        Get archive comment.
        Compatible with zipfile.ZipFile.comment.

        Returns:
            Archive comment as bytes (empty if no comment)
        """
        # 7z archives don't typically have comments like ZIP files
        # Return empty bytes for compatibility
        return b""

    def setcomment(self, comment: bytes) -> None:
        """
        Set archive comment.
        Compatible with zipfile.ZipFile.comment setter.

        Args:
            comment: Comment to set as bytes

        Note:
            7z format doesn't support comments like ZIP.
            This method is provided for compatibility but has no effect.
        """
        # 7z format doesn't support comments
        # This is a no-op for compatibility
        pass

    def copy_member(self, member_name: str, target_archive: "SevenZipFile") -> None:
        """
        Copy a member from this archive to another archive.

        Args:
            member_name: Name of the member to copy
            target_archive: Target archive to copy to

        Raises:
            ValueError: If target archive is not in write mode
            KeyError: If member is not found
        """
        if target_archive.mode == "r":
            raise ValueError("Target archive must be opened in write mode")

        if member_name not in self.namelist():
            raise KeyError(f"Member '{member_name}' not found in archive")

        # Read member data and write to target
        member_data = self.read(member_name)
        target_archive.writestr(member_name, member_data)

    def rename_member(self, old_name: str, new_name: str) -> None:
        """
        Rename a member in the archive.

        Args:
            old_name: Current name of the member
            new_name: New name for the member

        Raises:
            ValueError: If archive is in read mode
            KeyError: If member is not found
            NotImplementedError: This operation requires archive recreation
        """
        if self.mode == "r":
            raise ValueError("Cannot rename members in read mode")

        if old_name not in self.namelist():
            raise KeyError(f"Member '{old_name}' not found in archive")

        # This operation would require recreating the entire archive
        # which is complex and potentially memory intensive
        raise NotImplementedError(
            "Member renaming requires archive recreation. "
            "Consider extracting, renaming files, and recreating the archive."
        )

    def delete_member(self, name: str) -> None:
        """
        Delete a member from the archive.

        Args:
            name: Name of the member to delete

        Raises:
            ValueError: If archive is in read mode
            KeyError: If member is not found
            NotImplementedError: This operation requires archive recreation
        """
        if self.mode == "r":
            raise ValueError("Cannot delete members in read mode")

        if name not in self.namelist():
            raise KeyError(f"Member '{name}' not found in archive")

        # This operation would require recreating the entire archive
        # which is complex and potentially memory intensive
        raise NotImplementedError(
            "Member deletion requires archive recreation. "
            "Consider extracting desired files and recreating the archive."
        )

    def filter_members(self, filter_func: Callable[[str], bool]) -> List[str]:
        """
        Filter archive members using a custom function.

        Args:
            filter_func: Function that takes a member name and returns bool

        Returns:
            List of member names that match the filter

        Example:
            >>> # Get only .txt files
            >>> txt_files = sz.filter_members(lambda name: name.endswith('.txt'))
        """
        return [name for name in self.namelist() if filter_func(name)]

    def get_member_size(self, name: str) -> int:
        """
        Get the uncompressed size of a member.

        Args:
            name: Name of the archive member

        Returns:
            Uncompressed size in bytes

        Raises:
            KeyError: If member is not found
        """
        member_info = self.getinfo(name)
        return member_info.file_size if hasattr(member_info, "file_size") else 0

    def get_member_compressed_size(self, name: str) -> int:
        """
        Get the compressed size of a member.

        Args:
            name: Name of the archive member

        Returns:
            Compressed size in bytes

        Raises:
            KeyError: If member is not found
        """
        member_info = self.getinfo(name)
        return (
            member_info.compressed_size
            if hasattr(member_info, "compressed_size")
            else 0
        )


class ArchiveFileReader:
    """
    File-like object for reading individual files from an archive.
    Compatible with the file object returned by zipfile.ZipFile.open().
    """

    def __init__(self, archive: SevenZipFile, member_name: str):
        """
        Initialize archive file reader.

        Args:
            archive: SevenZipFile instance
            member_name: Name of the member to read
        """
        self.archive = archive
        self.member_name = member_name
        self._data: Optional[bytes] = None
        self._position = 0
        self._closed = False

    def read(self, size: int = -1) -> bytes:
        """
        Read bytes from the archive member.

        Args:
            size: Number of bytes to read (-1 for all)

        Returns:
            Bytes read from the member
        """
        if self._closed:
            raise ValueError("I/O operation on closed file")

        if self._data is None:
            # Lazy load the data
            self._data = self.archive.read(self.member_name)

        if size == -1:
            # Read all remaining data
            result = self._data[self._position :]
            self._position = len(self._data)
        else:
            # Read specified number of bytes
            end_pos = min(self._position + size, len(self._data))
            result = self._data[self._position : end_pos]
            self._position = end_pos

        return result

    def readline(self, size: int = -1) -> bytes:
        """
        Read a line from the archive member.

        Args:
            size: Maximum number of bytes to read

        Returns:
            Line as bytes (including newline character)
        """
        if self._closed:
            raise ValueError("I/O operation on closed file")

        if self._data is None:
            self._data = self.archive.read(self.member_name)

        # Find next newline
        start_pos = self._position
        newline_pos = self._data.find(b"\n", start_pos)

        # Include the newline character, or read to end if no newline found
        end_pos = len(self._data) if newline_pos == -1 else newline_pos + 1

        # Apply size limit if specified
        if size > 0:
            end_pos = min(end_pos, start_pos + size)

        result = self._data[start_pos:end_pos]
        self._position = end_pos
        return result

    def readlines(self) -> List[bytes]:
        """
        Read all lines from the archive member.

        Returns:
            List of lines as bytes
        """
        if self._data is None:
            self._data = self.archive.read(self.member_name)

        lines = []
        while self._position < len(self._data):
            line = self.readline()
            if not line:
                break
            lines.append(line)

        return lines

    def seek(self, offset: int, whence: int = 0) -> int:
        """
        Seek to a position in the archive member.

        Args:
            offset: Offset to seek to
            whence: Seek reference (0=start, 1=current, 2=end)

        Returns:
            New position
        """
        if self._closed:
            raise ValueError("I/O operation on closed file")

        if self._data is None:
            self._data = self.archive.read(self.member_name)

        if whence == 0:  # SEEK_SET
            self._position = offset
        elif whence == 1:  # SEEK_CUR
            self._position += offset
        elif whence == 2:  # SEEK_END
            self._position = len(self._data) + offset
        else:
            raise ValueError("whence must be 0, 1, or 2")

        # Clamp position to valid range
        self._position = max(0, min(self._position, len(self._data)))
        return self._position

    def tell(self) -> int:
        """
        Get current position in the archive member.

        Returns:
            Current position
        """
        return self._position

    def close(self) -> None:
        """Close the file reader."""
        self._closed = True
        self._data = None

    def __enter__(self) -> "ArchiveFileReader":
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[object],
    ) -> None:
        """Context manager exit."""
        self.close()

    def __iter__(self) -> Iterator[bytes]:
        """Iterate over lines in the file."""
        while True:
            line = self.readline()
            if not line:
                break
            yield line

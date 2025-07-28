"""
Core functionality for py7zz package.
Provides subprocess wrapper and main SevenZipFile class.
"""

import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Iterator, List, Optional, Union

# Python 3.8 compatibility - use string annotation for subprocess.CompletedProcess
from .config import Config, Presets
from .exceptions import (
    ExtractionError,
    FilenameCompatibilityError,
)
from .exceptions import (
    PyFileNotFoundError as FileNotFoundError,
)
from .filename_sanitizer import (
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
    try:
        from .bundled_info import get_bundled_7zz_version
        from .updater import get_cached_binary

        seven_zz_version = get_bundled_7zz_version()
        cached_binary = get_cached_binary(seven_zz_version, auto_update=True)
        if cached_binary and cached_binary.exists():
            return str(cached_binary)
    except ImportError:
        pass  # updater module not available
    except Exception:
        pass  # Auto-download failed, continue to error

    raise RuntimeError(
        "7zz binary not found. Please either:\n"
        "1. Install py7zz from PyPI (pip install py7zz) to get bundled binary\n"
        "2. Ensure internet connection for auto-download (source installs)\n"
        "3. Set PY7ZZ_BINARY environment variable to point to your 7zz binary"
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

    def add(self, name: Union[str, Path], arcname: Optional[str] = None) -> None:
        """
        Add file or directory to archive.

        Args:
            name: Path to file or directory to add
            arcname: Name in archive (defaults to name) - currently not implemented
        """
        if self.mode == "r":
            raise ValueError("Cannot add to archive opened in read mode")

        name = Path(name)
        if not name.exists():
            raise FileNotFoundError(f"File not found: {name}")

        # Build 7z command
        # TODO: Implement arcname support in future version
        _ = arcname  # Unused parameter

        args = ["a"]  # add command

        # Add configuration arguments
        args.extend(self.config.to_7z_args())

        # Add file and archive paths
        args.extend([str(self.file), str(name)])

        try:
            run_7z(args)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to add {name} to archive: {e.stderr}") from e

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
        file_list = self.list_contents()

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

    def list_contents(self) -> List[str]:
        """
        List archive contents.

        Returns:
            List of file names in the archive
        """
        if not self.file.exists():
            raise FileNotFoundError(f"Archive not found: {self.file}")

        args = ["l", str(self.file)]

        try:
            result = run_7z(args)
            # Parse the output to extract file names
            lines = result.stdout.split("\n")
            files = []

            # Find the start of the file list (after the header)
            in_file_list = False
            for line in lines:
                if "---" in line and "Name" in lines[lines.index(line) - 1]:
                    in_file_list = True
                    continue
                elif in_file_list and "---" in line:
                    break
                elif in_file_list and line.strip():
                    # Extract filename from the line (last column)
                    parts = line.split()
                    if len(parts) >= 6:  # Ensure we have enough columns
                        filename = " ".join(
                            parts[5:]
                        )  # Join in case filename has spaces
                        files.append(filename)

            return files
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to list archive contents: {e.stderr}") from e

    # zipfile/tarfile compatibility methods

    def namelist(self) -> List[str]:
        """
        Return a list of archive members by name.
        Compatible with zipfile.ZipFile.namelist() and tarfile.TarFile.getnames().
        """
        return self.list_contents()

    def getnames(self) -> List[str]:
        """
        Return a list of archive members by name.
        Compatible with tarfile.TarFile.getnames().
        """
        return self.list_contents()

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
        # TODO: Implement selective extraction with members parameter
        if members is not None:
            raise NotImplementedError("Selective extraction not yet implemented")

        self.extract(path, overwrite=True)

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
            raise ValueError("Cannot read from archive opened in write mode")

        if not self.file.exists():
            raise FileNotFoundError(f"Archive not found: {self.file}")

        with tempfile.TemporaryDirectory() as tmpdir:
            # Extract specific file to temporary directory
            args = ["e", str(self.file), f"-o{tmpdir}", name, "-y"]

            try:
                run_7z(args)

                # Read the extracted file
                extracted_file = Path(tmpdir) / name
                if extracted_file.exists():
                    return extracted_file.read_bytes()
                else:
                    raise FileNotFoundError(f"File not found in archive: {name}")

            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Failed to extract file {name}: {e.stderr}") from e

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

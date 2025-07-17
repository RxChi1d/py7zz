"""
Core functionality for py7zz package.
Provides subprocess wrapper and main SevenZipFile class.
"""

import os
import platform
import subprocess
import tempfile
from pathlib import Path
from typing import Iterator, List, Optional, Union

from .config import Config, Presets
from .exceptions import PyFileNotFoundError as FileNotFoundError

# Removed updater imports - py7zz now only uses bundled binaries


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

    # Use bundled binary (preferred for wheel packages) - platform-specific directories
    current_dir = Path(__file__).parent
    binaries_dir = current_dir / "binaries"

    # Platform-specific directory and binary name
    system = platform.system().lower()
    if system == "darwin":
        binary_path = binaries_dir / "macos" / "7zz"
    elif system == "linux":
        binary_path = binaries_dir / "linux" / "7zz"
    elif system == "windows":
        binary_path = binaries_dir / "windows" / "7zz.exe"
    else:
        raise RuntimeError(f"Unsupported platform: {system}")

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


def run_7z(args: List[str], cwd: Optional[str] = None) -> subprocess.CompletedProcess[str]:
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
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
        return result
    except subprocess.CalledProcessError as e:
        raise subprocess.CalledProcessError(e.returncode, cmd, e.output, e.stderr) from e


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

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[object]) -> None:
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
        Extract archive contents.

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
            run_7z(args)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to extract archive: {e.stderr}") from e

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
                        filename = " ".join(parts[5:])  # Join in case filename has spaces
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

    def extractall(self, path: Union[str, Path] = ".", members: Optional[List[str]] = None) -> None:
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

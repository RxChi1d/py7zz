"""
Core functionality for py7zz package.
Provides subprocess wrapper and main SevenZipFile class.
"""

import os
import platform
import subprocess
from pathlib import Path
from typing import List, Optional, Union


def get_version() -> str:
    """Get current package version."""
    return "0.1.0"


def find_7z_binary() -> str:
    """
    Find 7zz binary in order of preference:
    1. Environment variable PY7ZZ_BINARY
    2. System PATH
    3. Bundled binary
    """
    # Check environment variable first
    env_binary = os.environ.get("PY7ZZ_BINARY")
    if env_binary and Path(env_binary).exists():
        return env_binary
    
    # Check system PATH
    import shutil
    system_binary = shutil.which("7zz") or shutil.which("7z")
    if system_binary:
        return system_binary
    
    # Fall back to bundled binary
    current_dir = Path(__file__).parent
    binaries_dir = current_dir / "binaries"
    
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
    
    raise RuntimeError(
        "7zz binary not found. Please install 7-Zip or set PY7ZZ_BINARY environment variable."
    )


def run_7z(args: List[str], cwd: Optional[str] = None) -> subprocess.CompletedProcess:
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
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return result
    except subprocess.CalledProcessError as e:
        raise subprocess.CalledProcessError(
            e.returncode, cmd, e.output, e.stderr
        ) from e


class SevenZipFile:
    """
    A class for working with 7z archives.
    Similar interface to zipfile.ZipFile.
    """
    
    def __init__(self, file: Union[str, Path], mode: str = "r", level: str = "normal"):
        """
        Initialize SevenZipFile.
        
        Args:
            file: Path to the archive file
            mode: File mode ('r' for read, 'w' for write, 'a' for append)
            level: Compression level ('store', 'fastest', 'fast', 'normal', 'maximum', 'ultra')
        """
        self.file = Path(file)
        self.mode = mode
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
        pass
    
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
        
        # Build 7z command
        # TODO: Implement arcname support in future version
        level_map = {
            "store": "0",
            "fastest": "1", 
            "fast": "3",
            "normal": "5",
            "maximum": "7",
            "ultra": "9"
        }
        
        args = [
            "a",  # add command
            f"-mx{level_map[self.level]}",  # compression level
            str(self.file),
            str(name)
        ]
        
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
            lines = result.stdout.split('\n')
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
                        filename = ' '.join(parts[5:])  # Join in case filename has spaces
                        files.append(filename)
            
            return files
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to list archive contents: {e.stderr}") from e
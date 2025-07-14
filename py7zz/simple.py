"""
Simple Function API (Layer 1)

Provides one-line solutions for common archive operations.
This is the highest-level interface designed for 80% of use cases.
"""

from pathlib import Path
from typing import List, Optional, Union

from .core import SevenZipFile
from .exceptions import FileNotFoundError


def create_archive(
    archive_path: Union[str, Path],
    files: List[Union[str, Path]],
    preset: str = "balanced",
    password: Optional[str] = None
) -> None:
    """
    Create an archive with specified files.
    
    Args:
        archive_path: Path to the archive to create
        files: List of files/directories to add
        preset: Compression preset ("fast", "balanced", "backup", "ultra")
        password: Optional password protection
        
    Example:
        >>> py7zz.create_archive("backup.7z", ["documents/", "photos/"])
        >>> py7zz.create_archive("secure.7z", ["secret.txt"], password="mypass")
    """
    # Convert preset to compression level
    preset_map = {
        "fast": "fastest",
        "balanced": "normal", 
        "backup": "maximum",
        "ultra": "ultra"
    }
    
    level = preset_map.get(preset, "normal")
    
    # Create archive
    with SevenZipFile(archive_path, "w", level) as sz:
        if password:
            # TODO: Implement password support
            pass
            
        for file_path in files:
            path = Path(file_path)
            if path.exists():
                sz.add(file_path)
            else:
                raise FileNotFoundError(f"File or directory not found: {file_path}")


def extract_archive(
    archive_path: Union[str, Path],
    output_dir: Union[str, Path] = ".",
    overwrite: bool = True
) -> None:
    """
    Extract all files from an archive.
    
    Args:
        archive_path: Path to the archive to extract
        output_dir: Directory to extract files to (default: current directory)
        overwrite: Whether to overwrite existing files
        
    Example:
        >>> py7zz.extract_archive("backup.7z", "extracted/")
        >>> py7zz.extract_archive("data.zip", overwrite=False)
    """
    if not Path(archive_path).exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")
    
    with SevenZipFile(archive_path, "r") as sz:
        sz.extract(output_dir, overwrite=overwrite)


def list_archive(archive_path: Union[str, Path]) -> List[str]:
    """
    List all files in an archive.
    
    Args:
        archive_path: Path to the archive to list
        
    Returns:
        List of file names in the archive
        
    Example:
        >>> files = py7zz.list_archive("backup.7z")
        >>> print(f"Archive contains {len(files)} files")
    """
    if not Path(archive_path).exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")
    
    with SevenZipFile(archive_path, "r") as sz:
        return sz.namelist()


def compress_file(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    preset: str = "balanced"
) -> Path:
    """
    Compress a single file.
    
    Args:
        input_path: File to compress
        output_path: Output archive path (auto-generated if None)
        preset: Compression preset
        
    Returns:
        Path to the created archive
        
    Example:
        >>> compressed = py7zz.compress_file("large_file.txt")
        >>> print(f"Compressed to: {compressed}")
    """
    input_path = Path(input_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"File not found: {input_path}")
    
    if output_path is None:
        output_path = input_path.with_suffix(input_path.suffix + ".7z")
    else:
        output_path = Path(output_path)
    
    create_archive(output_path, [input_path], preset=preset)
    return output_path


def compress_directory(
    input_dir: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    preset: str = "balanced"
) -> Path:
    """
    Compress an entire directory.
    
    Args:
        input_dir: Directory to compress
        output_path: Output archive path (auto-generated if None)
        preset: Compression preset
        
    Returns:
        Path to the created archive
        
    Example:
        >>> compressed = py7zz.compress_directory("my_project/")
        >>> print(f"Project archived to: {compressed}")
    """
    input_dir = Path(input_dir)
    
    if not input_dir.exists():
        raise FileNotFoundError(f"Directory not found: {input_dir}")
    
    if not input_dir.is_dir():
        raise ValueError(f"Path is not a directory: {input_dir}")
    
    if output_path is None:
        output_path = input_dir.with_suffix(".7z")
    else:
        output_path = Path(output_path)
    
    create_archive(output_path, [input_dir], preset=preset)
    return output_path


def get_archive_info(archive_path: Union[str, Path]) -> dict:
    """
    Get detailed information about an archive.
    
    Args:
        archive_path: Path to the archive
        
    Returns:
        Dictionary with archive information
        
    Example:
        >>> info = py7zz.get_archive_info("backup.7z")
        >>> print(f"Files: {info['file_count']}, Size: {info['compressed_size']}")
    """
    if not Path(archive_path).exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")
    
    archive_path = Path(archive_path)
    
    with SevenZipFile(archive_path, "r") as sz:
        files = sz.namelist()
        
    # Get file size
    compressed_size = archive_path.stat().st_size
    
    return {
        "file_count": len(files),
        "compressed_size": compressed_size,
        "files": files,
        "format": archive_path.suffix.lower(),
        "path": str(archive_path)
    }


def test_archive(archive_path: Union[str, Path]) -> bool:
    """
    Test archive integrity.
    
    Args:
        archive_path: Path to the archive to test
        
    Returns:
        True if archive is OK, False otherwise
        
    Example:
        >>> if py7zz.test_archive("backup.7z"):
        ...     print("Archive is OK")
        ... else:
        ...     print("Archive is corrupted")
    """
    if not Path(archive_path).exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")
    
    with SevenZipFile(archive_path, "r") as sz:
        result = sz.testzip()
        return result is None
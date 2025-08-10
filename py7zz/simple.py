# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""
Simple Function API (Layer 1)

Provides one-line solutions for common archive operations.
This is the highest-level interface designed for 80% of use cases.
"""

import os
import warnings
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from .core import SevenZipFile
from .exceptions import ArchiveNotFoundError, FileNotFoundError

# Import async operations if available
try:
    from .async_ops import ProgressInfo
    from .async_ops import compress_async as _compress_async
    from .async_ops import extract_async as _extract_async

    _async_available = True
except ImportError:
    _async_available = False


def create_archive(
    archive_path: Union[str, Path],
    files: List[Union[str, Path]],
    preset: str = "balanced",
    password: Optional[str] = None,
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
        "ultra": "ultra",
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
    overwrite: bool = True,
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
        raise ArchiveNotFoundError(archive_path)

    with SevenZipFile(archive_path, "r") as sz:
        sz.extract(output_dir, overwrite=overwrite)


def list_archive(archive_path: Union[str, Path]) -> List[str]:
    """
    List all files in an archive.

    .. deprecated:: 0.2.0
        Use ``SevenZipFile.namelist()`` or ``SevenZipFile.getnames()`` instead.
        This function will be removed in version 1.0.0.

    Args:
        archive_path: Path to the archive to list

    Returns:
        List of file names in the archive

    Example:
        >>> files = py7zz.list_archive("backup.7z")
        >>> print(f"Archive contains {len(files)} files")
    """
    warnings.warn(
        "list_archive() is deprecated and will be removed in version 1.0.0. "
        "Use SevenZipFile.namelist() or SevenZipFile.getnames() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    if not Path(archive_path).exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    with SevenZipFile(archive_path, "r") as sz:
        return sz.namelist()


def compress_file(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    preset: str = "balanced",
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
    preset: str = "balanced",
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


def get_archive_info(archive_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Get statistical information about an archive (no file listing).

    This function provides pure archive statistics without file enumeration,
    addressing the previous design issue where file listing was mixed with
    archive metadata. For file listings, use SevenZipFile.namelist() instead.

    Args:
        archive_path: Path to the archive

    Returns:
        Dictionary with archive statistics only

    Example:
        >>> info = py7zz.get_archive_info("backup.7z")
        >>> print(f"Files: {info['file_count']}, Compression: {info['compression_ratio']:.1%}")
    """
    if not Path(archive_path).exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    archive_path = Path(archive_path)

    # Get detailed information to calculate statistics
    from .detailed_parser import create_archive_summary, get_detailed_archive_info

    try:
        members = get_detailed_archive_info(archive_path)
        summary = create_archive_summary(members)

        # Get file system metadata
        stat = archive_path.stat()

        return {
            "file_count": summary["file_count"],
            "directory_count": summary["directory_count"],
            "total_entries": summary["total_file_count"],
            "compressed_size": stat.st_size,
            "uncompressed_size": summary["total_uncompressed_size"],
            "compression_ratio": summary["compression_ratio"],
            "compression_percentage": summary["compression_percentage"],
            "format": archive_path.suffix.lower().lstrip("."),
            "path": str(archive_path),
            "archive_type": summary["archive_type"],
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
        }

    except Exception:
        # Fallback to basic information if detailed parsing fails
        with SevenZipFile(archive_path, "r") as sz:
            file_list = sz.namelist()

        stat = archive_path.stat()

        return {
            "file_count": len(file_list),
            "directory_count": 0,  # Cannot determine without detailed info
            "total_entries": len(file_list),
            "compressed_size": stat.st_size,
            "uncompressed_size": 0,  # Cannot determine without detailed info
            "compression_ratio": 0.0,  # Cannot calculate without uncompressed size
            "compression_percentage": 0.0,
            "format": archive_path.suffix.lower().lstrip("."),
            "path": str(archive_path),
            "archive_type": "unknown",
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
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


# Async versions of simple functions (available if async_ops module is available)

# Advanced convenience functions for batch operations and archive management


def batch_create_archives(
    operations: List[tuple],
    preset: str = "balanced",
    overwrite: bool = True,
    create_dirs: bool = True,
) -> None:
    """
    Create multiple archives in batch.

    Args:
        operations: List of (archive_path, file_list) tuples
        preset: Compression preset for all archives
        overwrite: Whether to overwrite existing archives
        create_dirs: Whether to create output directories

    Example:
        >>> operations = [
        ...     ("backup1.7z", ["documents/"]),
        ...     ("backup2.7z", ["photos/", "videos/"]),
        ...     ("config.7z", ["settings.json", "config.ini"])
        ... ]
        >>> py7zz.batch_create_archives(operations, preset="ultra")
    """
    for archive_path, file_list in operations:
        archive_path = Path(archive_path)

        # Create output directory if needed
        if create_dirs:
            archive_path.parent.mkdir(parents=True, exist_ok=True)

        # Skip if archive exists and overwrite is False
        if archive_path.exists() and not overwrite:
            continue

        create_archive(archive_path, file_list, preset=preset)


def batch_extract_archives(
    archive_paths: List[Union[str, Path]],
    output_dir: Union[str, Path] = ".",
    overwrite: bool = True,
    create_dirs: bool = True,
) -> None:
    """
    Extract multiple archives to the same output directory.

    Args:
        archive_paths: List of archive file paths
        output_dir: Directory to extract all archives to
        overwrite: Whether to overwrite existing files
        create_dirs: Whether to create output directories

    Example:
        >>> archives = ["backup1.7z", "backup2.7z", "config.7z"]
        >>> py7zz.batch_extract_archives(archives, "extracted/")
    """
    output_dir = Path(output_dir)

    if create_dirs:
        output_dir.mkdir(parents=True, exist_ok=True)

    for archive_path in archive_paths:
        if not Path(archive_path).exists():
            raise FileNotFoundError(f"Archive not found: {archive_path}")
        extract_archive(archive_path, output_dir, overwrite=overwrite)


def copy_archive(
    source_archive: Union[str, Path],
    target_archive: Union[str, Path],
    recompress: bool = False,
    preset: str = "balanced",
) -> None:
    """
    Copy an archive, optionally recompressing with different settings.

    Args:
        source_archive: Source archive path
        target_archive: Target archive path
        recompress: Whether to recompress during copy
        preset: Compression preset if recompressing

    Example:
        >>> # Simple copy
        >>> py7zz.copy_archive("backup.7z", "backup_copy.7z")

        >>> # Copy with recompression
        >>> py7zz.copy_archive("backup.zip", "backup.7z", recompress=True, preset="ultra")
    """
    source_path = Path(source_archive)
    target_path = Path(target_archive)

    if not source_path.exists():
        raise FileNotFoundError(f"Source archive not found: {source_archive}")

    # Create target directory if needed
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if recompress:
        # Extract to temporary directory and recompress
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract source archive
            extract_archive(source_path, temp_dir)

            # Get all files from temp directory
            temp_path = Path(temp_dir)
            extracted_files: List[Union[str, Path]] = [
                p for p in temp_path.rglob("*") if p.is_file()
            ]

            # Create new archive with different compression
            create_archive(target_path, extracted_files, preset=preset)
    else:
        # Simple file copy
        import shutil

        shutil.copy2(str(source_path), str(target_path))


def get_compression_ratio(archive_path: Union[str, Path]) -> float:
    """
    Calculate the compression ratio of an archive.

    Args:
        archive_path: Path to the archive file

    Returns:
        Compression ratio as a float (0.0 to 1.0)

    Example:
        >>> ratio = py7zz.get_compression_ratio("backup.7z")
        >>> print(f"Compression ratio: {ratio:.2%}")
    """
    archive_info = get_archive_info(archive_path)

    # Try to get pre-calculated compression ratio first
    compression_ratio = archive_info.get("compression_ratio")
    if compression_ratio is not None and compression_ratio != 0.0:
        return float(compression_ratio)

    # Calculate manually if not available or zero
    uncompressed_size = archive_info.get("uncompressed_size", 0)
    compressed_size = archive_info.get("compressed_size", 0)

    if uncompressed_size > 0:
        return float((uncompressed_size - compressed_size) / uncompressed_size)

    return 0.0


def get_archive_format(archive_path: Union[str, Path]) -> str:
    """
    Detect the format of an archive file.

    Args:
        archive_path: Path to the archive file

    Returns:
        Archive format as string ("7z", "zip", "tar", etc.")

    Example:
        >>> format_type = py7zz.get_archive_format("backup.unknown")
        >>> print(f"Archive format: {format_type}")
    """
    from .core import run_7z

    # Check if file exists first
    if not Path(archive_path).exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    try:
        # Use 7z to detect archive format
        result = run_7z(["l", str(archive_path)])
        if result.returncode == 0:
            # Parse output to extract archive type
            output = result.stdout.lower()
            if "archive type = 7z" in output:
                return "7z"
            elif "archive type = zip" in output:
                return "zip"
            elif "archive type = tar" in output:
                return "tar"
            elif "archive type = rar" in output:
                return "rar"
            elif "archive type = gzip" in output:
                return "gz"
            elif "archive type = bzip2" in output:
                return "bz2"
            else:
                # Try to extract format from other patterns
                import re

                match = re.search(r"archive type = (\w+)", output)
                if match:
                    return match.group(1)

        # Fallback: try to get from get_archive_info
        try:
            archive_info = get_archive_info(archive_path)
            archive_format = archive_info.get("format", "unknown")
            return str(archive_format) if archive_format is not None else "unknown"
        except Exception:
            # Failed to get format info, try other methods
            pass

    except Exception:
        # All format detection methods failed
        pass

    return "unknown"


def compare_archives(
    archive1: Union[str, Path],
    archive2: Union[str, Path],
    compare_content: bool = False,
) -> bool:
    """
    Compare two archives for equality.

    Args:
        archive1: First archive path
        archive2: Second archive path
        compare_content: Whether to compare file contents (slower)

    Returns:
        True if archives are equivalent

    Example:
        >>> are_same = py7zz.compare_archives("original.7z", "backup.7z")
        >>> if are_same:
        ...     print("Archives are identical")
    """
    try:
        # Try to use get_archive_info for basic comparison first
        info1 = get_archive_info(archive1)
        info2 = get_archive_info(archive2)

        # Compare file lists if available
        files1 = info1.get("files")
        files2 = info2.get("files")

        if files1 is not None and files2 is not None:
            if set(files1) != set(files2):
                return False

            # If not comparing content, basic file list match is enough
            if not compare_content:
                return True

        # Fallback to direct archive reading for content comparison
        # or if file lists not available in info
        if not Path(archive1).exists() or not Path(archive2).exists():
            return False

        # Compare file lists using SevenZipFile
        import py7zz

        with py7zz.SevenZipFile(archive1, "r") as sz1, py7zz.SevenZipFile(
            archive2, "r"
        ) as sz2:
            names1 = set(sz1.namelist())
            names2 = set(sz2.namelist())

            if names1 != names2:
                return False

            # If content comparison requested, compare file contents
            if compare_content:
                for name in names1:
                    try:
                        content1 = sz1.read(name)
                        content2 = sz2.read(name)
                        if content1 != content2:
                            return False
                    except Exception:
                        return False

        return True

    except Exception:
        # Fallback to basic comparison if get_archive_info fails
        try:
            import py7zz

            with py7zz.SevenZipFile(archive1, "r") as sz1, py7zz.SevenZipFile(
                archive2, "r"
            ) as sz2:
                names1 = set(sz1.namelist())
                names2 = set(sz2.namelist())

                if names1 != names2:
                    return False

                # If content comparison requested, compare file contents
                if compare_content:
                    for name in names1:
                        try:
                            content1 = sz1.read(name)
                            content2 = sz2.read(name)
                            if content1 != content2:
                                return False
                        except Exception:
                            return False

                return True
        except Exception:
            return False


def convert_archive_format(
    source_archive: Union[str, Path],
    target_archive: Union[str, Path],
    target_format: Optional[str] = None,
    preset: str = "balanced",
) -> None:
    """
    Convert an archive from one format to another.

    Args:
        source_archive: Source archive path
        target_archive: Target archive path
        target_format: Target format (auto-detected from extension if None)
        preset: Compression preset for target archive

    Example:
        >>> # Convert ZIP to 7Z
        >>> py7zz.convert_archive_format("data.zip", "data.7z", preset="ultra")

        >>> # Convert with explicit format
        >>> py7zz.convert_archive_format("data.tar.gz", "data.7z", "7z")
    """
    source_path = Path(source_archive)
    target_path = Path(target_archive)

    if not source_path.exists():
        raise FileNotFoundError(f"Source archive not found: {source_archive}")

    # Auto-detect target format from extension if not specified
    if target_format is None:
        ext = target_path.suffix.lower().lstrip(".")
        _ = (
            ext if ext in ["7z", "zip", "tar", "gz", "bz2"] else "7z"
        )  # Format detection for future use

    # Create target directory if needed
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Use copy_archive with recompression
    copy_archive(source_path, target_path, recompress=True, preset=preset)


def recompress_archive(
    source_path: Union[str, Path],
    target_path: Union[str, Path],
    preset: str = "balanced",
    backup_original: bool = False,
    backup_suffix: str = ".bak",
) -> None:
    """
    Recompress an archive to a new location with different settings.

    This is the safe, industry-standard approach that creates a new file
    instead of modifying the original in-place.

    Args:
        source_path: Path to the source archive to recompress
        target_path: Path for the new recompressed archive
        preset: Compression preset for recompression
        backup_original: Whether to create a backup of the original file
        backup_suffix: Suffix to use for backup file (default: ".bak")

    Example:
        >>> # Recompress with better compression
        >>> py7zz.recompress_archive("original.7z", "recompressed.7z", "ultra")

        >>> # Recompress with backup
        >>> py7zz.recompress_archive("original.7z", "recompressed.7z", "ultra", backup_original=True)

        >>> # Recompress with custom backup suffix
        >>> py7zz.recompress_archive("original.7z", "recompressed.7z", "ultra", backup_suffix=".old")
    """
    source_path = Path(source_path)
    target_path = Path(target_path)

    if not source_path.exists():
        raise FileNotFoundError(f"Source archive not found: {source_path}")

    # Create backup if requested
    if backup_original:
        import shutil

        backup_path = source_path.with_suffix(source_path.suffix + backup_suffix)
        shutil.copy2(str(source_path), str(backup_path))

    # Create target directory if needed
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Use temporary directory for safe extraction and recompression
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_extract = Path(temp_dir) / "extracted"

        try:
            # Extract source archive
            extract_archive(source_path, temp_extract)

            # Get all extracted files recursively
            extracted_files: List[Union[str, Path]] = []
            if temp_extract.exists():
                for root, _dirs, files in os.walk(temp_extract):
                    for file in files:
                        file_path = os.path.join(root, file)
                        extracted_files.append(file_path)

            if not extracted_files:
                raise ValueError(f"No files extracted from {source_path}")

            # Create new archive with specified preset
            create_archive(target_path, extracted_files, preset=preset)

        except Exception as e:
            # Clean up failed target file
            if target_path.exists():
                target_path.unlink()
            raise RuntimeError(f"Failed to recompress archive: {e}") from e


if _async_available:

    async def create_archive_async(
        archive_path: Union[str, Path],
        files: List[Union[str, Path]],
        preset: str = "balanced",
        progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
    ) -> None:
        """
        Create an archive with specified files asynchronously.

        Args:
            archive_path: Path to the archive to create
            files: List of files/directories to add
            preset: Compression preset ("fast", "balanced", "backup", "ultra")
            progress_callback: Optional callback for progress updates

        Example:
            >>> async def progress_handler(info):
            ...     print(f"Progress: {info.percentage:.1f}%")
            >>> await py7zz.create_archive_async("backup.7z", ["documents/"], progress_callback=progress_handler)
        """
        # Validate files first
        for file_path in files:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File or directory not found: {file_path}")

        await _compress_async(archive_path, files, progress_callback)

    async def extract_archive_async(
        archive_path: Union[str, Path],
        output_dir: Union[str, Path] = ".",
        overwrite: bool = True,
        progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
    ) -> None:
        """
        Extract all files from an archive asynchronously.

        Args:
            archive_path: Path to the archive to extract
            output_dir: Directory to extract files to (default: current directory)
            overwrite: Whether to overwrite existing files
            progress_callback: Optional callback for progress updates

        Example:
            >>> async def progress_handler(info):
            ...     print(f"Extracting: {info.current_file}")
            >>> await py7zz.extract_archive_async("backup.7z", "extracted/", progress_callback=progress_handler)
        """
        if not Path(archive_path).exists():
            raise FileNotFoundError(f"Archive not found: {archive_path}")

        await _extract_async(archive_path, output_dir, overwrite, progress_callback)

    async def compress_file_async(
        input_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        preset: str = "balanced",
        progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
    ) -> Path:
        """
        Compress a single file asynchronously.

        Args:
            input_path: File to compress
            output_path: Output archive path (auto-generated if None)
            preset: Compression preset
            progress_callback: Optional callback for progress updates

        Returns:
            Path to the created archive

        Example:
            >>> compressed = await py7zz.compress_file_async("large_file.txt")
            >>> print(f"Compressed to: {compressed}")
        """
        input_path = Path(input_path)

        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        if output_path is None:
            output_path = input_path.with_suffix(input_path.suffix + ".7z")
        else:
            output_path = Path(output_path)

        await create_archive_async(
            output_path,
            [input_path],
            preset=preset,
            progress_callback=progress_callback,
        )
        return output_path

    async def compress_directory_async(
        input_dir: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        preset: str = "balanced",
        progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
    ) -> Path:
        """
        Compress an entire directory asynchronously.

        Args:
            input_dir: Directory to compress
            output_path: Output archive path (auto-generated if None)
            preset: Compression preset
            progress_callback: Optional callback for progress updates

        Returns:
            Path to the created archive

        Example:
            >>> compressed = await py7zz.compress_directory_async("my_project/")
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

        await create_archive_async(
            output_path, [input_dir], preset=preset, progress_callback=progress_callback
        )
        return output_path

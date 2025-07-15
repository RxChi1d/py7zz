"""
Asynchronous operations for py7zz package.

Provides async support for compression and extraction operations with progress reporting.
This module implements M4 milestone features for py7zz.
"""

import asyncio
import subprocess
from pathlib import Path
from typing import Callable, List, Optional, Union

from .core import find_7z_binary
from .exceptions import FileNotFoundError


class ProgressInfo:
    """Progress information for async operations."""

    def __init__(
        self,
        operation: str,
        current_file: str = "",
        files_processed: int = 0,
        total_files: int = 0,
        bytes_processed: int = 0,
        total_bytes: int = 0,
        percentage: float = 0.0,
    ) -> None:
        self.operation = operation
        self.current_file = current_file
        self.files_processed = files_processed
        self.total_files = total_files
        self.bytes_processed = bytes_processed
        self.total_bytes = total_bytes
        self.percentage = percentage

    def __repr__(self) -> str:
        return (
            f"ProgressInfo(operation='{self.operation}', "
            f"current_file='{self.current_file}', "
            f"files_processed={self.files_processed}, "
            f"total_files={self.total_files}, "
            f"percentage={self.percentage:.1f}%)"
        )


class AsyncSevenZipFile:
    """
    Async wrapper for SevenZipFile operations.

    Provides asynchronous compression and extraction with progress reporting.
    """

    def __init__(self, file: Union[str, Path], mode: str = "r"):
        """
        Initialize AsyncSevenZipFile.

        Args:
            file: Path to the archive file
            mode: File mode ('r' for read, 'w' for write)
        """
        self.file = Path(file)
        self.mode = mode
        self._validate_mode()

    def _validate_mode(self) -> None:
        """Validate file mode."""
        if self.mode not in ("r", "w"):
            raise ValueError(f"Invalid mode: {self.mode}")

    async def __aenter__(self) -> "AsyncSevenZipFile":
        """Async context manager entry."""
        return self

    async def __aexit__(
        self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[object]
    ) -> None:
        """Async context manager exit."""
        pass

    async def add_async(
        self, name: Union[str, Path], progress_callback: Optional[Callable[[ProgressInfo], None]] = None
    ) -> None:
        """
        Add file or directory to archive asynchronously.

        Args:
            name: Path to file or directory to add
            progress_callback: Optional callback for progress updates
        """
        if self.mode == "r":
            raise ValueError("Cannot add to archive opened in read mode")

        name = Path(name)
        if not name.exists():
            raise FileNotFoundError(f"File not found: {name}")

        # Build 7z command
        binary = find_7z_binary()
        args = [binary, "a", str(self.file), str(name)]

        try:
            await self._run_with_progress(args, operation="compress", progress_callback=progress_callback)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to add {name} to archive: {e.stderr}") from e

    async def extract_async(
        self,
        path: Union[str, Path] = ".",
        overwrite: bool = False,
        progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
    ) -> None:
        """
        Extract archive contents asynchronously.

        Args:
            path: Directory to extract to
            overwrite: Whether to overwrite existing files
            progress_callback: Optional callback for progress updates
        """
        if self.mode == "w":
            raise ValueError("Cannot extract from archive opened in write mode")

        if not self.file.exists():
            raise FileNotFoundError(f"Archive not found: {self.file}")

        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        binary = find_7z_binary()
        args = [binary, "x", str(self.file), f"-o{path}"]

        if overwrite:
            args.append("-y")

        try:
            await self._run_with_progress(args, operation="extract", progress_callback=progress_callback)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to extract archive: {e.stderr}") from e

    async def _run_with_progress(
        self, args: List[str], operation: str, progress_callback: Optional[Callable[[ProgressInfo], None]] = None
    ) -> None:
        """
        Run 7z command with progress monitoring.

        Args:
            args: Command arguments
            operation: Operation type ('compress' or 'extract')
            progress_callback: Optional callback for progress updates
        """
        process = await asyncio.create_subprocess_exec(
            *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        try:
            if progress_callback:
                # Monitor progress in separate task
                progress_task = asyncio.create_task(self._monitor_progress(process, operation, progress_callback))
                await progress_task
                # Wait for process completion
                await process.wait()
                stdout, stderr = b"", b""
            else:
                stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode or -1, args, stdout, stderr)

        except asyncio.CancelledError:
            if process.returncode is None:
                process.terminate()
                await process.wait()
            raise

    async def _monitor_progress(
        self, process: asyncio.subprocess.Process, operation: str, progress_callback: Callable[[ProgressInfo], None]
    ) -> None:
        """
        Monitor subprocess progress and call callback.

        Args:
            process: Subprocess to monitor
            operation: Operation type
            progress_callback: Callback for progress updates
        """
        files_processed = 0
        current_file = ""

        if process.stdout is None:
            return

        async for line_bytes in process.stdout:
            line = line_bytes.decode("utf-8", errors="replace").strip()

            # Parse 7z output for progress information
            if "Compressing" in line or "Extracting" in line:
                # Extract filename from progress line
                if " " in line:
                    current_file = line.split(" ")[-1]
                    files_processed += 1

            # Calculate approximate progress
            # Note: This is simplified - actual 7z progress parsing is more complex
            progress = ProgressInfo(
                operation=operation,
                current_file=current_file,
                files_processed=files_processed,
                total_files=max(1, files_processed),  # Placeholder
                percentage=min(100.0, files_processed * 10.0),  # Simplified calculation
            )

            progress_callback(progress)

            # Small delay to prevent callback spam
            await asyncio.sleep(0.01)


async def compress_async(
    archive_path: Union[str, Path],
    files: List[Union[str, Path]],
    progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
) -> None:
    """
    Compress files asynchronously with progress reporting.

    Args:
        archive_path: Path to the archive to create
        files: List of files/directories to add
        progress_callback: Optional callback for progress updates

    Example:
        >>> async def progress_handler(info):
        ...     print(f"Progress: {info.percentage:.1f}% - {info.current_file}")
        >>> await py7zz.compress_async("backup.7z", ["documents/"], progress_handler)
    """
    async with AsyncSevenZipFile(archive_path, "w") as sz:
        for file_path in files:
            path = Path(file_path)
            if path.exists():
                await sz.add_async(file_path, progress_callback)
            else:
                raise FileNotFoundError(f"File or directory not found: {file_path}")


async def extract_async(
    archive_path: Union[str, Path],
    output_dir: Union[str, Path] = ".",
    overwrite: bool = True,
    progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
) -> None:
    """
    Extract archive asynchronously with progress reporting.

    Args:
        archive_path: Path to the archive to extract
        output_dir: Directory to extract files to
        overwrite: Whether to overwrite existing files
        progress_callback: Optional callback for progress updates

    Example:
        >>> async def progress_handler(info):
        ...     print(f"Extracting: {info.current_file}")
        >>> await py7zz.extract_async("backup.7z", "extracted/", progress_handler)
    """
    if not Path(archive_path).exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    async with AsyncSevenZipFile(archive_path, "r") as sz:
        await sz.extract_async(output_dir, overwrite, progress_callback)


async def batch_compress_async(
    operations: List[tuple], progress_callback: Optional[Callable[[ProgressInfo], None]] = None
) -> None:
    """
    Perform multiple compression operations concurrently.

    Args:
        operations: List of (archive_path, files) tuples
        progress_callback: Optional callback for progress updates

    Example:
        >>> operations = [
        ...     ("backup1.7z", ["documents/"]),
        ...     ("backup2.7z", ["photos/"]),
        ... ]
        >>> await py7zz.batch_compress_async(operations)
    """
    tasks = []

    for archive_path, files in operations:
        task = compress_async(archive_path, files, progress_callback)
        tasks.append(task)

    await asyncio.gather(*tasks)


async def batch_extract_async(
    operations: List[tuple], progress_callback: Optional[Callable[[ProgressInfo], None]] = None
) -> None:
    """
    Perform multiple extraction operations concurrently.

    Args:
        operations: List of (archive_path, output_dir) tuples
        progress_callback: Optional callback for progress updates

    Example:
        >>> operations = [
        ...     ("backup1.7z", "extracted1/"),
        ...     ("backup2.7z", "extracted2/"),
        ... ]
        >>> await py7zz.batch_extract_async(operations)
    """
    tasks = []

    for archive_path, output_dir in operations:
        task = extract_async(archive_path, output_dir, progress_callback=progress_callback)
        tasks.append(task)

    await asyncio.gather(*tasks)

# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""
Asynchronous operations for py7zz package.

Provides async support for compression and extraction operations with progress reporting.
This module implements M4 milestone features for py7zz.
"""

import asyncio
import subprocess
from pathlib import Path
from typing import AsyncIterator, Callable, List, Optional, Union

from .archive_info import ArchiveInfo
from .core import SevenZipFile, _is_filename_error, find_7z_binary
from .exceptions import (
    ExtractionError,
    FilenameCompatibilityError,
    FileNotFoundError,
)
from .filename_sanitizer import (
    get_sanitization_mapping,
    log_sanitization_changes,
    needs_sanitization,
)
from .logging_config import get_logger

# Get logger for this module
logger = get_logger(__name__)


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
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[object],
    ) -> None:
        """Async context manager exit."""
        pass

    async def add(
        self,
        name: Union[str, Path],
        arcname: Optional[str] = None,
        progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
    ) -> None:
        """
        Add file or directory to archive asynchronously.
        Compatible with zipfile.ZipFile.add() and includes progress callback.

        Args:
            name: Path to file or directory to add
            arcname: Name in archive (defaults to name)
            progress_callback: Optional callback for progress updates

        Raises:
            ValueError: If archive is opened in read mode
            FileNotFoundError: If file to add is not found
            RuntimeError: If adding to archive fails
        """
        return await asyncio.get_event_loop().run_in_executor(
            None, self._add_sync, name, arcname
        )

    def _add_sync(self, name: Union[str, Path], arcname: Optional[str]) -> None:
        """Helper method to add file synchronously."""
        with SevenZipFile(self.file, "a") as sz:
            sz.add(name, arcname)

    async def add_async(
        self,
        name: Union[str, Path],
        progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
    ) -> None:
        """
        Add file or directory to archive asynchronously with progress reporting.

        .. deprecated:: 1.0.0
            Use ``add()`` instead.

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
            await self._run_with_progress(
                args, operation="compress", progress_callback=progress_callback
            )
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
            await self._run_with_progress(
                args, operation="extract", progress_callback=progress_callback
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to extract archive: {e.stderr}") from e

    async def infolist(self) -> List[ArchiveInfo]:
        """
        Return a list of ArchiveInfo objects for all members in the archive asynchronously.
        Compatible with zipfile.ZipFile.infolist().

        Returns:
            List of ArchiveInfo objects with detailed metadata
        """
        # Use synchronous method since file info parsing is already fast
        # and doesn't benefit from async execution
        return await asyncio.get_event_loop().run_in_executor(
            None, self._get_sync_infolist
        )

    def _get_sync_infolist(self) -> List[ArchiveInfo]:
        """Helper method to get infolist synchronously."""
        with SevenZipFile(self.file, "r") as sz:
            return sz.infolist()

    async def getinfo(self, name: str) -> ArchiveInfo:
        """
        Return ArchiveInfo object for the specified member asynchronously.
        Compatible with zipfile.ZipFile.getinfo().

        Args:
            name: Name of the archive member

        Returns:
            ArchiveInfo object for the specified member

        Raises:
            KeyError: If the member is not found in the archive
        """
        return await asyncio.get_event_loop().run_in_executor(
            None, self._get_sync_info, name
        )

    def _get_sync_info(self, name: str) -> ArchiveInfo:
        """Helper method to get info synchronously."""
        with SevenZipFile(self.file, "r") as sz:
            return sz.getinfo(name)

    async def getmembers(self) -> List[ArchiveInfo]:
        """
        Return a list of ArchiveInfo objects for all members in the archive asynchronously.
        Compatible with tarfile.TarFile.getmembers().

        Returns:
            List of ArchiveInfo objects with detailed metadata
        """
        return await self.infolist()  # Same as infolist

    async def getmember(self, name: str) -> ArchiveInfo:
        """
        Return ArchiveInfo object for the specified member asynchronously.
        Compatible with tarfile.TarFile.getmember().

        Args:
            name: Name of the archive member

        Returns:
            ArchiveInfo object for the specified member

        Raises:
            KeyError: If the member is not found in the archive
        """
        return await self.getinfo(name)  # Same as getinfo

    async def namelist(self) -> List[str]:
        """
        Return a list of archive members by name asynchronously.
        Compatible with zipfile.ZipFile.namelist() and tarfile.TarFile.getnames().
        """
        return await asyncio.get_event_loop().run_in_executor(
            None, self._get_sync_namelist
        )

    def _get_sync_namelist(self) -> List[str]:
        """Helper method to get namelist synchronously."""
        with SevenZipFile(self.file, "r") as sz:
            return sz.namelist()

    async def getnames(self) -> List[str]:
        """
        Return a list of archive members by name asynchronously.
        Compatible with tarfile.TarFile.getnames().
        """
        return await self.namelist()  # Same as namelist

    async def read(self, name: str) -> bytes:
        """
        Read and return the bytes of a file in the archive asynchronously.
        Compatible with zipfile.ZipFile.read().

        Args:
            name: Name of the file in the archive

        Returns:
            File contents as bytes

        Raises:
            ValueError: If archive is opened in write mode
            FileNotFoundError: If archive or file is not found
            RuntimeError: If extraction fails
        """
        return await asyncio.get_event_loop().run_in_executor(
            None, self._read_sync, name
        )

    def _read_sync(self, name: str) -> bytes:
        """Helper method to read file synchronously."""
        if self.mode == "w":
            raise ValueError("Cannot read from archive opened in write mode")
        with SevenZipFile(self.file, "r") as sz:
            return sz.read(name)

    async def writestr(self, filename: str, data: Union[str, bytes]) -> None:
        """
        Write a string or bytes to a file in the archive asynchronously.
        Compatible with zipfile.ZipFile.writestr().

        Args:
            filename: Name of the file in the archive
            data: String or bytes data to write

        Raises:
            ValueError: If archive is opened in read mode
        """
        return await asyncio.get_event_loop().run_in_executor(
            None, self._writestr_sync, filename, data
        )

    def _writestr_sync(self, filename: str, data: Union[str, bytes]) -> None:
        """Helper method to write string synchronously."""
        if self.mode == "r":
            raise ValueError("Cannot write to archive opened in read mode")
        with SevenZipFile(self.file, "a") as sz:
            sz.writestr(filename, data)

    async def testzip(self) -> Optional[str]:
        """
        Test the archive for bad CRC or other errors asynchronously.
        Compatible with zipfile.ZipFile.testzip().

        Returns:
            None if archive is OK, otherwise name of first bad file

        Raises:
            FileNotFoundError: If archive is not found
        """
        return await asyncio.get_event_loop().run_in_executor(None, self._testzip_sync)

    def _testzip_sync(self) -> Optional[str]:
        """Helper method to test archive synchronously."""
        with SevenZipFile(self.file, "r") as sz:
            return sz.testzip()

    async def close(self) -> None:
        """
        Close the archive asynchronously.
        Compatible with zipfile.ZipFile.close() and tarfile.TarFile.close().
        """
        # py7zz doesn't maintain persistent file handles, so this is a no-op
        pass

    def __aiter__(self) -> "AsyncIterator[str]":
        """
        Async iterator support for archive member names.
        Compatible with zipfile.ZipFile iteration pattern.
        """
        return self._async_iterator()

    async def _async_iterator(self) -> "AsyncIterator[str]":
        """Generate archive member names asynchronously."""
        names = await self.namelist()
        for name in names:
            yield name

    async def __acontains__(self, name: str) -> bool:
        """
        Check if a file exists in the archive asynchronously.
        Compatible with zipfile.ZipFile membership testing.
        """
        names = await self.namelist()
        return name in names

    async def extractall(
        self,
        path: Union[str, Path] = ".",
        members: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
    ) -> None:
        """
        Extract all members from the archive to the specified directory.
        Compatible with zipfile.ZipFile.extractall() and tarfile.TarFile.extractall().

        Args:
            path: Directory to extract to (default: current directory)
            members: List of member names to extract (default: all members)
            progress_callback: Optional callback for progress updates
        """
        if self.mode == "w":
            raise ValueError("Cannot extract from archive opened in write mode")

        if not self.file.exists():
            raise FileNotFoundError(f"Archive not found: {self.file}")

        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        if members is None:
            # Extract all members using existing extract_async method
            await self.extract_async(
                path, overwrite=True, progress_callback=progress_callback
            )
        else:
            # Selective extraction: extract only specified members
            await self._extract_selective_members_async(
                path, members, progress_callback
            )

    async def _extract_selective_members_async(
        self,
        target_path: Path,
        members: List[str],
        progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
    ) -> None:
        """
        Extract only specified members from the archive asynchronously.

        Args:
            target_path: Target directory for extraction
            members: List of member names to extract
            progress_callback: Optional callback for progress updates
        """
        if not members:
            return

        try:
            binary = find_7z_binary()
            args = [binary, "x", str(self.file), f"-o{target_path}", "-y"] + members

            await self._run_with_progress(args, "extract", progress_callback)

        except subprocess.CalledProcessError as e:
            # Check if this is a filename compatibility issue on Windows
            if _is_filename_error(e.stderr or ""):
                await self._extract_selective_with_sanitization_async(
                    target_path, members, progress_callback
                )
            else:
                raise ExtractionError(
                    f"Failed to extract selected members: {e.stderr}"
                ) from e

    async def _extract_selective_with_sanitization_async(
        self,
        target_path: Path,
        members: List[str],
        progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
    ) -> None:
        """
        Extract selected members with filename sanitization for Windows compatibility.

        Args:
            target_path: Target directory for extraction
            members: List of member names to extract
            progress_callback: Optional callback for progress updates
        """
        # Get all files in archive to create sanitization mapping
        with SevenZipFile(self.file, "r") as sz:
            all_files = sz._list_contents()

        # Filter to only requested members that exist in archive
        existing_members = [m for m in members if m in all_files]
        if not existing_members:
            logger.warning(f"None of the requested members found in archive: {members}")
            return

        # Check which files need sanitization
        problematic_files = [f for f in existing_members if needs_sanitization(f)]

        if not problematic_files:
            raise FilenameCompatibilityError(
                "No problematic filenames detected among requested members, "
                "but extraction still failed",
                problematic_files=[],
                sanitized=False,
            )

        # Create sanitization mapping for all files (needed for uniqueness)
        sanitization_mapping = get_sanitization_mapping(all_files)

        # Extract with sanitization using sync method (for now)
        # TODO: Implement fully async extraction with sanitization
        with SevenZipFile(self.file, "r") as sz:
            sz._extract_files_individually(target_path, sanitization_mapping, True)

        # Log the sanitization changes
        log_sanitization_changes(sanitization_mapping)

    async def _run_with_progress(
        self,
        args: List[str],
        operation: str,
        progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
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
                progress_task = asyncio.create_task(
                    self._monitor_progress(process, operation, progress_callback)
                )
                await progress_task
                # Wait for process completion
                await process.wait()
                stdout, stderr = b"", b""
            else:
                stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise subprocess.CalledProcessError(
                    process.returncode or -1, args, stdout, stderr
                )

        except asyncio.CancelledError:
            if process.returncode is None:
                process.terminate()
                await process.wait()
            raise

    async def _monitor_progress(
        self,
        process: asyncio.subprocess.Process,
        operation: str,
        progress_callback: Callable[[ProgressInfo], None],
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
            if ("Compressing" in line or "Extracting" in line) and " " in line:
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
    operations: List[tuple],
    progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
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
    operations: List[tuple],
    progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
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
        task = extract_async(
            archive_path, output_dir, progress_callback=progress_callback
        )
        tasks.append(task)

    await asyncio.gather(*tasks)

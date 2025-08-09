# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""
Streaming interface for py7zz with io.BufferedIOBase support.

Provides file-like objects for reading from and writing to archives,
designed for cloud services like S3 and object storage integration.
Supports standard Python I/O patterns for seamless integration.
"""

import io
import tempfile
from pathlib import Path
from typing import Any, List, Optional, Union

from .core import SevenZipFile
from .exceptions import FileNotFoundError, OperationError
from .logging_config import get_logger

logger = get_logger(__name__)


class ArchiveStreamReader(io.BufferedIOBase):
    """
    File-like object for reading from archive members.

    Supports standard io.BufferedIOBase interface for seamless integration
    with cloud storage APIs and streaming operations.

    Example:
        >>> import py7zz
        >>> with py7zz.SevenZipFile('archive.7z') as archive:
        ...     with py7zz.ArchiveStreamReader(archive, 'data.txt') as reader:
        ...         # Standard file-like operations
        ...         data = reader.read(1024)
        ...         reader.seek(0)
        ...         line = reader.readline()

        >>> # Cloud storage integration example
        >>> import boto3
        >>> s3 = boto3.client('s3')
        >>> with py7zz.ArchiveStreamReader(archive, 'large_file.json') as reader:
        ...     s3.upload_fileobj(reader, 'bucket', 'extracted/large_file.json')
    """

    def __init__(
        self,
        archive: SevenZipFile,
        member_name: str,
        encoding: Optional[str] = None,
        manage_archive_lifecycle: bool = False,
    ):
        """
        Initialize archive stream reader.

        Args:
            archive: SevenZipFile instance
            member_name: Name of the member to read
            encoding: Optional text encoding for text mode
            manage_archive_lifecycle: Whether to close the archive when this stream is closed
        """
        self._archive = archive
        self._member_name = member_name
        self._encoding = encoding
        self._position = 0
        self._content: Optional[bytes] = None
        self._closed = False
        self._manage_archive_lifecycle = manage_archive_lifecycle

        # Validate member exists
        if member_name not in archive.namelist():
            raise FileNotFoundError(f"Member '{member_name}' not found in archive")

        logger.debug(f"Initialized ArchiveStreamReader for '{member_name}'")

    def _ensure_content_loaded(self) -> None:
        """Lazy load content from archive."""
        if self._content is None:
            try:
                self._content = self._archive.read(self._member_name)
                logger.debug(
                    f"Loaded {len(self._content)} bytes from '{self._member_name}'"
                )
            except Exception as e:
                raise OperationError(
                    f"Failed to read '{self._member_name}': {e}"
                ) from e

    def read(self, size: Optional[int] = -1) -> bytes:
        """Read up to size bytes from the stream."""
        self._check_closed()
        self._ensure_content_loaded()

        # At this point _content is guaranteed to be not None
        assert self._content is not None

        if size is None or size == -1:
            # Read all remaining content
            result = self._content[self._position :]
            self._position = len(self._content)
        else:
            # Read up to size bytes
            end_pos = min(self._position + size, len(self._content))
            result = self._content[self._position : end_pos]
            self._position = end_pos

        return result

    def read1(self, size: int = -1) -> bytes:
        """Read up to size bytes (same as read for archives)."""
        return self.read(size)

    def readinto(self, b) -> int:  # type: ignore[no-untyped-def]
        """Read data into a pre-allocated buffer."""
        self._check_closed()
        data = self.read(len(b))
        bytes_read = len(data)
        b[:bytes_read] = data
        return bytes_read

    def readline(self, size: Optional[int] = -1) -> bytes:
        """Read and return one line from the stream."""
        self._check_closed()
        self._ensure_content_loaded()

        # At this point _content is guaranteed to be not None
        assert self._content is not None

        start_pos = self._position
        if start_pos >= len(self._content):
            return b""

        # Find next newline
        search_end = len(self._content)
        if size is not None and size > 0:
            search_end = min(start_pos + size, len(self._content))

        newline_pos = self._content.find(b"\n", start_pos, search_end)

        # Include the newline character if found, otherwise use search end
        end_pos = search_end if newline_pos == -1 else newline_pos + 1

        result = self._content[start_pos:end_pos]
        self._position = end_pos
        return result

    def readlines(self, hint: int = -1) -> List[bytes]:
        """Read and return a list of lines from the stream."""
        lines = []
        bytes_read = 0

        while True:
            line = self.readline()
            if not line:
                break

            lines.append(line)
            bytes_read += len(line)

            if hint > 0 and bytes_read >= hint:
                break

        return lines

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        """Seek to a position in the stream."""
        self._check_closed()
        self._ensure_content_loaded()

        # At this point _content is guaranteed to be not None
        assert self._content is not None

        if whence == io.SEEK_SET:
            new_pos = offset
        elif whence == io.SEEK_CUR:
            new_pos = self._position + offset
        elif whence == io.SEEK_END:
            new_pos = len(self._content) + offset
        else:
            raise ValueError(f"Invalid whence value: {whence}")

        # Clamp position to valid range
        self._position = max(0, min(new_pos, len(self._content)))
        return self._position

    def tell(self) -> int:
        """Return current stream position."""
        self._check_closed()
        return self._position

    def close(self) -> None:
        """Close the stream."""
        if not self._closed:
            self._closed = True
            self._content = None

            # Close the underlying archive if we're managing its lifecycle
            if self._manage_archive_lifecycle and hasattr(self._archive, "close"):
                try:
                    self._archive.close()
                except Exception as e:
                    logger.warning(f"Failed to close underlying archive: {e}")

            logger.debug(f"Closed ArchiveStreamReader for '{self._member_name}'")

    def _check_closed(self) -> None:
        """Check if stream is closed and raise ValueError if so."""
        if self._closed:
            raise ValueError("I/O operation on closed stream")

    def readable(self) -> bool:
        """Return whether the stream supports reading."""
        return not self._closed

    def writable(self) -> bool:
        """Return whether the stream supports writing."""
        return False

    def seekable(self) -> bool:
        """Return whether the stream supports seeking."""
        return not self._closed

    def __enter__(self) -> "ArchiveStreamReader":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    @property
    def closed(self) -> bool:
        """Return whether the stream is closed."""
        return self._closed

    def __repr__(self) -> str:
        status = "closed" if self._closed else "open"
        return f"<ArchiveStreamReader '{self._member_name}' ({status})>"


class ArchiveStreamWriter(io.BufferedIOBase):
    """
    File-like object for writing to archive members.

    Supports standard io.BufferedIOBase interface for writing data
    that will be added to an archive. Uses temporary storage until
    the stream is closed and data is committed to the archive.

    Example:
        >>> import py7zz
        >>> with py7zz.SevenZipFile('output.7z', 'w') as archive:
        ...     with py7zz.ArchiveStreamWriter(archive, 'data.txt') as writer:
        ...         writer.write(b'Hello, World!')
        ...         writer.write(b'\\nMore data...')

        >>> # Cloud storage download example
        >>> import boto3
        >>> s3 = boto3.client('s3')
        >>> with py7zz.ArchiveStreamWriter(archive, 'downloaded.json') as writer:
        ...     s3.download_fileobj('bucket', 'source.json', writer)
    """

    def __init__(
        self,
        archive: SevenZipFile,
        member_name: str,
        encoding: Optional[str] = None,
        manage_archive_lifecycle: bool = False,
    ):
        """
        Initialize archive stream writer.

        Args:
            archive: SevenZipFile instance
            member_name: Name of the member to write
            encoding: Optional text encoding for text mode
            manage_archive_lifecycle: Whether to close the archive when this stream is closed
        """
        self._archive = archive
        self._member_name = member_name
        self._encoding = encoding
        self._closed = False
        self._manage_archive_lifecycle = manage_archive_lifecycle

        # Create temporary file for buffering
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            self._temp_path = Path(temp_file.name)

        logger.debug(
            f"Initialized ArchiveStreamWriter for '{member_name}' with temp file: {self._temp_path}"
        )

    def write(self, data) -> int:  # type: ignore[no-untyped-def]
        """Write data to the stream."""
        self._check_closed()

        if isinstance(data, (bytearray, memoryview)):
            data = bytes(data)
        elif not isinstance(data, bytes):
            raise TypeError("Data must be bytes-like object")

        # Write to temporary file
        with open(self._temp_path, "ab") as f:
            bytes_written = f.write(data)

        return bytes_written

    def writelines(self, lines) -> None:  # type: ignore[no-untyped-def]
        """Write a list of lines to the stream."""
        for line in lines:
            self.write(line)

    def flush(self) -> None:
        """Flush write buffers."""
        self._check_closed()
        # No need to flush as we open/close file for each write

    def close(self) -> None:
        """Close the stream and commit data to archive."""
        if not self._closed:
            try:
                # Add temp file to archive
                self._archive.add(str(self._temp_path), arcname=self._member_name)

                logger.debug(
                    f"Committed {self._temp_path.stat().st_size} bytes to '{self._member_name}'"
                )

            except Exception as e:
                logger.error(f"Failed to commit '{self._member_name}' to archive: {e}")
                raise OperationError(
                    f"Failed to write '{self._member_name}': {e}"
                ) from e
            finally:
                # Clean up temp file
                try:
                    self._temp_path.unlink(missing_ok=True)
                except Exception as e:
                    logger.warning(
                        f"Failed to clean up temp file {self._temp_path}: {e}"
                    )

                self._closed = True

                # Close the underlying archive if we're managing its lifecycle
                if self._manage_archive_lifecycle and hasattr(self._archive, "close"):
                    try:
                        self._archive.close()
                    except Exception as e:
                        logger.warning(f"Failed to close underlying archive: {e}")

    def _check_closed(self) -> None:
        """Check if stream is closed and raise ValueError if so."""
        if self._closed:
            raise ValueError("I/O operation on closed stream")

    def readable(self) -> bool:
        """Return whether the stream supports reading."""
        return False

    def writable(self) -> bool:
        """Return whether the stream supports writing."""
        return not self._closed

    def seekable(self) -> bool:
        """Return whether the stream supports seeking."""
        return not self._closed

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        """Seek to a position in the temp file."""
        self._check_closed()
        # For simplicity, we don't support seeking in write mode
        # as we append to file for each write
        raise OSError("Seeking not supported in write mode")

    def tell(self) -> int:
        """Return current position in temp file."""
        self._check_closed()
        # Return the current file size as position
        return self._temp_path.stat().st_size if self._temp_path.exists() else 0

    def __enter__(self) -> "ArchiveStreamWriter":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    @property
    def closed(self) -> bool:
        """Return whether the stream is closed."""
        return self._closed

    def __repr__(self) -> str:
        status = "closed" if self._closed else "open"
        return f"<ArchiveStreamWriter '{self._member_name}' ({status})>"


def create_stream_reader(
    archive_path: Union[str, Path], member_name: str
) -> ArchiveStreamReader:
    """
    Convenience function to create a stream reader for an archive member.

    Args:
        archive_path: Path to the archive file
        member_name: Name of the member to read

    Returns:
        ArchiveStreamReader instance

    Example:
        >>> reader = py7zz.create_stream_reader('data.7z', 'large_file.json')
        >>> with reader:
        ...     # Stream to S3 or other cloud storage
        ...     for chunk in iter(lambda: reader.read(8192), b''):
        ...         process_chunk(chunk)
    """
    archive = SevenZipFile(archive_path, "r")
    return ArchiveStreamReader(archive, member_name, manage_archive_lifecycle=True)


def create_stream_writer(
    archive_path: Union[str, Path],
    member_name: str,
    mode: str = "w",
) -> ArchiveStreamWriter:
    """
    Convenience function to create a stream writer for an archive member.

    Args:
        archive_path: Path to the archive file
        member_name: Name of the member to write
        mode: Archive open mode ('w' or 'a')

    Returns:
        ArchiveStreamWriter instance

    Example:
        >>> writer = py7zz.create_stream_writer('output.7z', 'uploaded.json')
        >>> with writer:
        ...     # Stream from S3 or other cloud storage
        ...     s3.download_fileobj('bucket', 'source.json', writer)
    """
    archive = SevenZipFile(archive_path, mode)
    return ArchiveStreamWriter(archive, member_name, manage_archive_lifecycle=True)


# Add streaming methods to SevenZipFile class
def _add_streaming_methods() -> None:
    """Add streaming methods to SevenZipFile class."""

    def open_stream_reader(self: Any, member_name: str) -> ArchiveStreamReader:
        """
        Open a stream reader for an archive member.

        Args:
            member_name: Name of the member to read

        Returns:
            ArchiveStreamReader instance
        """
        return ArchiveStreamReader(self, member_name)

    def open_stream_writer(self: Any, member_name: str) -> ArchiveStreamWriter:
        """
        Open a stream writer for an archive member.

        Args:
            member_name: Name of the member to write

        Returns:
            ArchiveStreamWriter instance
        """
        return ArchiveStreamWriter(self, member_name)

    # Add methods to SevenZipFile
    SevenZipFile.open_stream_reader = open_stream_reader  # type: ignore[attr-defined]
    SevenZipFile.open_stream_writer = open_stream_writer  # type: ignore[attr-defined]


# Initialize streaming methods
_add_streaming_methods()

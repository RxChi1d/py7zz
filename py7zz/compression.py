"""
Compression Algorithm Interface Module

Provides a simple interface similar to modern compression libraries for single-stream compression.
This is a complement to SevenZipFile archive functionality, not a replacement.
"""

import tempfile
from pathlib import Path
from typing import Union

from .core import run_7z


def compress(data: Union[str, bytes], algorithm: str = "lzma2", level: int = 5) -> bytes:
    """
    Compress a single data block, similar to zstd.compress()

    Args:
        data: Data to compress
        algorithm: Compression algorithm (lzma2, lzma, ppmd, bzip2, deflate)
        level: Compression level (0-9)

    Returns:
        Compressed byte data
    """
    if isinstance(data, str):
        data = data.encode("utf-8")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Write to temporary file
        input_file = tmpdir_path / "input.dat"
        input_file.write_bytes(data)

        # Compress as 7z single-file archive
        output_file = tmpdir_path / "output.7z"
        args = [
            "a",
            str(output_file),
            str(input_file),
            f"-mx{level}",
            f"-m0={algorithm}",
            "-ms=off",  # Disable solid mode
        ]

        run_7z(args)

        # Read compressed result
        return output_file.read_bytes()


def decompress(data: bytes) -> bytes:
    """
    Decompress a single data block, similar to zstd.decompress()

    Args:
        data: Compressed byte data

    Returns:
        Decompressed byte data
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Write compressed data
        input_file = tmpdir_path / "input.7z"
        input_file.write_bytes(data)

        # Decompress
        output_dir = tmpdir_path / "output"
        args = ["x", str(input_file), f"-o{output_dir}", "-y"]

        run_7z(args)

        # Find decompressed files
        output_files = list(output_dir.glob("*"))
        if not output_files:
            raise ValueError("No files found in archive")

        # Return first file's content
        return output_files[0].read_bytes()


class Compressor:
    """
    Compressor class, provides an interface similar to zstd.ZstdCompressor
    """

    def __init__(self, algorithm: str = "lzma2", level: int = 5):
        self.algorithm = algorithm
        self.level = level

    def compress(self, data: Union[str, bytes]) -> bytes:
        """Compress data"""
        return compress(data, self.algorithm, self.level)


class Decompressor:
    """
    Decompressor class, provides an interface similar to zstd.ZstdDecompressor
    """

    def decompress(self, data: bytes) -> bytes:
        """Decompress data"""
        return decompress(data)


# Convenience functions, mimicking modern compression libraries
def lzma2_compress(data: Union[str, bytes], level: int = 5) -> bytes:
    """LZMA2 compression"""
    return compress(data, "lzma2", level)


def lzma2_decompress(data: bytes) -> bytes:
    """LZMA2 decompression"""
    return decompress(data)


def bzip2_compress(data: Union[str, bytes], level: int = 5) -> bytes:
    """BZIP2 compression"""
    return compress(data, "bzip2", level)


def bzip2_decompress(data: bytes) -> bytes:
    """BZIP2 decompression"""
    return decompress(data)

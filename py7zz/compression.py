# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""
Advanced Compression Algorithm Interface Module

Provides comprehensive compression algorithm interfaces similar to modern compression libraries
for single-stream compression. This module offers multiple compression strategies,
stream compression, and integration with the main archive functionality.

This is a complement to SevenZipFile archive functionality, not a replacement.
"""

import tempfile
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union

from .config import Config, Presets
from .core import run_7z
from .exceptions import CompressionError, ConfigurationError

# Supported compression algorithms with their optimal settings
ALGORITHM_PROFILES: Dict[str, Dict[str, Any]] = {
    "lzma2": {
        "name": "LZMA2",
        "description": "High compression ratio with good speed",
        "optimal_level": 5,
        "max_level": 9,
        "best_for": ["general", "text", "code"],
        "memory_usage": "medium",
    },
    "lzma": {
        "name": "LZMA",
        "description": "Original LZMA algorithm, good compression",
        "optimal_level": 5,
        "max_level": 9,
        "best_for": ["text", "code"],
        "memory_usage": "medium",
    },
    "ppmd": {
        "name": "PPMd",
        "description": "Excellent for text compression",
        "optimal_level": 7,
        "max_level": 9,
        "best_for": ["text", "xml", "json"],
        "memory_usage": "high",
    },
    "bzip2": {
        "name": "BZIP2",
        "description": "Good compression with moderate speed",
        "optimal_level": 6,
        "max_level": 9,
        "best_for": ["general", "mixed"],
        "memory_usage": "low",
    },
    "deflate": {
        "name": "Deflate",
        "description": "Fast compression with decent ratio",
        "optimal_level": 6,
        "max_level": 9,
        "best_for": ["fast", "mixed"],
        "memory_usage": "low",
    },
}


def get_algorithm_info(algorithm: str) -> Dict[str, Any]:
    """
    Get detailed information about a compression algorithm.

    Args:
        algorithm: Algorithm name

    Returns:
        Dictionary with algorithm information

    Raises:
        ConfigurationError: If algorithm is not supported
    """
    if algorithm not in ALGORITHM_PROFILES:
        available = ", ".join(ALGORITHM_PROFILES.keys())
        raise ConfigurationError(
            "algorithm", algorithm, f"Unsupported. Available: {available}"
        )

    return ALGORITHM_PROFILES[algorithm].copy()


def list_algorithms() -> List[str]:
    """
    List all supported compression algorithms.

    Returns:
        List of algorithm names
    """
    return list(ALGORITHM_PROFILES.keys())


def recommend_algorithm(
    content_type: str = "general", priority: str = "balanced"
) -> str:
    """
    Recommend optimal algorithm based on content type and priority.

    Args:
        content_type: Type of content ("text", "code", "mixed", "general")
        priority: Optimization priority ("speed", "size", "balanced")

    Returns:
        Recommended algorithm name
    """
    if priority == "speed":
        return "deflate"
    elif priority == "size":
        if content_type in ["text", "xml", "json"]:
            return "ppmd"
        else:
            return "lzma2"
    else:  # balanced
        if content_type in ["text", "code"]:
            return "lzma2"
        else:
            return "bzip2"


def compress(
    data: Union[str, bytes],
    algorithm: str = "lzma2",
    level: Optional[int] = None,
    config: Optional[Config] = None,
) -> bytes:
    """
    Compress a single data block with enhanced options.

    Args:
        data: Data to compress
        algorithm: Compression algorithm
        level: Compression level (auto-selected if None)
        config: Advanced configuration options

    Returns:
        Compressed byte data

    Raises:
        CompressionError: If compression fails
        ConfigurationError: If algorithm/settings are invalid
    """
    if isinstance(data, str):
        data = data.encode("utf-8")

    # Validate algorithm
    if algorithm not in ALGORITHM_PROFILES:
        available = ", ".join(ALGORITHM_PROFILES.keys())
        raise ConfigurationError(
            "algorithm", algorithm, f"Unsupported. Available: {available}"
        )

    # Auto-select level if not specified
    if level is None:
        level = int(ALGORITHM_PROFILES[algorithm]["optimal_level"])

    # Validate level
    max_level = int(ALGORITHM_PROFILES[algorithm]["max_level"])
    if not 0 <= level <= max_level:
        raise ConfigurationError(
            "level", str(level), f"out of range for {algorithm} (0-{max_level})"
        )

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Write to temporary file
            input_file = tmpdir_path / "input.dat"
            input_file.write_bytes(data)

            # Build compression arguments
            output_file = tmpdir_path / "output.7z"
            args = [
                "a",
                str(output_file),
                str(input_file),
                f"-mx{level}",
                f"-m0={algorithm}",
                "-ms=off",  # Disable solid mode for single-stream compression
            ]

            # Apply advanced config if provided
            if config:
                config_args = config.to_7z_args()
                # Filter out conflicting arguments
                filtered_args = [
                    arg for arg in config_args if not arg.startswith(("-mx", "-m0="))
                ]
                args.extend(filtered_args)

            run_7z(args)

            # Read compressed result
            return output_file.read_bytes()

    except Exception as e:
        raise CompressionError(f"Compression failed with {algorithm}: {e}") from e


def decompress(data: bytes, expected_size: Optional[int] = None) -> bytes:
    """
    Decompress a single data block with enhanced validation.

    Args:
        data: Compressed byte data
        expected_size: Expected decompressed size for validation (optional)

    Returns:
        Decompressed byte data

    Raises:
        CompressionError: If decompression fails
    """
    if not data:
        raise CompressionError("No data provided for decompression")

    try:
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
                raise CompressionError("No files found in compressed data")

            # Return first file's content
            result = output_files[0].read_bytes()

            # Validate size if expected
            if expected_size is not None and len(result) != expected_size:
                raise CompressionError(
                    f"Decompressed size mismatch: expected {expected_size}, got {len(result)}"
                )

            return result

    except Exception as e:
        if isinstance(e, CompressionError):
            raise
        raise CompressionError(f"Decompression failed: {e}") from e


class BaseCompressor(ABC):
    """
    Abstract base class for all compressor implementations.
    """

    @abstractmethod
    def compress(self, data: Union[str, bytes]) -> bytes:
        """Compress data."""
        pass

    @abstractmethod
    def get_algorithm_info(self) -> Dict[str, Any]:
        """Get information about the compression algorithm."""
        pass


class Compressor(BaseCompressor):
    """
    Advanced compressor class with configuration support.
    Provides an interface similar to zstd.ZstdCompressor but with more options.
    """

    def __init__(
        self,
        algorithm: str = "lzma2",
        level: Optional[int] = None,
        config: Optional[Config] = None,
    ):
        """
        Initialize compressor with algorithm and settings.

        Args:
            algorithm: Compression algorithm to use
            level: Compression level (auto-selected if None)
            config: Advanced configuration options
        """
        # Validate algorithm
        if algorithm not in ALGORITHM_PROFILES:
            available = ", ".join(ALGORITHM_PROFILES.keys())
            raise ConfigurationError(
                "algorithm", algorithm, f"Unsupported. Available: {available}"
            )

        self.algorithm = algorithm
        self.level = (
            level
            if level is not None
            else int(ALGORITHM_PROFILES[algorithm]["optimal_level"])
        )
        self.config = config

        # Validate level
        max_level = int(ALGORITHM_PROFILES[algorithm]["max_level"])
        if not 0 <= self.level <= max_level:
            raise ConfigurationError(
                "level",
                str(self.level),
                f"out of range for {algorithm} (0-{max_level})",
            )

    def compress(self, data: Union[str, bytes]) -> bytes:
        """
        Compress data using configured algorithm and settings.

        Args:
            data: Data to compress

        Returns:
            Compressed byte data
        """
        return compress(data, self.algorithm, self.level, self.config)

    def get_algorithm_info(self) -> Dict[str, Any]:
        """
        Get information about the configured compression algorithm.

        Returns:
            Dictionary with algorithm information
        """
        info = get_algorithm_info(self.algorithm)
        info["configured_level"] = self.level
        info["config"] = self.config
        return info

    def estimate_compressed_size(self, data_size: int) -> Dict[str, int]:
        """
        Estimate compressed size for given input size.

        Args:
            data_size: Input data size in bytes

        Returns:
            Dictionary with size estimates (min, max, typical)
        """
        # Rough estimates based on algorithm characteristics
        estimates = {
            "lzma2": {"min": 0.15, "max": 0.7, "typical": 0.3},
            "lzma": {"min": 0.15, "max": 0.7, "typical": 0.32},
            "ppmd": {"min": 0.1, "max": 0.6, "typical": 0.25},
            "bzip2": {"min": 0.2, "max": 0.8, "typical": 0.4},
            "deflate": {"min": 0.3, "max": 0.9, "typical": 0.5},
        }

        ratios = estimates.get(self.algorithm, estimates["lzma2"])

        return {
            "min_size": int(data_size * ratios["min"]),
            "max_size": int(data_size * ratios["max"]),
            "typical_size": int(data_size * ratios["typical"]),
            "input_size": data_size,
        }


class Decompressor:
    """
    Enhanced decompressor class with validation and error handling.
    Provides an interface similar to zstd.ZstdDecompressor.
    """

    def __init__(self, validate_size: bool = True):
        """
        Initialize decompressor.

        Args:
            validate_size: Whether to validate decompressed size when expected size is known
        """
        self.validate_size = validate_size
        self._stats = {
            "total_decompressed": 0,
            "operations_count": 0,
            "errors_count": 0,
        }

    def decompress(self, data: bytes, expected_size: Optional[int] = None) -> bytes:
        """
        Decompress data with enhanced validation.

        Args:
            data: Compressed byte data
            expected_size: Expected decompressed size for validation

        Returns:
            Decompressed byte data
        """
        try:
            self._stats["operations_count"] += 1

            if self.validate_size:
                result = decompress(data, expected_size)
            else:
                result = decompress(data)

            self._stats["total_decompressed"] += len(result)
            return result

        except Exception:
            self._stats["errors_count"] += 1
            raise

    def get_stats(self) -> Dict[str, int]:
        """
        Get decompression statistics.

        Returns:
            Dictionary with statistics
        """
        return self._stats.copy()

    def reset_stats(self) -> None:
        """Reset decompression statistics."""
        self._stats = {
            "total_decompressed": 0,
            "operations_count": 0,
            "errors_count": 0,
        }


class StreamCompressor:
    """
    Stream-based compressor for handling large data that doesn't fit in memory.
    """

    def __init__(self, algorithm: str = "lzma2", level: Optional[int] = None):
        """
        Initialize stream compressor.

        Args:
            algorithm: Compression algorithm
            level: Compression level
        """
        self.compressor = Compressor(algorithm, level)
        self.buffer_size = 1024 * 1024  # 1MB buffer

    def compress_stream(
        self, input_stream: BinaryIO, output_stream: BinaryIO
    ) -> Dict[str, Union[int, float]]:
        """
        Compress data from input stream to output stream.

        Args:
            input_stream: Input binary stream
            output_stream: Output binary stream

        Returns:
            Dictionary with compression statistics
        """
        total_input = 0
        total_output = 0

        # Read all data first (7z requires full data for single-stream compression)
        input_data = input_stream.read()
        total_input = len(input_data)

        # Compress
        compressed_data = self.compressor.compress(input_data)
        total_output = len(compressed_data)

        # Write to output stream
        output_stream.write(compressed_data)

        return {
            "input_size": total_input,
            "output_size": total_output,
            "compression_ratio": total_output / total_input if total_input > 0 else 0.0,
            "space_savings": 1 - (total_output / total_input)
            if total_input > 0
            else 0.0,
        }


class StreamDecompressor:
    """
    Stream-based decompressor for handling large compressed data.
    """

    def __init__(self) -> None:
        """Initialize stream decompressor."""
        self.decompressor = Decompressor()

    def decompress_stream(
        self, input_stream: BinaryIO, output_stream: BinaryIO
    ) -> Dict[str, Union[int, float]]:
        """
        Decompress data from input stream to output stream.

        Args:
            input_stream: Input binary stream with compressed data
            output_stream: Output binary stream for decompressed data

        Returns:
            Dictionary with decompression statistics
        """
        # Read all compressed data
        compressed_data = input_stream.read()
        total_input = len(compressed_data)

        # Decompress
        decompressed_data = self.decompressor.decompress(compressed_data)
        total_output = len(decompressed_data)

        # Write to output stream
        output_stream.write(decompressed_data)

        return {
            "input_size": total_input,
            "output_size": total_output,
            "decompression_ratio": total_output / total_input
            if total_input > 0
            else 0.0,
        }


# Enhanced convenience functions with better error handling and options
def lzma2_compress(
    data: Union[str, bytes],
    level: Optional[int] = None,
    config: Optional[Config] = None,
) -> bytes:
    """
    LZMA2 compression with enhanced options.

    Args:
        data: Data to compress
        level: Compression level (auto-selected if None)
        config: Advanced configuration options

    Returns:
        Compressed byte data
    """
    return compress(data, "lzma2", level, config)


def lzma2_decompress(data: bytes, expected_size: Optional[int] = None) -> bytes:
    """
    LZMA2 decompression with validation.

    Args:
        data: Compressed byte data
        expected_size: Expected decompressed size for validation

    Returns:
        Decompressed byte data
    """
    return decompress(data, expected_size)


def bzip2_compress(
    data: Union[str, bytes],
    level: Optional[int] = None,
    config: Optional[Config] = None,
) -> bytes:
    """
    BZIP2 compression with enhanced options.

    Args:
        data: Data to compress
        level: Compression level (auto-selected if None)
        config: Advanced configuration options

    Returns:
        Compressed byte data
    """
    return compress(data, "bzip2", level, config)


def bzip2_decompress(data: bytes, expected_size: Optional[int] = None) -> bytes:
    """
    BZIP2 decompression with validation.

    Args:
        data: Compressed byte data
        expected_size: Expected decompressed size for validation

    Returns:
        Decompressed byte data
    """
    return decompress(data, expected_size)


def ppmd_compress(
    data: Union[str, bytes],
    level: Optional[int] = None,
    config: Optional[Config] = None,
) -> bytes:
    """
    PPMd compression optimized for text data.

    Args:
        data: Data to compress (text recommended)
        level: Compression level (auto-selected if None)
        config: Advanced configuration options

    Returns:
        Compressed byte data
    """
    return compress(data, "ppmd", level, config)


def ppmd_decompress(data: bytes, expected_size: Optional[int] = None) -> bytes:
    """
    PPMd decompression with validation.

    Args:
        data: Compressed byte data
        expected_size: Expected decompressed size for validation

    Returns:
        Decompressed byte data
    """
    return decompress(data, expected_size)


def deflate_compress(
    data: Union[str, bytes],
    level: Optional[int] = None,
    config: Optional[Config] = None,
) -> bytes:
    """
    Deflate compression for fast compression needs.

    Args:
        data: Data to compress
        level: Compression level (auto-selected if None)
        config: Advanced configuration options

    Returns:
        Compressed byte data
    """
    return compress(data, "deflate", level, config)


def deflate_decompress(data: bytes, expected_size: Optional[int] = None) -> bytes:
    """
    Deflate decompression with validation.

    Args:
        data: Compressed byte data
        expected_size: Expected decompressed size for validation

    Returns:
        Decompressed byte data
    """
    return decompress(data, expected_size)


# Utility functions
def benchmark_algorithms(
    test_data: bytes,
    algorithms: Optional[List[str]] = None,
    levels: Optional[List[int]] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Benchmark different compression algorithms on test data.

    Args:
        test_data: Data to test compression on
        algorithms: List of algorithms to test (all if None)
        levels: List of levels to test (optimal only if None)

    Returns:
        Dictionary with benchmark results
    """
    if algorithms is None:
        algorithms = list_algorithms()

    results = {}

    for algorithm in algorithms:
        algo_info = get_algorithm_info(algorithm)
        test_levels = levels if levels is not None else [algo_info["optimal_level"]]

        for level in test_levels:
            key = f"{algorithm}_level_{level}"

            try:
                # Test compression
                start_time = time.time()
                compressed = compress(test_data, algorithm, level)
                compress_time = time.time() - start_time

                # Test decompression
                start_time = time.time()
                decompressed = decompress(compressed)
                decompress_time = time.time() - start_time

                # Verify data integrity
                data_valid = decompressed == test_data

                results[key] = {
                    "algorithm": algorithm,
                    "level": level,
                    "input_size": len(test_data),
                    "compressed_size": len(compressed),
                    "compression_ratio": len(compressed) / len(test_data),
                    "space_savings": 1 - (len(compressed) / len(test_data)),
                    "compress_time": compress_time,
                    "decompress_time": decompress_time,
                    "total_time": compress_time + decompress_time,
                    "compress_speed": len(test_data) / compress_time
                    if compress_time > 0
                    else 0,
                    "decompress_speed": len(test_data) / decompress_time
                    if decompress_time > 0
                    else 0,
                    "data_valid": data_valid,
                }

            except Exception as e:
                results[key] = {
                    "algorithm": algorithm,
                    "level": level,
                    "error": str(e),
                    "data_valid": False,
                }

    return results


def compress_with_preset(
    data: Union[str, bytes], preset_name: str, algorithm_override: Optional[str] = None
) -> bytes:
    """
    Compress data using a predefined preset configuration.

    Args:
        data: Data to compress
        preset_name: Name of preset configuration
        algorithm_override: Override algorithm from preset

    Returns:
        Compressed byte data
    """
    config = Presets.get_preset(preset_name)

    # Use algorithm from config, or override if specified
    algorithm = algorithm_override if algorithm_override else config.compression

    # Convert compression level to 7z level
    level = config.level

    return compress(data, algorithm, level, config)


# Integration with py7zz config system
def create_compressor_from_preset(preset_name: str) -> Compressor:
    """
    Create a compressor using a py7zz preset configuration.

    Args:
        preset_name: Name of the preset ("fast", "balanced", "backup", etc.)

    Returns:
        Configured compressor instance
    """
    config = Presets.get_preset(preset_name)
    return Compressor(algorithm=config.compression, level=config.level, config=config)


def get_compression_info() -> Dict[str, Any]:
    """
    Get comprehensive information about available compression options.

    Returns:
        Dictionary with compression capabilities and recommendations
    """
    return {
        "algorithms": {name: get_algorithm_info(name) for name in list_algorithms()},
        "presets": {
            name: {
                "config": Presets.get_preset(name).__dict__,
                "description": getattr(Presets, name).__doc__ or "",
            }
            for name in Presets.list_presets()
        },
        "recommendations": {
            "text_files": recommend_algorithm("text", "size"),
            "code_files": recommend_algorithm("code", "balanced"),
            "mixed_content": recommend_algorithm("mixed", "balanced"),
            "fast_compression": recommend_algorithm("general", "speed"),
            "maximum_compression": recommend_algorithm("general", "size"),
        },
    }


# File-based compression utilities
def compress_file_content(
    file_path: Union[str, Path],
    algorithm: str = "lzma2",
    level: Optional[int] = None,
    output_path: Optional[Union[str, Path]] = None,
) -> Path:
    """
    Compress the content of a file using single-stream compression.

    Args:
        file_path: Path to input file
        algorithm: Compression algorithm
        level: Compression level
        output_path: Output file path (auto-generated if None)

    Returns:
        Path to compressed file
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise CompressionError(f"Input file not found: {file_path}")

    # Read file content
    try:
        data = file_path.read_bytes()
    except Exception as e:
        raise CompressionError(f"Failed to read file {file_path}: {e}") from e

    # Generate output path if not provided
    if output_path is None:
        output_path = file_path.with_suffix(file_path.suffix + ".compressed")
    else:
        output_path = Path(output_path)

    # Compress data
    compressed_data = compress(data, algorithm, level)

    # Write compressed data
    try:
        output_path.write_bytes(compressed_data)
    except Exception as e:
        raise CompressionError(
            f"Failed to write compressed file {output_path}: {e}"
        ) from e

    return output_path


def decompress_file_content(
    compressed_file_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
) -> Path:
    """
    Decompress a file created by compress_file_content.

    Args:
        compressed_file_path: Path to compressed file
        output_path: Output file path (auto-generated if None)

    Returns:
        Path to decompressed file
    """
    compressed_file_path = Path(compressed_file_path)

    if not compressed_file_path.exists():
        raise CompressionError(f"Compressed file not found: {compressed_file_path}")

    # Read compressed data
    try:
        compressed_data = compressed_file_path.read_bytes()
    except Exception as e:
        raise CompressionError(
            f"Failed to read compressed file {compressed_file_path}: {e}"
        ) from e

    # Generate output path if not provided
    if output_path is None:
        output_path = compressed_file_path.with_suffix("")
        if output_path.suffix == ".compressed":
            output_path = output_path.with_suffix("")
    else:
        output_path = Path(output_path)

    # Decompress data
    decompressed_data = decompress(compressed_data)

    # Write decompressed data
    try:
        output_path.write_bytes(decompressed_data)
    except Exception as e:
        raise CompressionError(
            f"Failed to write decompressed file {output_path}: {e}"
        ) from e

    return output_path

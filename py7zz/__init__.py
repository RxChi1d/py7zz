"""
py7zz - Python wrapper for 7zz CLI tool

Provides a consistent OOP interface across platforms (macOS, Linux, Windows)
with automatic update mechanisms.
"""

# Configuration and Presets
from .config import Config, Presets, create_custom_config, get_recommended_preset
from .core import SevenZipFile, run_7z

# Version information
from .version import (
    get_version,
    get_py7zz_version,
    get_7zz_version,
    get_version_info,
    parse_version,
    generate_auto_version,
    generate_dev_version,
    get_version_type,
    is_release_version,
    is_auto_version,
    is_dev_version,
    VersionType,
)

# Exceptions
from .exceptions import (
    ArchiveNotFoundError,
    BinaryNotFoundError,
    CompressionError,
    ConfigurationError,
    CorruptedArchiveError,
    ExtractionError,
    FileNotFoundError,
    InsufficientSpaceError,
    InvalidPasswordError,
    OperationTimeoutError,
    PasswordRequiredError,
    Py7zzError,
    UnsupportedFormatError,
)

# Layer 1: Simple Function API
from .simple import (
    compress_directory,
    compress_file,
    create_archive,
    extract_archive,
    get_archive_info,
    list_archive,
    test_archive,
)

# Optional compression algorithm interface
try:
    from .compression import (
        Compressor,
        Decompressor,
        bzip2_compress,
        bzip2_decompress,
        compress,
        decompress,
        lzma2_compress,
        lzma2_decompress,
    )
    _compression_available = True
except ImportError:
    _compression_available = False

# Build __all__ list based on available modules
__all__ = [
    # Core API (Layer 2)
    "SevenZipFile", "run_7z",
    
    # Version information
    "get_version", "get_py7zz_version", "get_7zz_version", "get_version_info",
    "parse_version", "generate_auto_version", "generate_dev_version", "get_version_type",
    "is_release_version", "is_auto_version", "is_dev_version", "VersionType",
    
    # Simple API (Layer 1)
    "create_archive", "extract_archive", "list_archive",
    "compress_file", "compress_directory", "get_archive_info", "test_archive",
    
    # Configuration
    "Config", "Presets", "create_custom_config", "get_recommended_preset",
    
    # Exceptions
    "Py7zzError", "FileNotFoundError", "ArchiveNotFoundError",
    "CompressionError", "ExtractionError", "CorruptedArchiveError",
    "UnsupportedFormatError", "PasswordRequiredError", "InvalidPasswordError",
    "BinaryNotFoundError", "InsufficientSpaceError", "ConfigurationError",
    "OperationTimeoutError",
]

# Add compression API if available
if _compression_available:
    __all__.extend([
        "compress", "decompress", "Compressor", "Decompressor",
        "lzma2_compress", "lzma2_decompress", "bzip2_compress", "bzip2_decompress"
    ])

__version__ = "1.0.0+7zz24.07"
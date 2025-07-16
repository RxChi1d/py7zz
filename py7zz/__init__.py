"""
py7zz - Python wrapper for 7zz CLI tool

Provides a consistent OOP interface across platforms (macOS, Linux, Windows)
with automatic update mechanisms.
"""

# Configuration and Presets
# Bundled information
from .bundled_info import (
    get_bundled_7zz_version,
    get_release_type,
    get_version_info,
    is_auto_release,
    is_dev_release,
    is_stable_release,
)
from .config import Config, Presets, create_custom_config, get_recommended_preset
from .core import SevenZipFile, run_7z

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

# Version information
from .version import (
    __version__,
    generate_auto_version,
    generate_dev_version,
    get_base_version,
    get_build_number,
    get_version,
    get_version_type,
    is_auto_version,
    is_dev_version,
    is_stable_version,
    parse_version,
)
from .version import (
    get_version_info as get_legacy_version_info,
)

# Import async simple functions if available
try:
    from .simple import (
        compress_directory_async,  # noqa: F401
        compress_file_async,  # noqa: F401
        create_archive_async,  # noqa: F401
        extract_archive_async,  # noqa: F401
    )

    _simple_async_available = True
except ImportError:
    _simple_async_available = False

# Optional compression algorithm interface
try:
    from .compression import (
        Compressor,  # noqa: F401
        Decompressor,  # noqa: F401
        bzip2_compress,  # noqa: F401
        bzip2_decompress,  # noqa: F401
        compress,  # noqa: F401
        decompress,  # noqa: F401
        lzma2_compress,  # noqa: F401
        lzma2_decompress,  # noqa: F401
    )

    _compression_available = True
except ImportError:
    _compression_available = False

# Optional async operations interface
try:
    from .async_ops import (
        AsyncSevenZipFile,  # noqa: F401
        ProgressInfo,  # noqa: F401
        batch_compress_async,  # noqa: F401
        batch_extract_async,  # noqa: F401
        compress_async,  # noqa: F401
        extract_async,  # noqa: F401
    )

    _async_available = True
except ImportError:
    _async_available = False

# Build __all__ list based on available modules
__all__ = [
    # Core API (Layer 2)
    "SevenZipFile",
    "run_7z",
    # Version information
    "__version__",
    "get_version",
    "get_version_info",
    "get_legacy_version_info",
    "parse_version",
    "generate_auto_version",
    "generate_dev_version",
    "get_version_type",
    "is_auto_version",
    "is_dev_version",
    "is_stable_version",
    "get_base_version",
    "get_build_number",
    # Bundled information
    "get_bundled_7zz_version",
    "get_release_type",
    "is_stable_release",
    "is_auto_release",
    "is_dev_release",
    # Simple API (Layer 1)
    "create_archive",
    "extract_archive",
    "list_archive",
    "compress_file",
    "compress_directory",
    "get_archive_info",
    "test_archive",
    # Configuration
    "Config",
    "Presets",
    "create_custom_config",
    "get_recommended_preset",
    # Exceptions
    "Py7zzError",
    "FileNotFoundError",
    "ArchiveNotFoundError",
    "CompressionError",
    "ExtractionError",
    "CorruptedArchiveError",
    "UnsupportedFormatError",
    "PasswordRequiredError",
    "InvalidPasswordError",
    "BinaryNotFoundError",
    "InsufficientSpaceError",
    "ConfigurationError",
    "OperationTimeoutError",
]

# Add compression API if available
if _compression_available:
    __all__.extend(
        [
            "compress",
            "decompress",
            "Compressor",
            "Decompressor",
            "lzma2_compress",
            "lzma2_decompress",
            "bzip2_compress",
            "bzip2_decompress",
        ]
    )

# Add async API if available
if _async_available:
    __all__.extend(
        [
            "AsyncSevenZipFile",
            "ProgressInfo",
            "compress_async",
            "extract_async",
            "batch_compress_async",
            "batch_extract_async",
        ]
    )

# Add async simple API if available
if _simple_async_available:
    __all__.extend(["create_archive_async", "extract_archive_async", "compress_file_async", "compress_directory_async"])

# Version is now managed centrally in version.py
# __version__ is imported from .version at the top of this file

# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""
py7zz - Python wrapper for 7zz CLI tool

Provides a consistent OOP interface across platforms (macOS, Linux, Windows)
with automatic update mechanisms and Windows filename compatibility.
"""

# Initialize logging early
from .logging_config import ensure_default_logging

ensure_default_logging()

# Bundled information
# Archive information classes
from .archive_info import ArchiveInfo  # noqa: E402
from .bundled_info import (  # noqa: E402
    get_bundled_7zz_version,
    get_release_type,
    get_version_info,
    is_auto_release,
    is_dev_release,
    is_stable_release,
)

# Structured callback system
from .callbacks import (  # noqa: E402
    OperationStage,
    OperationType,
    ProgressCallback,
    ProgressInfo,
    ProgressTracker,
    console_progress_callback,
    create_callback,
    detailed_console_callback,
    json_progress_callback,
)

# Configuration and Presets
from .config import (  # noqa: E402
    Config,
    GlobalConfig,
    PresetRecommender,
    Presets,
    create_custom_config,
    get_recommended_preset,
)

# Core functionality
from .core import ArchiveFileReader, SevenZipFile, run_7z  # noqa: E402

# Exceptions
from .exceptions import (  # noqa: E402
    ArchiveNotFoundError,
    BinaryNotFoundError,
    CompatibilityError,
    CompressionError,
    ConfigurationError,
    CorruptedArchiveError,
    ExtractionError,
    FilenameCompatibilityError,
    FileNotFoundError,
    InsufficientSpaceError,
    InvalidPasswordError,
    OperationError,
    OperationTimeoutError,
    PasswordRequiredError,
    Py7zzError,
    SecurityError,
    UnsupportedFormatError,
    # Enhanced exception classes
    ValidationError,
    ZipBombError,
    # Error utility functions
    classify_error_type,
    get_error_suggestions,
    # Error handling decorators
    handle_7z_errors,
    handle_file_errors,
    handle_validation_errors,
)

# Filename sanitization utilities
from .filename_sanitizer import (  # noqa: E402
    get_safe_filename,
    is_valid_windows_filename,
    sanitize_filename_simple as sanitize_filename,
)

# Logging configuration
from .logging_config import (  # noqa: E402
    PerformanceLogger,
    clear_logging_handlers,
    disable_file_logging,
    disable_warnings,
    enable_debug_logging,
    enable_file_logging,
    enable_performance_monitoring,
    enable_structured_logging,
    get_log_statistics,
    get_logging_config,
    log_performance,
    performance_decorator,
    set_log_level,
    setup_logging,
)

# Security utilities
from .security import (  # noqa: E402
    SecurityConfig,
    check_file_count_security,
    get_default_security_config,
    perform_security_checks,
    set_default_security_config,
)

# Simple Function API (Layer 1)
from .simple import (  # noqa: E402
    # Advanced convenience functions
    batch_create_archives,
    batch_extract_archives,
    compare_archives,
    # Basic operations
    compress_directory,
    compress_file,
    convert_archive_format,
    copy_archive,
    create_archive,
    extract_archive,
    get_archive_format,
    get_archive_info,
    get_compression_ratio,
    list_archive,
    recompress_archive,
    test_archive,
)

# Streaming interface for cloud integration
from .streaming import (  # noqa: E402
    ArchiveStreamReader,
    ArchiveStreamWriter,
    create_stream_reader,
    create_stream_writer,
)

# Thread-safe configuration management
from .thread_safe_config import (  # noqa: E402
    PRESET_CONFIGS,
    ImmutableConfig,
    ThreadSafeGlobalConfig,
    apply_preset,
    get_preset_config,
    with_preset,
)

# Version information
from .version import (  # noqa: E402
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

# Get dynamic version from the version module with error handling
try:
    __version__ = get_version()
except Exception:
    # Fallback to a reasonable default if version detection fails
    __version__ = "1.1.1"
from .version import (  # noqa: E402
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
        batch_compress_async,  # noqa: F401
        batch_extract_async,  # noqa: F401
        compress_async,  # noqa: F401
        extract_async,  # noqa: F401
    )
    from .async_ops import (
        ProgressInfo as AsyncProgressInfo,  # noqa: F401
    )

    _async_available = True
except ImportError:
    _async_available = False

# Build __all__ list based on available modules
__all__ = [
    # Core API (Layer 2)
    "SevenZipFile",
    "ArchiveFileReader",
    "run_7z",
    # Archive information classes
    "ArchiveInfo",
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
    # Simple API (Layer 1) - Basic operations
    "create_archive",
    "extract_archive",
    "list_archive",
    "compress_file",
    "compress_directory",
    "get_archive_info",
    "test_archive",
    # Simple API (Layer 1) - Advanced convenience functions
    "batch_create_archives",
    "batch_extract_archives",
    "copy_archive",
    "get_compression_ratio",
    "get_archive_format",
    "compare_archives",
    "convert_archive_format",
    "recompress_archive",
    # Configuration
    "Config",
    "Presets",
    "create_custom_config",
    "get_recommended_preset",
    # Logging
    "setup_logging",
    "enable_debug_logging",
    "disable_warnings",
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
    "FilenameCompatibilityError",
    "SecurityError",
    "ZipBombError",
    # Enhanced exception handling
    "ValidationError",
    "OperationError",
    "CompatibilityError",
    "handle_7z_errors",
    "handle_file_errors",
    "handle_validation_errors",
    "classify_error_type",
    "get_error_suggestions",
    # Filename sanitization utilities
    "sanitize_filename",
    "is_valid_windows_filename",
    "get_safe_filename",
    # Security utilities
    "SecurityConfig",
    "check_file_count_security",
    "get_default_security_config",
    "perform_security_checks",
    "set_default_security_config",
]

# Add compression API if available
if _compression_available:
    __all__.extend(
        [
            # Core compression functions
            "compress",
            "decompress",
            # Compressor classes
            "BaseCompressor",
            "Compressor",
            "Decompressor",
            "StreamCompressor",
            "StreamDecompressor",
            # Algorithm-specific functions
            "lzma2_compress",
            "lzma2_decompress",
            "bzip2_compress",
            "bzip2_decompress",
            "ppmd_compress",
            "ppmd_decompress",
            "deflate_compress",
            "deflate_decompress",
            # Utility functions
            "get_algorithm_info",
            "list_algorithms",
            "recommend_algorithm",
            "benchmark_algorithms",
            "compress_with_preset",
            "create_compressor_from_preset",
            "get_compression_info",
            "compress_file_content",
            "decompress_file_content",
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
    __all__.extend(
        [
            "create_archive_async",
            "extract_archive_async",
            "compress_file_async",
            "compress_directory_async",
        ]
    )

# Version is now managed centrally in version.py
# __version__ is imported from .version at the top of this file

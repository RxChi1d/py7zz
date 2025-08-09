<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: 2025 py7zz contributors
-->

# py7zz API Reference

A Python wrapper for the 7zz CLI tool providing cross-platform archive operations with Windows filename compatibility.

## Table of Contents

- [Quick Start](#quick-start)
  - [Installation](#installation)
  - [Basic Usage](#basic-usage)
- [Core Classes](#core-classes)
  - [SevenZipFile](#sevenzipfile)
  - [ArchiveInfo](#archiveinfo)
  - [ArchiveFileReader](#archivefilereader)
- [Simple Function API](#simple-function-api)
  - [Basic Operations](#basic-operations)
  - [Batch Operations](#batch-operations)
  - [Archive Utilities](#archive-utilities)
- [Asynchronous API](#asynchronous-api)
  - [AsyncSevenZipFile](#asyncsevenzipfile)
  - [Async Functions](#async-functions)
  - [Progress Callbacks](#progress-callbacks)
- [Configuration](#configuration)
  - [Config Class](#config-class)
  - [Presets](#presets)
  - [GlobalConfig](#globalconfig)
  - [ThreadSafeGlobalConfig](#threadsafeglobalconfig)
  - [ImmutableConfig](#immutableconfig)
- [Streaming Interface](#streaming-interface)
  - [ArchiveStreamReader](#archivestreamreader)
  - [ArchiveStreamWriter](#archivestreamwriter)
- [Exception Handling](#exception-handling)
  - [Exception Hierarchy](#exception-hierarchy)
  - [Exception Classes](#exception-classes)
  - [Error Utilities](#error-utilities)
- [Logging Configuration](#logging-configuration)
  - [Setup Functions](#setup-functions)
  - [Configuration Functions](#configuration-functions)
  - [Performance Logging](#performance-logging)
- [Version Information](#version-information)
  - [Version Functions](#version-functions)
  - [Release Type Functions](#release-type-functions)
- [Library Migration Guide](#library-migration-guide)
  - [From zipfile](#from-zipfile)
  - [From tarfile](#from-tarfile)
- [Windows Filename Compatibility](#windows-filename-compatibility)
- [Best Practices](#best-practices)

## Quick Start

### Installation

```bash
pip install py7zz
```

### Basic Usage

```python
import py7zz

# Create an archive
py7zz.create_archive('backup.7z', ['documents/', 'photos/'])

# Extract an archive
py7zz.extract_archive('backup.7z', 'extracted/')

# List archive contents
with py7zz.SevenZipFile('backup.7z', 'r') as sz:
    files = sz.namelist()
    print(f"Archive contains {len(files)} files")
```

## Core Classes

### SevenZipFile

Main class for working with archives, compatible with Python's `zipfile.ZipFile` and `tarfile.TarFile`.

#### Constructor

```python
SevenZipFile(file, mode='r', level='normal', preset=None, config=None)
```

**Parameters:**
- `file` (str | Path): Path to the archive file
- `mode` (str): File mode ('r', 'w', 'a')
- `level` (str): Compression level ('store', 'fastest', 'fast', 'normal', 'maximum', 'ultra')
- `preset` (str, optional): Compression preset (alternative to level)
- `config` (Config, optional): Advanced configuration object

**Raises:**
- `FileNotFoundError`: Archive file not found (read mode)
- `BinaryNotFoundError`: 7zz binary not found
- `ValidationError`: Invalid parameters

#### Reading Methods

**`namelist() -> List[str]`**
Get list of archive member names (zipfile compatible).

**`getnames() -> List[str]`**
Get list of archive member names (tarfile compatible).

**`infolist() -> List[ArchiveInfo]`**
Get detailed information about all members (zipfile compatible).

**`getmembers() -> List[ArchiveInfo]`**
Get detailed information about all members (tarfile compatible).

**`getinfo(name: str) -> ArchiveInfo`**
Get information about specific member (zipfile compatible).
- **Raises:** `KeyError` if member not found

**`getmember(name: str) -> ArchiveInfo`**
Get information about specific member (tarfile compatible).
- **Raises:** `KeyError` if member not found

**`read(name: str) -> bytes`**
Read file content as bytes.
- **Returns:** File content as bytes
- **Raises:** `FileNotFoundError`, `ExtractionError`

**`readall() -> bytes`**
Read all files from archive as concatenated bytes.

**`open(name: str, mode: str = "r") -> ArchiveFileReader`**
Open file as file-like object.

#### Extraction Methods

**`extractall(path: str = ".", members: Optional[List[str]] = None) -> None`**
Extract all files or specified members.

**`extract(path: str = ".", overwrite: bool = False) -> None`**
Extract all contents with filename compatibility handling.

#### Writing Methods

**`add(name: str | Path, arcname: Optional[str] = None) -> None`**
Add file or directory to archive.

**`writestr(filename: str, data: str | bytes) -> None`**
Write data directly to archive file.

#### Utility Methods

**`testzip() -> Optional[str]`**
Test archive integrity. Returns None if OK, or name of first bad file.

**`copy_member(member_name: str, target_archive: SevenZipFile) -> None`**
Copy member to another archive.

**`filter_members(filter_func: Callable[[str], bool]) -> List[str]`**
Filter members using custom function.

**`get_member_size(name: str) -> int`**
Get uncompressed size of member.

**`get_member_compressed_size(name: str) -> int`**
Get compressed size of member.

**`close() -> None`**
Close the archive.

**`setpassword(pwd: Optional[bytes]) -> None`**
Set password for encrypted archives.

**`comment() -> bytes`**
Get archive comment.

**`setcomment(comment: bytes) -> None`**
Set archive comment.

### ArchiveInfo

Information about archive members, compatible with both `zipfile.ZipInfo` and `tarfile.TarInfo`.

#### Attributes

**File Information:**
- `filename` (str): Member name in archive
- `file_size` (int): Uncompressed size in bytes
- `compress_size` (int): Compressed size in bytes
- `type` (str): File type ('file', 'dir', 'link')

**Time Information:**
- `date_time` (tuple): Last modification time as (year, month, day, hour, minute, second)
- `mtime` (float): Modification time as Unix timestamp

**Compression Information:**
- `CRC` (int): CRC-32 checksum
- `method` (str): Compression method used
- `compress_type` (str): Compression type
- `solid` (bool): Whether file is in solid block
- `encrypted` (bool): Whether file is encrypted

**File Attributes:**
- `mode` (int): File permissions (Unix/Linux)
- `uid` (int): User ID
- `gid` (int): Group ID
- `external_attr` (int): External file attributes

#### Methods

**`is_dir() -> bool`**
Check if member is a directory.

**`isfile() -> bool`**
Check if member is a regular file (zipfile compatible).

**`isdir() -> bool`**
Check if member is a directory (zipfile compatible).

**`get_compression_ratio() -> float`**
Calculate compression ratio for this member.

**`from_zipinfo(zipinfo) -> ArchiveInfo`**
Create from zipfile.ZipInfo object (class method).

**`from_tarinfo(tarinfo) -> ArchiveInfo`**
Create from tarfile.TarInfo object (class method).

### ArchiveFileReader

File-like object for reading archive members.

#### Methods

**`read(size: int = -1) -> bytes`**
Read bytes from archive member.

**`readline(size: int = -1) -> bytes`**
Read a line from archive member.

**`readlines() -> List[bytes]`**
Read all lines from archive member.

**`seek(offset: int, whence: int = 0) -> int`**
Seek to position in archive member.

**`tell() -> int`**
Get current position in archive member.

**`close() -> None`**
Close the file reader.

## Simple Function API

### Basic Operations

**`create_archive(archive_path, files, preset="balanced") -> None`**
Create archive from files/directories.

**Parameters:**
- `archive_path` (str | Path): Output archive path
- `files` (List[str | Path]): Files/directories to archive
- `preset` (str): Compression preset ('fast', 'balanced', 'backup', 'ultra')

**`extract_archive(archive_path, output_dir=".", overwrite=True) -> None`**
Extract archive with automatic Windows filename compatibility.

**`list_archive(archive_path) -> List[str]`**
List all files in an archive (deprecated, use SevenZipFile.namelist()).

**`compress_file(input_path, output_path=None, preset="balanced") -> Path`**
Compress a single file.

**`compress_directory(input_dir, output_path=None, preset="balanced") -> Path`**
Compress a directory.

**`test_archive(archive_path) -> bool`**
Test archive integrity.

**`get_archive_info(archive_path) -> Dict[str, Any]`**
Get archive statistics. Returns dictionary with:
- `file_count` (int): Number of files
- `uncompressed_size` (int): Total uncompressed size
- `compressed_size` (int): Total compressed size
- `compression_ratio` (float): Compression ratio

### Batch Operations

**`batch_create_archives(operations, preset="balanced") -> None`**
Create multiple archives efficiently.

**Parameters:**
- `operations` (List[Tuple[str, List[str]]]): List of (archive_path, files) tuples
- `preset` (str): Compression preset

**`batch_extract_archives(archive_paths, output_dir=".", overwrite=True, create_dirs=True) -> None`**
Extract multiple archives.

### Archive Utilities

**`get_compression_ratio(archive_path) -> float`**
Calculate compression ratio (0.0 = no compression, 1.0 = 100% compression).

**`get_archive_format(archive_path) -> str`**
Detect archive format ('7z', 'zip', 'tar', etc.).

**`compare_archives(archive1, archive2, compare_content=False) -> bool`**
Compare two archives for equality.

**`convert_archive_format(source_archive, target_archive, target_format=None, preset="balanced") -> None`**
Convert archive between formats.

**`copy_archive(source_archive, target_archive, recompress=False, preset="balanced") -> None`**
Copy archive, optionally recompressing.

**`recompress_archive(source_path, target_path, preset="balanced", backup_original=False, backup_suffix=".bak") -> None`**
Recompress an archive to a new location with different settings.

This is the safe, industry-standard approach that creates a new file instead of modifying the original in-place.

**Args:**
    source_path (str | Path): Path to the source archive to recompress.
    target_path (str | Path): Path for the new recompressed archive.
    preset (str): Compression preset for recompression. Defaults to "balanced".
    backup_original (bool): Whether to create a backup of the original file. Defaults to False.
    backup_suffix (str): Suffix to use for backup file. Defaults to ".bak".

**Example:**
    >>> py7zz.recompress_archive("original.7z", "recompressed.7z", "ultra")
    >>> py7zz.recompress_archive("original.7z", "recompressed.7z", "ultra", backup_original=True)

## Asynchronous API

### AsyncSevenZipFile

Asynchronous wrapper for SevenZipFile operations.

```python
async with py7zz.AsyncSevenZipFile('archive.7z', 'r') as asz:
    names = await asz.namelist()
    content = await asz.read('file.txt')
```

#### Methods

**`await namelist() -> List[str]`**
Get list of archive member names asynchronously.

**`await getnames() -> List[str]`**
Get list of archive member names asynchronously (tarfile compatible).

**`await infolist() -> List[ArchiveInfo]`**
Get detailed information about all members.

**`await getmembers() -> List[ArchiveInfo]`**
Get detailed information about all members (tarfile compatible).

**`await read(name: str) -> bytes`**
Read file content asynchronously.

**`await writestr(filename: str, data: Union[str, bytes]) -> None`**
Write data to archive asynchronously.

**`await add(name: Union[str, Path], arcname=None, progress_callback=None) -> None`**
Add file to archive with optional progress callback.

**`await extractall(path=".", members=None, progress_callback=None) -> None`**
Extract archive with optional progress callback.

**`await testzip() -> Optional[str]`**
Test archive integrity asynchronously.

### Async Functions

**`create_archive_async(archive_path, files, progress_callback=None) -> None`**
Create archive asynchronously with progress reporting.

**`extract_archive_async(archive_path, output_dir=".", overwrite=True, progress_callback=None) -> None`**
Extract archive asynchronously with progress reporting.

**`compress_file_async(input_path, output_path=None, preset="balanced", progress_callback=None) -> Path`**
Compress file asynchronously.

**`compress_directory_async(input_dir, output_path=None, preset="balanced", progress_callback=None) -> Path`**
Compress directory asynchronously.

**`batch_compress_async(operations, progress_callback=None) -> None`**
Compress multiple archives concurrently.

**`batch_extract_async(operations, progress_callback=None) -> None`**
Extract multiple archives concurrently.

### Progress Callbacks

Progress callbacks receive `ProgressInfo` objects with the following structure:

#### ProgressInfo

**Attributes:**
- `operation_type` (OperationType): COMPRESS, EXTRACT, TEST, etc.
- `operation_stage` (OperationStage): STARTING, PROCESSING, COMPLETED, etc.
- `percentage` (float): Progress percentage (0.0-100.0)
- `bytes_processed` (int): Number of bytes processed
- `total_bytes` (Optional[int]): Total bytes to process
- `speed_bps` (Optional[float]): Processing speed in bytes per second
- `elapsed_time` (float): Elapsed time in seconds
- `estimated_remaining` (Optional[float]): Estimated remaining time
- `current_file` (Optional[str]): Currently processing file
- `files_processed` (int): Number of files completed
- `total_files` (Optional[int]): Total number of files
- `metadata` (Dict[str, Any]): Additional metadata

**Methods:**
- `format_speed() -> str`: Format speed as human-readable string
- `format_time(seconds: float) -> str`: Format time as human-readable string

#### Predefined Callbacks

**`console_progress_callback(progress: ProgressInfo) -> None`**
Simple console progress display.

**`detailed_console_callback(progress: ProgressInfo) -> None`**
Detailed console progress with comprehensive information.

**`json_progress_callback(progress: ProgressInfo) -> None`**
JSON-formatted progress output.

**`create_callback(callback_type: str, **options) -> Callable`**
Factory function for creating callbacks ('console', 'detailed', 'json').

## Configuration

### Config Class

Main configuration class for compression settings.

**Attributes:**
- `compression_level` (int): Compression level (0-9)
- `compression_method` (str): Method (lzma2, bzip2, etc.)
- `solid` (bool): Enable solid compression
- `threads` (Optional[Union[bool, int]]): Thread count (int=N threads, True=all cores, False=single thread). Defaults to all cores.
- `memory_limit` (Optional[str]): Memory limit (e.g., "1g", "512m")
- `encrypt` (bool): Enable file content encryption (AES-256)
- `encrypt_headers` (bool): Enable header encryption (file names and structure)
- `password` (Optional[str]): Archive password
- `volume_size` (Optional[str]): Split volume size
- `exclude_patterns` (List[str]): Files to exclude
- `include_patterns` (List[str]): Files to include

### Presets

Predefined compression configurations.

**Available Presets:**
- `Presets.FAST`: Fast compression, low ratio
- `Presets.BALANCED`: Balanced speed and compression
- `Presets.MAXIMUM`: Maximum compression
- `Presets.ULTRA`: Ultra compression (slow)
- `Presets.STORE`: No compression
- `Presets.BACKUP`: Optimized for backups

**`create_custom_config(**kwargs) -> Config`**
Create custom configuration.

**`get_recommended_preset(purpose: str) -> Config`**
Get recommended preset for purpose ('backup', 'distribution', 'storage').

### GlobalConfig

Global configuration management.

**Class Methods:**
- `set_default_preset(preset_name: str) -> None`
- `get_default_preset() -> str`
- `load_user_config() -> None`
- `save_user_config() -> None`
- `get_user_config_path() -> Path`

### ThreadSafeGlobalConfig

Thread-safe global configuration manager.

**Class Methods:**
- `get_config() -> ImmutableConfig`
- `set_config(config: ImmutableConfig) -> None`
- `update_config(**changes) -> ImmutableConfig`
- `temporary_config(**changes) -> ContextManager[ImmutableConfig]`
- `reset_to_defaults() -> None`

### ImmutableConfig

Immutable configuration for thread-safe operations.

**Attributes:**
- `compression` (str): Method ('lzma2', 'bzip2', 'ppmd', 'deflate')
- `level` (int): Compression level (0-9)
- `solid` (bool): Enable solid compression
- `threads` (Optional[int]): Number of threads
- `memory_limit` (Optional[str]): Memory limit ('1g', '512m')
- `password` (Optional[str]): Archive password
- `encrypt_filenames` (bool): Encrypt file names
- `preset_name` (str): Configuration preset name

**Methods:**
- `replace(**changes) -> ImmutableConfig`: Create new config with changes

**Preset Functions:**
- `get_preset_config(preset_name: str) -> ImmutableConfig`
- `apply_preset(preset_name: str) -> None`
- `with_preset(preset_name: str) -> ContextManager[ImmutableConfig]`

## Streaming Interface

### ArchiveStreamReader

Stream files from archives without extracting to disk.

```python
with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    with ArchiveStreamReader(sz, 'large_file.txt') as reader:
        while True:
            chunk = reader.read(8192)
            if not chunk:
                break
            # Process chunk
```

**Methods:**
- `read(size: int = -1) -> bytes`
- `readline(size: int = -1) -> bytes`
- `readinto(buffer: bytearray) -> int`
- `seek(offset: int, whence: int = 0) -> int`
- `tell() -> int`
- `close() -> None`

### ArchiveStreamWriter

Stream data directly into archives.

```python
with py7zz.SevenZipFile('output.7z', 'w') as sz:
    with ArchiveStreamWriter(sz, 'streamed_data.txt') as writer:
        for data_chunk in large_data_source():
            writer.write(data_chunk)
```

**Methods:**
- `write(data: bytes) -> int`
- `flush() -> None`
- `seek(offset: int, whence: int = 0) -> int`
- `tell() -> int`
- `close() -> None`

**Convenience Functions:**
- `create_stream_reader(archive_path: str, member_name: str) -> ArchiveStreamReader`
- `create_stream_writer(archive_path: str, member_name: str) -> ArchiveStreamWriter`

## Exception Handling

### Exception Hierarchy

```
Py7zzError (base exception)
├── ValidationError
├── OperationError
├── CompatibilityError
├── FileNotFoundError
├── ArchiveNotFoundError
├── CompressionError
├── ExtractionError
├── CorruptedArchiveError
├── UnsupportedFormatError
├── FilenameCompatibilityError
├── PasswordRequiredError
├── InvalidPasswordError
├── BinaryNotFoundError
├── InsufficientSpaceError
├── ConfigurationError
└── OperationTimeoutError
```

### Exception Classes

All exceptions inherit from `Py7zzError` and provide:
- Enhanced error messages
- Context information
- Actionable suggestions

**FilenameCompatibilityError** includes:
- `problematic_files` (List[str]): Files with issues
- `sanitized` (bool): Whether sanitization succeeded
- `error_details` (Dict): Detailed error information

### Error Utilities

**`handle_7z_errors(func) -> Callable`**
Decorator for handling 7z-specific errors.

**`handle_file_errors(func) -> Callable`**
Decorator for handling file-related errors.

**`handle_validation_errors(func) -> Callable`**
Decorator for handling validation errors.

**`classify_error_type(error: Exception) -> str`**
Classify error type for logging.

**`get_error_suggestions(error: Exception) -> List[str]`**
Get actionable suggestions for resolving errors.

## Logging Configuration

### Setup Functions

**`setup_logging(level="INFO", **options) -> None`**
Configure py7zz logging.

**Parameters:**
- `level` (str): Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
- `enable_filename_warnings` (bool): Show filename compatibility warnings
- `console_output` (bool): Enable console logging
- `log_file` (str, optional): Path for log file output
- `structured` (bool): Use structured JSON logging
- `performance_monitoring` (bool): Enable performance logging

**`enable_debug_logging() -> None`**
Enable debug logging.

**`disable_warnings() -> None`**
Disable warning messages.

### Configuration Functions

**`set_log_level(level: str) -> None`**
Set logging level.

**`enable_file_logging(log_file: str, max_file_size: int = 10485760, backup_count: int = 3) -> None`**
Enable file logging with rotation.

**`disable_file_logging() -> None`**
Disable file logging.

**`enable_structured_logging(enable: bool = True) -> None`**
Enable/disable structured JSON logging.

**`enable_performance_monitoring(enable: bool = True) -> None`**
Enable/disable performance monitoring.

**`get_logging_config() -> Dict`**
Get current logging configuration.

**`get_log_statistics() -> Dict`**
Get logging statistics.

**`clear_logging_handlers() -> None`**
Clear all logging handlers.

### Performance Logging

**`log_performance(operation: str, duration: float, size: Optional[int] = None, **kwargs) -> None`**
Log performance metrics. Can also be used as a decorator.

**Args:**
    operation (str): Name of the operation being logged.
    duration (float): Duration in seconds (ignored in decorator mode).
    size (Optional[int]): Size of data processed in bytes.
    **kwargs: Additional metadata to log.

**Examples:**
    Direct usage:
    >>> log_performance("compression", 2.5, size=1024000)

    Decorator usage:
    >>> @log_performance("my_operation")
    ... def my_function():
    ...     # Function implementation
    ...     pass

**`PerformanceLogger`** context manager:
```python
with PerformanceLogger("compression", size=file_size) as perf:
    # Perform operation
    pass
# Automatically logs duration and throughput
```

## Version Information

### Version Functions

**`get_version() -> str`**
Get current py7zz version.

**`parse_version(version_string: str) -> Tuple[int, int, int, str, int]`**
Parse version string into components.

**`get_base_version() -> str`**
Get base version without pre-release suffix.

**`get_build_number() -> int`**
Get build number.

**`get_version_type() -> str`**
Get version type ('stable', 'auto', 'dev').

**`is_stable_version() -> bool`**
Check if current version is stable.

**`is_auto_version() -> bool`**
Check if current version is auto-release.

**`is_dev_version() -> bool`**
Check if current version is development.

**`generate_auto_version(base_version: str, build_number: int) -> str`**
Generate auto-release version string.

**`generate_dev_version(base_version: str, build_number: int) -> str`**
Generate development version string.

### Release Type Functions

**`get_bundled_7zz_version() -> str`**
Get bundled 7zz binary version.

**`get_release_type() -> str`**
Get release type ('stable', 'auto', 'dev').

**`is_stable_release() -> bool`**
Check if stable release.

**`is_auto_release() -> bool`**
Check if auto-release.

**`is_dev_release() -> bool`**
Check if development release.

**`get_version_info() -> Dict[str, str]`**
Get complete version information dictionary.

## Library Migration Guide

### From zipfile

py7zz provides complete `zipfile.ZipFile` compatibility:

```python
# OLD (zipfile)
import zipfile

with zipfile.ZipFile('archive.zip', 'r') as zf:
    names = zf.namelist()
    info = zf.getinfo('file.txt')
    content = zf.read('file.txt')
    zf.extractall('output/')

# NEW (py7zz) - Identical API
import py7zz

with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    names = sz.namelist()          # Same method
    info = sz.getinfo('file.txt')  # Same method
    content = sz.read('file.txt')  # Same method
    sz.extractall('output/')       # Same method
```

### From tarfile

py7zz also supports `tarfile.TarFile` methods:

```python
# OLD (tarfile)
import tarfile

with tarfile.open('archive.tar.gz', 'r:gz') as tf:
    names = tf.getnames()
    members = tf.getmembers()
    tf.extractall('output/')

# NEW (py7zz) - Compatible API
import py7zz

with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    names = sz.getnames()       # tarfile compatible
    members = sz.getmembers()   # tarfile compatible
    sz.extractall('output/')    # Same method
```

## Windows Filename Compatibility

py7zz automatically handles Windows filename restrictions when extracting archives created on Unix/Linux systems.

### Automatic Sanitization Rules

| Issue | Example | Solution | Reason |
|-------|---------|----------|---------|
| Invalid characters | `file:name.txt` | `file_name.txt` | Windows doesn't allow `:` |
| Reserved names | `CON.txt` | `CON_file.txt` | Windows reserved name |
| Multiple issues | `PRN<>file.txt` | `PRN__file.txt` | Multiple invalid chars |
| Long filenames | `very-long-filename...` | `very-long-fil_a1b2c3d4.txt` | 255 char limit + hash |
| Trailing spaces | `filename ` | `filename` | Windows compatibility |

### Platform Behavior

- **Windows**: Automatic filename sanitization applied when needed
- **Unix/Linux/macOS**: No modification (not needed)

## Best Practices

### Performance Optimization

```python
# For backup/storage - prioritize compression
py7zz.create_archive('backup.7z', ['data/'], preset='ultra')

# For distribution - balance speed and size
py7zz.create_archive('release.7z', ['app/'], preset='balanced')

# For temporary archives - prioritize speed
py7zz.create_archive('temp.7z', ['cache/'], preset='fast')
```

### Memory Management

```python
# For large archives, use streaming
with py7zz.SevenZipFile('huge.7z', 'r') as sz:
    # Don't load all files at once
    for name in sz.namelist():
        if name.endswith('.log'):
            # Process one file at a time
            content = sz.read(name)
            process_log_file(content)
```

### Error Handling Patterns

```python
def safe_archive_operation(archive_path, operation):
    """Robust archive operation with comprehensive error handling."""
    try:
        return operation(archive_path)
    except py7zz.FileNotFoundError:
        return {"error": "Archive not found", "recoverable": False}
    except py7zz.CorruptedArchiveError:
        return {"error": "Archive corrupted", "recoverable": False}
    except py7zz.FilenameCompatibilityError as e:
        return {"error": "Filename issues", "recoverable": True, "details": e.problematic_files}
    except py7zz.InsufficientSpaceError:
        return {"error": "Not enough space", "recoverable": True}
    except py7zz.Py7zzError as e:
        return {"error": f"Archive operation failed: {e}", "recoverable": True}
```

---

*This documentation covers py7zz's production-ready features. All examples are tested and functional. For the latest updates, visit the [GitHub repository](https://github.com/rxchi1d/py7zz).*

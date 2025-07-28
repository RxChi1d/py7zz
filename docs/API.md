# py7zz API Reference

Complete API documentation for py7zz, a Python wrapper for the 7zz CLI tool with Windows filename compatibility.

## Table of Contents

- [Simple Function API](#simple-function-api)
- [Object-Oriented API](#object-oriented-api)
- [Async Operations API](#async-operations-api)
- [Advanced Configuration](#advanced-configuration)
- [Windows Filename Compatibility](#windows-filename-compatibility)
- [Logging Configuration](#logging-configuration)
- [Exception Handling](#exception-handling)
- [Progress Callbacks](#progress-callbacks)
- [Version Information](#version-information)

## Simple Function API

### `create_archive(archive_path, files, preset="balanced")`

Create an archive with the specified files.

**Parameters:**
- `archive_path` (str): Path to the output archive
- `files` (List[str]): List of files/directories to archive
- `preset` (str, optional): Compression preset ('fast', 'balanced', 'backup', 'ultra')

**Returns:** None

**Example:**
```python
import py7zz

# Basic usage
py7zz.create_archive('backup.7z', ['documents/', 'photos/'])

# With preset
py7zz.create_archive(
    'backup.7z',
    ['documents/'],
    preset='ultra'
)
```

### `extract_archive(archive_path, output_dir=".", overwrite=True)`

Extract an archive to the specified directory with automatic Windows filename compatibility handling.

**Parameters:**
- `archive_path` (str): Path to the archive file
- `output_dir` (str): Directory to extract files to (default: current directory)
- `overwrite` (bool): Whether to overwrite existing files

**Returns:** None

**Raises:**
- `FilenameCompatibilityError`: When filename issues cannot be resolved
- `ExtractionError`: When extraction fails for other reasons

**Example:**
```python
# Basic extraction (automatic filename handling on Windows)
py7zz.extract_archive('backup.7z', 'extracted/')

# Extract without overwriting existing files
py7zz.extract_archive('backup.7z', 'extracted/', overwrite=False)

# On Windows, files with problematic names are automatically renamed:
# 'CON.txt' -> 'CON_file.txt'
# 'file:name.txt' -> 'file_name.txt'
```

### `list_archive(archive_path)`

List contents of an archive.

**Parameters:**
- `archive_path` (str): Path to the archive file

**Returns:** List[str] - List of file paths in the archive

**Example:**
```python
files = py7zz.list_archive('backup.7z')
for file in files:
    print(file)
```

### `test_archive(archive_path)`

Test archive integrity.

**Parameters:**
- `archive_path` (str): Path to the archive file

**Returns:** bool - True if archive is valid, False otherwise

**Example:**
```python
if py7zz.test_archive('backup.7z'):
    print("Archive is OK")
else:
    print("Archive is corrupted")
```

### `get_archive_info(archive_path)`

Get detailed information about an archive.

**Parameters:**
- `archive_path` (str): Path to the archive file

**Returns:** Dict[str, Any] - Archive information including file count, size, compression ratio

**Example:**
```python
info = py7zz.get_archive_info('backup.7z')
print(f"Files: {info['file_count']}")
print(f"Compressed size: {info['compressed_size']}")
print(f"Uncompressed size: {info['uncompressed_size']}")
print(f"Compression ratio: {info['compression_ratio']:.1%}")
```

## Object-Oriented API

### `SevenZipFile(archive_path, mode='r', level='normal', preset=None, config=None)`

Main class for working with 7z archives, similar to `zipfile.ZipFile`.

**Parameters:**
- `archive_path` (str): Path to the archive file
- `mode` (str): Open mode ('r', 'w', 'a')
- `level` (str): Compression level ('store', 'fastest', 'fast', 'normal', 'maximum', 'ultra')
- `preset` (str, optional): Compression preset ('fast', 'balanced', 'backup', 'ultra')
- `config` (Config, optional): Advanced compression configuration

**Example:**
```python
# Reading an archive
with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    files = sz.namelist()
    content = sz.read('file.txt')

# Writing an archive
with py7zz.SevenZipFile('archive.7z', 'w', preset='balanced') as sz:
    sz.add('file.txt')
    sz.add('folder/')
```

#### Methods

##### `namelist()`

Get list of files in the archive.

**Returns:** List[str] - List of file paths

##### `read(path)`

Read a file from the archive.

**Parameters:**
- `path` (str): Path to the file in the archive

**Returns:** bytes - File content

##### `extract(path, output_dir)`

Extract a specific file from the archive.

**Parameters:**
- `path` (str): Path to the file in the archive
- `output_dir` (str): Directory to extract to

**Returns:** None

##### `extractall(output_dir)`

Extract all files from the archive.

**Parameters:**
- `output_dir` (str): Directory to extract to

**Returns:** None

##### `add(path, arcname=None)`

Add a file or directory to the archive.

**Parameters:**
- `path` (str): Path to the file/directory to add
- `arcname` (str, optional): Name to use in the archive

**Returns:** None

##### `close()`

Close the archive file.

**Returns:** None

## Async Operations API

### `create_archive_async(archive_path, files, *, preset=None, password=None, progress_callback=None)`

Async version of `create_archive`.

**Parameters:** Same as `create_archive`

**Returns:** None

**Example:**
```python
import asyncio
import py7zz

async def main():
    await py7zz.create_archive_async('backup.7z', ['documents/'])

asyncio.run(main())
```

### `extract_archive_async(archive_path, output_dir, *, password=None, progress_callback=None)`

Async version of `extract_archive`.

**Parameters:** Same as `extract_archive`

**Returns:** None

### `batch_compress_async(operations, progress_callback=None)`

Compress multiple archives concurrently.

**Parameters:**
- `operations` (List[Tuple[str, List[str]]]): List of (archive_path, files) tuples
- `progress_callback` (callable, optional): Progress callback function

**Returns:** None

**Example:**
```python
async def main():
    operations = [
        ('backup1.7z', ['folder1/']),
        ('backup2.7z', ['folder2/']),
        ('backup3.7z', ['folder3/'])
    ]
    
    await py7zz.batch_compress_async(operations)

asyncio.run(main())
```

### `batch_extract_async(operations, progress_callback=None)`

Extract multiple archives concurrently.

**Parameters:**
- `operations` (List[Tuple[str, str]]): List of (archive_path, output_dir) tuples
- `progress_callback` (callable, optional): Progress callback function

**Returns:** None

## Advanced Configuration

### `Config`

Advanced compression configuration class.

**Parameters:**
- `level` (int): Compression level (0-9)
- `method` (str): Compression method ('LZMA', 'LZMA2', 'PPMd', 'BZip2', 'Deflate')
- `dictionary_size` (str): Dictionary size ('1m', '4m', '8m', '16m', '32m', '64m')
- `word_size` (int): Word size (8-273, for PPMd method)
- `solid` (bool): Enable solid compression
- `threads` (int): Number of threads to use
- `header_compression` (bool): Enable header compression
- `header_encryption` (bool): Enable header encryption

**Example:**
```python
config = py7zz.Config(
    level=9,
    method='LZMA2',
    dictionary_size='64m',
    solid=True,
    threads=4,
    header_compression=True
)

with py7zz.SevenZipFile('archive.7z', 'w', config=config) as sz:
    sz.add('data/')
```

### `create_custom_config(**kwargs)`

Create a custom compression configuration.

**Parameters:** Same as `Config`

**Returns:** Config

**Example:**
```python
config = py7zz.create_custom_config(
    level=7,
    method='LZMA2',
    dictionary_size='32m',
    solid=True
)
```

## Windows Filename Compatibility

py7zz automatically handles Windows filename restrictions when extracting archives, particularly those created on Unix/Linux systems.

### Automatic Filename Sanitization

On Windows systems, py7zz automatically detects and resolves filename compatibility issues:

```python
import py7zz

# Extract with automatic filename handling
py7zz.extract_archive('unix-archive.7z', 'output/')

# Object-oriented interface also handles filenames automatically
with py7zz.SevenZipFile('problematic.zip', 'r') as sz:
    sz.extract('output/')  # Filenames automatically sanitized
```

### Sanitization Rules

The following transformations are applied automatically:

| Issue | Example | Solution |
|-------|---------|----------|
| Invalid characters | `file:name.txt` | `file_name.txt` |
| Reserved names | `CON.txt` | `CON_file.txt` |
| Multiple issues | `PRN<file>.txt` | `PRN_file_file_.txt` |
| Long filenames | `very-long...` | `very-long-fil_a1b2c3d4.txt` |
| Trailing spaces/dots | `filename .` | `filename` |

### Platform Behavior

- **Windows**: Automatic filename sanitization when needed
- **Unix/Linux/macOS**: No filename modification (not needed)

### Error Handling

```python
try:
    py7zz.extract_archive('problematic.7z', 'output/')
except py7zz.FilenameCompatibilityError as e:
    print(f"Filename issues encountered: {len(e.problematic_files)} files")
    print(f"Sanitization {'successful' if e.sanitized else 'failed'}")
```

## Logging Configuration

Control logging output for filename compatibility warnings and other operations.

### Setup Logging

```python
import py7zz

# Configure logging level
py7zz.setup_logging("INFO")        # Default - shows warnings
py7zz.setup_logging("DEBUG")       # Verbose output
py7zz.setup_logging("ERROR")       # Only errors

# Quick configuration methods
py7zz.enable_debug_logging()       # Enable debug mode
py7zz.disable_warnings()           # Hide filename warnings
```

### Example Log Output

When extracting archives with problematic filenames:

```
INFO [py7zz] Extraction failed due to filename compatibility issues, attempting with sanitized names
WARNING [py7zz] Windows filename compatibility: 3 files renamed
WARNING [py7zz]   'CON.txt' -> 'CON_file.txt' (reason: reserved name: CON)
WARNING [py7zz]   'file:name.txt' -> 'file_name.txt' (reason: invalid characters: ':')
WARNING [py7zz]   'file*.log' -> 'file_.log' (reason: invalid characters: '*')
INFO [py7zz] Successfully extracted 15 files with sanitized names
```

### Logging Levels

| Level | What's Shown |
|-------|--------------|
| `DEBUG` | All operations, file movements, detailed progress |
| `INFO` | Operation start/completion, filename warnings |
| `WARNING` | Filename compatibility warnings only |
| `ERROR` | Only error messages |

## Exception Handling

### Exception Hierarchy

```
Py7zzError (base exception)
├── BinaryNotFoundError
├── CompressionError
├── ExtractionError
├── FilenameCompatibilityError
├── FileNotFoundError
├── ArchiveNotFoundError
├── CorruptedArchiveError
├── UnsupportedFormatError
├── PasswordRequiredError
├── InvalidPasswordError
├── InsufficientSpaceError
├── ConfigurationError
└── OperationTimeoutError
```

### Exception Details

#### `Py7zzError`

Base exception for all py7zz errors.

#### `BinaryNotFoundError`

Raised when the 7zz binary is not found.

#### `CompressionError`

Raised when compression fails.

#### `ExtractionError`

Raised when extraction fails.

#### `FilenameCompatibilityError`

Raised when filename compatibility issues are encountered during extraction on Windows.

**Attributes:**
- `problematic_files` (List[str]): List of problematic filenames
- `sanitized` (bool): Whether sanitization was attempted

**Example:**
```python
try:
    py7zz.extract_archive('problematic.7z', 'output/')
except py7zz.FilenameCompatibilityError as e:
    print(f"{len(e.problematic_files)} files had naming issues")
    if e.sanitized:
        print("Files were successfully renamed")
    else:
        print("Could not resolve all filename issues")
```

#### `FileNotFoundError`

Raised when a file is not found.

#### `ArchiveNotFoundError`

Raised when an archive file is not found.

#### `CorruptedArchiveError`

Raised when the archive is invalid or corrupted.

#### `UnsupportedFormatError`

Raised when trying to work with an unsupported archive format.

#### `PasswordRequiredError`

Raised when a password is required but not provided.

#### `InvalidPasswordError`

Raised when an incorrect password is provided.

#### `ConfigurationError`

Raised when there's an error in configuration parameters.

#### `OperationTimeoutError`

Raised when an operation times out.

#### `InsufficientSpaceError`

Raised when there is insufficient disk space.

**Example:**
```python
try:
    py7zz.create_archive('backup.7z', ['nonexistent/'])
except py7zz.FileNotFoundError:
    print("Source file not found")
except py7zz.CompressionError as e:
    print(f"Compression failed: {e}")
except py7zz.InsufficientSpaceError:
    print("Not enough disk space")
except py7zz.CorruptedArchiveError:
    print("Archive is corrupted")
except py7zz.Py7zzError as e:
    print(f"General error: {e}")
```

## Progress Callbacks

### Progress Information

Progress callbacks receive a `ProgressInfo` object with the following attributes:

- `operation` (str): Current operation ('compress', 'extract', 'test')
- `percentage` (float): Completion percentage (0.0-100.0)
- `current_file` (str): Currently processed file
- `files_processed` (int): Number of files processed
- `total_files` (int): Total number of files
- `bytes_processed` (int): Bytes processed
- `total_bytes` (int): Total bytes to process

### Callback Function Signature

```python
def progress_callback(info: ProgressInfo) -> None:
    # Handle progress information
    pass
```

### Examples

#### Basic Progress Display

```python
def progress_handler(info):
    print(f"{info.operation}: {info.percentage:.1f}% - {info.current_file}")

py7zz.create_archive('backup.7z', ['data/'], progress_callback=progress_handler)
```

#### Advanced Progress Display

```python
def detailed_progress_handler(info):
    print(f"Operation: {info.operation}")
    print(f"Progress: {info.percentage:.1f}%")
    print(f"Current file: {info.current_file}")
    print(f"Files: {info.files_processed}/{info.total_files}")
    print(f"Size: {info.bytes_processed}/{info.total_bytes} bytes")
    print("-" * 40)

py7zz.create_archive('backup.7z', ['data/'], progress_callback=detailed_progress_handler)
```

#### Async Progress Display

```python
async def async_progress_handler(info):
    # Can perform async operations here
    await asyncio.sleep(0)  # Yield control
    print(f"Async progress: {info.percentage:.1f}%")

await py7zz.create_archive_async(
    'backup.7z',
    ['data/'],
    progress_callback=async_progress_handler
)
```

## Version Information

### `get_version()`

Get the current py7zz version in PEP 440 format.

**Returns:** str - Current py7zz version

**Example:**
```python
version = py7zz.get_version()
print(version)  # "1.0.0"
```

### `get_bundled_7zz_version()`

Get the bundled 7zz version for the current py7zz version.

**Returns:** str - Bundled 7zz version

**Example:**
```python
version = py7zz.get_bundled_7zz_version()
print(version)  # "24.07"
```

### `get_version_info()`

Get comprehensive version information including release details.

**Returns:** Dict[str, str] - Complete version information dictionary

**Example:**
```python
info = py7zz.get_version_info()
print(info)
# {
#     'py7zz_version': '1.0.0',
#     'bundled_7zz_version': '24.07',
#     'release_type': 'stable',
#     'release_date': '2024-07-15',
#     'github_tag': 'v1.0.0',
#     'changelog_url': 'https://github.com/rxchi1d/py7zz/releases/tag/v1.0.0'
# }
```

**Note:** Advanced version checking functions (get_release_type, is_stable_version, etc.) are planned for future releases. Current implementation provides basic version information through get_version_info().

## CLI Version Commands

py7zz provides command-line tools for version information:

```bash
# Human-readable version information
py7zz version

# JSON format
py7zz version --format json

# Quick version check
py7zz --py7zz-version
py7zz -V
```

## Format Support

### Supported Formats

py7zz supports reading and writing various archive formats:

| Format | Extension | Read | Write | Notes |
|--------|-----------|------|-------|-------|
| 7Z | .7z | ✅ | ✅ | Native format, best compression |
| ZIP | .zip | ✅ | ✅ | Wide compatibility |
| TAR | .tar | ✅ | ✅ | Unix standard |
| GZIP | .gz, .gzip | ✅ | ✅ | Single file compression |
| BZIP2 | .bz2 | ✅ | ✅ | Better compression than gzip |
| XZ | .xz | ✅ | ✅ | Excellent compression |
| LZ4 | .lz4 | ✅ | ✅ | Very fast compression |
| ZSTD | .zst | ✅ | ✅ | Modern, fast compression |
| RAR | .rar | ✅ | ❌ | Extract only |
| CAB | .cab | ✅ | ❌ | Windows cabinet files |
| ISO | .iso | ✅ | ❌ | Disc images |
| WIM | .wim | ✅ | ❌ | Windows imaging format |
| And 40+ more... | Various | ✅ | Various | See 7-Zip documentation |

### Format Detection

py7zz automatically detects the archive format based on file extensions:

```python
py7zz.create_archive('backup.7z', ['data/'])    # 7Z format
py7zz.create_archive('backup.zip', ['data/'])   # ZIP format
py7zz.create_archive('backup.tar', ['data/'])   # TAR format
py7zz.create_archive('backup.tar.gz', ['data/']) # TAR.GZ format
```

## Best Practices

### 1. Choose the Right Format

```python
# For maximum compression (long-term storage)
py7zz.create_archive('storage.7z', ['data/'], preset='ultra')

# For wide compatibility
py7zz.create_archive('portable.zip', ['data/'], preset='balanced')

# For Unix systems
py7zz.create_archive('backup.tar.gz', ['data/'], preset='balanced')
```

### 2. Use Appropriate Presets

```python
# Fast for temporary files
py7zz.create_archive('temp.7z', ['cache/'], preset='fast')

# Balanced for general use
py7zz.create_archive('backup.7z', ['data/'], preset='balanced')

# Ultra for long-term storage
py7zz.create_archive('archive.7z', ['important/'], preset='ultra')
```

### 3. Handle Large Files with Async

```python
async def process_large_files():
    # Use async for large operations
    await py7zz.create_archive_async('huge.7z', ['bigdata/'])
    
    # Process multiple archives concurrently
    tasks = [
        ('backup1.7z', ['folder1/']),
        ('backup2.7z', ['folder2/']),
        ('backup3.7z', ['folder3/'])
    ]
    await py7zz.batch_compress_async(tasks)
```

### 4. Implement Progress Reporting

```python
def progress_handler(info):
    # Clear line and print progress
    print(f"\r{info.operation}: {info.percentage:.1f}% - {info.current_file}", end='')

py7zz.create_archive('backup.7z', ['data/'], progress_callback=progress_handler)
print()  # New line after completion
```

### 5. Proper Error Handling

```python
def safe_create_archive(archive_path, files):
    try:
        py7zz.create_archive(archive_path, files)
        return True
    except py7zz.FileNotFoundError:
        print("Some files not found")
        return False
    except py7zz.InsufficientSpaceError:
        print("Not enough disk space")
        return False
    except py7zz.Py7zzError as e:
        print(f"Archive creation failed: {e}")
        return False
```

## Migration from zipfile/tarfile

For detailed migration instructions, see [MIGRATION.md](MIGRATION.md).

### Quick Migration Examples

#### From zipfile

```python
# OLD (zipfile)
import zipfile
with zipfile.ZipFile('archive.zip', 'w') as zf:
    zf.write('file.txt')

# NEW (py7zz)
import py7zz
with py7zz.SevenZipFile('archive.7z', 'w') as sz:
    sz.add('file.txt')
```

#### From tarfile

```python
# OLD (tarfile)
import tarfile
with tarfile.open('archive.tar.gz', 'w:gz') as tf:
    tf.add('file.txt')

# NEW (py7zz)
import py7zz
with py7zz.SevenZipFile('archive.tar.gz', 'w') as sz:
    sz.add('file.txt')
```

## CLI Interface

py7zz also provides a command-line interface:

```bash
# Get version information
py7zz version
py7zz version --format json
py7zz --py7zz-version
py7zz -V

# Direct 7zz operations (pass-through)
py7zz a backup.7z documents/ photos/
py7zz x backup.7z
py7zz l backup.7z
py7zz t backup.7z
```

For more CLI options, run:
```bash
py7zz --help
```
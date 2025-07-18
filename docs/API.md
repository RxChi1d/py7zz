# py7zz API Reference

Complete API documentation for py7zz, a Python wrapper for the 7zz CLI tool.

## Table of Contents

- [Simple Function API](#simple-function-api)
- [Object-Oriented API](#object-oriented-api)
- [Async Operations API](#async-operations-api)
- [Advanced Configuration](#advanced-configuration)
- [Exception Handling](#exception-handling)
- [Progress Callbacks](#progress-callbacks)
- [Version Information](#version-information)

## Simple Function API

### `create_archive(archive_path, files, *, preset=None, password=None, progress_callback=None)`

Create an archive with the specified files.

**Parameters:**
- `archive_path` (str): Path to the output archive
- `files` (List[str]): List of files/directories to archive
- `preset` (str, optional): Compression preset ('fast', 'balanced', 'backup', 'ultra')
- `password` (str, optional): Password for encrypted archives
- `progress_callback` (callable, optional): Progress callback function

**Returns:** None

**Example:**
```python
import py7zz

# Basic usage
py7zz.create_archive('backup.7z', ['documents/', 'photos/'])

# With preset and password
py7zz.create_archive(
    'secure_backup.7z',
    ['sensitive_data/'],
    preset='ultra',
    password='my_secret_password'
)

# With progress callback
def progress_handler(info):
    print(f"Progress: {info.percentage:.1f}%")

py7zz.create_archive(
    'large_backup.7z',
    ['big_folder/'],
    progress_callback=progress_handler
)
```

### `extract_archive(archive_path, output_dir, *, password=None, progress_callback=None)`

Extract an archive to the specified directory.

**Parameters:**
- `archive_path` (str): Path to the archive file
- `output_dir` (str): Directory to extract files to
- `password` (str, optional): Password for encrypted archives
- `progress_callback` (callable, optional): Progress callback function

**Returns:** None

**Example:**
```python
# Basic extraction
py7zz.extract_archive('backup.7z', 'extracted/')

# With password
py7zz.extract_archive('secure_backup.7z', 'extracted/', password='my_secret_password')
```

### `list_archive(archive_path, *, password=None)`

List contents of an archive.

**Parameters:**
- `archive_path` (str): Path to the archive file
- `password` (str, optional): Password for encrypted archives

**Returns:** List[str] - List of file paths in the archive

**Example:**
```python
files = py7zz.list_archive('backup.7z')
for file in files:
    print(file)
```

### `test_archive(archive_path, *, password=None)`

Test archive integrity.

**Parameters:**
- `archive_path` (str): Path to the archive file
- `password` (str, optional): Password for encrypted archives

**Returns:** bool - True if archive is valid, False otherwise

**Example:**
```python
if py7zz.test_archive('backup.7z'):
    print("Archive is OK")
else:
    print("Archive is corrupted")
```

### `get_archive_info(archive_path, *, password=None)`

Get detailed information about an archive.

**Parameters:**
- `archive_path` (str): Path to the archive file
- `password` (str, optional): Password for encrypted archives

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

### `SevenZipFile(archive_path, mode='r', *, preset=None, password=None, config=None)`

Main class for working with 7z archives, similar to `zipfile.ZipFile`.

**Parameters:**
- `archive_path` (str): Path to the archive file
- `mode` (str): Open mode ('r', 'w', 'a')
- `preset` (str, optional): Compression preset ('fast', 'balanced', 'backup', 'ultra')
- `password` (str, optional): Password for encrypted archives
- `config` (CompressionConfig, optional): Advanced compression configuration

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

### `batch_compress_async(tasks, *, progress_callback=None)`

Compress multiple archives concurrently.

**Parameters:**
- `tasks` (List[Tuple[str, List[str]]]): List of (archive_path, files) tuples
- `progress_callback` (callable, optional): Progress callback function

**Returns:** None

**Example:**
```python
async def main():
    tasks = [
        ('backup1.7z', ['folder1/']),
        ('backup2.7z', ['folder2/']),
        ('backup3.7z', ['folder3/'])
    ]
    
    await py7zz.batch_compress_async(tasks)

asyncio.run(main())
```

### `batch_extract_async(tasks, *, progress_callback=None)`

Extract multiple archives concurrently.

**Parameters:**
- `tasks` (List[Tuple[str, str]]): List of (archive_path, output_dir) tuples
- `progress_callback` (callable, optional): Progress callback function

**Returns:** None

## Advanced Configuration

### `CompressionConfig`

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
config = py7zz.CompressionConfig(
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

**Parameters:** Same as `CompressionConfig`

**Returns:** CompressionConfig

**Example:**
```python
config = py7zz.create_custom_config(
    level=7,
    method='LZMA2',
    dictionary_size='32m',
    solid=True
)
```

## Exception Handling

### Exception Hierarchy

```
Py7zzError (base exception)
├── BinaryNotFoundError
├── CompressionError
├── ExtractionError
├── FileNotFoundError
├── InvalidArchiveError
├── PasswordRequiredError
├── WrongPasswordError
└── InsufficientSpaceError
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

#### `FileNotFoundError`

Raised when a file is not found.

#### `InvalidArchiveError`

Raised when the archive is invalid or corrupted.

#### `PasswordRequiredError`

Raised when a password is required but not provided.

#### `WrongPasswordError`

Raised when an incorrect password is provided.

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
except py7zz.Py7zzError as e:
    print(f"General error: {e}")
```

## Progress Callbacks

### Progress Information

Progress callbacks receive a `ProgressInfo` object with the following attributes:

- `operation` (str): Current operation ('compress', 'extract', 'test')
- `percentage` (float): Completion percentage (0.0-100.0)
- `current_file` (str): Currently processed file
- `processed_files` (int): Number of files processed
- `total_files` (int): Total number of files
- `processed_size` (int): Bytes processed
- `total_size` (int): Total bytes to process
- `speed` (float): Processing speed in bytes/second
- `eta` (float): Estimated time to completion in seconds

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
    print(f"Files: {info.processed_files}/{info.total_files}")
    print(f"Size: {info.processed_size}/{info.total_size} bytes")
    print(f"Speed: {info.speed:.1f} bytes/s")
    print(f"ETA: {info.eta:.1f} seconds")
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
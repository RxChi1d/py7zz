# py7zz API Reference

Complete API documentation for py7zz, a Python wrapper for the 7zz CLI tool with Windows filename compatibility.

## Table of Contents

- [Simple Function API](#simple-function-api)
- [Object-Oriented API](#object-oriented-api)
- [Archive Information Classes](#archive-information-classes)
- [Industry Standard Compatibility](#industry-standard-compatibility)
- [Async Operations API](#async-operations-api)
- [Configuration API](#configuration-api)
- [Logging Integration](#logging-integration)
- [Advanced Configuration](#advanced-configuration)
- [Windows Filename Compatibility](#windows-filename-compatibility)
- [Progress Callbacks](#progress-callbacks)
- [Exception Handling](#exception-handling)
- [Version Information](#version-information)

## Simple Function API

py7zz provides a comprehensive Layer 1 Simple Function API with basic operations and advanced convenience functions for power users.

### Basic Operations

#### `create_archive(archive_path, files, preset="balanced")`

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

#### `extract_archive(archive_path, output_dir=".", overwrite=True)`

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

#### `list_archive(archive_path)`

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

#### `test_archive(archive_path)`

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

#### `get_archive_info(archive_path)`

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

### Advanced Convenience Functions

py7zz provides powerful convenience functions for advanced archive operations:

#### `batch_create_archives(operations, preset="balanced", overwrite=True, create_dirs=True)`

Create multiple archives in one operation with optimized performance.

**Parameters:**
- `operations` (List[Tuple[str, List[str]]]): List of (archive_path, source_paths) tuples
- `preset` (str, optional): Compression preset for all archives
- `overwrite` (bool): Whether to overwrite existing archives
- `create_dirs` (bool): Whether to create output directories

**Returns:** None

**Example:**
```python
import py7zz

# Create multiple archives efficiently
operations = [
    ('backup_docs.7z', ['documents/']),
    ('backup_photos.7z', ['photos/', 'screenshots/']),
    ('backup_code.7z', ['projects/', 'scripts/'])
]

py7zz.batch_create_archives(operations, preset='balanced')
```

#### `batch_extract_archives(archive_paths, output_dir=".", overwrite=True, create_dirs=True)`

Extract multiple archives to a common directory.

**Parameters:**
- `archive_paths` (List[str]): List of archive paths to extract
- `output_dir` (str): Common output directory
- `overwrite` (bool): Whether to overwrite existing files
- `create_dirs` (bool): Whether to create output directories

**Returns:** None

**Example:**
```python
# Extract multiple archives to organized directories
archives = ['backup1.7z', 'backup2.7z', 'backup3.7z']
py7zz.batch_extract_archives(archives, 'extracted/')
```

#### `copy_archive(source_archive, target_archive, recompress=False, preset="balanced")`

Copy an archive, optionally recompressing with different settings.

**Parameters:**
- `source_archive` (str): Source archive path
- `target_archive` (str): Target archive path
- `recompress` (bool): Whether to recompress (vs simple copy)
- `preset` (str): Compression preset if recompressing

**Returns:** None

**Example:**
```python
# Simple copy
py7zz.copy_archive('original.7z', 'backup.7z')

# Copy and recompress with better compression
py7zz.copy_archive('fast.7z', 'storage.7z', recompress=True, preset='ultra')
```

#### `get_compression_ratio(archive_path)`

Calculate the compression ratio for an archive.

**Parameters:**
- `archive_path` (str): Path to the archive file

**Returns:** float - Compression ratio as decimal (0.0 = no compression, 1.0 = 100% compression)

**Example:**
```python
ratio = py7zz.get_compression_ratio('backup.7z')
print(f"Compression saved {ratio:.1%} space")
```

#### `get_archive_format(archive_path)`

Detect the format of an archive file.

**Parameters:**
- `archive_path` (str): Path to the archive file

**Returns:** str - Archive format ('7z', 'zip', 'tar', 'gzip', etc.)

**Example:**
```python
format_type = py7zz.get_archive_format('unknown_archive.bin')
print(f"Archive format: {format_type}")
```

#### `compare_archives(archive1, archive2, compare_content=False)`

Compare two archives for equality.

**Parameters:**
- `archive1` (str): First archive path
- `archive2` (str): Second archive path
- `compare_content` (bool): Whether to compare file contents (slow but thorough)

**Returns:** bool - True if archives are equivalent

**Example:**
```python
# Quick comparison (file list and sizes)
if py7zz.compare_archives('backup1.7z', 'backup2.7z'):
    print("Archives have same files")

# Deep comparison (includes content)
if py7zz.compare_archives('v1.7z', 'v2.7z', compare_content=True):
    print("Archives are identical")
```

#### `convert_archive_format(source_archive, target_archive, target_format=None, preset="balanced")`

Convert an archive from one format to another.

**Parameters:**
- `source_archive` (str): Source archive path
- `target_archive` (str): Target archive path
- `target_format` (str, optional): Target format (auto-detected from extension if None)
- `preset` (str): Compression preset for target archive

**Returns:** None

**Example:**
```python
# Convert ZIP to 7Z for better compression
py7zz.convert_archive_format('old.zip', 'new.7z', preset='ultra')

# Convert 7Z to ZIP for compatibility
py7zz.convert_archive_format('archive.7z', 'portable.zip')
```

#### `recompress_archive(archive_path, new_preset, backup_original=True, backup_suffix=".backup")`

Recompress an archive with different settings.

**Parameters:**
- `archive_path` (str): Archive to recompress
- `new_preset` (str): New compression preset
- `backup_original` (bool): Whether to keep original as backup
- `backup_suffix` (str): Suffix for backup file

**Returns:** None

**Example:**
```python
# Recompress for better compression, keeping original
py7zz.recompress_archive('data.7z', 'ultra', backup_original=True)
# Creates: data.7z (recompressed) and data.7z.backup (original)

# Recompress for faster access, no backup
py7zz.recompress_archive('archive.7z', 'fast', backup_original=False)
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

##### `extractall(output_dir, members=None)`

Extract all files from the archive, with optional selective extraction.

**Parameters:**
- `output_dir` (str): Directory to extract to
- `members` (Optional[List[str]]): List of specific members to extract (zipfile/tarfile compatible)

**Returns:** None

**Example:**
```python
# Extract everything
sz.extractall('output/')

# Extract specific files (zipfile/tarfile compatible)
sz.extractall('output/', members=['file1.txt', 'folder/file2.txt'])
```

##### `add(path, arcname=None)`

Add a file or directory to the archive with optional custom naming.

**Parameters:**
- `path` (str): Path to the file/directory to add
- `arcname` (str, optional): Custom name to use in the archive (zipfile compatible)

**Returns:** None

**Example:**
```python
# Add with original name
sz.add('file.txt')

# Add with custom name (zipfile compatible)
sz.add('file.txt', arcname='renamed.txt')
sz.add('src/data.txt', arcname='backup/data.txt')
```

##### `infolist()`

Get detailed information about all archive members (zipfile.ZipFile compatible).

**Returns:** List[ArchiveInfo] - List of archive member information objects

**Example:**
```python
info_list = sz.infolist()
for info in info_list:
    print(f"{info.filename}: {info.file_size} bytes")
    print(f"  Compressed: {info.compress_size} bytes")
    print(f"  Ratio: {info.get_compression_ratio():.1%}")
```

##### `getinfo(name)`

Get detailed information about a specific archive member (zipfile.ZipFile compatible).

**Parameters:**
- `name` (str): Name of the archive member

**Returns:** ArchiveInfo - Archive member information object

**Raises:**
- `KeyError`: If the member is not found in the archive

**Example:**
```python
info = sz.getinfo('file.txt')
print(f"Size: {info.file_size}")
print(f"Modified: {info.date_time}")
print(f"CRC: {info.CRC:08X}")
```

##### `getmembers()`

Get detailed information about all archive members (tarfile.TarFile compatible).

**Returns:** List[ArchiveInfo] - List of archive member information objects

**Example:**
```python
members = sz.getmembers()
for member in members:
    print(f"{member.filename} ({member.type})")
    if hasattr(member, 'mode'):
        print(f"  Mode: {oct(member.mode)}")
```

##### `getmember(name)`

Get detailed information about a specific archive member (tarfile.TarFile compatible).

**Parameters:**
- `name` (str): Name of the archive member

**Returns:** ArchiveInfo - Archive member information object

**Raises:**
- `KeyError`: If the member is not found in the archive

##### `getnames()`

Get list of archive member names (tarfile.TarFile compatible).

**Returns:** List[str] - List of member names

**Example:**
```python
names = sz.getnames()
for name in names:
    print(name)
```

##### New Enhanced Methods

py7zz 1.0+ adds powerful new methods to SevenZipFile for complete industry standard compatibility:

##### `open(name, mode="r")`

Open a file in the archive for reading, returning a file-like object (zipfile compatible).

**Parameters:**
- `name` (str): Name of the file in the archive
- `mode` (str): Open mode ('r' for read)

**Returns:** ArchiveFileReader - File-like object for reading

**Example:**
```python
with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    with sz.open('config.txt') as f:
        content = f.read()
        print(content.decode('utf-8'))
```

##### `readall()`

Read and return the bytes of all files in the archive as a bytes object.

**Returns:** bytes - Concatenated content of all files

##### `setpassword(pwd)`

Set password for encrypted archives (zipfile compatible).

**Parameters:**
- `pwd` (Optional[bytes]): Password as bytes, or None to clear

**Example:**
```python
with py7zz.SevenZipFile('encrypted.7z', 'r') as sz:
    sz.setpassword(b'secret_password')
    content = sz.read('encrypted_file.txt')
```

##### `comment()`

Get archive comment (zipfile compatible).

**Returns:** bytes - Archive comment as bytes

##### `setcomment(comment)`

Set archive comment (zipfile compatible).

**Parameters:**
- `comment` (bytes): Comment to set as bytes

##### `copy_member(member_name, target_archive)`

Copy a member from this archive to another archive.

**Parameters:**
- `member_name` (str): Name of the member to copy
- `target_archive` (SevenZipFile): Target archive object

**Example:**
```python
with py7zz.SevenZipFile('source.7z', 'r') as src:
    with py7zz.SevenZipFile('target.7z', 'w') as dst:
        src.copy_member('important.txt', dst)
```

##### `filter_members(filter_func)`

Filter archive members using a custom function.

**Parameters:**
- `filter_func` (Callable[[str], bool]): Function that returns True for members to include

**Returns:** List[str] - List of member names that match the filter

**Example:**
```python
with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    # Get all Python files
    python_files = sz.filter_members(lambda name: name.endswith('.py'))
    
    # Get all files in a specific directory
    docs = sz.filter_members(lambda name: name.startswith('docs/'))
```

##### `get_member_size(name)`

Get the uncompressed size of a specific member.

**Parameters:**
- `name` (str): Name of the archive member

**Returns:** int - Uncompressed size in bytes

##### `get_member_compressed_size(name)`

Get the compressed size of a specific member.

**Parameters:**
- `name` (str): Name of the archive member

**Returns:** int - Compressed size in bytes

**Example:**
```python
with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    original_size = sz.get_member_size('large_file.txt')
    compressed_size = sz.get_member_compressed_size('large_file.txt')
    ratio = 1 - (compressed_size / original_size)
    print(f"Compression saved {ratio:.1%} space")
```

##### `close()`

Close the archive file.

**Returns:** None

## Archive Information Classes

### `ArchiveInfo`

Represents information about a member in an archive, compatible with both `zipfile.ZipInfo` and `tarfile.TarInfo`.

**Attributes:**
- `filename` (str): Name of the archive member
- `file_size` (int): Uncompressed size in bytes
- `compress_size` (int): Compressed size in bytes
- `date_time` (Optional[tuple]): Last modification time as (year, month, day, hour, minute, second)
- `CRC` (int): CRC-32 checksum
- `method` (str): Compression method used
- `type` (str): File type ('file', 'dir', 'link')
- `mode` (Optional[int]): File permissions (Unix-style)
- `uid` (Optional[int]): User ID (Unix-style)
- `gid` (Optional[int]): Group ID (Unix-style)
- `mtime` (Optional[float]): Modification time as timestamp
- `attributes` (int): File attributes
- `comment` (str): File comment
- `encrypted` (Optional[bool]): Whether the file is encrypted
- `solid` (Optional[bool]): Whether the file is part of solid compression

**Example:**
```python
import py7zz

with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    info = sz.getinfo('file.txt')
    
    # Basic information
    print(f"Name: {info.filename}")
    print(f"Size: {info.file_size} bytes")
    print(f"Compressed: {info.compress_size} bytes")
    print(f"CRC: {info.CRC:08X}")
    
    # Time information
    if info.date_time:
        year, month, day, hour, minute, second = info.date_time
        print(f"Modified: {year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}")
    
    # Compression information
    print(f"Method: {info.method}")
    print(f"Ratio: {info.get_compression_ratio():.1%}")
```

#### Methods

##### `is_dir()`

Check if the archive member is a directory.

**Returns:** bool - True if directory, False otherwise

##### `isfile()`

Check if the archive member is a regular file (zipfile.ZipInfo compatible).

**Returns:** bool - True if regular file, False otherwise

##### `isdir()`

Check if the archive member is a directory (zipfile.ZipInfo compatible).

**Returns:** bool - True if directory, False otherwise

##### `get_compression_ratio()`

Calculate the compression ratio.

**Returns:** float - Compression ratio as a decimal (0.0 = no compression, 1.0 = 100% compression)

##### `from_zipinfo(zipinfo)`

Create an ArchiveInfo object from a zipfile.ZipInfo object.

**Parameters:**
- `zipinfo` (zipfile.ZipInfo): Source ZipInfo object

**Returns:** ArchiveInfo - New ArchiveInfo instance

**Example:**
```python
import zipfile
import py7zz

# Convert from zipfile.ZipInfo
with zipfile.ZipFile('archive.zip', 'r') as zf:
    zip_info = zf.getinfo('file.txt')
    archive_info = py7zz.ArchiveInfo.from_zipinfo(zip_info)
    print(f"Converted: {archive_info.filename}")
```

##### `from_tarinfo(tarinfo)`

Create an ArchiveInfo object from a tarfile.TarInfo object.

**Parameters:**
- `tarinfo` (tarfile.TarInfo): Source TarInfo object

**Returns:** ArchiveInfo - New ArchiveInfo instance

**Example:**
```python
import tarfile
import py7zz

# Convert from tarfile.TarInfo
with tarfile.open('archive.tar.gz', 'r:gz') as tf:
    tar_info = tf.getmember('file.txt')
    archive_info = py7zz.ArchiveInfo.from_tarinfo(tar_info)
    print(f"Converted: {archive_info.filename}")
```

## Industry Standard Compatibility

py7zz provides complete compatibility with Python's standard library archive modules.

### zipfile.ZipFile Compatibility

py7zz's `SevenZipFile` class provides all major `zipfile.ZipFile` methods:

```python
import py7zz

# zipfile-style usage
with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    # Get list of files
    names = sz.namelist()
    
    # Get detailed information
    info_list = sz.infolist()
    info = sz.getinfo('file.txt')
    
    # Extract files
    sz.extractall('output/')
    sz.extractall('output/', members=['file1.txt', 'file2.txt'])

# Write archives
with py7zz.SevenZipFile('archive.7z', 'w') as sz:
    sz.add('file.txt')
    sz.add('src/data.txt', arcname='backup/data.txt')
```

### tarfile.TarFile Compatibility

py7zz also provides `tarfile.TarFile` compatible methods:

```python
import py7zz

# tarfile-style usage
with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    # Get member information
    members = sz.getmembers()
    member = sz.getmember('file.txt')
    
    # Get member names
    names = sz.getnames()
    
    # Extract specific members
    sz.extractall('output/', members=['file1.txt', 'dir/'])
```

### Migration Examples

#### From zipfile

```python
# OLD (zipfile)
import zipfile

with zipfile.ZipFile('archive.zip', 'r') as zf:
    names = zf.namelist()
    info = zf.getinfo('file.txt')
    info_list = zf.infolist()
    zf.extractall('output/')
    zf.extractall('output/', members=['file1.txt'])

# NEW (py7zz) - Identical API
import py7zz

with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    names = sz.namelist()           # Same method
    info = sz.getinfo('file.txt')   # Same method, returns ArchiveInfo
    info_list = sz.infolist()       # Same method, returns List[ArchiveInfo]
    sz.extractall('output/')        # Same method
    sz.extractall('output/', members=['file1.txt'])  # Same parameters
```

#### From tarfile

```python
# OLD (tarfile)
import tarfile

with tarfile.open('archive.tar.gz', 'r:gz') as tf:
    names = tf.getnames()
    members = tf.getmembers()
    member = tf.getmember('file.txt')
    tf.extractall('output/')

# NEW (py7zz) - Compatible API
import py7zz

with py7zz.SevenZipFile('archive.tar.gz', 'r') as sz:
    names = sz.getnames()           # tarfile compatible
    members = sz.getmembers()       # tarfile compatible
    member = sz.getmember('file.txt')  # tarfile compatible
    sz.extractall('output/')        # Same method
```

### Advanced Compatibility Features

#### Unified ArchiveInfo Objects

Both zipfile and tarfile compatible methods return the same `ArchiveInfo` objects:

```python
with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    # All these methods return ArchiveInfo objects
    zipfile_style = sz.infolist()[0]  # ArchiveInfo
    tarfile_style = sz.getmembers()[0]  # ArchiveInfo (same object)
    
    # Access properties using either style
    print(f"zipfile style: {zipfile_style.file_size}")
    print(f"tarfile style: {tarfile_style.size}")  # Same value, different name
```

#### Factory Methods for Conversion

Convert existing archive info objects:

```python
import zipfile
import tarfile
import py7zz

# Convert from zipfile
with zipfile.ZipFile('archive.zip', 'r') as zf:
    zip_info = zf.getinfo('file.txt')
    archive_info = py7zz.ArchiveInfo.from_zipinfo(zip_info)

# Convert from tarfile
with tarfile.open('archive.tar.gz', 'r:gz') as tf:
    tar_info = tf.getmember('file.txt')
    archive_info = py7zz.ArchiveInfo.from_tarinfo(tar_info)
```

## Async Operations API

py7zz provides comprehensive asynchronous support for all archive operations, enabling non-blocking I/O with progress reporting capabilities.

### `AsyncSevenZipFile`

Asynchronous wrapper for `SevenZipFile` operations with complete industry standard compatibility.

**Parameters:**
- `file` (Union[str, Path]): Path to the archive file
- `mode` (str): File mode ('r' for read, 'w' for write)

**Example:**
```python
import asyncio
import py7zz

async def async_operations():
    # Reading archives asynchronously
    async with py7zz.AsyncSevenZipFile('archive.7z', 'r') as asz:
        names = await asz.namelist()
        content = await asz.read('file.txt')
        
    # Writing archives asynchronously
    async with py7zz.AsyncSevenZipFile('new_archive.7z', 'w') as asz:
        await asz.add('file.txt', arcname='renamed.txt')
        await asz.writestr('data.txt', 'Hello, World!')

asyncio.run(async_operations())
```

#### Complete Method Reference

##### Information Methods

**`await namelist()`**
Get list of archive member names asynchronously (zipfile compatible).

**Returns:** List[str] - List of file paths

**`await getnames()`**
Get list of archive member names asynchronously (tarfile compatible).

**Returns:** List[str] - List of file paths

**`await infolist()`**
Get detailed information about all archive members (zipfile compatible).

**Returns:** List[ArchiveInfo] - List of archive member information objects

**`await getmembers()`**
Get detailed information about all archive members (tarfile compatible).

**Returns:** List[ArchiveInfo] - List of archive member information objects

**`await getinfo(name)`**
Get detailed information about a specific member (zipfile compatible).

**Parameters:**
- `name` (str): Name of the archive member

**Returns:** ArchiveInfo - Archive member information object

**`await getmember(name)`**
Get detailed information about a specific member (tarfile compatible).

**Parameters:**
- `name` (str): Name of the archive member

**Returns:** ArchiveInfo - Archive member information object

##### File Operations

**`await read(name)`**
Read and return the bytes of a file in the archive asynchronously.

**Parameters:**
- `name` (str): Name of the file in the archive

**Returns:** bytes - File content

**Raises:**
- `ValueError`: If archive is opened in write mode
- `FileNotFoundError`: If file is not found in archive

**Example:**
```python
async with py7zz.AsyncSevenZipFile('archive.7z', 'r') as asz:
    content = await asz.read('file.txt')
    print(content.decode('utf-8'))
```

**`await writestr(filename, data)`**
Write a string or bytes to a file in the archive asynchronously.

**Parameters:**
- `filename` (str): Name of the file in the archive
- `data` (Union[str, bytes]): String or bytes data to write

**Raises:**
- `ValueError`: If archive is opened in read mode

**Example:**
```python
async with py7zz.AsyncSevenZipFile('archive.7z', 'w') as asz:
    await asz.writestr('config.txt', 'debug=true')
    await asz.writestr('binary.dat', b'\x00\x01\x02\x03')
```

**`await add(name, arcname=None, progress_callback=None)`**
Add file or directory to archive asynchronously with optional custom naming.

**Parameters:**
- `name` (Union[str, Path]): Path to file/directory to add
- `arcname` (str, optional): Custom name to use in the archive
- `progress_callback` (callable, optional): Progress callback function

**Example:**
```python
async with py7zz.AsyncSevenZipFile('archive.7z', 'w') as asz:
    # Add with original name
    await asz.add('file.txt')
    
    # Add with custom name (zipfile compatible)
    await asz.add('data.txt', arcname='backup/data.txt')
    
    # Add with progress callback
    def progress_handler(info):
        print(f"Progress: {info.percentage:.1f}%")
    
    await asz.add('large_file.txt', progress_callback=progress_handler)
```

##### Extraction Methods

**`await extractall(path=".", members=None, progress_callback=None)`**
Extract all members from the archive asynchronously.

**Parameters:**
- `path` (Union[str, Path]): Directory to extract to (default: current directory)
- `members` (Optional[List[str]]): List of member names to extract (default: all)
- `progress_callback` (callable, optional): Progress callback function

**Example:**
```python
async with py7zz.AsyncSevenZipFile('archive.7z', 'r') as asz:
    # Extract everything
    await asz.extractall('output/')
    
    # Extract specific files (zipfile/tarfile compatible)
    await asz.extractall('output/', members=['file1.txt', 'folder/file2.txt'])
    
    # Extract with progress reporting
    def progress_handler(info):
        print(f"Extracting: {info.current_file}")
    
    await asz.extractall('output/', progress_callback=progress_handler)
```

##### Testing and Validation

**`await testzip()`**
Test the archive for bad CRC or other errors asynchronously.

**Returns:** Optional[str] - None if archive is OK, otherwise name of first bad file

**Example:**
```python
async with py7zz.AsyncSevenZipFile('archive.7z', 'r') as asz:
    result = await asz.testzip()
    if result is None:
        print("Archive is OK")
    else:
        print(f"Archive has issues with: {result}")
```

**`await close()`**
Close the archive asynchronously (for API completeness).

##### Iteration Support

**`async for name in asz:`**
Async iterator support for archive member names.

**Example:**
```python
async with py7zz.AsyncSevenZipFile('archive.7z', 'r') as asz:
    async for name in asz:
        print(f"Found file: {name}")
        content = await asz.read(name)
        # Process content...
```

**`await asz.__acontains__(name)`**
Check if a file exists in the archive asynchronously.

**Parameters:**
- `name` (str): Name to check

**Returns:** bool - True if file exists in archive

**Example:**
```python
async with py7zz.AsyncSevenZipFile('archive.7z', 'r') as asz:
    if await asz.__acontains__('config.txt'):
        config = await asz.read('config.txt')
```

#### Complete Usage Example

```python
import asyncio
import py7zz

async def comprehensive_async_example():
    # Create archive with multiple files
    async with py7zz.AsyncSevenZipFile('demo.7z', 'w') as asz:
        # Add files with different methods
        await asz.add('README.md')
        await asz.add('src/main.py', arcname='main.py')
        await asz.writestr('version.txt', '1.0.0')
        await asz.writestr('metadata.json', '{"created": "2024"}')
    
    # Read and analyze archive
    async with py7zz.AsyncSevenZipFile('demo.7z', 'r') as asz:
        # Test archive integrity
        test_result = await asz.testzip()
        print(f"Archive test: {'OK' if test_result is None else f'Error: {test_result}'}")
        
        # Get archive information
        info_list = await asz.infolist()
        members = await asz.getmembers()  # Same data, tarfile style
        
        print(f"Archive contains {len(info_list)} files:")
        for info in info_list:
            print(f"  {info.filename}: {info.file_size} bytes")
        
        # Iterate through all files
        async for filename in asz:
            if filename.endswith('.txt'):
                content = await asz.read(filename)
                print(f"Content of {filename}: {content.decode('utf-8')}")
        
        # Check for specific files
        if await asz.__acontains__('main.py'):
            main_content = await asz.read('main.py')
            print(f"main.py size: {len(main_content)} bytes")
        
        # Extract specific files
        await asz.extractall('extracted/', members=['version.txt', 'metadata.json'])

# Run the example
asyncio.run(comprehensive_async_example())
```

### Simple Async Functions

The simple function API also provides async versions for high-level operations.

#### `create_archive_async(archive_path, files, preset="balanced", progress_callback=None)`

Create an archive with specified files asynchronously.

**Parameters:**
- `archive_path` (Union[str, Path]): Path to the output archive
- `files` (List[Union[str, Path]]): List of files/directories to archive
- `preset` (str, optional): Compression preset ('fast', 'balanced', 'backup', 'ultra')
- `progress_callback` (callable, optional): Progress callback function

**Returns:** None

**Example:**
```python
import asyncio
import py7zz

async def progress_handler(info):
    print(f"Creating archive: {info.percentage:.1f}% - {info.current_file}")

async def main():
    # Basic usage
    await py7zz.create_archive_async('backup.7z', ['documents/', 'photos/'])
    
    # With preset and progress
    await py7zz.create_archive_async(
        'backup.7z',
        ['documents/'],
        preset='ultra',
        progress_callback=progress_handler
    )

asyncio.run(main())
```

#### `extract_archive_async(archive_path, output_dir=".", overwrite=True, progress_callback=None)`

Extract an archive to the specified directory asynchronously with automatic Windows filename compatibility handling.

**Parameters:**
- `archive_path` (Union[str, Path]): Path to the archive file
- `output_dir` (Union[str, Path]): Directory to extract files to (default: current directory)
- `overwrite` (bool): Whether to overwrite existing files
- `progress_callback` (callable, optional): Progress callback function

**Returns:** None 

**Raises:**
- `FilenameCompatibilityError`: When filename issues cannot be resolved
- `ExtractionError`: When extraction fails for other reasons

**Example:**
```python
async def extraction_progress(info):
    print(f"Extracting: {info.current_file} ({info.percentage:.1f}%)")

async def main():
    # Basic extraction with automatic filename handling
    await py7zz.extract_archive_async('backup.7z', 'extracted/')
    
    # Extract with progress reporting
    await py7zz.extract_archive_async(
        'backup.7z',
        'extracted/',
        progress_callback=extraction_progress
    )

asyncio.run(main())
```

#### `compress_file_async(input_path, output_path=None, preset="balanced", progress_callback=None)`

Compress a single file asynchronously.

**Parameters:**
- `input_path` (Union[str, Path]): File to compress
- `output_path` (Union[str, Path], optional): Output archive path (auto-generated if None)
- `preset` (str): Compression preset
- `progress_callback` (callable, optional): Progress callback function

**Returns:** Path - Path to the created archive

**Example:**
```python
async def main():
    compressed = await py7zz.compress_file_async('large_file.txt')
    print(f"Compressed to: {compressed}")

asyncio.run(main())
```

#### `compress_directory_async(input_dir, output_path=None, preset="balanced", progress_callback=None)`

Compress an entire directory asynchronously.

**Parameters:**
- `input_dir` (Union[str, Path]): Directory to compress
- `output_path` (Union[str, Path], optional): Output archive path (auto-generated if None)
- `preset` (str): Compression preset
- `progress_callback` (callable, optional): Progress callback function

**Returns:** Path - Path to the created archive

**Example:**
```python
async def main():
    compressed = await py7zz.compress_directory_async('my_project/')
    print(f"Project archived to: {compressed}")

asyncio.run(main())
```

#### `batch_compress_async(operations, progress_callback=None)`

Compress multiple archives concurrently for maximum efficiency.

**Parameters:**
- `operations` (List[Tuple[Union[str, Path], List[Union[str, Path]]]]): List of (archive_path, files) tuples
- `progress_callback` (callable, optional): Progress callback function

**Returns:** None

**Example:**
```python
async def batch_progress(info):
    print(f"Batch operation: {info.operation} - {info.current_file}")

async def main():
    # Define multiple compression tasks
    operations = [
        ('backup1.7z', ['documents/']),
        ('backup2.7z', ['photos/']),
        ('backup3.7z', ['projects/'])
    ]
    
    # Execute all compressions concurrently
    await py7zz.batch_compress_async(operations, progress_callback=batch_progress)
    print("All archives created successfully!")

asyncio.run(main())
```

#### `batch_extract_async(operations, progress_callback=None)`

Extract multiple archives concurrently for maximum efficiency.

**Parameters:**
- `operations` (List[Tuple[Union[str, Path], Union[str, Path]]]): List of (archive_path, output_dir) tuples
- `progress_callback` (callable, optional): Progress callback function

**Returns:** None

**Example:**
```python
async def main():
    # Define multiple extraction tasks
    operations = [
        ('backup1.7z', 'extracted1/'),
        ('backup2.7z', 'extracted2/'),
        ('backup3.7z', 'extracted3/')
    ]
    
    # Execute all extractions concurrently
    await py7zz.batch_extract_async(operations)
    print("All archives extracted successfully!")

asyncio.run(main())
```

### Async Progress Reporting

All async functions support progress reporting through callback functions that receive `ProgressInfo` objects:

```python
import asyncio
import py7zz

async def detailed_progress_handler(info):
    """Comprehensive progress reporting for async operations."""
    print(f"Operation: {info.operation}")
    print(f"Progress: {info.percentage:.1f}%")
    print(f"Current file: {info.current_file}")
    print(f"Files processed: {info.files_processed}/{info.total_files}")
    if info.total_bytes > 0:
        print(f"Bytes processed: {info.bytes_processed}/{info.total_bytes}")
    print("-" * 50)

async def main():
    # Use progress reporting with any async function
    await py7zz.create_archive_async(
        'large_backup.7z',
        ['large_directory/'],
        preset='ultra',
        progress_callback=detailed_progress_handler
    )

asyncio.run(main())
```

### Error Handling in Async Operations

Async operations use the same exception hierarchy as synchronous operations:

```python
import asyncio
import py7zz

async def safe_async_operation():
    try:
        await py7zz.create_archive_async('backup.7z', ['nonexistent/'])
    except py7zz.FileNotFoundError:
        print("Source files not found")
    except py7zz.CompressionError as e:
        print(f"Compression failed: {e}")
    except py7zz.InsufficientSpaceError:
        print("Not enough disk space")
    except py7zz.Py7zzError as e:
        print(f"General error: {e}")

asyncio.run(safe_async_operation())
```

## Advanced Features API

py7zz 1.1+ includes features designed for production environments, cloud integration, and high-performance applications.

### Cloud Integration & Streaming

#### `ArchiveStreamReader`

Stream files directly from archives without extracting to disk, compatible with `io.BufferedIOBase`.

**Parameters:**
- `archive` (SevenZipFile): Source archive object
- `member_name` (str): Name of the file to stream
- `encoding` (str, optional): Text encoding for the file

**Returns:** ArchiveStreamReader object implementing `io.BufferedIOBase`

**Example:**
```python
import py7zz
import boto3  # for AWS S3 example

# Stream archive content directly to cloud storage
with py7zz.SevenZipFile('large_archive.7z', 'r') as sz:
    # Stream specific file to S3 without local extraction
    with sz.open_stream('big_data.csv') as stream:
        s3_client = boto3.client('s3')
        s3_client.upload_fileobj(stream, 'my-bucket', 'data/big_data.csv')

# Convenience function for common use cases
with py7zz.create_stream_reader('archive.7z', 'data.txt') as reader:
    data = reader.read(1024)  # Read in chunks
```

**Methods:**
- `read(size=-1)`: Read up to size bytes
- `readline(size=-1)`: Read a line from the stream
- `readinto(buffer)`: Read into a pre-allocated buffer
- `seek(offset, whence=0)`: Seek to position in stream
- `tell()`: Get current position
- `close()`: Close the stream

#### `ArchiveStreamWriter`

Stream data directly into archives without creating intermediate files.

**Parameters:**
- `archive` (SevenZipFile): Target archive object
- `member_name` (str): Name for the file in the archive

**Returns:** ArchiveStreamWriter object implementing `io.BufferedIOBase`

**Example:**
```python
import py7zz

# Stream data directly from source to archive
with py7zz.SevenZipFile('output.7z', 'w') as sz:
    # Stream large dataset directly to archive
    with sz.open_stream_writer('processed_data.csv') as writer:
        for chunk in process_large_dataset():
            writer.write(chunk)  # Direct streaming, no intermediate files

# Create archive from cloud data
with py7zz.create_stream_writer('cloud_backup.7z', 'backup.json') as writer:
    cloud_data = download_from_api()
    writer.write(cloud_data)
```

**Methods:**
- `write(data)`: Write bytes to the stream
- `flush()`: Flush write buffers
- `seek(offset, whence=0)`: Seek to position in stream
- `tell()`: Get current position
- `close()`: Close and finalize the stream

#### Cloud Service Integration Examples

**Amazon S3:**
```python
import py7zz
import boto3

# Upload archive stream to S3
s3_client = boto3.client('s3')
with py7zz.SevenZipFile('data.7z', 'r') as sz:
    with sz.open_stream('large_file.txt') as stream:
        s3_client.upload_fileobj(stream, 'bucket', 'key')

# Download from S3 and create archive
response = s3_client.get_object(Bucket='bucket', Key='data.txt')
with py7zz.SevenZipFile('backup.7z', 'w') as sz:
    with sz.open_stream_writer('data.txt') as writer:
        for chunk in response['Body'].iter_chunks():
            writer.write(chunk)
```

**Azure Blob Storage:**
```python
import py7zz
from azure.storage.blob import BlobServiceClient

# Stream to Azure Blob
blob_client = BlobServiceClient.from_connection_string(conn_str)
with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    with sz.open_stream('data.csv') as stream:
        blob_client.upload_blob('container', 'data.csv', stream)
```

### Thread-Safe Configuration

#### `ImmutableConfig`

Frozen configuration objects for thread-safe operations.

**Parameters:**
- `compression` (str): Compression method ('lzma2', 'bzip2', etc.)
- `level` (int): Compression level (0-9)
- `solid` (bool): Enable solid compression
- `threads` (int, optional): Number of threads to use
- `memory_limit` (str, optional): Memory limit (e.g., '2g', '512m')
- `password` (str, optional): Archive password
- `encrypt_filenames` (bool): Encrypt file names
- `preset_name` (str): Configuration preset name

**Returns:** ImmutableConfig object

**Example:**
```python
import py7zz

# Create immutable configuration
config = py7zz.ImmutableConfig(
    level=8,
    compression="lzma2",
    solid=True,
    threads=4,
    memory_limit="1g",
    preset_name="production_backup"
)

# Configuration is immutable - cannot be modified
# config.level = 9  # This would raise an error

# Create new configuration with changes
production_config = config.replace(level=9, threads=8)
```

**Methods:**
- `replace(**changes)`: Create new config with specified changes
- `to_dict()`: Convert to dictionary
- `from_dict(data)`: Create from dictionary (class method)
- `validate()`: Validate configuration and return warnings

#### `ThreadSafeGlobalConfig`

Thread-safe global configuration manager with RWLock pattern.

**Example:**
```python
import py7zz
import threading
from concurrent.futures import ThreadPoolExecutor

# Set global configuration (thread-safe)
config = py7zz.ImmutableConfig(level=7, preset_name="production")
py7zz.ThreadSafeGlobalConfig.set_config(config)

def worker_task(data_folder):
    # Thread-safe access to global config
    current_config = py7zz.ThreadSafeGlobalConfig.get_config()
    print(f"Using preset: {current_config.preset_name}")
    
    # Temporary configuration changes per thread
    with py7zz.ThreadSafeGlobalConfig.temporary_config(level=9) as temp_config:
        # This thread uses level=9, others unaffected
        py7zz.create_archive(f'{data_folder}.7z', [data_folder])
    
    # Original configuration restored automatically

# Safe concurrent execution
with ThreadPoolExecutor(max_workers=8) as executor:
    tasks = ['data_1', 'data_2', 'data_3', 'data_4']
    executor.map(worker_task, tasks)
```

**Class Methods:**
- `get_config()`: Get current global configuration
- `set_config(config)`: Set global configuration
- `update_config(**changes)`: Update global configuration
- `temporary_config(**changes)`: Context manager for temporary changes
- `load_from_file(path)`: Load configuration from JSON file
- `save_to_file(path)`: Save configuration to JSON file
- `load_user_config()`: Load from default user config location
- `save_user_config()`: Save to default user config location
- `reset_to_defaults()`: Reset to default configuration
- `get_config_info()`: Get configuration information and statistics

#### Preset Management Functions

**`get_preset_config(preset_name)`**

Get immutable preset configuration.

**Parameters:**
- `preset_name` (str): Name of the preset ('fast', 'balanced', 'backup', 'ultra')

**Returns:** ImmutableConfig object

**`apply_preset(preset_name)`**

Apply preset configuration globally.

**`with_preset(preset_name)`**

Context manager for operations with specific preset.

**Example:**
```python
import py7zz

# Get preset configuration
ultra_config = py7zz.get_preset_config("ultra")
print(f"Ultra preset level: {ultra_config.level}")

# Apply preset globally
py7zz.apply_preset("fast")

# Use preset for specific operations
with py7zz.with_preset("ultra"):
    # Operations in this context use ultra compression
    py7zz.create_archive('high_compression.7z', ['important_data/'])

# Original preset restored after context
```

### Structured Progress Callbacks

#### `ProgressInfo`

Progress information structure for operations monitoring.

**Attributes:**
- `percentage` (float): Progress as percentage (0.0 - 100.0)
- `bytes_processed` (int): Number of bytes processed
- `total_bytes` (Optional[int]): Total bytes to process
- `speed_bps` (Optional[float]): Processing speed in bytes per second
- `elapsed_time` (float): Elapsed time in seconds
- `estimated_remaining` (Optional[float]): Estimated remaining time
- `operation_type` (OperationType): Type of operation
- `operation_stage` (OperationStage): Current stage of operation
- `current_file` (Optional[str]): Currently processing file
- `files_processed` (int): Number of files completed
- `total_files` (Optional[int]): Total number of files
- `metadata` (Dict[str, Any]): Extensible metadata dictionary

**Properties:**
- `completion_ratio`: Progress as ratio (0.0 - 1.0)
- `bytes_remaining`: Remaining bytes to process
- `files_remaining`: Remaining files to process

**Methods:**
- `format_speed()`: Format speed as human-readable string
- `format_time(seconds)`: Format time duration as human-readable string

**Example:**
```python
import py7zz

def progress_callback(progress: py7zz.ProgressInfo):
    print(f"Operation: {progress.operation_type.value}")
    print(f"Stage: {progress.operation_stage.value}")
    print(f"Progress: {progress.percentage:.2f}%")
    print(f"Speed: {progress.format_speed()}")
    print(f"ETA: {progress.format_time(progress.estimated_remaining)}")
    print(f"Current file: {progress.current_file}")
    print(f"Files: {progress.files_processed}/{progress.total_files}")
    
    # Send metrics to monitoring system
    metrics.gauge('compression.progress', progress.percentage)
    metrics.gauge('compression.speed_mbps', progress.speed_bps / 1024 / 1024)

# Use structured progress callback
py7zz.create_archive(
    'data.7z',
    ['large_dataset/'],
    progress_callback=progress_callback
)
```

#### `ProgressTracker`

Manual progress tracking helper for custom operations.

**Parameters:**
- `operation_type` (OperationType): Type of operation being tracked
- `callback` (ProgressCallback, optional): Callback function for progress updates
- `total_bytes` (int, optional): Total bytes to process
- `total_files` (int, optional): Total files to process
- `update_interval` (float): Minimum interval between callbacks (default: 0.1s)

**Example:**
```python
import py7zz

def custom_progress_callback(progress: py7zz.ProgressInfo):
    print(f"Custom operation: {progress.percentage:.1f}%")

# Manual progress tracking
tracker = py7zz.ProgressTracker(
    operation_type=py7zz.OperationType.COMPRESS,
    callback=custom_progress_callback,
    total_bytes=1000000,
    total_files=10
)

# Update progress manually
tracker.update(bytes_processed=250000, current_file="file1.txt")
tracker.update(bytes_processed=500000, current_file="file2.txt")
tracker.complete()  # Mark as completed
```

**Methods:**
- `update(**kwargs)`: Update progress state
- `set_stage(stage)`: Set operation stage
- `complete()`: Mark operation as completed
- `fail(error_message=None)`: Mark operation as failed

#### Predefined Callback Functions

**`console_progress_callback(progress)`**

Simple console progress display.

**`detailed_console_callback(progress)`**

Detailed console progress with comprehensive information.

**`json_progress_callback(progress)`**

JSON-formatted progress output for logging/analysis.

**`create_callback(callback_type, **options)`**

Factory function for creating callbacks.

**Parameters:**
- `callback_type` (str): Type of callback ('console', 'detailed', 'json')
- `**options`: Additional options for callback configuration

**Example:**
```python
import py7zz

# Use predefined callbacks
py7zz.create_archive('data.7z', ['files/'], 
                    progress_callback=py7zz.console_progress_callback)

# Or use factory function
detailed_callback = py7zz.create_callback("detailed")
py7zz.create_archive('logs.7z', ['logs/'], progress_callback=detailed_callback)

# JSON callback for structured logging
json_callback = py7zz.create_callback("json")
py7zz.create_archive('metrics.7z', ['metrics/'], progress_callback=json_callback)
```

### Logging Integration

#### `setup_logging(level, **options)`

Configure py7zz logging features.

**Parameters:**
- `level` (str): Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
- `enable_filename_warnings` (bool): Show filename compatibility warnings
- `console_output` (bool): Enable console logging
- `log_file` (str, optional): Path for log file output
- `max_file_size` (int): Maximum log file size before rotation
- `backup_count` (int): Number of backup log files to keep
- `structured` (bool): Use structured JSON logging
- `performance_monitoring` (bool): Enable performance logging

**Example:**
```python
import py7zz

# Basic logging setup
py7zz.setup_logging("INFO")

# Enterprise logging with all features
py7zz.setup_logging(
    "INFO",
    structured=True,              # JSON structured logs
    performance_monitoring=True,  # Performance metrics
    log_file="py7zz.log",        # File logging with rotation
    max_file_size=50*1024*1024,  # 50MB max file size
    backup_count=5               # Keep 5 backup files
)
```

#### `get_logger(name)`

Get a logger integrated with py7zz's logging hierarchy.

**Parameters:**
- `name` (str): Logger name (typically `__name__`)

**Returns:** logging.Logger object

**Example:**
```python
import logging
import py7zz

# Standard Python logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# py7zz integrates with your logging hierarchy
logger = py7zz.logging_config.get_logger(__name__)
logger.info("Starting archive processing")

# py7zz operations will use your logging configuration
py7zz.create_archive('data.7z', ['files/'])
```

#### Performance Monitoring

**`PerformanceLogger(operation)`**

Context manager for automatic performance logging.

**Parameters:**
- `operation` (str): Description of the operation being monitored

**Example:**
```python
import py7zz

# Automatic performance monitoring
with py7zz.PerformanceLogger("bulk_compression"):
    py7zz.batch_create_archives([
        ('backup1.7z', ['data1/']),
        ('backup2.7z', ['data2/']),
        ('backup3.7z', ['data3/'])
    ])

# Performance metrics automatically logged:
# - Operation start/end times
# - Duration
# - Success/failure status
# - Exception details (if any)
```

**`log_performance(operation)`**

Decorator for automatic performance logging.

**Example:**
```python
import py7zz

@py7zz.log_performance("custom_archive_operation")
def create_custom_archive(source_dir, output_path):
    # Your custom archive creation logic
    py7zz.create_archive(output_path, [source_dir], preset='ultra')
    return output_path

# Function calls are automatically timed and logged
result = create_custom_archive('data/', 'output.7z')
```

#### Logging Control Functions

**`enable_debug_logging()`**

Enable debug logging for troubleshooting.

**`disable_warnings()`**

Disable filename compatibility warnings.

**`enable_file_logging(log_file, **options)`**

Enable file logging with current configuration.

**`enable_structured_logging(enable=True)`**

Enable or disable structured JSON logging.

**`enable_performance_monitoring(enable=True)`**

Enable or disable performance monitoring.

**`set_log_level(level)`**

Change logging level for all py7zz loggers.

**`get_log_statistics()`**

Get comprehensive logging statistics and information.

**Example:**
```python
import py7zz

# Configure logging for different environments
if production_environment:
    py7zz.setup_logging(
        "WARNING",
        log_file="/var/log/py7zz.log",
        structured=True,
        performance_monitoring=True
    )
else:
    py7zz.enable_debug_logging()

# Dynamic logging control
py7zz.set_log_level("DEBUG")  # Increase verbosity for debugging
py7zz.disable_warnings()      # Reduce noise in production

# Get logging statistics
stats = py7zz.get_log_statistics()
print(f"Active handlers: {stats['active_handlers']}")
print(f"Log level: {stats['config']['level']}")
```

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

### Global Configuration Management

py7zz 1.0+ provides powerful global configuration management for user preferences and intelligent preset recommendations.

#### `GlobalConfig`

Manages persistent user configuration across all py7zz operations.

##### `GlobalConfig.set_default_preset(preset)`

Set the default compression preset for all operations.

**Parameters:**
- `preset` (str): Default preset name ('fast', 'balanced', 'backup', 'ultra')

**Example:**
```python
import py7zz

# Set ultra compression as default for all operations
py7zz.GlobalConfig.set_default_preset('ultra')

# Now all operations use ultra preset by default
py7zz.create_archive('backup.7z', ['data/'])  # Uses 'ultra' preset
```

##### `GlobalConfig.get_default_preset()`

Get the current default preset.

**Returns:** str - Current default preset name

##### `GlobalConfig.load_user_config(config_path=None)`

Load user configuration from file.

**Parameters:**
- `config_path` (Optional[str]): Custom config file path (uses default if None)

##### `GlobalConfig.save_user_config(config_path=None)`

Save current configuration to file.

**Parameters:**
- `config_path` (Optional[str]): Custom config file path (uses default if None)

##### `GlobalConfig.get_smart_recommendation(file_paths, usage_type=None, priority="balanced")`

Get intelligent preset recommendation based on file analysis.

**Parameters:**
- `file_paths` (List[str]): Files to analyze for optimal preset
- `usage_type` (Optional[str]): Usage context ('backup', 'distribution', 'storage')
- `priority` (str): Optimization priority ('speed', 'balanced', 'compression')

**Returns:** str - Recommended preset name

**Example:**
```python
# Get smart recommendation based on file content
files = ['documents/', 'images/', 'videos/']
recommended = py7zz.GlobalConfig.get_smart_recommendation(
    files, 
    usage_type='backup',
    priority='compression'
)
print(f"Recommended preset: {recommended}")

# Create archive with recommended settings
py7zz.create_archive('smart_backup.7z', files, preset=recommended)
```

#### `PresetRecommender`

Advanced preset recommendation system with content analysis.

##### `PresetRecommender.analyze_content(file_paths)`

Analyze file content to determine optimal compression strategy.

**Parameters:**
- `file_paths` (List[str]): Files and directories to analyze

**Returns:** Dict[str, Any] - Detailed analysis results

**Example:**
```python
analysis = py7zz.PresetRecommender.analyze_content(['project/'])
print(f"File types found: {analysis['file_types']}")
print(f"Total size: {analysis['total_size']}")
print(f"Compressibility: {analysis['compressibility_score']}")
```

##### `PresetRecommender.recommend_for_content(file_paths)`

Get preset recommendation based on content analysis.

**Parameters:**
- `file_paths` (List[str]): Files to analyze

**Returns:** str - Recommended preset name

**Example:**
```python
# Analyze mixed content and get recommendation
files = ['source_code/', 'media/', 'documents/']
preset = py7zz.PresetRecommender.recommend_for_content(files)
print(f"Optimal preset for content: {preset}")
```

##### `PresetRecommender.recommend_for_usage(usage_type)`

Get preset recommendation based on intended usage.

**Parameters:**
- `usage_type` (str): Usage context ('backup', 'distribution', 'storage', 'temporary')

**Returns:** str - Recommended preset name

**Example:**
```python
# Get preset for different use cases
backup_preset = py7zz.PresetRecommender.recommend_for_usage('backup')
storage_preset = py7zz.PresetRecommender.recommend_for_usage('storage')
temp_preset = py7zz.PresetRecommender.recommend_for_usage('temporary')

print(f"Backup: {backup_preset}, Storage: {storage_preset}, Temp: {temp_preset}")
```

### Advanced Configuration Examples

#### Smart Preset Selection

```python
import py7zz

def smart_archive_creation(files, archive_path):
    """Create archive with intelligent preset selection."""
    
    # Analyze content for optimal settings
    analysis = py7zz.PresetRecommender.analyze_content(files)
    
    # Get recommendation based on content and usage
    if analysis['total_size'] > 1024 * 1024 * 1024:  # > 1GB
        # Large files - prioritize speed
        preset = py7zz.GlobalConfig.get_smart_recommendation(
            files, usage_type='backup', priority='speed'
        )
    else:
        # Smaller files - prioritize compression
        preset = py7zz.GlobalConfig.get_smart_recommendation(
            files, usage_type='storage', priority='compression'
        )
    
    print(f"Using preset '{preset}' based on content analysis")
    py7zz.create_archive(archive_path, files, preset=preset)

# Usage
smart_archive_creation(['project/'], 'intelligent_backup.7z')
```

#### User Preference Management

```python
import py7zz

def setup_user_preferences():
    """Configure py7zz according to user preferences."""
    
    # Set default preset for all operations
    py7zz.GlobalConfig.set_default_preset('balanced')
    
    # Save preferences for future sessions
    py7zz.GlobalConfig.save_user_config()
    
    print("User preferences saved!")

def create_archives_with_preferences():
    """Create archives using saved user preferences."""
    
    # Load saved preferences
    py7zz.GlobalConfig.load_user_config()
    
    # All operations now use saved default preset
    py7zz.create_archive('backup1.7z', ['docs/'])      # Uses saved default
    py7zz.create_archive('backup2.7z', ['photos/'])    # Uses saved default
    
    # Override for specific operations
    py7zz.create_archive('quick.7z', ['temp/'], preset='fast')  # Override

# Setup and usage
setup_user_preferences()
create_archives_with_preferences()
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

py7zz 1.0+ provides a unified exception handling system with enhanced error context, actionable suggestions, and decorator-based error handling.

### Enhanced Exception Hierarchy

```
Py7zzError (enhanced base exception)
├── ValidationError (input validation failures)
├── OperationError (execution failures)
├── CompatibilityError (platform/format compatibility issues)
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

### Enhanced Base Exception

#### `Py7zzError`

Enhanced base exception with context tracking, error classification, and actionable suggestions.

**New Features:**
- **Context tracking**: Detailed error context information
- **Actionable suggestions**: Specific steps to resolve the error
- **Error classification**: Automatic error type classification
- **Chain preservation**: Complete error chain with `raise ... from` support

**Methods:**
- `get_detailed_info()` - Get comprehensive error information
- `add_context(key, value)` - Add context information
- `add_suggestion(suggestion)` - Add resolution suggestion

**Example:**
```python
try:
    py7zz.create_archive('backup.7z', ['nonexistent/'])
except py7zz.Py7zzError as e:
    # Get detailed error information
    info = e.get_detailed_info()
    print(f"Error type: {info['error_type']}")
    print(f"Message: {info['message']}")
    print(f"Context: {info['context']}")
    print("Suggestions:")
    for suggestion in info['suggestions']:
        print(f"  - {suggestion}")
```

### New Enhanced Exception Classes

#### `ValidationError`

Raised when input validation fails with parameter-specific context.

**Attributes:**
- Inherits all `Py7zzError` features
- Automatically tracks problematic parameter information

**Example:**
```python
try:
    py7zz.create_archive('', [])  # Invalid parameters
except py7zz.ValidationError as e:
    print(f"Validation failed: {e}")
    # Get suggestions for fixing the input
    suggestions = py7zz.get_error_suggestions(e)
    for suggestion in suggestions:
        print(f"Try: {suggestion}")
```

#### `OperationError`

Raised when operations fail during execution with operation-specific context.

**Attributes:**
- Inherits all `Py7zzError` features  
- Automatically tracks operation context and error codes

**Example:**
```python
try:
    py7zz.extract_archive('corrupted.7z', 'output/')
except py7zz.OperationError as e:
    print(f"Operation failed: {e}")
    if hasattr(e, 'error_code'):
        print(f"Exit code: {e.error_code}")
    
    # Operation-specific suggestions
    info = e.get_detailed_info()
    print("Context:", info['context'])
```

#### `CompatibilityError`

Raised when compatibility issues are encountered with platform-specific context.

**Attributes:**
- Inherits all `Py7zzError` features
- Automatically tracks platform and compatibility information

### Error Handling Utilities

#### `classify_error_type(error)`

Classify error type for logging and debugging.

**Parameters:**
- `error` (Exception): Error to classify

**Returns:** str - Error classification ('validation', 'operation', 'compatibility', 'py7zz', 'system')

#### `get_error_suggestions(error)`

Get actionable suggestions for resolving the error.

**Parameters:**
- `error` (Exception): Error to analyze

**Returns:** List[str] - List of actionable suggestions

**Example:**
```python
try:
    py7zz.extract_archive('missing.7z', 'output/')
except Exception as e:
    error_type = py7zz.classify_error_type(e)
    suggestions = py7zz.get_error_suggestions(e)
    
    print(f"Error type: {error_type}")
    print("Suggestions:")
    for suggestion in suggestions:
        print(f"  - {suggestion}")
```

### Decorator-Based Error Handling

py7zz provides decorators for consistent error handling across different operation types:

#### `@handle_7z_errors`

Decorator for handling 7zz subprocess errors uniformly.

#### `@handle_file_errors` 

Decorator for handling file system errors uniformly.

#### `@handle_validation_errors`

Decorator for handling input validation errors uniformly.

**Example Custom Function:**
```python
import py7zz

@py7zz.handle_file_errors
@py7zz.handle_validation_errors
def custom_archive_operation(archive_path, files):
    """Custom function with unified error handling."""
    if not archive_path:
        raise ValueError("Archive path cannot be empty")
    
    # Function implementation...
    py7zz.create_archive(archive_path, files)

# Usage with automatic error transformation
try:
    custom_archive_operation('', ['files/'])
except py7zz.ValidationError as e:
    print(f"Input validation failed: {e}")
    # Automatically gets actionable suggestions
```

### Comprehensive Error Handling Example

```python
import py7zz

def robust_archive_operations():
    """Demonstrate comprehensive error handling."""
    
    try:
        # Create archive with potential issues
        py7zz.create_archive('backup.7z', ['sensitive_files/'])
        
    except py7zz.ValidationError as e:
        print(f"Input validation error: {e}")
        # Get detailed context about what parameter failed
        context = e.get_detailed_info()['context']
        if 'parameter' in context:
            print(f"Problem with parameter: {context['parameter']}")
            
    except py7zz.OperationError as e:
        print(f"Operation failed: {e}")
        # Check for specific error codes
        if hasattr(e, 'error_code') and e.error_code == 2:
            print("This might be a permission issue")
            
    except py7zz.CompatibilityError as e:
        print(f"Compatibility issue: {e}")
        # Get platform-specific suggestions
        suggestions = e.get_detailed_info()['suggestions']
        for suggestion in suggestions:
            print(f"Platform fix: {suggestion}")
            
    except py7zz.FilenameCompatibilityError as e:
        print(f"Filename issues: {len(e.problematic_files)} files")
        if e.sanitized:
            print("Files were automatically renamed for Windows compatibility")
        else:
            print("Could not resolve all filename issues")
            
    except py7zz.Py7zzError as e:
        # Generic handler with full error analysis
        error_info = e.get_detailed_info()
        print(f"General py7zz error: {error_info['error_type']}")
        print(f"Message: {error_info['message']}")
        
        if error_info['context']:
            print("Context:", error_info['context'])
            
        if error_info['suggestions']:
            print("Suggestions:")
            for suggestion in error_info['suggestions']:
                print(f"  - {suggestion}")

# Run with comprehensive error handling
robust_archive_operations()
```

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

#### Advanced Progress Display with Rich Output

```python
import time
from pathlib import Path

def detailed_progress_handler(info):
    """Rich progress display with file size information."""
    print(f"\r[{info.operation.upper()}] ", end="")
    
    # Progress bar
    bar_width = 30
    filled = int(bar_width * info.percentage / 100)
    bar = "█" * filled + "░" * (bar_width - filled)
    print(f"[{bar}] {info.percentage:6.1f}%", end="")
    
    # File information
    if info.current_file:
        filename = Path(info.current_file).name
        if len(filename) > 25:
            filename = filename[:22] + "..."
        print(f" | {filename:25}", end="")
    
    # Statistics
    if info.total_files > 0:
        print(f" | Files: {info.files_processed:4}/{info.total_files:<4}", end="")
    
    if info.total_bytes > 0:
        processed_mb = info.bytes_processed / (1024 * 1024)
        total_mb = info.total_bytes / (1024 * 1024)
        print(f" | Size: {processed_mb:6.1f}/{total_mb:6.1f} MB", end="")
    
    print("", flush=True)

# Usage with different operations
py7zz.create_archive('backup.7z', ['data/'], progress_callback=detailed_progress_handler)
print()  # New line after completion
```

#### Progress Display with Time Estimation

```python
import time

class ProgressTracker:
    def __init__(self):
        self.start_time = time.time()
        self.last_percentage = 0
    
    def __call__(self, info):
        """Progress callback with time estimation."""
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        if info.percentage > 0:
            estimated_total = elapsed * 100 / info.percentage
            remaining = estimated_total - elapsed
            
            print(f"\r{info.operation}: {info.percentage:5.1f}% "
                  f"| Elapsed: {elapsed:6.1f}s "
                  f"| ETA: {remaining:6.1f}s "
                  f"| {info.current_file}", end="", flush=True)

# Usage
tracker = ProgressTracker()
py7zz.create_archive('large_backup.7z', ['large_data/'], progress_callback=tracker)
print()  # New line after completion
```

#### GUI Progress Integration (tkinter example)

```python
import tkinter as tk
from tkinter import ttk
import threading

class ArchiveProgressWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Archive Progress")
        self.root.geometry("500x200")
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.root, variable=self.progress_var, maximum=100
        )
        self.progress_bar.pack(fill="x", padx=20, pady=10)
        
        # Status labels
        self.status_label = tk.Label(self.root, text="Ready...")
        self.status_label.pack(pady=5)
        
        self.file_label = tk.Label(self.root, text="")
        self.file_label.pack(pady=5)
        
        self.stats_label = tk.Label(self.root, text="")
        self.stats_label.pack(pady=5)
    
    def progress_callback(self, info):
        """Thread-safe progress callback for GUI."""
        self.root.after(0, self._update_gui, info)
    
    def _update_gui(self, info):
        """Update GUI elements (must be called from main thread)."""
        self.progress_var.set(info.percentage)
        self.status_label.config(text=f"Operation: {info.operation.title()}")
        
        if info.current_file:
            filename = info.current_file
            if len(filename) > 50:
                filename = "..." + filename[-47:]
            self.file_label.config(text=f"Processing: {filename}")
        
        stats = f"Files: {info.files_processed}/{info.total_files}"
        if info.total_bytes > 0:
            stats += f" | Size: {info.bytes_processed/(1024*1024):.1f}/" \
                     f"{info.total_bytes/(1024*1024):.1f} MB"
        self.stats_label.config(text=stats)
        
        # Close window when complete
        if info.percentage >= 100:
            self.root.after(2000, self.root.destroy)
    
    def show(self):
        self.root.mainloop()

# Usage in separate thread
def create_archive_with_gui():
    progress_window = ArchiveProgressWindow()
    
    def archive_task():
        try:
            py7zz.create_archive(
                'backup.7z',
                ['data/'],
                progress_callback=progress_window.progress_callback
            )
        except Exception as e:
            progress_window.root.after(0, lambda: print(f"Error: {e}"))
    
    # Start archive creation in background thread
    threading.Thread(target=archive_task, daemon=True).start()
    
    # Show progress window in main thread
    progress_window.show()
```

#### Async Progress Display

```python
import asyncio

async def async_progress_handler(info):
    """Async progress handler with potential I/O operations."""
    # Can perform async operations here
    await asyncio.sleep(0)  # Yield control
    
    # Could write to async log file, send to server, etc.
    print(f"Async progress: {info.percentage:.1f}% - {info.current_file}")
    
    # Example: Write progress to async log
    # async with aiofiles.open('progress.log', 'a') as f:
    #     await f.write(f"{time.time()}: {info.percentage:.1f}%\n")

async def main():
    await py7zz.create_archive_async(
        'backup.7z',
        ['data/'],
        progress_callback=async_progress_handler
    )

asyncio.run(main())
```

#### Progress Logging to File

```python
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    filename='archive_progress.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def logging_progress_handler(info):
    """Log progress to file with timestamps."""
    message = (
        f"{info.operation}: {info.percentage:.1f}% "
        f"- File: {info.current_file} "
        f"- Progress: {info.files_processed}/{info.total_files}"
    )
    
    logging.info(message)
    
    # Also print to console
    print(f"\r{message}", end="", flush=True)

# Usage
py7zz.create_archive(
    'important_backup.7z',
    ['critical_data/'],
    progress_callback=logging_progress_handler
)
print()  # New line after completion
```

#### Batch Operation Progress Tracking

```python
import asyncio
from collections import defaultdict

class BatchProgressTracker:
    def __init__(self, total_operations):
        self.total_operations = total_operations
        self.completed_operations = 0
        self.operation_progress = defaultdict(float)
    
    def create_callback(self, operation_id):
        """Create a progress callback for a specific operation."""
        def callback(info):
            self.operation_progress[operation_id] = info.percentage
            
            # Calculate overall progress
            overall_progress = sum(self.operation_progress.values())
            overall_progress += self.completed_operations * 100
            overall_progress /= self.total_operations
            
            print(f"\rBatch Progress: {overall_progress:.1f}% "
                  f"| Operation {operation_id}: {info.percentage:.1f}% "
                  f"| File: {info.current_file}", end="", flush=True)
            
            # Mark operation as completed
            if info.percentage >= 100:
                self.completed_operations += 1
                if operation_id in self.operation_progress:
                    del self.operation_progress[operation_id]
        
        return callback

async def batch_with_progress():
    operations = [
        ('backup1.7z', ['folder1/']),
        ('backup2.7z', ['folder2/']),
        ('backup3.7z', ['folder3/'])
    ]
    
    tracker = BatchProgressTracker(len(operations))
    
    # Create tasks with individual progress tracking
    tasks = []
    for i, (archive_path, files) in enumerate(operations):
        callback = tracker.create_callback(i)
        task = py7zz.create_archive_async(
            archive_path, files, progress_callback=callback
        )
        tasks.append(task)
    
    # Execute all operations concurrently
    await asyncio.gather(*tasks)
    print("\nAll batch operations completed!")

asyncio.run(batch_with_progress())
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
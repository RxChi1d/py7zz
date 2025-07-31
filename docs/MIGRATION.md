# Migration Guide

This guide helps you migrate from Python's `zipfile` and `tarfile` to py7zz.

## Table of Contents

- [Quick Start](#quick-start)
- [API Compatibility](#api-compatibility)
- [Code Examples](#code-examples)
- [Advanced Features](#advanced-features)
- [Windows Compatibility](#windows-compatibility)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Installation

```bash
pip install py7zz
```

### Basic Migration

| Task | zipfile/tarfile | py7zz |
|------|----------------|-------|
| Import | `import zipfile` | `import py7zz` |
| Open archive | `zipfile.ZipFile()` | `py7zz.SevenZipFile()` |
| Extract all | `.extractall()` | `.extractall()` |
| List files | `.namelist()` | `.namelist()` |
| Read file | `.read()` | `.read()` |

## API Compatibility

py7zz provides complete compatibility with both `zipfile` and `tarfile` APIs.

### Supported Methods

#### zipfile.ZipFile Methods

| Method | Supported | Notes |
|--------|-----------|-------|
| `namelist()` | ✅ | Returns list of filenames |
| `infolist()` | ✅ | Returns list of ArchiveInfo objects |
| `getinfo(name)` | ✅ | Gets info for specific file |
| `read(name)` | ✅ | Reads file content |
| `extract(member, path)` | ✅ | Extracts single file |
| `extractall(path, members)` | ✅ | Extracts all or specific files |
| `writestr(name, data)` | ✅ | Writes string/bytes to archive |
| `write(filename, arcname)` | ✅ | Use `add(filename, arcname)` |
| `testzip()` | ✅ | Tests archive integrity |
| `close()` | ✅ | Closes archive |

#### tarfile.TarFile Methods

| Method | Supported | Notes |
|--------|-----------|-------|
| `getnames()` | ✅ | Returns list of filenames |
| `getmembers()` | ✅ | Returns list of ArchiveInfo objects |
| `getmember(name)` | ✅ | Gets info for specific file |
| `extractall(path)` | ✅ | Extracts all files |
| `extract(member, path)` | ✅ | Extracts single file |
| `add(name, arcname)` | ✅ | Adds file to archive |

## Code Examples

### Creating Archives

#### From zipfile

```python
# OLD
import zipfile

with zipfile.ZipFile('archive.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.write('file.txt')
    zf.write('folder/')
```

#### To py7zz

```python
# NEW
import py7zz

with py7zz.SevenZipFile('archive.7z', 'w') as sz:
    sz.add('file.txt')
    sz.add('folder/')

# Or simpler:
py7zz.create_archive('archive.7z', ['file.txt', 'folder/'])
```

### Extracting Archives

#### From zipfile

```python
# OLD
import zipfile

with zipfile.ZipFile('archive.zip', 'r') as zf:
    # Extract all
    zf.extractall('output/')
    
    # Extract specific files
    zf.extractall('output/', members=['file1.txt', 'file2.txt'])
```

#### To py7zz

```python
# NEW
import py7zz

with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    # Extract all (identical!)
    sz.extractall('output/')
    
    # Extract specific files (identical!)
    sz.extractall('output/', members=['file1.txt', 'file2.txt'])

# Or simpler:
py7zz.extract_archive('archive.7z', 'output/')
```

### Reading Files

#### From zipfile

```python
# OLD
import zipfile

with zipfile.ZipFile('archive.zip', 'r') as zf:
    # List files
    files = zf.namelist()
    
    # Read file content
    content = zf.read('data.txt')
    
    # Get file info
    info = zf.getinfo('data.txt')
    print(f"Size: {info.file_size}")
    print(f"Compressed: {info.compress_size}")
```

#### To py7zz

```python
# NEW
import py7zz

with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    # List files (identical!)
    files = sz.namelist()
    
    # Read file content (identical!)
    content = sz.read('data.txt')
    
    # Get file info (identical + more!)
    info = sz.getinfo('data.txt')
    print(f"Size: {info.file_size}")
    print(f"Compressed: {info.compress_size}")
    print(f"Method: {info.method}")  # Additional info
```

### Writing Data

#### From zipfile

```python
# OLD
import zipfile

with zipfile.ZipFile('archive.zip', 'w') as zf:
    # Add file with custom name
    zf.write('document.txt', arcname='docs/readme.txt')
    
    # Write string data
    zf.writestr('config.ini', '[settings]\nkey=value')
```

#### To py7zz

```python
# NEW
import py7zz

with py7zz.SevenZipFile('archive.7z', 'w') as sz:
    # Add file with custom name (note: method is 'add')
    sz.add('document.txt', arcname='docs/readme.txt')
    
    # Write string data (identical!)
    sz.writestr('config.ini', '[settings]\nkey=value')
```

### Testing Archives

#### From zipfile

```python
# OLD
import zipfile

with zipfile.ZipFile('archive.zip', 'r') as zf:
    bad_file = zf.testzip()
    if bad_file:
        print(f"Corrupted: {bad_file}")
    else:
        print("Archive OK")
```

#### To py7zz

```python
# NEW
import py7zz

with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    bad_file = sz.testzip()  # Identical!
    if bad_file:
        print(f"Corrupted: {bad_file}")
    else:
        print("Archive OK")

# Or simpler:
if py7zz.test_archive('archive.7z'):
    print("Archive OK")
```

## Advanced Features

### Async Operations

py7zz provides async support for better performance:

```python
import asyncio
import py7zz

async def process_archives():
    # Create archive asynchronously
    await py7zz.create_archive_async('backup.7z', ['data/'])
    
    # Extract with progress
    async def progress(info):
        print(f"Progress: {info.percentage:.1f}%")
    
    await py7zz.extract_archive_async(
        'backup.7z', 
        'output/',
        progress_callback=progress
    )

asyncio.run(process_archives())
```

### Compression Presets

py7zz offers optimized compression presets:

```python
# Fast compression
py7zz.create_archive('quick.7z', ['data/'], preset='fast')

# Balanced (default)
py7zz.create_archive('normal.7z', ['data/'], preset='balanced')

# Maximum compression
py7zz.create_archive('small.7z', ['data/'], preset='ultra')
```

### Batch Operations

Process multiple archives efficiently:

```python
# Extract multiple archives
archives = ['backup1.7z', 'backup2.zip', 'backup3.tar.gz']
py7zz.batch_extract_archives(archives, 'output/')

# Create multiple archives
operations = [
    ('docs.7z', ['documents/']),
    ('images.7z', ['photos/']),
    ('code.7z', ['src/'])
]
py7zz.batch_create_archives(operations)
```

### Format Support

py7zz supports many more formats than zipfile/tarfile:

```python
# All these work with the same API
formats = ['archive.7z', 'data.zip', 'backup.tar.gz', 'files.rar']

for archive in formats:
    with py7zz.SevenZipFile(archive, 'r') as sz:
        print(f"{archive}: {len(sz.namelist())} files")
```

## Windows Compatibility

### The Problem

Archives created on Unix/Linux often contain filenames that are invalid on Windows:

```python
# These filenames fail on Windows with zipfile/tarfile:
problematic_files = [
    'CON.txt',        # Reserved name
    'file:name.txt',  # Invalid character
    'data*.log',      # Invalid character
    'config ',        # Trailing space
]
```

### The Solution

py7zz automatically handles these issues:

```python
# Just works on Windows!
py7zz.extract_archive('unix-archive.tar.gz', 'output/')

# Automatic transformations:
# 'CON.txt' → 'CON_file.txt'
# 'file:name.txt' → 'file_name.txt'
# 'data*.log' → 'data_.log'
# 'config ' → 'config'
```

### Logging

Control how filename changes are reported:

```python
# Show warnings (default)
py7zz.setup_logging('INFO')

# Hide warnings
py7zz.disable_warnings()

# Show detailed info
py7zz.setup_logging('DEBUG')
```

## Error Handling

### Enhanced Exceptions

py7zz provides more detailed error information:

```python
import py7zz

try:
    py7zz.extract_archive('archive.7z', 'output/')
except py7zz.FileNotFoundError:
    print("Archive not found")
except py7zz.CorruptedArchiveError:
    print("Archive is corrupted")
except py7zz.PasswordRequiredError:
    print("Archive requires password")
except py7zz.FilenameCompatibilityError as e:
    print(f"Renamed {len(e.problematic_files)} files for Windows")
```

### Error Suggestions

Get helpful suggestions for common errors:

```python
try:
    py7zz.create_archive('backup.7z', ['nonexistent/'])
except py7zz.Py7zzError as e:
    print(f"Error: {e}")
    for suggestion in py7zz.get_error_suggestions(e):
        print(f"Try: {suggestion}")
```

## Troubleshooting

### Common Issues

#### "No module named 'py7zz'"
```bash
pip install py7zz
```

#### "7zz binary not found"
```bash
# Reinstall py7zz
pip install --force-reinstall py7zz
```

#### "Archive format not supported"
```python
# Check supported formats
print(py7zz.get_version_info())
```

### Migration Checklist

- [ ] Install py7zz: `pip install py7zz`
- [ ] Replace imports: `import py7zz`
- [ ] Update class names: `SevenZipFile`
- [ ] Change `write()` to `add()` for adding files
- [ ] Test on target platforms
- [ ] Consider using simple functions for basic operations
- [ ] Add async support where beneficial

### Performance Tips

1. **Use appropriate presets**
   ```python
   # For temporary files
   preset='fast'
   
   # For archival storage
   preset='ultra'
   ```

2. **Use async for large files**
   ```python
   await py7zz.extract_archive_async('large.7z')
   ```

3. **Batch operations when possible**
   ```python
   py7zz.batch_extract_archives(archives, 'output/')
   ```

## Getting Help

- [API Documentation](API.md)
- [GitHub Issues](https://github.com/rxchi1d/py7zz/issues)
- [GitHub Discussions](https://github.com/rxchi1d/py7zz/discussions)

## Summary

py7zz provides:
- ✅ Complete API compatibility
- ✅ Support for 50+ formats
- ✅ Automatic Windows compatibility
- ✅ Better error handling
- ✅ Async operations
- ✅ Simple one-line functions

Migration is typically as simple as changing the import and class name!
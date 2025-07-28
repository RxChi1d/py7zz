# Migration Guide: From zipfile/tarfile to py7zz

This guide helps you migrate from Python's standard library `zipfile` and `tarfile` modules to py7zz, which provides enhanced compression support for dozens of archive formats with a familiar interface and automatic Windows filename compatibility.

## Quick Start

### Installation
```bash
pip install py7zz
```

### Basic Usage Comparison

| Task | zipfile/tarfile | py7zz |
|------|----------------|-------|
| Create archive | `zipfile.ZipFile()` | `py7zz.SevenZipFile()` |
| Extract archive | `zf.extractall()` | `sz.extractall()` |
| List files | `zf.namelist()` | `sz.namelist()` |
| Read file | `zf.read()` | `sz.read()` |
| Add file | `zf.write()` | `sz.add()` |

## Industry Standard API Compatibility

py7zz 1.0+ provides complete compatibility with both `zipfile.ZipFile` and `tarfile.TarFile` APIs, making migration seamless.

### New Industry Standard Methods

py7zz now includes all standard archive library methods:

| Method | zipfile | tarfile | py7zz | Description |
|--------|---------|---------|-------|-------------|
| `namelist()` | ✅ | ❌ | ✅ | Get list of member names |
| `getnames()` | ❌ | ✅ | ✅ | Get list of member names (tarfile style) |
| `infolist()` | ✅ | ❌ | ✅ | Get detailed info for all members |
| `getmembers()` | ❌ | ✅ | ✅ | Get detailed info for all members (tarfile style) |
| `getinfo(name)` | ✅ | ❌ | ✅ | Get detailed info for specific member |
| `getmember(name)` | ❌ | ✅ | ✅ | Get detailed info for specific member (tarfile style) |
| `extractall(members=...)` | ✅ | ✅ | ✅ | Extract specific members only |
| `add(arcname=...)` | ✅ (write) | ❌ | ✅ | Add file with custom archive name |

### ArchiveInfo Class - Unified Archive Member Information

py7zz introduces the `ArchiveInfo` class, compatible with both `zipfile.ZipInfo` and `tarfile.TarInfo`:

```python
import py7zz

with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    # Get detailed information about archive members
    info = sz.getinfo('file.txt')
    
    # zipfile.ZipInfo compatible properties
    print(f"Filename: {info.filename}")
    print(f"File size: {info.file_size}")
    print(f"Compressed size: {info.compress_size}")
    print(f"CRC: {info.CRC:08X}")
    print(f"Date modified: {info.date_time}")
    
    # tarfile.TarInfo compatible properties
    print(f"Size: {info.size}")        # Same as file_size
    print(f"Mode: {oct(info.mode)}")   # File permissions
    print(f"Type: {info.type}")        # 'file', 'dir', 'link'
    print(f"UID: {info.uid}")          # User ID
    print(f"GID: {info.gid}")          # Group ID
    
    # Additional py7zz features
    print(f"Compression method: {info.method}")
    print(f"Compression ratio: {info.get_compression_ratio():.1%}")
    print(f"Is encrypted: {info.encrypted}")
```

## API Mapping

### 1. Creating Archives

#### zipfile
```python
import zipfile

# Create ZIP archive
with zipfile.ZipFile('archive.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.write('file.txt')
    zf.write('folder/', arcname='folder/')
```

#### tarfile
```python
import tarfile

# Create TAR archive
with tarfile.open('archive.tar.gz', 'w:gz') as tf:
    tf.add('file.txt')
    tf.add('folder/')
```

#### py7zz
```python
import py7zz

# Create 7z archive (or any supported format)
with py7zz.SevenZipFile('archive.7z', 'w') as sz:
    sz.add('file.txt')
    sz.add('folder/')

# Simple one-liner
py7zz.create_archive('archive.7z', ['file.txt', 'folder/'])
```

### 2. Extracting Archives

#### zipfile
```python
import zipfile

# Extract ZIP archive
with zipfile.ZipFile('archive.zip', 'r') as zf:
    zf.extractall('output_folder')
```

#### tarfile
```python
import tarfile

# Extract TAR archive
with tarfile.open('archive.tar.gz', 'r:gz') as tf:
    tf.extractall('output_folder')
```

#### py7zz
```python
import py7zz

# Extract archive (auto-detects format)
with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    sz.extractall('output_folder')

# Simple one-liner
py7zz.extract_archive('archive.7z', 'output_folder')
```

### 3. Listing Archive Contents

#### zipfile
```python
import zipfile

with zipfile.ZipFile('archive.zip', 'r') as zf:
    # Get basic file list
    file_list = zf.namelist()
    print(f"Archive contains {len(file_list)} files")
    
    # Get detailed information
    info_list = zf.infolist()
    for info in info_list:
        print(f"{info.filename}: {info.file_size} bytes")
```

#### tarfile
```python
import tarfile

with tarfile.open('archive.tar.gz', 'r:gz') as tf:
    # Get basic file list
    file_list = tf.getnames()
    print(f"Archive contains {len(file_list)} files")
    
    # Get detailed information
    members = tf.getmembers()
    for member in members:
        print(f"{member.name}: {member.size} bytes")
```

#### py7zz
```python
import py7zz

# Compatible with both zipfile and tarfile APIs
with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    # zipfile style
    file_list = sz.namelist()
    info_list = sz.infolist()
    
    # or tarfile style
    file_list = sz.getnames()
    members = sz.getmembers()
    
    print(f"Archive contains {len(file_list)} files")
    
    # Enhanced information available
    for info in info_list:
        print(f"{info.filename}: {info.file_size} bytes")
        print(f"  Compressed: {info.compress_size} bytes ({info.get_compression_ratio():.1%})")
        print(f"  Method: {info.method}")

# Simple one-liner (legacy)
file_list = py7zz.list_archive('archive.7z')
```

### 4. Reading Files from Archives

#### zipfile
```python
import zipfile

with zipfile.ZipFile('archive.zip', 'r') as zf:
    content = zf.read('file.txt')
    print(content.decode('utf-8'))
```

#### tarfile
```python
import tarfile

with tarfile.open('archive.tar.gz', 'r:gz') as tf:
    f = tf.extractfile('file.txt')
    content = f.read() if f else b''
    print(content.decode('utf-8'))
```

#### py7zz
```python
import py7zz

with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    content = sz.read('file.txt')
    print(content.decode('utf-8'))
```

### 5. Writing String Data to Archives

#### zipfile
```python
import zipfile

with zipfile.ZipFile('archive.zip', 'w') as zf:
    zf.writestr('config.txt', 'key=value\n')
```

#### tarfile
```python
import tarfile
import io

with tarfile.open('archive.tar.gz', 'w:gz') as tf:
    info = tarfile.TarInfo(name='config.txt')
    info.size = len(b'key=value\n')
    tf.addfile(info, io.BytesIO(b'key=value\n'))
```

#### py7zz
```python
import py7zz

with py7zz.SevenZipFile('archive.7z', 'w') as sz:
    sz.writestr('config.txt', 'key=value\n')
```

### 6. Testing Archive Integrity

#### zipfile
```python
import zipfile

with zipfile.ZipFile('archive.zip', 'r') as zf:
    bad_file = zf.testzip()
    if bad_file is None:
        print("Archive is OK")
    else:
        print(f"Corrupted file: {bad_file}")
```

#### tarfile
```python
import tarfile

try:
    with tarfile.open('archive.tar.gz', 'r:gz') as tf:
        tf.getnames()  # Will fail if corrupted
    print("Archive is OK")
except tarfile.TarError:
    print("Archive is corrupted")
```

#### py7zz
```python
import py7zz

# Compatible with zipfile API
with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    bad_file = sz.testzip()
    if bad_file is None:
        print("Archive is OK")
    else:
        print(f"Corrupted file: {bad_file}")

# Simple one-liner
if py7zz.test_archive('archive.7z'):
    print("Archive is OK")
else:
    print("Archive is corrupted")
```

## Advanced Features

### Compression Levels and Presets

#### zipfile
```python
import zipfile

# Limited compression options
with zipfile.ZipFile('archive.zip', 'w', 
                     compression=zipfile.ZIP_DEFLATED,
                     compresslevel=9) as zf:
    zf.write('file.txt')
```

#### py7zz
```python
import py7zz

# Use compression levels
with py7zz.SevenZipFile('archive.7z', 'w', level='ultra') as sz:
    sz.add('file.txt')

# Or use convenient presets
py7zz.create_archive('archive.7z', ['file.txt'], preset='ultra')

# Available presets: 'fast', 'balanced', 'backup', 'ultra'
# Available levels: 'store', 'fastest', 'fast', 'normal', 'maximum', 'ultra'
```

### Async Operations (py7zz exclusive)

```python
import py7zz
import asyncio

async def main():
    # Async archive creation with progress
    async def progress_handler(info):
        print(f"Progress: {info.percentage:.1f}% - {info.current_file}")
    
    await py7zz.create_archive_async(
        'large_archive.7z', 
        ['big_folder/'], 
        preset='balanced',
        progress_callback=progress_handler
    )
    
    # Async extraction
    await py7zz.extract_archive_async(
        'large_archive.7z', 
        'extracted/',
        progress_callback=progress_handler
    )

asyncio.run(main())
```

## Format Support Comparison

| Format | zipfile | tarfile | py7zz |
|--------|---------|---------|-------|
| ZIP | ✅ | ❌ | ✅ |
| TAR | ❌ | ✅ | ✅ |
| 7Z | ❌ | ❌ | ✅ |
| RAR | ❌ | ❌ | ✅ (extract only) |
| GZIP | ❌ | ✅ | ✅ |
| BZIP2 | ❌ | ✅ | ✅ |
| XZ | ❌ | ✅ | ✅ |
| LZ4 | ❌ | ❌ | ✅ |
| ZSTD | ❌ | ❌ | ✅ |
| And 50+ more | ❌ | ❌ | ✅ |

## Migration Checklist

### Step 1: Replace Imports
```python
# OLD
import zipfile
import tarfile

# NEW
import py7zz
```

### Step 2: Update Class Names
```python
# OLD
with zipfile.ZipFile('archive.zip', 'w') as zf:
    # ...

# NEW
with py7zz.SevenZipFile('archive.7z', 'w') as sz:
    # ...
```

### Step 3: Update Method Names
- `zf.write()` → `sz.add()`
- `tf.getnames()` → `sz.namelist()` (or keep `sz.getnames()`)
- `tf.extractall()` → `sz.extractall()` (same)
- `zf.read()` → `sz.read()` (same)

### Step 4: Consider Using Simple API
```python
# OLD - multiple lines
with zipfile.ZipFile('archive.zip', 'w') as zf:
    zf.write('file.txt')
    zf.write('folder/')

# NEW - one line
py7zz.create_archive('archive.7z', ['file.txt', 'folder/'])
```

## Complete Migration Examples

### Advanced zipfile Migration

#### Old zipfile Code
```python
import zipfile
import os

# Create archive with custom names
with zipfile.ZipFile('backup.zip', 'w') as zf:
    zf.write('config.txt', arcname='settings/config.txt')
    zf.write('data.json', arcname='backup/data.json')

# Extract specific files only
with zipfile.ZipFile('backup.zip', 'r') as zf:
    # Get information about specific files
    try:
        info = zf.getinfo('settings/config.txt')
        print(f"Config file size: {info.file_size}")
        print(f"Modified: {info.date_time}")
    except KeyError:
        print("Config file not found")
    
    # Extract only specific members
    zf.extractall('output/', members=['settings/config.txt', 'backup/data.json'])
    
    # Get all file information
    for info in zf.infolist():
        print(f"{info.filename}: {info.file_size} bytes, CRC: {info.CRC:08X}")
```

#### New py7zz Code (Identical API)
```python
import py7zz

# Create archive with custom names - IDENTICAL API
with py7zz.SevenZipFile('backup.7z', 'w') as sz:
    sz.add('config.txt', arcname='settings/config.txt')    # Same method!
    sz.add('data.json', arcname='backup/data.json')       # Same method!

# Extract specific files only - IDENTICAL API
with py7zz.SevenZipFile('backup.7z', 'r') as sz:
    # Get information about specific files - IDENTICAL API
    try:
        info = sz.getinfo('settings/config.txt')           # Same method!
        print(f"Config file size: {info.file_size}")       # Same property!
        print(f"Modified: {info.date_time}")               # Same property!
    except KeyError:
        print("Config file not found")
    
    # Extract only specific members - IDENTICAL API
    sz.extractall('output/', members=['settings/config.txt', 'backup/data.json'])
    
    # Get all file information - IDENTICAL API + Enhanced info
    for info in sz.infolist():                             # Same method!
        print(f"{info.filename}: {info.file_size} bytes, CRC: {info.CRC:08X}")
        # BONUS: Additional information available
        print(f"  Compression: {info.method}, Ratio: {info.get_compression_ratio():.1%}")
```

### Advanced tarfile Migration

#### Old tarfile Code
```python
import tarfile

# Create TAR archive
with tarfile.open('backup.tar.gz', 'w:gz') as tf:
    tf.add('src/', arcname='source')  # Custom name for directory

# Extract and analyze
with tarfile.open('backup.tar.gz', 'r:gz') as tf:
    # Get member information
    members = tf.getmembers()
    names = tf.getnames()
    
    print(f"Archive contains {len(names)} items")
    
    # Analyze each member
    for member in members:
        print(f"{member.name} ({member.type})")
        if member.isfile():
            print(f"  Size: {member.size} bytes")
            print(f"  Mode: {oct(member.mode)}")
            print(f"  UID/GID: {member.uid}/{member.gid}")
    
    # Get specific member
    try:
        member = tf.getmember('source/main.py')
        print(f"Found main.py: {member.size} bytes")
    except KeyError:
        print("main.py not found")
```

#### New py7zz Code (Compatible API)
```python
import py7zz

# Create archive - Enhanced but compatible
with py7zz.SevenZipFile('backup.7z', 'w') as sz:
    sz.add('src/', arcname='source')                       # Same as tarfile!

# Extract and analyze - Compatible API + enhancements
with py7zz.SevenZipFile('backup.7z', 'r') as sz:
    # Get member information - SAME METHODS
    members = sz.getmembers()                              # Same method!
    names = sz.getnames()                                  # Same method!
    
    print(f"Archive contains {len(names)} items")
    
    # Analyze each member - Enhanced compatibility
    for member in members:
        print(f"{member.filename} ({member.type})")        # filename works like name
        if member.isfile():                                # Same method!
            print(f"  Size: {member.size} bytes")          # size property available
            if hasattr(member, 'mode'):
                print(f"  Mode: {oct(member.mode)}")       # Same property!
            if hasattr(member, 'uid'):
                print(f"  UID/GID: {member.uid}/{member.gid}")  # Same properties!
        
        # BONUS: Additional 7z-specific information
        print(f"  Compression: {member.method}")
        print(f"  Ratio: {member.get_compression_ratio():.1%}")
    
    # Get specific member - SAME METHOD
    try:
        member = sz.getmember('source/main.py')            # Same method!
        print(f"Found main.py: {member.size} bytes")       # Same property!
    except KeyError:
        print("main.py not found")
```

### Async Migration for Large Operations

#### Old synchronous code
```python
import zipfile
import os
import time

def process_large_archives():
    start_time = time.time()
    
    # Process multiple archives sequentially
    for i in range(5):
        archive_name = f'large_archive_{i}.zip'
        with zipfile.ZipFile(archive_name, 'w') as zf:
            # Add large directory (blocks main thread)
            for root, dirs, files in os.walk('large_data/'):
                for file in files:
                    file_path = os.path.join(root, file)
                    zf.write(file_path)
        
        print(f"Created {archive_name}")
    
    print(f"Total time: {time.time() - start_time:.1f}s")
```

#### New async py7zz code
```python
import py7zz
import asyncio
import time

async def process_large_archives():
    start_time = time.time()
    
    # Progress callback for user feedback
    async def progress_callback(info):
        print(f"\r{info.operation}: {info.percentage:.1f}% - {info.current_file}", end='')
    
    # Process multiple archives concurrently
    tasks = []
    for i in range(5):
        archive_name = f'large_archive_{i}.7z'
        task = py7zz.create_archive_async(
            archive_name, 
            ['large_data/'], 
            preset='balanced',
            progress_callback=progress_callback
        )
        tasks.append(task)
    
    # Run all tasks concurrently
    await asyncio.gather(*tasks)
    
    print(f"\nTotal time: {time.time() - start_time:.1f}s")

# Run async operation
asyncio.run(process_large_archives())
```

## Common Migration Patterns

### 1. Batch Processing
```python
# OLD
import zipfile
import os

for root, dirs, files in os.walk('source'):
    for file in files:
        if file.endswith('.zip'):
            with zipfile.ZipFile(os.path.join(root, file), 'r') as zf:
                zf.extractall('extracted')

# NEW
import py7zz
from pathlib import Path

for archive in Path('source').rglob('*'):
    if archive.suffix.lower() in ['.zip', '.7z', '.rar', '.tar', '.gz']:
        py7zz.extract_archive(archive, 'extracted')
```

### 2. Error Handling
```python
# OLD
import zipfile

try:
    with zipfile.ZipFile('archive.zip', 'r') as zf:
        zf.extractall()
except zipfile.BadZipFile:
    print("Invalid ZIP file")
except FileNotFoundError:
    print("Archive not found")

# NEW
import py7zz

try:
    py7zz.extract_archive('archive.7z')
except py7zz.CorruptedArchiveError:
    print("Invalid archive file")
except py7zz.FilenameCompatibilityError as e:
    print(f"Filename issues resolved: {len(e.problematic_files)} files renamed")
except py7zz.FileNotFoundError:
    print("Archive not found")
```

### 3. Progress Monitoring
```python
# OLD - No built-in progress support
import zipfile

def extract_with_progress(archive_path, output_dir):
    with zipfile.ZipFile(archive_path, 'r') as zf:
        total_files = len(zf.namelist())
        for i, file in enumerate(zf.namelist()):
            zf.extract(file, output_dir)
            print(f"Progress: {i+1}/{total_files} ({(i+1)/total_files*100:.1f}%)")

# NEW - Built-in async progress support
import py7zz
import asyncio

async def extract_with_progress(archive_path, output_dir):
    async def progress_handler(info):
        print(f"Progress: {info.percentage:.1f}% - {info.current_file}")
    
    await py7zz.extract_archive_async(
        archive_path, 
        output_dir, 
        progress_callback=progress_handler
    )
```

## Best Practices

### 1. Use Context Managers
```python
# GOOD
with py7zz.SevenZipFile('archive.7z', 'w') as sz:
    sz.add('file.txt')
# File is automatically closed

# AVOID
sz = py7zz.SevenZipFile('archive.7z', 'w')
sz.add('file.txt')
sz.close()  # Manual close required
```

### 2. Choose Appropriate Presets
```python
# For fast backups
py7zz.create_archive('backup.7z', ['data/'], preset='fast')

# For balanced compression
py7zz.create_archive('archive.7z', ['data/'], preset='balanced')

# For maximum compression
py7zz.create_archive('small.7z', ['data/'], preset='ultra')
```

### 3. Handle Errors Gracefully
```python
import py7zz

try:
    py7zz.create_archive('archive.7z', ['nonexistent/'])
except py7zz.FileNotFoundError as e:
    print(f"File not found: {e}")
except py7zz.CompressionError as e:
    print(f"Compression failed: {e}")
except py7zz.Py7zzError as e:
    print(f"General error: {e}")
```

### 4. Use Async for Large Operations
```python
import py7zz
import asyncio

async def process_large_archive():
    # Use async for large files to avoid blocking
    await py7zz.create_archive_async(
        'large_backup.7z', 
        ['large_directory/'],
        preset='balanced'
    )

# Run async operation
asyncio.run(process_large_archive())
```

## Performance Considerations

### Compression Speed vs Ratio
- **'fast'**: Fastest compression, larger files
- **'balanced'**: Good balance of speed and compression
- **'backup'**: Better compression for long-term storage
- **'ultra'**: Maximum compression, slower speed

### Memory Usage
- py7zz uses subprocess calls, so memory usage is minimal
- Large archives are processed in chunks automatically
- No need to load entire archives into memory

### Async Benefits
- Non-blocking operations for large files
- Progress reporting for better user experience
- Better resource utilization in concurrent applications

## Troubleshooting

### Common Issues

1. **"7zz binary not found"**
   ```bash
   pip install --upgrade py7zz
   ```

2. **"Unsupported format"**
   ```python
   # Check version information
   print(py7zz.get_version())                    # Current py7zz version
   print(py7zz.get_bundled_7zz_version())        # Bundled 7zz version
   print(py7zz.get_version_info())               # Complete version details
   
   # Or use CLI for detailed version information
   # py7zz version
   # py7zz version --format json
   ```

3. **Permission errors**
   ```python
   # Ensure write permissions
   py7zz.extract_archive('archive.7z', 'output/', overwrite=True)
   ```

## Windows Filename Compatibility

One major advantage of migrating to py7zz is automatic handling of Windows filename restrictions, which is not available in the standard library modules.

### The Problem

When using zipfile/tarfile to extract archives created on Unix/Linux systems on Windows, you may encounter errors like:

```python
# OLD - zipfile fails with Windows-incompatible filenames
import zipfile

try:
    with zipfile.ZipFile('unix_archive.zip', 'r') as zf:
        zf.extractall('output/')  # Fails on Windows with files named 'CON.txt', 'file:name.txt', etc.
except Exception as e:
    print(f"Extraction failed: {e}")  # No automatic resolution
```

### The Solution

py7zz automatically handles these issues:

```python
# NEW - py7zz automatically resolves filename issues
import py7zz

# Extract with automatic filename sanitization on Windows
py7zz.extract_archive('unix_archive.zip', 'output/')
# Files are automatically renamed:
# 'CON.txt' -> 'CON_file.txt'
# 'file:name.txt' -> 'file_name.txt'
# 'file*.log' -> 'file_.log'

# Control logging output
py7zz.setup_logging("INFO")        # Show what was renamed (default)
py7zz.disable_warnings()           # Hide filename warnings
```

### Migration Benefits

| zipfile/tarfile | py7zz |
|----------------|-------|
| Fails on Windows with invalid filenames | Automatically sanitizes filenames |
| No built-in filename handling | Handles reserved names, invalid chars, long names |
| Manual error handling required | Detailed logging of changes |
| Platform-specific issues | Works consistently across platforms |

### Getting Help

- Check the [py7zz documentation](https://github.com/rxchi1d/py7zz)
- Report issues on [GitHub Issues](https://github.com/rxchi1d/py7zz/issues)
- For migration questions, include your original zipfile/tarfile code

## Conclusion

py7zz provides a seamless migration path from zipfile and tarfile with:
- **Familiar API**: Same methods and patterns you're used to
- **Enhanced Features**: Support for 50+ archive formats
- **Better Performance**: Efficient 7zz engine under the hood
- **Modern Features**: Async operations, progress reporting
- **Windows Compatibility**: Automatic filename sanitization
- **Cross-platform**: Works consistently on Windows, macOS, and Linux

The migration is straightforward - in most cases, you only need to change the import and class names. The rest of your code can remain largely unchanged while gaining access to advanced compression formats and features.
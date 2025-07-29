# Migration Guide: From zipfile/tarfile to py7zz

This guide helps you migrate from Python's standard library `zipfile` and `tarfile` modules to py7zz, which provides compression support for dozens of archive formats with a familiar interface and automatic Windows filename compatibility.

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

## Comprehensive Async API Migration Guide

py7zz provides complete asynchronous support for all archive operations, enabling non-blocking I/O and better resource utilization. This is especially valuable for large files, batch operations, and GUI applications.

### Async API Overview

py7zz offers two levels of async support:

1. **AsyncSevenZipFile**: Async version of SevenZipFile with complete method compatibility
2. **Simple Async Functions**: Async versions of high-level functions

### AsyncSevenZipFile Migration

#### From zipfile.ZipFile (synchronous)
```python
# OLD - Synchronous zipfile (blocks thread)
import zipfile

with zipfile.ZipFile('archive.zip', 'r') as zf:
    # All operations block the main thread
    names = zf.namelist()
    info = zf.getinfo('file.txt')
    content = zf.read('file.txt')
    zf.extractall('output/')
```

#### To AsyncSevenZipFile (non-blocking)
```python
# NEW - Asynchronous py7zz (non-blocking)
import py7zz
import asyncio

async def async_operations():
    async with py7zz.AsyncSevenZipFile('archive.7z', 'r') as asz:
        # All operations are non-blocking
        names = await asz.namelist()
        info = await asz.getinfo('file.txt')
        content = await asz.read('file.txt')
        await asz.extractall('output/')

asyncio.run(async_operations())
```

### Complete Method Mapping

| zipfile.ZipFile | AsyncSevenZipFile | Notes |
|----------------|-------------------|-------|
| `zf.namelist()` | `await asz.namelist()` | Non-blocking file listing |
| `zf.infolist()` | `await asz.infolist()` | Non-blocking info retrieval |
| `zf.getinfo(name)` | `await asz.getinfo(name)` | Non-blocking member info |
| `zf.read(name)` | `await asz.read(name)` | Non-blocking file reading |
| `zf.extractall()` | `await asz.extractall()` | Non-blocking extraction |
| `zf.write(file, arcname)` | `await asz.add(file, arcname)` | Non-blocking file addition |
| `zf.writestr(name, data)` | `await asz.writestr(name, data)` | Non-blocking string writing |
| `zf.testzip()` | `await asz.testzip()` | Non-blocking integrity test |

### tarfile.TarFile Async Migration

#### From tarfile (synchronous)
```python
# OLD - Synchronous tarfile
import tarfile

with tarfile.open('archive.tar.gz', 'r:gz') as tf:
    members = tf.getmembers()
    names = tf.getnames()
    member = tf.getmember('file.txt')
    tf.extractall('output/')
```

#### To AsyncSevenZipFile (async)
```python
# NEW - Asynchronous py7zz with tarfile compatibility
import py7zz
import asyncio

async def async_tar_operations():
    async with py7zz.AsyncSevenZipFile('archive.tar.gz', 'r') as asz:
        # tarfile-compatible async methods
        members = await asz.getmembers()
        names = await asz.getnames()
        member = await asz.getmember('file.txt')
        await asz.extractall('output/')

asyncio.run(async_tar_operations())
```

### Async Iterator Support

py7zz provides async iteration over archive members:

#### Old iteration pattern
```python
# OLD - Synchronous iteration
import zipfile

with zipfile.ZipFile('archive.zip', 'r') as zf:
    for filename in zf.namelist():
        content = zf.read(filename)
        # Process each file (blocks for each read)
        process_file(filename, content)
```

#### New async iteration pattern
```python
# NEW - Asynchronous iteration
import py7zz
import asyncio

async def process_archive():
    async with py7zz.AsyncSevenZipFile('archive.7z', 'r') as asz:
        # Iterate asynchronously over archive members
        async for filename in asz:
            content = await asz.read(filename)
            # Process each file (non-blocking)
            await async_process_file(filename, content)

asyncio.run(process_archive())
```

### Async Membership Testing

```python
# OLD - Synchronous membership testing
import zipfile

with zipfile.ZipFile('archive.zip', 'r') as zf:
    if 'config.txt' in zf.namelist():  # Loads entire file list
        content = zf.read('config.txt')

# NEW - Async membership testing
import py7zz
import asyncio

async def check_member():
    async with py7zz.AsyncSevenZipFile('archive.7z', 'r') as asz:
        if await asz.__acontains__('config.txt'):  # Non-blocking check
            content = await asz.read('config.txt')

asyncio.run(check_member())
```

### Simple Async Functions Migration

#### Basic Operations

**Synchronous → Asynchronous**
```python
# OLD - Blocking operations
import py7zz

# These block the main thread
py7zz.create_archive('backup.7z', ['data/'])
py7zz.extract_archive('backup.7z', 'output/')

# NEW - Non-blocking operations
import py7zz
import asyncio

async def async_operations():
    # These don't block the main thread
    await py7zz.create_archive_async('backup.7z', ['data/'])
    await py7zz.extract_archive_async('backup.7z', 'output/')

asyncio.run(async_operations())
```

#### Progress Reporting Migration

**From manual progress tracking:**
```python
# OLD - Manual progress tracking
import zipfile
import time

def extract_with_manual_progress(archive_path, output_dir):
    with zipfile.ZipFile(archive_path, 'r') as zf:
        files = zf.namelist()
        total = len(files)
        
        for i, filename in enumerate(files):
            zf.extract(filename, output_dir)
            print(f"Progress: {i+1}/{total} ({(i+1)/total*100:.1f}%)")
            time.sleep(0.01)  # Simulated processing time
```

**To automatic async progress:**
```python
# NEW - Automatic async progress reporting
import py7zz
import asyncio

async def extract_with_auto_progress(archive_path, output_dir):
    async def progress_handler(info):
        print(f"Progress: {info.percentage:.1f}% - {info.current_file}")
    
    await py7zz.extract_archive_async(
        archive_path, 
        output_dir,
        progress_callback=progress_handler
    )

asyncio.run(extract_with_auto_progress('archive.7z', 'output/'))
```

### Batch Operations Migration

#### From sequential processing
```python
# OLD - Sequential processing (slow)
import zipfile
import time

def process_multiple_archives():
    archives = ['archive1.zip', 'archive2.zip', 'archive3.zip']
    start_time = time.time()
    
    for archive in archives:
        with zipfile.ZipFile(archive, 'r') as zf:
            zf.extractall(f'output_{archive}/')
        print(f"Extracted {archive}")
    
    print(f"Total time: {time.time() - start_time:.1f}s")
```

#### To concurrent processing
```python
# NEW - Concurrent processing (fast)
import py7zz
import asyncio
import time

async def process_multiple_archives():
    archives = ['archive1.7z', 'archive2.7z', 'archive3.7z']
    start_time = time.time()
    
    # Define operations
    operations = [(archive, f'output_{archive}/') for archive in archives]
    
    # Process all archives concurrently
    await py7zz.batch_extract_async(operations)
    
    print(f"Total time: {time.time() - start_time:.1f}s")

asyncio.run(process_multiple_archives())
```

### GUI Application Integration

#### Thread-based GUI (old approach)
```python
# OLD - Thread-based approach (complex)
import zipfile
import threading
import tkinter as tk
from tkinter import ttk

class ArchiveApp:
    def __init__(self):
        self.root = tk.Tk()
        self.progress = ttk.Progressbar(self.root)
        self.progress.pack()
    
    def extract_archive(self, archive_path, output_dir):
        def extract_worker():
            try:
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    files = zf.namelist()
                    total = len(files)
                    
                    for i, filename in enumerate(files):
                        zf.extract(filename, output_dir)
                        # Update GUI from thread (complex)
                        self.root.after(0, self.update_progress, i+1, total)
            except Exception as e:
                self.root.after(0, self.show_error, str(e))
        
        # Start extraction in separate thread
        threading.Thread(target=extract_worker, daemon=True).start()
    
    def update_progress(self, current, total):
        self.progress['value'] = (current / total) * 100
        self.root.update()
    
    def show_error(self, error):
        print(f"Error: {error}")
```

#### Async GUI (new approach)
```python
# NEW - Async approach (simple)
import py7zz
import asyncio
import tkinter as tk
from tkinter import ttk

class AsyncArchiveApp:
    def __init__(self):
        self.root = tk.Tk()
        self.progress = ttk.Progressbar(self.root)
        self.progress.pack()
    
    async def extract_archive(self, archive_path, output_dir):
        async def progress_handler(info):
            # Update GUI directly (no thread complexity)
            self.progress['value'] = info.percentage
            self.root.update()
        
        try:
            await py7zz.extract_archive_async(
                archive_path, 
                output_dir,
                progress_callback=progress_handler
            )
        except Exception as e:
            print(f"Error: {e}")
    
    def run_async_task(self, archive_path, output_dir):
        # Schedule async task
        asyncio.create_task(self.extract_archive(archive_path, output_dir))
```

### Error Handling in Async Operations

#### Consistent error handling
```python
import py7zz
import asyncio

async def safe_async_operations():
    try:
        # All async operations use the same exceptions as sync
        await py7zz.create_archive_async('backup.7z', ['nonexistent/'])
    except py7zz.FileNotFoundError:
        print("Source files not found")
    except py7zz.CompressionError as e:
        print(f"Compression failed: {e}")
    except py7zz.FilenameCompatibilityError as e:
        print(f"Filename issues: {len(e.problematic_files)} files renamed")
    except py7zz.Py7zzError as e:
        print(f"General error: {e}")

asyncio.run(safe_async_operations())
```

### Performance Benefits of Async Migration

#### Concurrent Operations
```python
# OLD - Sequential (slow)
import zipfile
import time

def create_multiple_archives():
    start = time.time()
    
    for i in range(5):
        with zipfile.ZipFile(f'archive_{i}.zip', 'w') as zf:
            zf.write('large_file.txt')  # Blocks for each archive
    
    print(f"Sequential time: {time.time() - start:.1f}s")

# NEW - Concurrent (fast)
import py7zz
import asyncio
import time

async def create_multiple_archives():
    start = time.time()
    
    tasks = []
    for i in range(5):
        task = py7zz.create_archive_async(f'archive_{i}.7z', ['large_file.txt'])
        tasks.append(task)
    
    await asyncio.gather(*tasks)  # All archives created concurrently
    
    print(f"Concurrent time: {time.time() - start:.1f}s")

asyncio.run(create_multiple_archives())
```

### Migration Best Practices

#### 1. Start with Simple Functions
```python
# Easiest migration: replace function calls with async versions
# OLD
py7zz.create_archive('backup.7z', ['data/'])

# NEW
await py7zz.create_archive_async('backup.7z', ['data/'])
```

#### 2. Add Progress Reporting
```python
# Take advantage of built-in progress reporting
async def progress_handler(info):
    print(f"{info.operation}: {info.percentage:.1f}%")

await py7zz.create_archive_async(
    'backup.7z', 
    ['data/'], 
    progress_callback=progress_handler
)
```

#### 3. Use Batch Operations for Multiple Archives
```python
# Replace loops with batch operations
operations = [
    ('backup1.7z', ['folder1/']),
    ('backup2.7z', ['folder2/']),
    ('backup3.7z', ['folder3/'])
]

await py7zz.batch_compress_async(operations)
```

#### 4. Gradual Migration Strategy
```python
# You can mix sync and async operations during migration
import py7zz
import asyncio

def legacy_sync_operation():
    # Keep existing sync code working
    py7zz.create_archive('small.7z', ['config.txt'])

async def new_async_operation():
    # New async code for large operations
    await py7zz.create_archive_async('large.7z', ['big_data/'])

# Run both
legacy_sync_operation()
asyncio.run(new_async_operation())
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

### When to Use Async vs Sync

| Use Async When | Use Sync When |
|----------------|---------------|
| Processing large files (>100MB) | Small files (<10MB) |
| Batch operations | Single archive operations |
| GUI applications | Command-line scripts |
| Web applications | Simple automation scripts |
| Need progress reporting | Quick one-off tasks |
| I/O intensive operations | CPU intensive operations |

### Async Migration Checklist

- [ ] Replace `import zipfile`/`import tarfile` with `import py7zz`
- [ ] Add `import asyncio` to your imports
- [ ] Convert functions to async: `def` → `async def`
- [ ] Add `await` to all py7zz async calls
- [ ] Add progress callbacks where beneficial
- [ ] Use batch operations for multiple archives
- [ ] Replace sequential loops with concurrent operations
- [ ] Update error handling (same exceptions, async context)
- [ ] Test with `asyncio.run()` or integrate with existing async framework

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

One major advantage of migrating to py7zz is automatic handling of Windows filename restrictions, which is not available in the standard library modules. This is particularly important when working with archives created on Unix/Linux systems that contain filenames that are invalid on Windows.

### The Problem in Detail

Windows has several filename restrictions that don't exist on Unix/Linux systems:

#### 1. Reserved Names
Windows reserves certain names for system devices:
- **Device names**: `CON`, `PRN`, `AUX`, `NUL`
- **Serial ports**: `COM1`, `COM2`, ..., `COM9`
- **Parallel ports**: `LPT1`, `LPT2`, ..., `LPT9`

#### 2. Invalid Characters
Windows doesn't allow these characters in filenames:
- `<` `>` `:` `"` `|` `?` `*`
- Control characters (ASCII 0-31)

#### 3. Other Restrictions
- Filenames cannot end with a space or period
- Maximum filename length is 255 characters
- Path length cannot exceed 260 characters (in most cases)

### Common Failure Scenarios

#### zipfile Failures
```python
# OLD - zipfile fails with Windows-incompatible filenames
import zipfile

try:
    with zipfile.ZipFile('unix_archive.zip', 'r') as zf:
        zf.extractall('output/')  # Fails on Windows
except Exception as e:
    print(f"Extraction failed: {e}")
    # Typical errors:
    # "Cannot create 'CON.txt': The system cannot find the path specified"
    # "Cannot create 'file:name.txt': The filename, directory name, or volume label syntax is incorrect"
```

#### tarfile Failures
```python
# OLD - tarfile fails similarly
import tarfile

try:
    with tarfile.open('unix_archive.tar.gz', 'r:gz') as tf:
        tf.extractall('output/')  # Fails on Windows
except Exception as e:
    print(f"Extraction failed: {e}")
    # Similar Windows path errors
```

### The py7zz Solution

py7zz automatically detects and resolves all Windows filename compatibility issues:

```python
# NEW - py7zz automatically resolves filename issues
import py7zz

# Extract with automatic filename sanitization on Windows
py7zz.extract_archive('unix_archive.zip', 'output/')
# Files are automatically renamed according to sanitization rules
```

### Detailed Sanitization Rules

py7zz applies sanitization rules:

#### 1. Invalid Character Replacement
```python
# Original filename -> Sanitized filename
'file:name.txt'     -> 'file_name.txt'      # : replaced with _
'file<>name.log'    -> 'file___name.log'    # < and > replaced with _
'file*?.txt'        -> 'file__.txt'         # * and ? replaced with _
'file|name.dat'     -> 'file_name.dat'      # | replaced with _
'file"name.conf'    -> 'file_name.conf'     # " replaced with _
```

#### 2. Reserved Name Handling
```python
# Reserved device names get '_file' suffix
'CON.txt'           -> 'CON_file.txt'
'PRN.log'           -> 'PRN_file.log'
'AUX.dat'           -> 'AUX_file.dat'
'NUL.conf'          -> 'NUL_file.conf'
'COM1.port'         -> 'COM1_file.port'
'LPT1.printer'      -> 'LPT1_file.printer'
```

#### 3. Trailing Character Cleanup
```python
# Remove trailing spaces and periods
'filename '         -> 'filename'           # Trailing space removed
'filename.'         -> 'filename'           # Trailing period removed
'filename .txt'     -> 'filename.txt'       # Trailing space before extension
```

#### 4. Long Filename Handling
```python
# Very long filenames are truncated and get MD5 hash for uniqueness
'very-long-filename-that-exceeds-windows-255-character-limit...'
-> 'very-long-filename-that-exc_a1b2c3d4.txt'
```

#### 5. Control Character Removal
```python
# Control characters (ASCII 0-31) are replaced with _
'file\x00name.txt'  -> 'file_name.txt'      # Null character
'file\tnab.txt'     -> 'file_tab.txt'       # Tab character
```

### Comprehensive Migration Examples

#### Complete Error Scenario
```python
# OLD - Multiple failure points with zipfile
import zipfile
import os

problematic_files = [
    'CON.txt',          # Reserved name
    'file:name.txt',    # Invalid character
    'data*.log',        # Invalid character
    'config ',          # Trailing space
    'very-long-filename-that-will-cause-problems-on-windows-filesystem.txt'  # Too long
]

# Create archive on Unix/Linux (works fine)
with zipfile.ZipFile('problematic.zip', 'w') as zf:
    for filename in problematic_files:
        zf.writestr(filename, f"Content of {filename}")

# Try to extract on Windows (fails)
try:
    with zipfile.ZipFile('problematic.zip', 'r') as zf:
        zf.extractall('output/')  # Multiple failures
except Exception as e:
    print(f"Extraction failed: {e}")
    # Manual workaround required:
    # 1. List all files
    # 2. Check each filename for Windows compatibility
    # 3. Rename problematic files manually
    # 4. Extract with custom names
    # This is complex and error-prone!
```

#### py7zz Automatic Solution
```python
# NEW - All issues resolved automatically
import py7zz

# Same problematic archive extracts perfectly
py7zz.extract_archive('problematic.zip', 'output/')

# Automatic transformations applied:
# 'CON.txt' -> 'CON_file.txt'
# 'file:name.txt' -> 'file_name.txt'
# 'data*.log' -> 'data_.log'
# 'config ' -> 'config'
# 'very-long-filename...' -> 'very-long-filename-that-will-cau_a1b2c3d4.txt'

# All files extracted successfully with safe names!
```

### Advanced Filename Compatibility Features

#### 1. Uniqueness Guarantee
py7zz ensures no filename conflicts after sanitization:

```python
# If multiple files would result in the same sanitized name:
# Original files:
# 'file:name.txt'
# 'file?name.txt' 
# 'file*name.txt'

# py7zz ensures unique names:
# 'file_name.txt'
# 'file_name_1.txt'
# 'file_name_2.txt'
```

#### 2. Directory Structure Preservation
```python
# Original structure:
# 'folder/CON.txt'
# 'folder/file:name.txt'
# 'sub:dir/data.txt'

# Sanitized structure:
# 'folder/CON_file.txt'
# 'folder/file_name.txt'
# 'sub_dir/data.txt'

# Directory hierarchy is maintained with safe names
```

#### 3. Extension Preservation
```python
# File extensions are always preserved
'CON.txt'           -> 'CON_file.txt'      # .txt preserved
'data*.log.gz'      -> 'data_.log.gz'      # .log.gz preserved
'file?.tar.bz2'     -> 'file_.tar.bz2'     # .tar.bz2 preserved
```

### Logging and Transparency

py7zz provides detailed logging of all filename changes:

#### 1. Default Logging (INFO level)
```python
import py7zz

# Default behavior shows what was changed
py7zz.extract_archive('problematic.zip', 'output/')

# Console output:
# INFO [py7zz] Extraction failed due to filename compatibility issues, attempting with sanitized names
# WARNING [py7zz] Windows filename compatibility: 3 files renamed
# WARNING [py7zz]   'CON.txt' -> 'CON_file.txt' (reason: reserved name: CON)
# WARNING [py7zz]   'file:name.txt' -> 'file_name.txt' (reason: invalid characters: ':')
# WARNING [py7zz]   'data*.log' -> 'data_.log' (reason: invalid characters: '*')
# INFO [py7zz] Successfully extracted 15 files with sanitized names
```

#### 2. Custom Logging Control
```python
import py7zz

# Show detailed debug information
py7zz.setup_logging("DEBUG")
py7zz.extract_archive('problematic.zip', 'output/')

# Hide filename warnings (quiet mode)
py7zz.disable_warnings()
py7zz.extract_archive('problematic.zip', 'output/')

# Show only errors
py7zz.setup_logging("ERROR")
py7zz.extract_archive('problematic.zip', 'output/')
```

#### 3. Programmatic Access to Changes
```python
import py7zz

try:
    py7zz.extract_archive('problematic.zip', 'output/')
except py7zz.FilenameCompatibilityError as e:
    print(f"Filename issues encountered: {len(e.problematic_files)} files")
    print(f"Sanitization {'successful' if e.sanitized else 'failed'}")
    
    # Access list of problematic files
    for original_name in e.problematic_files:
        print(f"Problematic file: {original_name}")
```

### Object-Oriented API Compatibility

All filename compatibility features work with the object-oriented API:

```python
import py7zz

# SevenZipFile also handles filename issues automatically
with py7zz.SevenZipFile('problematic.zip', 'r') as sz:
    # All methods work with automatic filename sanitization
    sz.extractall('output/')                    # Auto-sanitizes all files
    sz.extractall('output/', members=['CON.txt'])  # Auto-sanitizes specific files
    sz.extract('output/')                       # Auto-sanitizes during extraction
```

### Async API Compatibility

Filename compatibility works seamlessly with async operations:

```python
import py7zz
import asyncio

async def async_extract_with_compatibility():
    # Async operations also handle filename issues
    await py7zz.extract_archive_async('problematic.zip', 'output/')
    
    # Object-oriented async API
    async with py7zz.AsyncSevenZipFile('problematic.zip', 'r') as asz:
        await asz.extractall('output/')

asyncio.run(async_extract_with_compatibility())
```

### Platform Behavior

#### Windows Systems
- Full filename sanitization is applied
- All Windows restrictions are handled
- Detailed logging shows what was changed

#### Unix/Linux/macOS Systems
- No filename modification (not needed)
- Original filenames are preserved exactly
- No performance overhead

#### Cross-Platform Development
```python
import py7zz

# This code works identically on all platforms
py7zz.extract_archive('archive.zip', 'output/')

# On Windows: filenames are sanitized as needed
# On Unix/Linux/macOS: filenames are preserved exactly
# Your code doesn't need to know or care about the platform
```

### Migration Benefits Summary

| Feature | zipfile/tarfile | py7zz |
|---------|----------------|-------|
| **Windows Reserved Names** | Hard failure | Automatic `_file` suffix |
| **Invalid Characters** | Hard failure | Automatic `_` replacement |
| **Long Filenames** | Hard failure | Automatic truncation + hash |
| **Trailing Spaces/Periods** | Hard failure | Automatic removal |
| **Control Characters** | Hard failure | Automatic replacement |
| **Uniqueness Conflicts** | Not handled | Automatic numbering |
| **Directory Structure** | Breaks | Preserved with safe names |
| **File Extensions** | May be lost | Always preserved |
| **Error Information** | Generic OS errors | Detailed compatibility errors |
| **Logging** | None | Comprehensive change tracking |
| **Cross-Platform** | Platform-specific behavior | Consistent across platforms |

## Advanced Migration: Production Features

py7zz 1.1+ includes features that extend beyond traditional archive operations. These features are designed for production environments and cloud integration.

### Cloud Integration & Streaming Interface

#### Traditional File-Based Approach
```python
# OLD - Traditional approach with intermediate files
import zipfile
import boto3
import tempfile

def upload_archive_to_s3(archive_path, bucket, key):
    # Step 1: Create archive locally
    with zipfile.ZipFile(archive_path, 'w') as zf:
        zf.write('large_file.csv')
    
    # Step 2: Upload entire file to S3
    s3_client = boto3.client('s3')
    with open(archive_path, 'rb') as f:
        s3_client.upload_fileobj(f, bucket, key)
    
    # Step 3: Clean up local file
    os.remove(archive_path)

def download_from_archive_s3(bucket, key, filename):
    # Step 1: Download entire archive
    s3_client = boto3.client('s3')
    with tempfile.NamedTemporaryFile() as tmp:
        s3_client.download_fileobj(bucket, key, tmp)
        
        # Step 2: Extract specific file
        with zipfile.ZipFile(tmp.name, 'r') as zf:
            return zf.read(filename)
```

#### py7zz Streaming Approach
```python
# NEW - Direct streaming without intermediate files
import py7zz
import boto3

def upload_archive_to_s3_streaming(bucket, key):
    s3_client = boto3.client('s3')
    
    # Create archive and stream directly to S3
    with py7zz.SevenZipFile('memory://archive.7z', 'w') as sz:
        # Stream large file directly from source to S3
        with sz.open_stream_writer('large_file.csv') as writer:
            # Data flows directly from source -> archive -> S3
            # No intermediate local files needed
            for chunk in get_data_chunks():
                writer.write(chunk)
            
            # Upload the stream directly
            s3_client.upload_fileobj(writer, bucket, key)

def download_from_archive_s3_streaming(bucket, key, filename):
    s3_client = boto3.client('s3')
    
    # Stream archive directly from S3 and extract file
    response = s3_client.get_object(Bucket=bucket, Key=key)
    
    with py7zz.SevenZipFile(response['Body'], 'r') as sz:
        # Stream specific file content directly
        with sz.open_stream(filename) as stream:
            return stream.read()  # Or process in chunks
```

#### Benefits of Streaming Approach
- **Memory Efficient**: No intermediate files stored locally
- **Faster**: Direct data flow without disk I/O
- **Scalable**: Handle archives larger than available disk space
- **Cost Effective**: Reduced storage and bandwidth usage

### Thread-Safe Configuration Management

#### Traditional Global Configuration Problems
```python
# OLD - Problematic global configuration
import threading

# Global variables are not thread-safe
compression_level = 5
compression_method = "lzma2"

def worker_thread(data):
    global compression_level, compression_method
    
    # Race condition: multiple threads modifying globals
    if data.size > 1000000:
        compression_level = 9  # Other threads see this change!
        compression_method = "lzma2"
    
    # This configuration might be changed by other threads
    create_archive(f'output_{threading.current_thread().ident}.7z', data)
```

#### py7zz Thread-Safe Configuration
```python
# NEW - Thread-safe immutable configuration
import py7zz
import threading
from concurrent.futures import ThreadPoolExecutor

# Immutable configuration objects
base_config = py7zz.ImmutableConfig(
    level=5,
    compression="lzma2",
    solid=True,
    preset_name="production"
)

# Thread-safe global configuration
py7zz.ThreadSafeGlobalConfig.set_config(base_config)

def worker_thread(data):
    # Each thread can safely access global config
    current_config = py7zz.ThreadSafeGlobalConfig.get_config()
    
    # Temporary configuration changes don't affect other threads
    with py7zz.ThreadSafeGlobalConfig.temporary_config(level=9) as temp_config:
        # Only this thread sees level=9
        py7zz.create_archive(f'output_{threading.current_thread().ident}.7z', data)
    
    # Original configuration automatically restored
    
# Safe concurrent execution
with ThreadPoolExecutor(max_workers=8) as executor:
    tasks = [data_chunk_1, data_chunk_2, data_chunk_3]
    executor.map(worker_thread, tasks)
```

### Advanced Progress Monitoring

#### Traditional Manual Progress Tracking
```python
# OLD - Manual progress tracking
import zipfile
import time

def extract_with_manual_progress(archive_path, output_dir):
    with zipfile.ZipFile(archive_path, 'r') as zf:
        files = zf.namelist()
        total_files = len(files)
        start_time = time.time()
        
        for i, filename in enumerate(files):
            zf.extract(filename, output_dir)
            
            # Manual calculations
            progress = (i + 1) / total_files * 100
            elapsed = time.time() - start_time
            if elapsed > 0 and progress > 0:
                estimated_total = elapsed / (progress / 100)
                remaining = estimated_total - elapsed
            else:
                remaining = None
            
            # Manual formatting
            print(f"Progress: {progress:.1f}% ({i+1}/{total_files})")
            if remaining:
                print(f"ETA: {remaining:.1f}s")
```

#### py7zz Structured Progress Monitoring
```python
# NEW - Structured progress information
import py7zz

def progress_callback(progress: py7zz.ProgressInfo):
    # Progress data automatically calculated
    print(f"Operation: {progress.operation_type.value}")
    print(f"Stage: {progress.operation_stage.value}")
    print(f"Progress: {progress.percentage:.2f}%")
    print(f"Speed: {progress.format_speed()}")
    print(f"ETA: {progress.format_time(progress.estimated_remaining)}")
    print(f"File: {progress.current_file}")
    print(f"Files: {progress.files_processed}/{progress.total_files}")
    
    # Send to monitoring system
    send_metrics({
        'operation_id': progress.metadata.get('operation_id'),
        'percentage': progress.percentage,
        'speed_bps': progress.speed_bps,
        'files_processed': progress.files_processed
    })

# Automatic progress tracking
py7zz.extract_archive(
    'large_archive.7z',
    'output/',
    progress_callback=progress_callback
)

# Multiple callback styles available
py7zz.extract_archive('data.7z', 'output/', 
                     progress_callback=py7zz.create_callback("json"))  # JSON output
py7zz.extract_archive('logs.7z', 'output/', 
                     progress_callback=py7zz.create_callback("detailed"))  # Detailed console
```

### Enterprise Logging Integration

#### Traditional Logging Challenges
```python
# OLD - Manual logging integration
import logging
import zipfile

# Custom logger setup
logger = logging.getLogger('myapp.archiving')

def create_archive_with_logging(archive_path, files):
    logger.info(f"Starting compression: {len(files)} files")
    start_time = time.time()
    
    try:
        with zipfile.ZipFile(archive_path, 'w') as zf:
            for i, file_path in enumerate(files):
                zf.write(file_path)
                # Manual progress logging
                if i % 100 == 0:
                    logger.info(f"Processed {i}/{len(files)} files")
        
        duration = time.time() - start_time
        logger.info(f"Compression completed in {duration:.2f}s")
        
    except Exception as e:
        logger.error(f"Compression failed: {e}")
        raise
```

#### py7zz Integrated Logging
```python
# NEW - Seamless Python logging integration
import logging
import py7zz

# Standard Python logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

# py7zz automatically integrates with your logging hierarchy
app_logger = logging.getLogger('myapp.archiving')
app_logger.info("Starting archive operations")

# py7zz respects your logging configuration
py7zz.setup_logging(
    "INFO",
    structured=True,              # JSON structured logs
    performance_monitoring=True,  # Automatic performance logging
    log_file="py7zz.log",        # File logging with rotation
    max_file_size=50*1024*1024   # 50MB max file size
)

# Automatic performance monitoring
with py7zz.PerformanceLogger("bulk_compression"):
    py7zz.batch_create_archives([
        ('backup1.7z', ['data1/']),
        ('backup2.7z', ['data2/']),
        ('backup3.7z', ['data3/'])
    ])

# Structured logging output automatically includes:
# - Operation timing
# - File counts and sizes
# - Compression ratios
# - Error context
# - Performance metrics
```

### Configuration Persistence and Management

#### Traditional Configuration Challenges
```python
# OLD - Manual configuration management
import json
import os

class ArchiveConfig:
    def __init__(self):
        self.compression_level = 5
        self.method = "deflate"
        self.solid = False
    
    def load_from_file(self, config_path):
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.compression_level = config.get('level', 5)
                self.method = config.get('method', 'deflate')
                self.solid = config.get('solid', False)
    
    def save_to_file(self, config_path):
        config = {
            'level': self.compression_level,
            'method': self.method,
            'solid': self.solid
        }
        with open(config_path, 'w') as f:
            json.dump(config, f)

# Manual configuration management
config = ArchiveConfig()
config.load_from_file('config.json')
```

#### py7zz Enterprise Configuration Management
```python
# NEW - Enterprise configuration management
import py7zz

# Automatic user configuration loading
py7zz.ThreadSafeGlobalConfig.load_user_config()  # Loads from ~/.config/py7zz/config.json

# Enterprise preset configurations
production_config = py7zz.ImmutableConfig(
    preset_name="production_backup",
    level=8,
    compression="lzma2",
    dictionary_size="128m",
    threads=None,  # Auto-detect
    solid=True,
    # Enterprise-specific settings
    memory_limit="2g",
    encrypt_filenames=False
)

# Configuration validation
warnings = production_config.validate()
if warnings:
    for warning in warnings:
        logger.warning(f"Config warning: {warning}")

# Thread-safe configuration management
py7zz.ThreadSafeGlobalConfig.set_config(production_config)

# Automatic configuration persistence
py7zz.ThreadSafeGlobalConfig.save_user_config()  # Saves to user config directory

# Environment-specific configurations
with py7zz.with_preset("ultra"):
    # Operations use ultra compression settings
    py7zz.create_archive('critical_backup.7z', ['important_data/'])

# Configuration information and monitoring
config_info = py7zz.ThreadSafeGlobalConfig.get_config_info()
print(f"Current preset: {config_info['preset_name']}")
print(f"Config warnings: {len(config_info['warnings'])}")
```

### Migration Path for Enterprise Features

#### Step 1: Replace Basic Operations
```python
# OLD
import zipfile
with zipfile.ZipFile('archive.zip', 'w') as zf:
    zf.write('file.txt')

# NEW
import py7zz
with py7zz.SevenZipFile('archive.7z', 'w') as sz:
    sz.add('file.txt')
```

#### Step 2: Add Thread-Safe Configuration
```python
# NEW - Add thread-safe configuration
py7zz.ThreadSafeGlobalConfig.set_config(
    py7zz.ImmutableConfig(level=7, preset_name="production")
)
```

#### Step 3: Implement Structured Progress Monitoring
```python
# NEW - Add enterprise progress monitoring
def progress_callback(progress: py7zz.ProgressInfo):
    metrics.gauge('compression.progress', progress.percentage)
    logger.info("Progress update", extra={
        'percentage': progress.percentage,
        'current_file': progress.current_file
    })

py7zz.create_archive('data.7z', ['files/'], progress_callback=progress_callback)
```

#### Step 4: Integrate Enterprise Logging
```python
# NEW - Add enterprise logging
py7zz.setup_logging(
    "INFO",
    structured=True,
    performance_monitoring=True,
    log_file="/var/log/archiving/py7zz.log"
)
```

#### Step 5: Add Cloud Streaming (Optional)
```python
# NEW - Add cloud integration where beneficial
with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    with sz.open_stream('large_data.csv') as stream:
        s3_client.upload_fileobj(stream, 'bucket', 'key')
```

### Real-World Use Cases

#### 1. Processing Unix-created Archives on Windows
```python
# Common scenario: Archive created on Linux server, processed on Windows client
import py7zz

# This just works, no special handling needed
py7zz.extract_archive('server_backup.tar.gz', 'local_data/')
```

#### 2. Cross-Platform Build Systems
```python
# Build artifacts from different platforms
import py7zz

archives = ['linux_build.7z', 'mac_build.7z', 'windows_build.7z']

for archive in archives:
    # Each archive may have platform-specific filename issues
    py7zz.extract_archive(archive, f'builds/{archive}/')
    # All extract successfully with compatible names
```

#### 3. Automated Archive Processing
```python
import py7zz
from pathlib import Path

# Process all archives in a directory
for archive_path in Path('archives').glob('*'):
    if archive_path.suffix.lower() in ['.zip', '.7z', '.tar', '.gz', '.bz2']:
        output_dir = f'extracted/{archive_path.stem}/'
        py7zz.extract_archive(archive_path, output_dir)
        # All archives extract successfully regardless of filename issues
```

### Troubleshooting Filename Issues

#### Common Error Messages and Solutions

**Error**: "The filename, directory name, or volume label syntax is incorrect"
```python
# OLD - Manual handling required
# Solution: Use py7zz for automatic handling
py7zz.extract_archive('problematic.zip', 'output/')
```

**Error**: "The system cannot find the path specified"
```python
# Often caused by reserved names like CON.txt
# py7zz automatically renames: CON.txt -> CON_file.txt
```

**Error**: "Access is denied"
```python
# May be caused by invalid characters or reserved names
# py7zz handles both automatically
```

#### Diagnostic Tools
```python
import py7zz

# Get detailed information about potential filename issues
info = py7zz.get_archive_info('problematic.zip')
print(f"Archive contains {info['file_count']} files")

# List all files to see potential issues
with py7zz.SevenZipFile('problematic.zip', 'r') as sz:
    files = sz.namelist()
    for filename in files:
        # Check for potential Windows issues manually if needed
        if any(char in filename for char in '<>:"|?*'):
            print(f"Potential issue: {filename}")
```

### Migration Checklist for Filename Compatibility

- [ ] Identify archives that may have cross-platform filename issues
- [ ] Replace zipfile/tarfile extraction with py7zz
- [ ] Configure logging level as needed (`py7zz.setup_logging()`)
- [ ] Test extraction on Windows with Unix-created archives
- [ ] Review log output to understand what files were renamed
- [ ] Update any code that relies on specific filenames
- [ ] Document any filename changes that affect your application

The automatic filename compatibility handling in py7zz eliminates a major source of cross-platform issues and makes your archive processing code more robust and reliable.

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

The migration is straightforward - in most cases, you only need to change the import and class names. The rest of your code can remain largely unchanged while gaining access to additional compression formats and features.
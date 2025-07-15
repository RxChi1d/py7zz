# Migration Guide: From zipfile/tarfile to py7zz

This guide helps you migrate from Python's standard library `zipfile` and `tarfile` modules to py7zz, which provides enhanced compression support for dozens of archive formats with a familiar interface.

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
    file_list = zf.namelist()
    print(f"Archive contains {len(file_list)} files")
```

#### tarfile
```python
import tarfile

with tarfile.open('archive.tar.gz', 'r:gz') as tf:
    file_list = tf.getnames()
    print(f"Archive contains {len(file_list)} files")
```

#### py7zz
```python
import py7zz

# Compatible with both zipfile and tarfile APIs
with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    file_list = sz.namelist()  # or sz.getnames()
    print(f"Archive contains {len(file_list)} files")

# Simple one-liner
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
   # Check supported formats
   print(py7zz.get_version())  # Shows supported formats
   ```

3. **Permission errors**
   ```python
   # Ensure write permissions
   py7zz.extract_archive('archive.7z', 'output/', overwrite=True)
   ```

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
- **Cross-platform**: Works on Windows, macOS, and Linux

The migration is straightforward - in most cases, you only need to change the import and class names. The rest of your code can remain largely unchanged while gaining access to advanced compression formats and features.
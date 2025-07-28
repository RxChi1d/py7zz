# py7zz

[![PyPI version](https://img.shields.io/pypi/v/py7zz.svg)](https://pypi.org/project/py7zz/)
[![Python versions](https://img.shields.io/pypi/pyversions/py7zz.svg)](https://pypi.org/project/py7zz/)
[![License](https://img.shields.io/pypi/l/py7zz.svg)](https://github.com/rxchi1d/py7zz/blob/main/LICENSE)
[![CI](https://github.com/rxchi1d/py7zz/workflows/CI/badge.svg)](https://github.com/rxchi1d/py7zz/actions)

A Python wrapper for the 7zz CLI tool, providing a consistent object-oriented interface across platforms (macOS, Linux, Windows) with automatic update mechanisms, Windows filename compatibility, and support for dozens of archive formats.

## Features

- **🔧 Industry Standard API Compatibility** - Complete `zipfile.ZipFile` and `tarfile.TarFile` API compatibility with enhanced features
- **🚀 One-line archive operations** - Simple API for common tasks
- **📦 50+ archive formats** - ZIP, 7Z, RAR, TAR, GZIP, BZIP2, XZ, LZ4, ZSTD, and more
- **🌐 Cross-platform** - Works on macOS, Linux, and Windows
- **⚡ Async operations** - Non-blocking operations with progress reporting
- **🔒 Secure** - Bundled 7zz binaries, no system dependencies
- **🎯 Smart presets** - Optimized settings for different use cases
- **🪟 Windows filename compatibility** - Automatic handling of Unix archive filenames on Windows
- **📊 Rich archive information** - Detailed metadata with compression ratios, file attributes, and more

## Quick Start

### Installation

```bash
pip install py7zz
```

### Basic Usage

```python
import py7zz

# Simple API - One-line operations
py7zz.create_archive('backup.7z', ['documents/', 'photos/'])
py7zz.extract_archive('backup.7z', 'extracted/')

# Industry Standard API - zipfile.ZipFile compatible
with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    # zipfile compatible methods
    files = sz.namelist()                    # List all files
    info_list = sz.infolist()               # Get detailed file info
    info = sz.getinfo('document.txt')       # Get specific file info
    
    # Enhanced information available
    print(f"File: {info.filename}")
    print(f"Size: {info.file_size} bytes")
    print(f"Compressed: {info.compress_size} bytes")
    print(f"Compression ratio: {info.get_compression_ratio():.1%}")
    print(f"Method: {info.method}")

# tarfile.TarFile compatible methods also available
with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    members = sz.getmembers()               # tarfile compatible
    member = sz.getmember('document.txt')   # tarfile compatible
    names = sz.getnames()                   # tarfile compatible
```

### Advanced Usage

```python
import py7zz

# Complete zipfile.ZipFile API compatibility
with py7zz.SevenZipFile('archive.7z', 'w', preset='ultra') as sz:
    # zipfile compatible methods with enhancements
    sz.add('file.txt')                          # Basic file addition
    sz.add('src/data.txt', arcname='backup/data.txt')  # Custom archive name
    sz.writestr('config.txt', 'setting=value') # String data

# Selective extraction (zipfile/tarfile compatible)
with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    # Extract specific files only
    sz.extractall('output/', members=['file1.txt', 'folder/file2.txt'])
    
    # Read file content
    content = sz.read('file.txt')
    
    # Archive integrity test
    bad_file = sz.testzip()  # Returns None if OK, filename if corrupted
```

### Async Operations

```python
import py7zz
import asyncio

async def main():
    # Async operations with progress reporting
    async def progress_handler(info):
        print(f"Progress: {info.percentage:.1f}% - {info.current_file}")
    
    await py7zz.create_archive_async(
        'large_backup.7z',
        ['big_folder/'],
        preset='balanced',
        progress_callback=progress_handler
    )
    
    await py7zz.extract_archive_async(
        'large_backup.7z',
        'extracted/',
        progress_callback=progress_handler
    )

asyncio.run(main())
```

## API Overview

py7zz provides a **layered API design** to serve different user needs:

### Layer 1: Simple Function API (80% of use cases)
```python
# One-line solutions
py7zz.create_archive('backup.7z', ['files/'])
py7zz.extract_archive('backup.7z', 'output/')
py7zz.list_archive('backup.7z')  # ⚠️ Deprecated - use SevenZipFile.namelist()
py7zz.test_archive('backup.7z')
```

### Layer 2: Industry Standard API (zipfile/tarfile compatibility)
```python
# Complete zipfile.ZipFile API compatibility
with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    # zipfile compatible methods
    files = sz.namelist()              # ✅ zipfile.ZipFile.namelist()
    info_list = sz.infolist()          # ✅ zipfile.ZipFile.infolist()  
    info = sz.getinfo('file.txt')      # ✅ zipfile.ZipFile.getinfo()
    sz.extractall('out/', members=['file.txt'])  # ✅ Selective extraction
    
    # tarfile compatible methods
    members = sz.getmembers()          # ✅ tarfile.TarFile.getmembers()
    member = sz.getmember('file.txt')  # ✅ tarfile.TarFile.getmember()
    names = sz.getnames()              # ✅ tarfile.TarFile.getnames()

# Enhanced ArchiveInfo objects (zipfile.ZipInfo & tarfile.TarInfo compatible)
info = sz.getinfo('document.txt')
print(f"Size: {info.file_size}")           # zipfile.ZipInfo.file_size
print(f"Compressed: {info.compress_size}") # zipfile.ZipInfo.compress_size
print(f"CRC: {info.CRC:08X}")             # zipfile.ZipInfo.CRC
print(f"Mode: {oct(info.mode)}")          # tarfile.TarInfo.mode (when available)
print(f"Compression: {info.get_compression_ratio():.1%}")  # 🚀 Enhanced feature
```

### Layer 3: Advanced Control API (power users)
```python
# Custom configurations and fine-grained control
config = py7zz.create_custom_config(
    level=7,
    method='LZMA2',
    dictionary_size='64m',
    solid=True
)
with py7zz.SevenZipFile('archive.7z', 'w', config=config) as sz:
    sz.add('data/')
```

### Layer 4: Async API (concurrent operations)
```python
# Non-blocking operations with progress
await py7zz.batch_compress_async(
    [('backup1.7z', ['folder1/']), ('backup2.7z', ['folder2/'])],
    progress_callback=progress_handler
)
```

**📚 [Complete API Documentation](docs/API.md)** - Detailed reference with all classes, methods, parameters, and advanced usage examples.

## Supported Formats

py7zz supports reading and writing many archive formats:

| Format | Read | Write | Notes |
|--------|------|-------|-------|
| 7Z | ✅ | ✅ | Native format, best compression |
| ZIP | ✅ | ✅ | Wide compatibility |
| TAR | ✅ | ✅ | Unix standard |
| GZIP | ✅ | ✅ | Single file compression |
| BZIP2 | ✅ | ✅ | Better compression than gzip |
| XZ | ✅ | ✅ | Excellent compression |
| LZ4 | ✅ | ✅ | Very fast compression |
| ZSTD | ✅ | ✅ | Modern, fast compression |
| RAR | ✅ | ❌ | Extract only |
| CAB | ✅ | ❌ | Windows cabinet files |
| ISO | ✅ | ❌ | Disc images |
| And 40+ more... | ✅ | Various | See full list in docs |

## Migration from zipfile/tarfile

py7zz provides **complete API compatibility** with Python's standard library `zipfile` and `tarfile` modules. Migration is as simple as changing the import and class name:

### zipfile.ZipFile → SevenZipFile
```python
# OLD (zipfile)
import zipfile
with zipfile.ZipFile('archive.zip', 'r') as zf:
    files = zf.namelist()                    # ✅ Same method
    info = zf.getinfo('file.txt')           # ✅ Same method
    info_list = zf.infolist()               # ✅ Same method
    zf.extractall('output/', members=['file.txt'])  # ✅ Same parameters

# NEW (py7zz) - Identical API + Enhanced Features
import py7zz
with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    files = sz.namelist()                    # ✅ Same method
    info = sz.getinfo('file.txt')           # ✅ Same method, returns ArchiveInfo
    info_list = sz.infolist()               # ✅ Same method, enhanced info
    sz.extractall('output/', members=['file.txt'])  # ✅ Same parameters
    
    # 🚀 Bonus: Additional information available
    print(f"Compression method: {info.method}")
    print(f"Compression ratio: {info.get_compression_ratio():.1%}")
```

### tarfile.TarFile → SevenZipFile
```python
# OLD (tarfile)
import tarfile
with tarfile.open('archive.tar.gz', 'r:gz') as tf:
    members = tf.getmembers()               # ✅ Same method
    member = tf.getmember('file.txt')       # ✅ Same method
    names = tf.getnames()                   # ✅ Same method

# NEW (py7zz) - Compatible API + Enhanced Features
import py7zz
with py7zz.SevenZipFile('archive.tar.gz', 'r') as sz:
    members = sz.getmembers()               # ✅ Same method name
    member = sz.getmember('file.txt')       # ✅ Same method name
    names = sz.getnames()                   # ✅ Same method name
```

### Key Benefits of Migration:
- **🔄 Identical API** - Same method names, same parameters, same behavior
- **📦 50+ Formats** - Support ZIP, TAR, 7Z, RAR, and many more formats
- **🚀 Enhanced Features** - Detailed compression info, better error handling
- **🪟 Windows Compatibility** - Automatic filename sanitization for Unix archives
- **⚡ Async Support** - All methods available in async form

**📖 [Complete Migration Guide](docs/MIGRATION.md)** - Detailed guide with advanced examples, error handling patterns, and best practices.

## Compression Presets

py7zz includes optimized presets for different scenarios:

| Preset | Use Case | Speed | Compression | Memory |
|--------|----------|-------|-------------|---------|
| `fast` | Quick backups, temporary files | ⚡⚡⚡ | ⭐⭐ | Low |
| `balanced` | General purpose (default) | ⚡⚡ | ⭐⭐⭐ | Medium |
| `backup` | Long-term storage | ⚡ | ⭐⭐⭐⭐ | Medium |
| `ultra` | Maximum compression | ⚡ | ⭐⭐⭐⭐⭐ | High |

```python
# Use presets
py7zz.create_archive('quick.7z', ['files/'], preset='fast')
py7zz.create_archive('storage.7z', ['files/'], preset='backup')
py7zz.create_archive('minimal.7z', ['files/'], preset='ultra')
```

## Installation Methods

py7zz supports multiple installation methods:

### 1. PyPI Installation (Recommended)
```bash
pip install py7zz
```
- Includes bundled 7zz binaries
- No additional setup required
- Automatic binary detection

### 2. Development Installation
```bash
git clone https://github.com/rxchi1d/py7zz.git
cd py7zz
pip install -e .
```
- Auto-downloads correct 7zz binary on first use
- Cached in `~/.cache/py7zz/` for offline use

### 3. Direct GitHub Installation
```bash
pip install git+https://github.com/rxchi1d/py7zz.git
```

## Windows Filename Compatibility

py7zz automatically handles Windows filename restrictions when extracting archives created on Unix/Linux systems:

```python
import py7zz

# Automatically handles problematic filenames
py7zz.extract_archive('unix-created-archive.7z', 'output/')
# Files like 'CON.txt' become 'CON_file.txt'
# Files like 'file:name.txt' become 'file_name.txt'

# Control logging output
py7zz.setup_logging("INFO")        # Show filename warnings (default)
py7zz.disable_warnings()           # Hide filename warnings
py7zz.enable_debug_logging()       # Show detailed debug info
```

### Automatic Filename Sanitization

When extracting on Windows, py7zz automatically:

- **Replaces invalid characters**: `< > : " | ? *` → `_`
- **Handles reserved names**: `CON.txt` → `CON_file.txt`
- **Truncates long names**: Very long filenames get shortened with hash
- **Removes trailing spaces/dots**: `filename ` → `filename`
- **Ensures uniqueness**: Prevents filename conflicts
- **Logs all changes**: Shows exactly what was renamed and why

| Original (Unix) | Windows Safe | Reason |
|----------------|--------------|---------|
| `file:name.txt` | `file_name.txt` | Invalid character `:` |
| `CON.txt` | `CON_file.txt` | Windows reserved name |
| `file<>*.zip` | `file___.zip` | Multiple invalid chars |
| `very-long-filename...` | `very-long-fil_a1b2c.txt` | Length + hash |

**This feature is automatic and only activates on Windows systems when needed.**

## Error Handling

py7zz provides specific exception types for better error handling:

```python
import py7zz

try:
    py7zz.extract_archive('problematic.7z', 'output/')
except py7zz.FilenameCompatibilityError as e:
    print(f"Filename issues resolved: {len(e.problematic_files)} files renamed")
except py7zz.FileNotFoundError:
    print("Source file not found")
except py7zz.CompressionError:
    print("Compression failed")
except py7zz.ExtractionError:
    print("Extraction failed")
except py7zz.InsufficientSpaceError:
    print("Not enough disk space")
except py7zz.Py7zzError as e:
    print(f"General error: {e}")
```

## Performance Tips

### 1. Choose the Right Preset
```python
# Fast for temporary files
py7zz.create_archive('temp.7z', ['cache/'], preset='fast')

# Balanced for general use
py7zz.create_archive('backup.7z', ['data/'], preset='balanced')

# Ultra for long-term storage
py7zz.create_archive('archive.7z', ['important/'], preset='ultra')
```

### 2. Use Async for Large Operations
```python
# Non-blocking for large files
await py7zz.create_archive_async('huge.7z', ['bigdata/'])

# Batch operations
await py7zz.batch_compress_async([
    ('backup1.7z', ['folder1/']),
    ('backup2.7z', ['folder2/']),
    ('backup3.7z', ['folder3/'])
])
```

### 3. Monitor Progress
```python
async def progress_handler(info):
    print(f"{info.operation}: {info.percentage:.1f}% - {info.current_file}")

await py7zz.create_archive_async(
    'backup.7z',
    ['data/'],
    progress_callback=progress_handler
)
```

## Requirements

- Python 3.8+ (including Python 3.13)
- No external dependencies (7zz binary is bundled)
- **Supported platforms:** 
  - macOS (Intel + Apple Silicon)
  - Linux x86_64 (manylinux compatible)
  - Windows x64

> **Note:** Pre-built wheels are available for the above platforms. Other architectures may require building from source.

## Version Information

```python
import py7zz

# Get version information
print(py7zz.get_version())                    # Current py7zz version
print(py7zz.get_bundled_7zz_version())        # Bundled 7zz version
print(py7zz.get_version_info())               # Complete version details

# CLI version commands
# py7zz version                    # Human-readable format
# py7zz version --format json     # JSON format
```

## Development

### Setup Development Environment
```bash
git clone https://github.com/rxchi1d/py7zz.git
cd py7zz
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

### Run Tests
```bash
# Using uv (recommended)
uv run pytest              # Run tests
uv run ruff check --fix .  # Lint and fix
uv run mypy .              # Type checking

# Traditional commands
source .venv/bin/activate
pytest                     # Run tests
ruff check --fix .        # Lint and fix
mypy .                     # Type checking
```

### Code Quality
```bash
# Using uv (recommended)
uv run ruff format .       # Format code
uv run ruff check .        # Check style
uv run mypy .              # Type checking

# Traditional commands
source .venv/bin/activate
ruff format .              # Format code
ruff check .               # Check style
mypy .                     # Type checking
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for detailed information on:

- Setting up the development environment
- Code style and testing requirements
- Commit message conventions
- Pull request process

**Quick Start:**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow the [commit message conventions](CONTRIBUTING.md#commit-message-convention)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure all tests pass and code follows the style guidelines.

## License

py7zz is distributed under a dual license:

- **py7zz Python code**: BSD-3-Clause License
- **Bundled 7zz binary**: GNU Lesser General Public License (LGPL) v2.1

The py7zz Python wrapper code is licensed under the BSD-3-Clause license, allowing for flexible use in both open-source and commercial projects. The bundled 7zz binary from the 7-Zip project is licensed under LGPL-2.1, which requires that any modifications to the 7zz binary itself be made available under the same license.

Since py7zz uses the 7zz binary as a separate executable (not statically linked), users can freely use py7zz in their projects while complying with both licenses. For complete license information, see [LICENSE](LICENSE) and [7ZZ_LICENSE](7ZZ_LICENSE).

## Acknowledgments

- Built on top of the excellent [7-Zip](https://www.7-zip.org/) project
- Inspired by Python's `zipfile` and `tarfile` modules
- Uses the [7zz CLI tool](https://github.com/ip7z/7zip) for archive operations

## Links

- **📚 Complete API Documentation**: [docs/API.md](docs/API.md)
- **🔄 Migration Guide**: [docs/MIGRATION.md](docs/MIGRATION.md)
- **🤝 Contributing Guide**: [CONTRIBUTING.md](CONTRIBUTING.md)
- **📦 PyPI Package**: [py7zz on PyPI](https://pypi.org/project/py7zz/)
- **🐛 Issue Tracker**: [GitHub Issues](https://github.com/rxchi1d/py7zz/issues)
- **💻 Source Code**: [GitHub Repository](https://github.com/rxchi1d/py7zz)

---

**🚀 Ready to get started?** Check out the [Migration Guide](docs/MIGRATION.md) if you're coming from zipfile/tarfile, or dive into the examples above!
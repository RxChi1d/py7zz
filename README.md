# py7zz

[![PyPI version](https://badge.fury.io/py/py7zz.svg)](https://badge.fury.io/py/py7zz)
[![Python versions](https://img.shields.io/pypi/pyversions/py7zz.svg)](https://pypi.org/project/py7zz/)
[![License](https://img.shields.io/pypi/l/py7zz.svg)](https://github.com/rxchi1d/py7zz/blob/main/LICENSE)
[![Tests](https://github.com/rxchi1d/py7zz/workflows/Tests/badge.svg)](https://github.com/rxchi1d/py7zz/actions)

A Python wrapper for the 7zz CLI tool, providing a consistent object-oriented interface across platforms (macOS, Linux, Windows) with automatic update mechanisms and support for dozens of archive formats.

## Features

- **🚀 One-line archive operations** - Simple API for common tasks
- **🔧 zipfile/tarfile compatibility** - Drop-in replacement with familiar interface
- **📦 50+ archive formats** - ZIP, 7Z, RAR, TAR, GZIP, BZIP2, XZ, LZ4, ZSTD, and more
- **🌐 Cross-platform** - Works on macOS, Linux, and Windows
- **⚡ Async operations** - Non-blocking operations with progress reporting
- **🔒 Secure** - Bundled 7zz binaries, no system dependencies
- **🎯 Smart presets** - Optimized settings for different use cases

## Quick Start

### Installation

```bash
pip install py7zz
```

### Basic Usage

```python
import py7zz

# Create archive (simple API)
py7zz.create_archive('backup.7z', ['documents/', 'photos/'])

# Extract archive
py7zz.extract_archive('backup.7z', 'extracted/')

# List archive contents
files = py7zz.list_archive('backup.7z')
print(f"Archive contains {len(files)} files")

# Test archive integrity
if py7zz.test_archive('backup.7z'):
    print("Archive is OK")
```

### Advanced Usage

```python
import py7zz

# Object-oriented interface (similar to zipfile.ZipFile)
with py7zz.SevenZipFile('archive.7z', 'w', preset='ultra') as sz:
    sz.add('file.txt')
    sz.add('folder/')

# Read files from archive
with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    content = sz.read('file.txt')
    files = sz.namelist()
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
py7zz.list_archive('backup.7z')
py7zz.test_archive('backup.7z')
```

### Layer 2: Object-Oriented API (zipfile/tarfile compatibility)
```python
# Similar to zipfile.ZipFile
with py7zz.SevenZipFile('archive.7z', 'w') as sz:
    sz.add('file.txt')
    sz.extractall('output/')
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

py7zz is designed as a drop-in replacement for Python's `zipfile` and `tarfile` modules:

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

**📖 [Complete Migration Guide](docs/MIGRATION.md)** - Detailed guide for migrating from zipfile/tarfile with examples and best practices.

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

## Error Handling

py7zz provides specific exception types for better error handling:

```python
import py7zz

try:
    py7zz.create_archive('backup.7z', ['nonexistent/'])
except py7zz.FileNotFoundError:
    print("Source file not found")
except py7zz.CompressionError:
    print("Compression failed")
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

- Python 3.8+
- No external dependencies (7zz binary is bundled)
- Supported platforms: macOS, Linux, Windows x64

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

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
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
- **📦 PyPI Package**: [py7zz on PyPI](https://pypi.org/project/py7zz/)
- **🐛 Issue Tracker**: [GitHub Issues](https://github.com/rxchi1d/py7zz/issues)
- **💻 Source Code**: [GitHub Repository](https://github.com/rxchi1d/py7zz)

---

**🚀 Ready to get started?** Check out the [Migration Guide](docs/MIGRATION.md) if you're coming from zipfile/tarfile, or dive into the examples above!
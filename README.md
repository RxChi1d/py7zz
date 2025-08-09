<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: 2025 py7zz contributors
-->

# py7zz

[![PyPI](https://img.shields.io/pypi/v/py7zz)](https://pypi.org/project/py7zz/)
[![Python](https://img.shields.io/pypi/pyversions/py7zz)](https://pypi.org/project/py7zz/)
[![License](https://img.shields.io/pypi/l/py7zz)](https://github.com/rxchi1d/py7zz/blob/main/LICENSE)
[![CI](https://github.com/rxchi1d/py7zz/workflows/CI/badge.svg)](https://github.com/rxchi1d/py7zz/actions)

A Python wrapper for 7zz CLI tool providing cross-platform archive operations with built-in security protection, Windows filename compatibility, and comprehensive API support.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Advanced Features](#advanced-features)
- [Migration Guide](#migration-guide)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Cross-platform**: Windows, macOS, Linux
- **50+ formats**: 7Z, ZIP, TAR, RAR, and more
- **API compatible**: Drop-in replacement for `zipfile`/`tarfile`
- **Windows compatibility**: Automatic filename sanitization
- **Security protection**: ZIP bomb detection and file count limits
- **Async support**: Non-blocking operations with progress
- **Zero dependencies**: Bundled 7zz binary

## Installation

```bash
pip install py7zz
```

For development:
```bash
git clone https://github.com/rxchi1d/py7zz.git
cd py7zz
pip install -e .
```

## Quick Start

### Basic Usage

```python
import py7zz

# Create archive
py7zz.create_archive('backup.7z', ['documents/', 'photos/'])

# Extract archive
py7zz.extract_archive('backup.7z', 'extracted/')

# List contents
with py7zz.SevenZipFile('backup.7z', 'r') as sz:
    print(sz.namelist())
```

### Drop-in Replacement

```python
# OLD: zipfile
import zipfile
with zipfile.ZipFile('archive.zip', 'r') as zf:
    zf.extractall('output/')

# NEW: py7zz (identical API)
import py7zz
with py7zz.SevenZipFile('archive.7z', 'r') as sz:
    sz.extractall('output/')
```

### Async Operations

```python
import asyncio
import py7zz

async def main():
    await py7zz.create_archive_async('backup.7z', ['data/'])
    await py7zz.extract_archive_async('backup.7z', 'output/')

asyncio.run(main())
```

## API Reference

### Core Classes

#### `SevenZipFile(file, mode='r', preset=None)`

Main class for archive operations, compatible with `zipfile.ZipFile`.

**Parameters:**
- `file`: Path to archive
- `mode`: 'r' (read), 'w' (write), 'a' (append)
- `preset`: Compression preset ('fast', 'balanced', 'ultra')

**Methods:**
- `namelist()`: List all files
- `extractall(path, members)`: Extract files
- `add(name, arcname)`: Add file
- `read(name)`: Read file content
- `testzip()`: Test integrity

### Simple Functions

#### `create_archive(path, files, preset='balanced')`
Create archive from files.

#### `extract_archive(path, output_dir='.')`
Extract all files from archive.

#### `test_archive(path)`
Test archive integrity.

### Security Features

#### `SecurityConfig(max_file_count=5000, max_compression_ratio=100.0, max_total_size=10737418240)`
Configure security limits for archive processing.

#### `check_file_count_security(file_list, config=None)`
Check if archive file count exceeds security limits.

### Filename Utilities

#### `sanitize_filename(filename)`
Sanitize filename for Windows compatibility.

#### `is_valid_windows_filename(filename)`
Check if filename is valid on Windows.

#### `get_safe_filename(filename, existing_names=None)`
Get Windows-compatible filename with conflict resolution.

### Async API

#### `AsyncSevenZipFile`
Async version of SevenZipFile with identical methods.

#### `create_archive_async()`, `extract_archive_async()`
Async versions of simple functions.

### Configuration

#### Compression Presets
- `'fast'`: Quick compression
- `'balanced'`: Default
- `'ultra'`: Maximum compression

#### Logging
```python
py7zz.setup_logging('INFO')  # Configure logging
py7zz.disable_warnings()     # Hide warnings
```

### Exception Handling

py7zz provides specific exceptions for different error conditions:

```python
from py7zz.exceptions import (
    ZipBombError,           # Potential ZIP bomb detected
    SecurityError,          # Security limits exceeded
    PasswordRequiredError,  # Archive requires password
    FileNotFoundError,      # File or archive not found
    CorruptedArchiveError   # Archive is corrupted
)

try:
    py7zz.extract_archive('archive.7z')
except ZipBombError:
    print("Archive may be a ZIP bomb")
except PasswordRequiredError:
    print("Archive is password protected")
except CorruptedArchiveError:
    print("Archive is corrupted")
```

See [API Documentation](docs/API.md) for complete reference.

## Migration Guide

### From zipfile

```python
# Change import
import py7zz  # was: import zipfile

# Change class name
with py7zz.SevenZipFile('archive.7z', 'r') as sz:  # was: zipfile.ZipFile
    sz.extractall()  # Same API!
```

### From tarfile

```python
# Change import
import py7zz  # was: import tarfile

# Use same class
with py7zz.SevenZipFile('archive.tar.gz', 'r') as sz:  # was: tarfile.open
    sz.extractall()  # Same API!
```

See [Migration Guide](docs/MIGRATION.md) for detailed instructions.

## Supported Formats

| Format | Read | Write |
|--------|------|-------|
| 7Z | ✅ | ✅ |
| ZIP | ✅ | ✅ |
| TAR | ✅ | ✅ |
| RAR | ✅ | ❌ |
| GZIP | ✅ | ✅ |
| BZIP2 | ✅ | ✅ |
| XZ | ✅ | ✅ |

And 40+ more formats for reading.

## Advanced Features

### Security Protection

Built-in protection against malicious archives:

```python
from py7zz import SecurityConfig, ZipBombError

# Configure security limits
config = SecurityConfig(max_file_count=1000, max_compression_ratio=50.0)

try:
    py7zz.extract_archive('suspicious.zip')
except ZipBombError as e:
    print(f"Potential ZIP bomb detected: {e}")
```

### Windows Filename Compatibility

Automatically handles Windows restrictions and provides utilities:

```python
from py7zz import sanitize_filename, is_valid_windows_filename

# Auto-sanitization during extraction
py7zz.extract_archive('unix-archive.tar.gz')  # Files sanitized automatically

# Manual filename utilities
safe_name = sanitize_filename("invalid<file>name.txt")  # → "invalid_file_name.txt"
is_valid = is_valid_windows_filename("CON.txt")  # → False
```

### Progress Monitoring

```python
async def progress_callback(info):
    print(f"Progress: {info.percentage:.1f}%")

await py7zz.extract_archive_async('large.7z', progress_callback=progress_callback)
```

### Batch Operations

```python
archives = ['backup1.7z', 'backup2.7z', 'backup3.7z']
py7zz.batch_extract_archives(archives, 'output/')
```

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/rxchi1d/py7zz.git
cd py7zz

# Install dependencies
pip install -e .
```

### Testing

```bash
# Run tests
pytest

# Check code quality
ruff check .
mypy .
```

### Code Style

- Follow PEP 8
- Use type hints
- Maximum line length: 88
- Format with `ruff format`

## Requirements

- Python 3.8+
- No external dependencies
- Supported platforms:
  - Windows x64
  - macOS (Intel & Apple Silicon)
  - Linux x86_64

## Version Information

py7zz follows [PEP 440](https://peps.python.org/pep-0440/) versioning standard:

```python
import py7zz
print(py7zz.get_version())           # py7zz version (e.g., "1.0.0")
print(py7zz.get_bundled_7zz_version())  # 7zz version

# Version types supported:
# - Stable: 1.0.0
# - Alpha: 1.0.0a1
# - Beta: 1.0.0b1
# - Release Candidate: 1.0.0rc1
# - Development: 1.0.0.dev1
```

## Contributing

We welcome contributions! See [Contributing Guide](CONTRIBUTING.md) for:

- Development setup
- Code style guidelines
- Commit conventions
- Pull request process

## Support

- **Documentation**: [API Reference](docs/API.md)
- **Issues**: [GitHub Issues](https://github.com/rxchi1d/py7zz/issues)
- **Discussions**: [GitHub Discussions](https://github.com/rxchi1d/py7zz/discussions)

## License

Python source code: MIT (see LICENSE)
Bundled runtime: 7-Zip 7zz under its own licenses (LGPL v2.1 + unRAR; parts BSD).
See THIRD_PARTY_NOTICES.md and licenses/7zip-LICENSE.txt.

## Acknowledgments

Built on [7-Zip](https://www.7-zip.org/) by Igor Pavlov.

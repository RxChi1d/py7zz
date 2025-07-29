# py7zz

[![PyPI version](https://img.shields.io/pypi/v/py7zz.svg)](https://pypi.org/project/py7zz/)
[![Python versions](https://img.shields.io/pypi/pyversions/py7zz.svg)](https://pypi.org/project/py7zz/)
[![License](https://img.shields.io/pypi/l/py7zz.svg)](https://github.com/rxchi1d/py7zz/blob/main/LICENSE)
[![CI](https://github.com/rxchi1d/py7zz/workflows/CI/badge.svg)](https://github.com/rxchi1d/py7zz/actions)

A Python wrapper for the 7zz CLI tool, providing a consistent object-oriented interface across platforms (macOS, Linux, Windows) with automatic update mechanisms, Windows filename compatibility, and support for dozens of archive formats.

## Features

- **🔧 Industry Standard API Compatibility** - Complete `zipfile.ZipFile` and `tarfile.TarFile` API compatibility
- **🚀 5-Layer API Design** - From simple one-liners to expert-level control
- **⚡ Batch Operations** - Multiple archive operations, format conversion, comparison tools
- **📦 50+ archive formats** - ZIP, 7Z, RAR, TAR, GZIP, BZIP2, XZ, LZ4, ZSTD, and more
- **🌐 Cross-platform** - Works on macOS, Linux, and Windows
- **🔄 Async operations** - Non-blocking operations with progress reporting
- **🔒 Secure** - Bundled 7zz binaries, no system dependencies
- **🎯 Preset configurations** - Optimized compression settings for different use cases
- **⚙️ Global configuration management** - Persistent user preferences and configuration presets
- **🪟 Windows filename compatibility** - Automatic handling of Unix archive filenames on Windows
- **📊 Archive information** - Detailed metadata with compression ratios and file attributes
- **🛠️ Exception handling** - Structured error context with actionable suggestions
- **☁️ Cloud integration** - Streaming interface for S3/Azure Blob/GCS direct read/write
- **🔒 Thread-safe configuration** - Immutable config objects with context managers
- **📈 Structured progress callbacks** - Progress information with speed, timing, and metadata
- **📝 Logging integration** - Standard Python logging.getLogger("py7zz") hierarchy support

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

### Cloud Integration & Streaming

```python
import py7zz
import boto3  # for AWS S3 example

# Streaming interface for cloud services (io.BufferedIOBase compatible)
with py7zz.SevenZipFile('large_archive.7z', 'r') as sz:
    # Stream file directly to S3 without local disk
    with sz.open_stream('big_data.csv') as stream:
        s3_client = boto3.client('s3')
        s3_client.upload_fileobj(stream, 'my-bucket', 'data/big_data.csv')
    
    # Stream multiple files to cloud storage
    for member in sz.infolist():
        if member.filename.endswith('.log'):
            with sz.open_stream(member.filename) as stream:
                # Direct streaming to Azure Blob, GCS, etc.
                cloud_upload(stream, member.filename)

# Create archives with cloud streaming
with py7zz.SevenZipFile('cloud_backup.7z', 'w') as sz:
    # Stream data directly from cloud to archive
    with sz.open_stream_writer('backup_data.json') as writer:
        cloud_data = download_from_cloud('backup_data.json')
        writer.write(cloud_data)
```

### Thread-Safe Enterprise Configuration

```python
import py7zz
import threading

# Thread-safe global configuration management
def worker_thread(thread_id):
    # Each thread can safely access global config
    config = py7zz.ThreadSafeGlobalConfig.get_config()
    print(f"Thread {thread_id} using preset: {config.preset_name}")
    
    # Temporary configuration changes per thread
    with py7zz.ThreadSafeGlobalConfig.temporary_config(level=9, solid=False):
        # Operations in this context use the temporary config
        py7zz.create_archive(f'output_{thread_id}.7z', [f'data_{thread_id}/'])
    # Original config restored automatically

# Immutable configuration objects
config = py7zz.ImmutableConfig(
    level=7,
    compression="lzma2",
    solid=True,
    threads=4
)

# Safe to share across threads - cannot be modified
production_config = config.replace(level=9, preset_name="production")

# Context manager for preset-based operations
with py7zz.with_preset("ultra"):
    # All operations use ultra compression settings
    py7zz.create_archive('high_compression.7z', ['important_data/'])
```

### Advanced Progress Monitoring

```python
import py7zz

# Structured progress callbacks
def progress_callback(progress: py7zz.ProgressInfo):
    # Progress information structure
    print(f"Operation: {progress.operation_type.value}")
    print(f"Stage: {progress.operation_stage.value}")
    print(f"Progress: {progress.percentage:.2f}%")
    print(f"Speed: {progress.format_speed()}")
    print(f"ETA: {progress.format_time(progress.estimated_remaining)}")
    print(f"Current file: {progress.current_file}")
    print(f"Files: {progress.files_processed}/{progress.total_files}")
    
    # Custom metadata available
    if progress.metadata.get('custom_tracking_id'):
        print(f"Tracking ID: {progress.metadata['custom_tracking_id']}")

# Multiple callback styles available
py7zz.create_archive('data.7z', ['files/'], 
                    progress_callback=py7zz.create_callback("detailed"))
py7zz.create_archive('logs.7z', ['logs/'], 
                    progress_callback=py7zz.create_callback("json"))

# Manual progress tracking for custom operations
tracker = py7zz.ProgressTracker(
    operation_type=py7zz.OperationType.COMPRESS,
    callback=enterprise_progress_callback,
    total_bytes=1000000
)

# Update progress as operation proceeds
tracker.update(bytes_processed=250000, current_file="data1.txt")
tracker.update(bytes_processed=500000, current_file="data2.txt") 
tracker.complete()
```

### Enterprise Logging Integration

```python
import logging
import py7zz

# Standard Python logging integration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

# py7zz integrates with your logging hierarchy
logger = logging.getLogger('myapp.archiving')
logger.info("Starting archive operations")

# py7zz respects your logging configuration
py7zz.setup_logging("INFO", structured=True, performance_monitoring=True)

# File logging with rotation
py7zz.enable_file_logging('py7zz.log', max_size=10*1024*1024, backup_count=5)

# Structured JSON logging for analysis
py7zz.enable_structured_logging(True)

# Performance monitoring
with py7zz.PerformanceLogger("bulk_compression"):
    py7zz.batch_create_archives([
        ('backup1.7z', ['data1/']),
        ('backup2.7z', ['data2/']),
        ('backup3.7z', ['data3/'])
    ])
```

## API Overview

py7zz provides a **6-layer API architecture** designed for progressive complexity:

### Layer 1: Simple Function API (80% of use cases)
```python
# Basic operations - one-line solutions
py7zz.create_archive('backup.7z', ['files/'])
py7zz.extract_archive('backup.7z', 'output/')
py7zz.test_archive('backup.7z')

# Advanced convenience functions - power user operations
py7zz.batch_create_archives([
    ('docs.7z', ['documents/']),
    ('photos.7z', ['pictures/']),
    ('code.7z', ['projects/'])
])
py7zz.copy_archive('original.7z', 'backup.7z', recompress=True, preset='ultra')
py7zz.convert_archive_format('old.zip', 'new.7z')
py7zz.compare_archives('backup1.7z', 'backup2.7z')
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

# Global configuration management
py7zz.GlobalConfig.set_default_preset('ultra')
recommended = py7zz.GlobalConfig.get_smart_recommendation(
    ['documents/', 'photos/'], 
    usage_type='backup',
    priority='compression'
)

# Intelligent preset recommendations
analysis = py7zz.PresetRecommender.analyze_content(['project/'])
optimal_preset = py7zz.PresetRecommender.recommend_for_content(['mixed_data/'])
```

### Layer 4: Async API (concurrent operations)
```python
# Non-blocking operations with progress
await py7zz.batch_compress_async(
    [('backup1.7z', ['folder1/']), ('backup2.7z', ['folder2/'])],
    progress_callback=progress_handler
)

# Complete async SevenZipFile interface
async with py7zz.AsyncSevenZipFile('archive.7z', 'r') as asz:
    names = await asz.namelist()
    content = await asz.read('file.txt')
    await asz.extractall('output/', progress_callback=progress_handler)
```

### Layer 5: Expert API (direct 7zz access)
```python
# Direct 7zz command access for maximum flexibility
result = py7zz.run_7z(['a', 'archive.7z', 'files/', '-mx=9', '-ms=on'])
print(f"Exit code: {result.returncode}")
```

### Layer 6: Cloud Integration API
```python
# Cloud streaming interface
import py7zz
import boto3

# Thread-safe configuration management
with py7zz.ThreadSafeGlobalConfig.temporary_config(
    level=9,
    threads=8,
    preset_name="production_backup"
):
    # Streaming to cloud storage
    with py7zz.SevenZipFile('enterprise_backup.7z', 'w') as sz:
        # Stream data directly from S3 to archive
        s3_client = boto3.client('s3')
        
        with sz.open_stream_writer('data/large_dataset.csv') as writer:
            s3_obj = s3_client.get_object(Bucket='data-lake', Key='raw/dataset.csv')
            for chunk in s3_obj['Body'].iter_chunks(1024*1024):
                writer.write(chunk)

# Structured progress monitoring
def monitoring_callback(progress: py7zz.ProgressInfo):
    # Send metrics to monitoring system
    metrics.gauge('compression.progress', progress.percentage)
    metrics.gauge('compression.speed_mbps', progress.speed_bps / 1024 / 1024)
    
    # Log structured data for analysis
    logger.info("Compression progress", extra={
        'operation_id': progress.metadata.get('operation_id'),
        'stage': progress.operation_stage.value,
        'percentage': progress.percentage,
        'current_file': progress.current_file
    })

# Logging with performance monitoring
py7zz.setup_logging(
    "INFO",
    structured=True,
    performance_monitoring=True,
    log_file="/var/log/archiving/py7zz.log"
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
- **🚀 Additional Features** - Detailed compression info, improved error handling
- **🪟 Windows Compatibility** - Automatic filename sanitization for Unix archives
- **⚡ Async Support** - All methods available in async form

**📖 [Complete Migration Guide](docs/MIGRATION.md)** - Migration guide with examples, error handling patterns, and best practices.

## Advanced Features

py7zz includes features for production environments and cloud integration:

### Cloud Integration & Streaming Interface

Stream archives directly to/from cloud storage without local disk space:

```python
import py7zz
import boto3

# Stream files from archive directly to S3
with py7zz.SevenZipFile('backup.7z', 'r') as sz:
    with sz.open_stream('large_data.csv') as stream:
        # io.BufferedIOBase compatible - works with any cloud SDK
        s3_client.upload_fileobj(stream, 'my-bucket', 'data/large_data.csv')

# Create archives from cloud data streams
with py7zz.SevenZipFile('cloud_backup.7z', 'w') as sz:
    with sz.open_stream_writer('backup_data.json') as writer:
        # Stream directly from cloud to archive
        for chunk in cloud_data_stream():
            writer.write(chunk)
```

**Supported Cloud Services:**
- Amazon S3 (`boto3`)
- Azure Blob Storage (`azure-storage-blob`)
- Google Cloud Storage (`google-cloud-storage`)
- Any service supporting `io.BufferedIOBase`

### Thread-Safe Configuration Management

Safe concurrent access with immutable configuration objects:

```python
import py7zz
from concurrent.futures import ThreadPoolExecutor

# Thread-safe global configuration
py7zz.ThreadSafeGlobalConfig.set_config(
    py7zz.ImmutableConfig(level=7, threads=4, preset_name="production")
)

def worker_task(data_folder):
    # Each thread safely accesses global config
    config = py7zz.ThreadSafeGlobalConfig.get_config()
    
    # Temporary config changes per operation
    with py7zz.ThreadSafeGlobalConfig.temporary_config(level=9):
        py7zz.create_archive(f'{data_folder}.7z', [data_folder])

# Safe concurrent execution
with ThreadPoolExecutor(max_workers=8) as executor:
    tasks = [f'data_{i}' for i in range(20)]
    executor.map(worker_task, tasks)
```

### Structured Progress Monitoring

Rich progress information for monitoring and analytics:

```python
import py7zz

def monitoring_callback(progress: py7zz.ProgressInfo):
    # Rich structured progress data
    metrics = {
        'operation': progress.operation_type.value,
        'stage': progress.operation_stage.value,
        'percentage': progress.percentage,
        'speed_mbps': progress.speed_bps / 1024 / 1024 if progress.speed_bps else 0,
        'eta_seconds': progress.estimated_remaining,
        'files_processed': progress.files_processed,
        'current_file': progress.current_file
    }
    
    # Send to monitoring system (Prometheus, DataDog, etc.)
    send_metrics(metrics)
    
    # Structured logging for analysis
    logger.info("Archive progress", extra=metrics)

# Multiple callback styles for different needs
py7zz.create_archive('data.7z', ['files/'], 
                    progress_callback=py7zz.create_callback("json"))  # JSON output
py7zz.create_archive('logs.7z', ['logs/'], 
                    progress_callback=monitoring_callback)  # Custom monitoring
```

### Enhanced Logging Integration

Professional logging integration with Python's standard logging:

```python
import logging
import py7zz

# Standard Python logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# py7zz integrates seamlessly with your logging hierarchy
app_logger = logging.getLogger('myapp.archiving')
app_logger.info("Starting batch compression")

# Enterprise logging features
py7zz.setup_logging(
    level="INFO",
    structured=True,              # JSON structured logs
    performance_monitoring=True,  # Performance metrics
    log_file="py7zz.log",        # File logging with rotation
    max_file_size=50*1024*1024   # 50MB max file size
)

# Performance monitoring context manager
with py7zz.PerformanceLogger("batch_compression"):
    py7zz.batch_create_archives([
        ('backup1.7z', ['data1/']),
        ('backup2.7z', ['data2/']),
        ('backup3.7z', ['data3/'])
    ])
```

### Configuration Management

Persistent configuration with validation and presets:

```python
import py7zz

# Load/save user configuration
py7zz.ThreadSafeGlobalConfig.load_user_config()   # Load from ~/.config/py7zz/config.json
py7zz.ThreadSafeGlobalConfig.save_user_config()   # Save current config

# Enterprise preset management
enterprise_config = py7zz.ImmutableConfig(
    preset_name="production_backup",
    level=8,
    compression="lzma2",
    dictionary_size="128m",
    threads=None,  # Auto-detect
    solid=True
)

# Validate configuration
warnings = enterprise_config.validate()
if warnings:
    for warning in warnings:
        logger.warning(f"Config warning: {warning}")

# Apply configuration globally
py7zz.ThreadSafeGlobalConfig.set_config(enterprise_config)
```

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

py7zz 1.0+ provides a **unified exception handling system** with structured error context and actionable suggestions:

```python
import py7zz

try:
    py7zz.extract_archive('problematic.7z', 'output/')
except py7zz.ValidationError as e:
    print(f"Input validation error: {e}")
    # Get specific suggestions for fixing the input
    for suggestion in py7zz.get_error_suggestions(e):
        print(f"  Try: {suggestion}")
        
except py7zz.OperationError as e:
    print(f"Operation failed: {e}")
    # Get detailed error context
    context = e.get_detailed_info()
    print(f"Error context: {context['context']}")
    print(f"Suggestions: {context['suggestions']}")
    
except py7zz.FilenameCompatibilityError as e:
    print(f"Filename issues: {len(e.problematic_files)} files")
    if e.sanitized:
        print("✅ Files automatically renamed for Windows compatibility")
        
except py7zz.Py7zzError as e:
    # Enhanced base exception with full error analysis
    error_info = e.get_detailed_info()
    print(f"Error: {error_info['message']}")
    print(f"Type: {error_info['error_type']}")
    if error_info['suggestions']:
        print("Suggestions:")
        for suggestion in error_info['suggestions']:
            print(f"  - {suggestion}")
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
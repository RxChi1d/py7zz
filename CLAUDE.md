# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

py7zz is a Python package that wraps the official 7zz CLI tool, providing a consistent OOP interface across platforms (macOS, Debian-family Linux, Windows x64) with automatic update mechanisms. The project follows a "Vibe Coding" workflow emphasizing rapid iteration, CI/CD integration, and enforced code formatting.

**Project Vision**: Enable users to "pip install py7zz" and immediately compress/decompress dozens of formats without pre-installing 7-Zip, with the wheel containing platform-specific 7zz binaries.

## Development Commands

### Environment Setup
```bash
uv venv                    # Create virtual environment
source .venv/bin/activate  # Activate virtual environment (required for direct tool usage)

# Set development binary path (optional for development)
export PY7ZZ_BINARY=/opt/homebrew/bin/7zz  # macOS with Homebrew
# export PY7ZZ_BINARY=/usr/bin/7zz         # Linux systems
# export PY7ZZ_BINARY=/path/to/7zz.exe     # Windows systems
```

### Installation Methods

py7zz supports multiple installation methods to accommodate different use cases:

#### 1. Production Installation (Recommended)
```bash
pip install py7zz
```
- Includes bundled 7zz binary for version consistency
- No additional setup required
- Automatic binary detection and version pairing

#### 2. Development Installation (From Source)
```bash
# Clone repository and install in editable mode
git clone https://github.com/rxchi1d/py7zz.git
cd py7zz
pip install -e .
```
- Auto-downloads correct 7zz binary on first use
- Cached in ~/.cache/py7zz/ for offline use
- Ensures version consistency without system dependency

#### 3. Direct GitHub Installation
```bash
# Install latest development version
pip install git+https://github.com/rxchi1d/py7zz.git
```
- Installs directly from GitHub repository
- Auto-downloads correct 7zz binary on first use
- No need for local git clone or system 7zz

#### Binary Discovery Order (Hybrid Approach)
py7zz finds 7zz binary in this order:
1. **PY7ZZ_BINARY** environment variable (development/testing only)
2. **Bundled binary** (PyPI wheel packages)
3. **Auto-downloaded binary** (source installs - cached in ~/.cache/py7zz/)

**Key Features:**
- **Isolation**: Never uses system 7zz to avoid conflicts
- **Version consistency**: Each py7zz version paired with specific 7zz version
- **Automatic**: Source installs auto-download correct binary on first use
- **Caching**: Downloaded binaries cached for offline use

This ensures reliability, isolation, and version consistency across all installation methods.

### Dependency Management
**IMPORTANT**: All dependencies must be managed through `uv add` commands. Never manually edit `pyproject.toml` or use `uv pip install` directly.

```bash
# Runtime dependencies
uv add requests rich typer packaging

# Development dependencies  
uv add --dev pytest ruff mypy
```

### Core Development Loop
```bash
ruff check . --fix         # Style check and auto-fix (or uv run ruff check . --fix)
pytest -q                  # Run unit tests (or uv run pytest -q)
mypy .                     # Type checking (or uv run mypy .)
```

**Note**: Commands can be run directly if virtual environment is activated (`source .venv/bin/activate`), or prefixed with `uv run` if not activated.

### Code Formatting
```bash
uv run ruff format .       # Format code (use as pre-commit hook)
```

## Architecture

### Project Structure
```
py7zz/
├── __init__.py            # exports SevenZipFile, get_version
├── core.py                # subprocess glue, banner parsing
├── binaries/              # platform-specific 7zz binaries
│   ├── macos/7zz         # macOS binary
│   ├── linux/7zz         # Linux binary  
│   └── windows/7zz.exe   # Windows binary
├── updater.py             # GitHub API integration & auto-download for source installs
├── pyproject.toml         # build-system = "hatchling"
├── README.md
└── .github/workflows/
    ├── check.yml          # lint+test on push/PR
    ├── build.yml          # wheel matrix & publish on tag
    └── watch_release.yml  # nightly build automation
```

### Key Components
- **SevenZipFile**: Main API class similar to zipfile interface
- **core.run_7z()**: Subprocess wrapper for 7zz CLI execution
- **Binary resolution**: Hybrid approach with isolation and version consistency
- **Version consistency**: Each py7zz version is paired with a specific 7zz version for stability
- **Three-tier versioning**: Release (stable), Auto (basic stable), Dev (unstable)

### API Design

py7zz follows a **layered API design** to serve different user needs and skill levels:

#### Layer 1: Simple Function API (80% of use cases)
```python
import py7zz

# Simplest usage - one-line solutions
py7zz.create_archive("archive.7z", ["file1.txt", "folder/"])
py7zz.extract_archive("archive.7z", "output/")
py7zz.list_archive("archive.7z")

# Single data compression
compressed = py7zz.compress("Hello, World!")
decompressed = py7zz.decompress(compressed)
```

#### Layer 2: Compatibility API (Migration users)
```python
from py7zz import SevenZipFile

# Fully compatible with zipfile.ZipFile API
with SevenZipFile("archive.7z", "w") as sz:
    sz.add("file.txt")
    sz.writestr("data.txt", "content")

with SevenZipFile("archive.7z", "r") as sz:
    files = sz.namelist()
    content = sz.read("file.txt")
    sz.extractall("output/")
```

#### Layer 3: Advanced Control API (Power users)
```python
from py7zz import SevenZipFile

# Fine-grained control with presets
with SevenZipFile("archive.7z", "w", preset="ultra") as sz:
    sz.add("file.txt")

# Custom configuration
config = py7zz.Config(
    compression="lzma2",
    level=9,
    solid=True,
    threads=4,
    password="secret"
)
py7zz.create_archive("archive.7z", files, config=config)
```

#### Layer 4: Native 7zz API (Expert users)
```python
from py7zz import run_7z

# Direct 7zz command access
result = run_7z(["a", "-mx9", "-mhe", "archive.7z", "file.txt"])

# Or use CLI: 7zz a -mx9 -mhe archive.7z file.txt
```

#### Design Principles
1. **Progressive Complexity**: Simple → Standard → Advanced → Expert
2. **Smart Defaults**: Automatic optimal settings based on usage patterns
3. **Format Transparency**: Auto-detect format from file extension
4. **Migration Friendly**: Minimal code changes from zipfile/tarfile
5. **Error Handling**: Clear, actionable error messages

#### Preset Configurations
```python
# Built-in presets for common scenarios
py7zz.create_archive("backup.7z", files, preset="backup")      # High compression, solid
py7zz.create_archive("temp.7z", files, preset="fast")          # Fast compression
py7zz.create_archive("distribution.7z", files, preset="balanced") # Balanced speed/size
```

## CI/CD Pipeline

### GitHub Actions Workflows
1. **check.yml**: Runs on push/PR - executes ruff, pytest, mypy (PR gate)
2. **build.yml**: Triggered on tag push - builds wheels for all platforms with matrix builds
3. **watch_release.yml**: Daily check (cron: "0 3 * * *") for new 7zz releases, creates auto builds for testing

### Three-Tier Version System
- **🟢 Release** (`1.0.0+7zz24.07`): Stable, manually released, production-ready
- **🟡 Auto** (`1.0.0.auto+7zz24.08`): Basic stable, auto-released when 7zz updates
- **🔴 Dev** (`1.1.0-dev.1+7zz24.07`): Unstable, manually released for testing new features

### Code Quality Requirements
- **Ruff**: Enforced code style with line-length=120, select=["E", "F", "I", "UP", "B"]
- **MyPy**: Type checking required for all code
- **Pytest**: Unit tests must pass before merge
- All checks must pass in CI before PR merge

## Development Notes

- Project uses `uv` for dependency management exclusively
- Binary distribution includes platform-specific 7zz executables downloaded from GitHub releases
- Nightly builds automatically created when new 7zz releases are detected
- Cross-platform compatibility: macOS, Debian-family Linux, Windows x64
- License: BSD-3 + LGPL 2.1 (preserving 7-Zip license)

## Build System

### Binary Distribution
- CI downloads platform-specific assets (`7z{ver}-{os}-{arch}.tar.xz`)
- Verifies SHA256 checksums
- Extracts to `binaries/<platform>/7zz[.exe]`
- Packages in wheel for distribution

### Version Management
- Each py7zz version is paired with a specific 7zz version for consistency
- No runtime auto-updates - users must upgrade the entire py7zz package
- Nightly builds available for testing new 7zz releases before official release
- Official releases require manual testing and approval

## Milestones

The project follows a structured development plan:
- **M1**: Repository setup, basic API, manual binary download (3 days)
- **M2**: Cross-platform wheel builds, CI setup (4 days)
- **M3**: GitHub API integration, nightly build automation (3 days)
- **M4**: Async operations, progress reporting (3 days)
- **M5**: Documentation, type hints, PyPI release (2 days)
  - Create MIGRATION.md for zipfile/tarfile users
  - Add migration guide link to README.md
  - Complete API documentation and examples
  - Finalize type hints and docstrings
  - Prepare for PyPI release

**Total estimated time: 15 working days**

## Binary Management & Installation Strategy

### Hybrid Binary Distribution Approach

py7zz implements a hybrid approach to ensure **isolation** and **version consistency**:

#### Design Principles
1. **Never use system 7zz** - Avoids version conflicts and ensures reproducible behavior
2. **Version pairing** - Each py7zz version is paired with a specific 7zz version
3. **Automatic handling** - Users don't need to manually install or configure 7zz
4. **Offline capability** - Downloaded binaries are cached for offline use

#### Implementation Strategy

**PyPI Wheel Distribution (Production)**:
- Uses GitHub Actions to download 7zz binaries from https://github.com/ip7z/7zip/releases
- Embeds platform-specific binaries in wheel packages
- Users get bundled binary with `pip install py7zz`
- No internet connection required after installation

**Source Installation (Development)**:
- Empty `py7zz/binaries/` directory in git repository
- Auto-downloads correct 7zz binary on first use via `updater.py`
- Caches in `~/.cache/py7zz/{version}/` directory
- Requires internet connection for first use only

#### Binary Discovery Priority
```python
def find_7z_binary() -> str:
    # 1. Environment variable (development/testing only)
    if PY7ZZ_BINARY and exists: return PY7ZZ_BINARY
    
    # 2. Bundled binary (PyPI wheel packages)
    if bundled_binary and exists: return bundled_binary
    
    # 3. Auto-downloaded binary (source installs)
    if auto_download_successful: return cached_binary
    
    # 4. Error - no system fallback
    raise RuntimeError("7zz binary not found")
```

#### Version Consistency Mechanism
- `version.py` defines: `PY7ZZ_VERSION = "1.0.0"` and `SEVEN_ZZ_VERSION = "24.07"`
- Full version: `1.0.0+7zz24.07`
- Auto-download uses `get_7zz_version()` to ensure correct binary version
- Asset naming: `24.07` → `2407` for GitHub release URLs

#### Cache Management
- Location: `~/.cache/py7zz/{version}/7zz[.exe]`
- Automatic cleanup via `updater.cleanup_old_versions()`
- Preserved across py7zz reinstalls
- Platform-specific binary extraction from tar.xz/exe files

### Configuration Requirements

#### pyproject.toml Binary Inclusion
```toml
[tool.hatch.build.targets.wheel]
packages = ["py7zz"]
include = [
    "py7zz/binaries/**/*",
]

[tool.hatch.build.targets.wheel.force-include]
"py7zz/binaries" = "py7zz/binaries"
```

#### GitHub Actions Binary Download
```yaml
# .github/workflows/build.yml
- name: Download 7zz binary
  run: |
    VERSION="${{ steps.get_version.outputs.version }}"
    DOWNLOAD_URL="https://github.com/ip7z/7zip/releases/download/${VERSION}/7z${VERSION}-${PLATFORM}.tar.xz"
    mkdir -p "py7zz/binaries/${PLATFORM}"
    curl -L -o "/tmp/asset.tar.xz" "$DOWNLOAD_URL"
    tar -xf "/tmp/asset.tar.xz" -C "/tmp"
    find /tmp -name "7zz" -exec cp {} "py7zz/binaries/${PLATFORM}/" \;
    chmod +x "py7zz/binaries/${PLATFORM}/7zz"
```

#### Error Handling & Fallbacks
```python
# core.py - No system fallback
raise RuntimeError(
    "7zz binary not found. Please either:\n"
    "1. Install py7zz from PyPI (pip install py7zz) to get bundled binary\n"
    "2. Ensure internet connection for auto-download (source installs)\n"
    "3. Set PY7ZZ_BINARY environment variable to point to your 7zz binary"
)
```

### Testing Requirements

#### Installation Method Testing
- Test PyPI wheel installation with bundled binary
- Test source installation with auto-download
- Test environment variable override
- Test offline functionality after cache population
- Test version consistency across installation methods

#### Binary Verification
- Verify binary executability: `7zz --help`
- Verify version matching: parse output for version string
- Verify platform compatibility: correct architecture
- Verify cache persistence across sessions

This hybrid approach ensures py7zz works reliably across all installation methods while maintaining strict version control and system isolation.
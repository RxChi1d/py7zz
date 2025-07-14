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

# Set development binary path (required for development)
export PY7ZZ_BINARY=/opt/homebrew/bin/7zz  # macOS with Homebrew
# export PY7ZZ_BINARY=/usr/bin/7zz         # Linux systems
# export PY7ZZ_BINARY=/path/to/7zz.exe     # Windows systems
```

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
├── updater.py             # GitHub API integration (used by CI only)
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
- **Binary resolution**: 1) `PY7ZZ_BINARY` env var → 2) bundled binary (wheel package)
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
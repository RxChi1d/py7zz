# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

py7zz is a Python package that wraps the official 7zz CLI tool, providing a consistent OOP interface across platforms (macOS, Debian-family Linux, Windows x64) with automatic update mechanisms. The project follows a "Vibe Coding" workflow emphasizing rapid iteration, CI/CD integration, and enforced code formatting.

**Project Vision**: Enable users to "pip install py7zz" and immediately compress/decompress dozens of formats without pre-installing 7-Zip, with the wheel containing platform-specific 7zz binaries.

## Development Commands

### Environment Setup
```bash
uv venv                    # Create virtual environment
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
ruff check . --fix         # Style check and auto-fix
pytest -q                  # Run unit tests
mypy .                     # Type checking
```

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
├── updater.py             # fetch & cache latest 7zz releases
├── pyproject.toml         # build-system = "hatchling"
├── README.md
└── .github/workflows/
    ├── check.yml          # lint+test on push/PR
    ├── build.yml          # wheel matrix & publish on tag
    └── watch_release.yml  # nightly release-watcher
```

### Key Components
- **SevenZipFile**: Main API class similar to zipfile interface
- **core.run_7z()**: Subprocess wrapper for 7zz CLI execution
- **updater.check()**: GitHub API integration for automatic updates
- **Binary resolution**: 1) `SEVENZIP_BINARY` env var → 2) `shutil.which("7zz")` → 3) bundled binary

### API Design
```python
from py7zz import SevenZipFile

# Create archive
with SevenZipFile("archive.7z", "w", level="ultra") as z:
    z.add("src/")
    z.add("README.md")

# Extract archive
SevenZipFile("archive.7z").extract("./out", overwrite=True)
```

## CI/CD Pipeline

### GitHub Actions Workflows
1. **check.yml**: Runs on push/PR - executes ruff, pytest, mypy (PR gate)
2. **build.yml**: Triggered on tag push - builds wheels for all platforms with matrix builds
3. **watch_release.yml**: Daily check (cron: "0 3 * * *") for new 7zz releases from https://github.com/ip7z/7zip/releases, auto-publishes updates

### Code Quality Requirements
- **Ruff**: Enforced code style with line-length=120, select=["E", "F", "I", "UP", "B"]
- **MyPy**: Type checking required for all code
- **Pytest**: Unit tests must pass before merge
- All checks must pass in CI before PR merge

## Development Notes

- Project uses `uv` for dependency management exclusively
- Binary distribution includes platform-specific 7zz executables downloaded from GitHub releases
- Automatic updates via GitHub API monitoring ip7z/7zip releases with 7-day rotation
- Cross-platform compatibility: macOS, Debian-family Linux, Windows x64
- License: BSD-3 + LGPL 2.1 (preserving 7-Zip license)

## Build System

### Binary Distribution
- CI downloads platform-specific assets (`7z{ver}-{os}-{arch}.tar.xz`)
- Verifies SHA256 checksums
- Extracts to `binaries/<platform>/7zz[.exe]`
- Packages in wheel for distribution

### Self-Update Mechanism
- `updater.check()` calls GitHub REST API
- Downloads new versions to `~/.cache/py7zz/<ver>`
- Can be disabled with `auto_update=False`
- Results cached for 24 hours

## Milestones

The project follows a structured development plan:
- **M1**: Repository setup, basic API, manual binary download (3 days)
- **M2**: Cross-platform wheel builds, CI setup (4 days)
- **M3**: Auto-update module, release watching (3 days)
- **M4**: Async operations, progress reporting (3 days)
- **M5**: Documentation, type hints, PyPI release (2 days)

**Total estimated time: 15 working days**
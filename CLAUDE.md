# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

py7zz is a Python package that wraps the official 7zz CLI tool, providing a consistent OOP interface across platforms (macOS, Linux, Windows) with automatic update mechanisms. The project follows a "Vibe Coding" workflow emphasizing rapid iteration, CI/CD integration, and enforced code formatting.

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

### Planned Project Structure
```
py7zz/
├── __init__.py            # exports SevenZipFile, get_version
├── core.py                # subprocess glue, banner parsing
├── binaries/              # platform-specific 7zz binaries
├── updater.py             # fetch & cache latest 7zz releases
├── pyproject.toml         # build-system = "hatchling"
└── .github/workflows/
    ├── check.yml          # lint+test on push/PR
    ├── build.yml          # wheel matrix & publish on tag
    └── watch_release.yml  # nightly release-watcher
```

### Key Components
- **SevenZipFile**: Main API class similar to zipfile interface
- **core.run_7z()**: Subprocess wrapper for 7zz CLI execution
- **updater.check()**: GitHub API integration for automatic updates
- **Binary resolution**: Environment var → system PATH → bundled binary

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
1. **check.yml**: Runs on push/PR - executes ruff, pytest, mypy
2. **build.yml**: Triggered on tag push - builds wheels for all platforms
3. **watch_release.yml**: Daily check for new 7zz releases, auto-publishes updates

### Code Quality Requirements
- **Ruff**: Enforced code style with line-length=120, select=["E", "F", "I", "UP", "B"]
- **MyPy**: Type checking required for all code
- **Pytest**: Unit tests must pass before merge
- All checks must pass in CI before PR merge

## Development Notes

- Project uses `uv` for dependency management exclusively
- Binary distribution includes platform-specific 7zz executables
- Automatic updates via GitHub API monitoring ip7z/7zip releases
- Cross-platform compatibility is a core requirement
- License: BSD-3 + LGPL 2.1 (preserving 7-Zip license)

## Milestones

The project follows a structured development plan:
- **M1**: Repository setup, basic API, manual binary download
- **M2**: Cross-platform wheel builds, CI setup
- **M3**: Auto-update module, release watching
- **M4**: Async operations, progress reporting
- **M5**: Documentation, type hints, PyPI release
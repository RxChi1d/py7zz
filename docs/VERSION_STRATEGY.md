# Version Strategy

This document describes py7zz's versioning strategy and release process.

## Table of Contents

- [Overview](#overview)
- [Version Format](#version-format)
- [Release Types](#release-types)
- [Version Lifecycle](#version-lifecycle)
- [Implementation](#implementation)
- [User Guide](#user-guide)

## Overview

py7zz uses [PEP 440](https://www.python.org/dev/peps/pep-0440/) compliant versioning with a three-tier stability system:

1. **Release** - Stable production releases
2. **Auto** - Automated 7zz binary updates
3. **Dev** - Development builds for testing

## Version Format

### Release Versions (Stable)
- **Format:** `{major}.{minor}.{patch}`
- **Example:** `1.0.0`, `1.2.3`
- **Stability:** Production-ready

### Auto Versions (Alpha)
- **Format:** `{major}.{minor}.{patch}a{N}`
- **Example:** `1.0.0a1`, `1.0.0a2`
- **Stability:** Stable with updated 7zz binary

### Dev Versions (Development)
- **Format:** `{major}.{minor}.{patch}.dev{N}`
- **Example:** `1.1.0.dev1`, `2.0.0.dev1`
- **Stability:** Unstable, for testing only

## Release Types

### 🟢 Release (Most Stable)

**Characteristics:**
- Manual release process
- Full testing and validation
- Human review and approval
- Production recommended

**When to use:**
- Production environments
- Critical applications
- Long-term stability needed

### 🟡 Auto (Basic Stable)

**Characteristics:**
- Automated release when 7zz updates
- Only binary update, no code changes
- Basic automated testing
- Early access to new 7zz features

**When to use:**
- Need latest 7zz features
- Non-critical environments
- Testing new formats

### 🔴 Dev (Unstable)

**Characteristics:**
- Manual release for new features
- May contain breaking changes
- Limited testing
- Preview of upcoming features

**When to use:**
- Testing new py7zz features
- Development environments only
- Contributing to py7zz

## Version Lifecycle

```
1.0.0 (Release) → 1.0.0a1 (Auto) → 1.0.0a2 (Auto) → 1.1.0.dev1 (Dev) → 1.1.0 (Release)
```

### Example Timeline

1. **v1.0.0** - Released with 7zz 24.07
2. **v1.0.0a1** - Auto-released when 7zz 24.08 available
3. **v1.0.0a2** - Auto-released when 7zz 24.09 available
4. **v1.1.0.dev1** - Dev release with new py7zz features
5. **v1.1.0** - Next stable release

## Implementation

### Version Information

```python
# Get version information
import py7zz

print(py7zz.get_version())              # '1.0.0'
print(py7zz.get_bundled_7zz_version())  # '24.07'
print(py7zz.get_version_type())         # 'stable'
print(py7zz.get_version_info())         # Complete details
```

### Version Registry

Each version tracks:
- py7zz version number
- Bundled 7zz version
- Release date
- Release type
- GitHub tag
- Changelog URL

### Automation

**Auto Release Process:**
1. GitHub Actions monitors 7zz releases
2. New 7zz release triggers auto build
3. Alpha version created automatically
4. Published to PyPI with pre-release flag

## User Guide

### Installation

#### Latest Stable
```bash
pip install py7zz
```

#### Specific Version
```bash
# Stable release
pip install py7zz==1.0.0

# Auto release
pip install py7zz==1.0.0a1

# Dev release
pip install py7zz==1.1.0.dev1
```

#### Pre-release Versions
```bash
# Include pre-releases
pip install --pre py7zz
```

### Version Selection

| Need | Recommended | Command |
|------|-------------|---------|
| Production stability | Release | `pip install py7zz` |
| Latest 7zz features | Auto | `pip install py7zz==1.0.0a1` |
| Test new features | Dev | `pip install py7zz==1.1.0.dev1` |

### Checking Versions

#### Python API
```python
import py7zz

# Basic version check
version = py7zz.get_version()
if py7zz.is_stable_version():
    print("Running stable version")

# Detailed information
info = py7zz.get_version_info()
print(f"py7zz: {info['py7zz_version']}")
print(f"7zz: {info['bundled_7zz_version']}")
print(f"Type: {info['release_type']}")
```

#### Command Line
```bash
# Version information
py7zz version
py7zz version --format json

# Quick version check
py7zz --version
py7zz -V
```

### Upgrade Strategy

#### Conservative (Recommended)
```bash
# Only stable releases
pip install --upgrade py7zz
```

#### Balanced
```bash
# Include alpha releases
pip install --upgrade --pre py7zz
```

#### Bleeding Edge
```bash
# Latest from GitHub
pip install --upgrade git+https://github.com/rxchi1d/py7zz.git
```

## Best Practices

### For Users

1. **Production:** Use only stable releases
2. **Testing:** Use auto releases for new 7zz features
3. **Development:** Use dev releases to preview features

### For Contributors

1. **Version Bumping:** Follow semantic versioning
2. **Changelog:** Update for all releases
3. **Testing:** Ensure CI passes before release

### Version Pinning

#### requirements.txt
```txt
# Pin to specific stable version
py7zz==1.0.0

# Allow patch updates
py7zz~=1.0.0

# Allow minor updates
py7zz>=1.0.0,<2.0.0
```

#### pyproject.toml
```toml
[project]
dependencies = [
    "py7zz>=1.0.0",  # Minimum version
    "py7zz~=1.0.0",  # Compatible release
]
```

## Migration Notes

### From Legacy Versions

Old format (pre-1.0):
```
1.0.0+7zz24.07      # No longer used
1.0.0.auto+7zz24.08 # No longer used
```

New format (1.0+):
```
1.0.0     # Stable
1.0.0a1   # Auto
1.0.0.dev1 # Dev
```

### Breaking Changes

Breaking changes only in:
- Major version updates (1.x → 2.x)
- Dev releases (clearly marked)

## Monitoring Updates

### GitHub Releases
- Watch repository for releases
- Subscribe to release notifications
- Check [Releases](https://github.com/rxchi1d/py7zz/releases)

### PyPI
- Check [PyPI page](https://pypi.org/project/py7zz/)
- Use `pip list --outdated`

### Changelog
- Each release includes changelog
- Details in GitHub release notes
- Breaking changes clearly marked

## Summary

py7zz's three-tier version system provides:
- **Stability** with release versions
- **Currency** with auto versions
- **Innovation** with dev versions

Choose the right version for your needs!
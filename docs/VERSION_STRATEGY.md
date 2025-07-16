# py7zz PEP 440 Compliant Version Control Strategy

## Overview

py7zz adopts a PEP 440 compliant version management strategy to ensure compatibility with PyPI and provide users with clear version stability levels. This strategy maintains the original three-tier stability concept while conforming to Python packaging standards.

## Version Categories and Stability

### 🟢 **Release (Stable)** - Most Stable
- **Format:** `{major}.{minor}.{patch}`
- **Example:** `1.0.0`
- **Stability:** Most stable, fully tested
- **Release Method:** Manual release with human review and testing
- **Use Case:** Recommended for production environments

### 🟡 **Auto (Alpha)** - Automated 7zz Updates
- **Format:** `{major}.{minor}.{patch}a{N}`
- **Example:** `1.0.0a1`, `1.0.0a2`
- **Stability:** Basic stable, only 7zz binary updates
- **Release Method:** Automatic release when 7zz has new versions
- **Use Case:** Users who need latest 7zz features but don't want to wait for official releases

### 🔴 **Dev (Development)** - Development Builds
- **Format:** `{major}.{minor}.{patch}.dev{N}`
- **Example:** `1.1.0.dev1`, `1.1.0.dev2`
- **Stability:** Unstable, contains py7zz features under development
- **Release Method:** Manual release for testing new features
- **Use Case:** Developers and early testers

## Version Upgrade Path

```
Release 1.0.0 (bundled 7zz 24.07)
    ↓ (7zz updates to 24.08)
Auto 1.0.0a1 (bundled 7zz 24.08)  ← Automatic release
    ↓ (7zz updates to 24.09)
Auto 1.0.0a2 (bundled 7zz 24.09)  ← Automatic release
    ↓ (py7zz new feature development)
Dev 1.1.0.dev1 (bundled 7zz 24.09)     ← Manual release
    ↓ (Testing complete, ready for official release)
Release 1.1.0 (bundled 7zz 24.09)     ← Manual release
```

## Version Management Implementation

### 1. Version Information Storage

```python
# py7zz/version.py
__version__ = "1.0.0"

# py7zz/bundled_info.py
VERSION_REGISTRY = {
    "1.0.0": {
        "7zz_version": "24.07",
        "release_date": "2024-07-15",
        "release_type": "stable",
        "github_tag": "v1.0.0",
        "changelog_url": "https://github.com/rxchi1d/py7zz/releases/tag/v1.0.0"
    },
    "1.0.0a1": {
        "7zz_version": "24.08",
        "release_date": "2024-08-15",
        "release_type": "auto",
        "github_tag": "v1.0.0a1",
        "changelog_url": "https://github.com/rxchi1d/py7zz/releases/tag/v1.0.0a1"
    },
    "1.1.0.dev1": {
        "7zz_version": "24.08",
        "release_date": "2024-08-20",
        "release_type": "dev",
        "github_tag": "v1.1.0.dev1",
        "changelog_url": "https://github.com/rxchi1d/py7zz/releases/tag/v1.1.0.dev1"
    }
}
```

### 2. Version Information API

```python
# Get comprehensive version information
def get_version_info():
    return {
        "py7zz_version": __version__,
        "bundled_7zz_version": info.get("7zz_version", "unknown"),
        "release_type": info.get("release_type", "unknown"),
        "release_date": info.get("release_date", "unknown"),
        "github_tag": info.get("github_tag", f"v{__version__}"),
        "changelog_url": info.get("changelog_url", f"https://github.com/rxchi1d/py7zz/releases/tag/v{__version__}")
    }
```

### 3. CI/CD Integration

#### GitHub Release Tags
- **Stable**: `v1.0.0`
- **Auto**: `v1.0.0a1`
- **Dev**: `v1.1.0.dev1`

#### Build Workflow
- `build.yml` parses PEP 440 version tags
- Automatic binary download and wheel building
- PyPI publishing for tagged releases

#### Watch Release Workflow
- `watch_release.yml` monitors 7zz releases
- Automatically creates alpha versions for new 7zz releases
- Creates GitHub releases with appropriate pre-release flags

## User Experience

### Installation Commands
```bash
# Install latest stable version
pip install py7zz

# Install specific version
pip install py7zz==1.0.0a1

# Install from specific tag
pip install git+https://github.com/rxchi1d/py7zz.git@v1.0.0a1
```

### Version Information Access
```python
# Python API
import py7zz
print(py7zz.get_version())                    # Current version
print(py7zz.get_bundled_7zz_version())        # Bundled 7zz version
print(py7zz.get_version_info())               # Complete details

# CLI
py7zz version                    # Human-readable format
py7zz version --format json     # JSON format
```

### CLI Usage
```bash
# Version information
py7zz version
py7zz --py7zz-version
py7zz -V

# Direct 7zz operations (pass-through)
py7zz a archive.7z files/
py7zz x archive.7z
py7zz l archive.7z
```

## Advantages of PEP 440 Compliance

1. **Standard Compliance**: Fully compliant with PEP 440 and PyPI requirements
2. **Unified Versioning**: GitHub Release and PyPI versions are identical
3. **Stability Logic**: Maintains original three-tier stability architecture
4. **Automation Support**: Enables automatic 7zz version updates
5. **Tool Compatibility**: Works with all Python packaging tools
6. **User Clarity**: Clear version types and upgrade paths

## Migration from Legacy Format

### Legacy Format (Deprecated)
```
1.0.0+7zz24.07        # Release
1.0.0.auto+7zz24.08   # Auto
1.1.0-dev.1+7zz24.07  # Dev
```

### New PEP 440 Format
```
1.0.0        # Release
1.0.0a1      # Auto (alpha)
1.1.0.dev1   # Dev
```

### Key Changes
- Removed `+7zz{version}` suffix (causes PyPI rejection)
- 7zz version tracking moved to `VERSION_REGISTRY`
- Unified version format across all platforms
- Enhanced version information API

## Implementation Steps

1. **Update Version Files**: Modified `version.py` and created `bundled_info.py`
2. **Update CI/CD**: Modified workflows to support PEP 440 tags
3. **Update Documentation**: Updated all references to new version format
4. **Update CLI**: Enhanced version commands and changed entry point
5. **Testing**: Comprehensive testing of all version scenarios

This strategy ensures py7zz remains compliant with Python packaging standards while maintaining its unique three-tier stability system and automatic 7zz update capabilities.
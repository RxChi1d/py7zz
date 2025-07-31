# py7zz PEP 440 Compliant Version Control Strategy

## Overview

py7zz adopts a PEP 440 compliant version management strategy with **manual version control**. Only project authors can create Git tags to trigger releases, ensuring full control over version numbering and release timing while maintaining compatibility with PyPI standards.

## Version Categories and Release Types

### 🟢 **Stable Release** - Production Ready
- **Git Tag Format:** `vX.Y.Z`
- **PyPI Version:** `X.Y.Z`
- **Example:** `v1.0.0` → `1.0.0`
- **Stability:** Most stable, fully tested
- **Release Method:** Manual Git tag by project author
- **Source Requirement:** Must originate from `main` branch ancestry
- **Use Case:** Recommended for production environments

### 🟡 **Alpha Pre-release** - Early Testing
- **Git Tag Format:** `vX.Y.ZaN`
- **PyPI Version:** `X.Y.ZaN`
- **Example:** `v1.1.0a1` → `1.1.0a1`
- **Stability:** Pre-release with new features
- **Release Method:** Manual Git tag by project author
- **Source Requirement:** Can originate from any branch
- **Use Case:** Early testing of new features

### 🟠 **Beta Pre-release** - Feature Complete
- **Git Tag Format:** `vX.Y.ZbN`
- **PyPI Version:** `X.Y.ZbN`
- **Example:** `v1.1.0b1` → `1.1.0b1`
- **Stability:** Feature complete, bug fixing phase
- **Release Method:** Manual Git tag by project author
- **Source Requirement:** Can originate from any branch
- **Use Case:** Feature testing and feedback collection

### 🔴 **Release Candidate** - Near Stable
- **Git Tag Format:** `vX.Y.ZrcN`
- **PyPI Version:** `X.Y.ZrcN`
- **Example:** `v1.1.0rc1` → `1.1.0rc1`
- **Stability:** Release candidate, minimal changes expected
- **Release Method:** Manual Git tag by project author
- **Source Requirement:** Can originate from any branch
- **Use Case:** Final validation before stable release

## Version Upgrade Path

```
Stable 1.0.0    ← Manual release (from main branch)
    ↓ (Feature development begins)
Alpha 1.1.0a1   ← Manual release (from feature branch)
    ↓ (More development)
Alpha 1.1.0a2   ← Manual release (additional features)
    ↓ (Feature complete)
Beta 1.1.0b1    ← Manual release (feature freeze)
    ↓ (Bug fixes)
RC 1.1.0rc1     ← Manual release (release candidate)
    ↓ (Final validation)
Stable 1.1.0    ← Manual release (from main branch)
```

**Key Points:**
- All versions are manually controlled by project authors
- Stable releases must come from main branch ancestry
- Pre-releases can come from any branch
- No automatic version bumping or 7zz version tracking

## Version Management Implementation

### 1. Dynamic Version from Git Tags

py7zz uses **hatch-vcs** for dynamic version generation from Git tags:

```toml
# pyproject.toml
[tool.hatch.version]
source = "vcs"

[tool.hatch.version.raw-options]
git_describe_command = "git describe --tags --match='v*'"
local_scheme = "no-local-version"
```

### 2. Single Source of Truth

- **Git Tags**: The only source of version information
- **No hardcoded versions**: All versions derived from Git tags
- **PyPI Compatibility**: Automatic PEP 440 compliance
- **Build-time Resolution**: Version determined during wheel building

### 3. Version Information API

```python
# Get version information
def get_version():
    """Get current py7zz version."""
    return __version__

def get_version_info():
    """Get comprehensive version details."""
    return {
        "py7zz_version": __version__,
        "bundled_7zz_version": "25.00",  # Hardcoded for stability
        "github_tag": f"v{__version__}",
        "changelog_url": f"https://github.com/rxchi1d/py7zz/releases/tag/v{__version__}"
    }
```

### 4. CI/CD Integration

#### Supported Git Tag Formats
- **Stable**: `v1.0.0`
- **Alpha**: `v1.1.0a1`
- **Beta**: `v1.1.0b1`
- **RC**: `v1.1.0rc1`

#### Build Workflow (`.github/workflows/build.yml`)
- Validates PEP 440 tag format
- Enforces main branch ancestry for stable releases
- Builds cross-platform wheels with embedded 7zz binary
- Publishes to PyPI with correct pre-release flags
- Creates GitHub releases with auto-generated notes

#### Release Notes Generation
- **Stable releases**: Use Release Drafter based on PR titles
- **Pre-releases**: Auto-generate from commit history
- **Categorization**: Follows Conventional Commits format

## User Experience

### Installation Commands
```bash
# Install latest stable version
pip install py7zz

# Install specific stable version
pip install py7zz==1.2.0

# Install pre-release version
pip install py7zz==1.3.0a1

# Install from specific Git tag
pip install git+https://github.com/rxchi1d/py7zz.git@v1.2.0
```

### Version Information Access
```python
# Python API
import py7zz
print(py7zz.get_version())          # Current version
print(py7zz.get_version_info())     # Complete details

# CLI
py7zz --version                     # Version information
py7zz version                       # Detailed version info
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

## Advantages of Manual PEP 440 Compliance

1. **Standard Compliance**: Fully compliant with PEP 440 and PyPI requirements
2. **Unified Versioning**: GitHub Release and PyPI versions are identical
3. **Quality Control**: Manual releases ensure proper testing and validation
4. **Branch Flexibility**: Pre-releases can come from feature branches
5. **Tool Compatibility**: Works with all Python packaging tools
6. **Clear Stability**: PyPI automatically handles pre-release vs stable classification

## Release Process

### For Project Authors

#### Creating a Stable Release
```bash
# Ensure you're on main branch
git checkout main
git pull origin main

# Create and push tag
git tag v1.2.0
git push origin v1.2.0
```

#### Creating a Pre-release
```bash
# Can be on any branch
git tag v1.3.0a1
git push origin v1.3.0a1
```

### Automated Workflow
1. **Tag Creation**: Project author creates Git tag
2. **Validation**: Build workflow validates tag format
3. **Ancestry Check**: Stable releases verified against main branch
4. **Building**: Cross-platform wheels built with 7zz binary
5. **Publishing**: Automatic PyPI and GitHub release
6. **Release Notes**: Auto-generated based on release type

## Key Features

- **Manual Control**: Only project authors can trigger releases
- **PEP 440 Compliance**: Full compatibility with PyPI standards
- **Branch Flexibility**: Pre-releases from any branch, stable from main
- **Automatic Validation**: Build workflow enforces format and ancestry rules
- **Unified Releases**: GitHub and PyPI releases created simultaneously
- **7zz Stability**: Hardcoded 7zz version (25.00) for consistent behavior

This strategy provides full control over version management while ensuring compliance with Python packaging standards and maintaining release quality through manual oversight.
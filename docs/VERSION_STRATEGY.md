# py7zz Three-Tier Version Control Strategy

## Version Categories and Stability

py7zz adopts a three-tier version management strategy to provide users with different stability levels:

### 🟢 **Release (Stable)** - Most Stable
- **Format:** `{major}.{minor}.{patch}+7zz{7zz_version}`
- **Example:** `1.0.0+7zz24.07`
- **Stability:** Most stable, fully tested
- **Release Method:** Manual release with human review and testing
- **Use Case:** Recommended for production environments

### 🟡 **Auto (Basic Stable)** - Automated 7zz Updates
- **Format:** `{major}.{minor}.{patch}.auto+7zz{7zz_version}`
- **Example:** `1.0.0.auto+7zz24.08`
- **Stability:** Basic stable, only 7zz binary updates
- **Release Method:** Automatic release when 7zz has new versions
- **Use Case:** Users who need latest 7zz features but don't want to wait for official releases

### 🔴 **Dev (Unstable)** - Development Builds
- **Format:** `{major}.{minor}.{patch}-dev.{build}+7zz{7zz_version}`
- **Example:** `1.1.0-dev.1+7zz24.07`
- **Stability:** Unstable, contains py7zz features under development
- **Release Method:** Manual release for testing new features
- **Use Case:** Developers and early testers

## Version Upgrade Path

```
Release 1.0.0+7zz24.07
    ↓ (7zz updates to 24.08)
Auto 1.0.0.auto+7zz24.08  ← Automatic release
    ↓ (py7zz new feature development)
Dev 1.1.0-dev.1+7zz24.08  ← Manual release
    ↓ (Testing complete, ready for official release)
Release 1.1.0+7zz24.08  ← Manual release
```

## Version Management Rules

### py7zz Semantic Version Numbers
- **Major (1.x.x)**: Major architectural changes or API incompatible changes
- **Minor (x.1.x)**: New feature additions, backward compatible
- **Patch (x.x.1)**: Bug fixes, backward compatible
- **Build (.dev.x)**: Development version build number

### 7zz Version Numbers (Following Upstream)
- Directly use official 7zz version numbers
- Format: `YY.MM` (e.g., 24.07, 24.08)

## Version Update Strategy

### 1. 7zz Version Updates (Automatic Release)
- Automatically triggered when 7zz has new version releases
- Generate auto-update version: `{current_version}.auto+7zz{new_7zz_version}`
- Example: `1.0.0+7zz24.07` → `1.0.0.auto+7zz24.08`

### 2. py7zz Feature Development (Manual Release)
- Development version: `{next_version}-dev.{build}+7zz{7zz_version}`
- Example: `1.1.0-dev.1+7zz24.08`
- Build number increments: `1.1.0-dev.2+7zz24.08`

### 3. Official Version Release (Manual Release)
- Upgrade from development version to official version
- Example: `1.1.0-dev.5+7zz24.08` → `1.1.0+7zz24.08`

## Implementation

### 1. Version Information Storage
```python
# py7zz/version.py
PY7ZZ_VERSION = "1.0.0"
SEVEN_ZZ_VERSION = "24.07"
FULL_VERSION = f"{PY7ZZ_VERSION}+7zz{SEVEN_ZZ_VERSION}"
```

### 2. Dynamic Version Generation
```python
def get_version_info():
    return {
        "py7zz_version": PY7ZZ_VERSION,
        "7zz_version": SEVEN_ZZ_VERSION,
        "full_version": FULL_VERSION
    }
```

### 3. CI/CD Integration
- `pyproject.toml` uses complete version numbers
- Automation scripts adjust versions based on 7zz updates
- Nightly builds automatically generate development version numbers

## User Experience

### Installation Commands
```bash
# Install specific version
pip install py7zz==1.0.0+7zz24.07

# Install latest version
pip install py7zz

# Check version information
python -c "import py7zz; print(py7zz.get_version_info())"
```

### Version Display
```python
>>> import py7zz
>>> py7zz.get_version()
'1.0.0+7zz24.07'
>>> py7zz.get_version_info()
{'py7zz_version': '1.0.0', '7zz_version': '24.07', 'full_version': '1.0.0+7zz24.07'}
```

## Advantages

1. **Clarity**: Users can immediately see the included 7zz version
2. **Standardization**: Complies with PEP 440 semantic versioning specification
3. **Manageability**: Independent control of py7zz and 7zz versions
4. **Compatibility**: Compatible with existing Python package management tools
5. **Automation**: Supports CI/CD automatic version management

## Migration Plan

1. Create `py7zz/version.py` file
2. Update `pyproject.toml` version number format
3. Modify CI/CD scripts to support new version numbers
4. Update documentation and example code
5. Release first version using new version number format
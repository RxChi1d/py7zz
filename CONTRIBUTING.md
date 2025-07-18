# Contributing to py7zz

Thank you for your interest in contributing to py7zz! This document provides guidelines for contributing to the project.

## Quick Start

1. **Fork and Clone**
   ```bash
   git clone https://github.com/rxchi1d/py7zz.git
   cd py7zz
   ```

2. **Set up Development Environment**
   ```bash
   # Install uv (if not already installed)
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Create virtual environment and install dependencies
   uv sync --dev
   
   # Activate virtual environment
   source .venv/bin/activate  # Unix/macOS
   # or .venv\Scripts\activate  # Windows
   ```

3. **Run Quality Checks**
   ```bash
   uv run ruff format .        # Format code
   uv run ruff check --fix .   # Lint and fix issues
   uv run mypy .              # Type checking
   uv run pytest             # Run tests
   ```

## Development Workflow

### Making Changes

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Follow the code style and architecture patterns
   - Add tests for new functionality
   - Update documentation if needed

3. **Test Your Changes**
   ```bash
   # Run the complete quality check pipeline
   uv run ruff format .
   uv run ruff check --fix .
   uv run mypy .
   uv run pytest
   ```

4. **Commit Your Changes**
   - Follow our [commit message convention](#commit-message-convention)
   - Make atomic commits with clear purposes

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

### Code Style

- **Line Length**: 88 characters maximum
- **Linting**: Use Ruff with project configuration
- **Type Hints**: Required for all Python code
- **Import Sorting**: Automated by Ruff
- **Formatting**: Black-compatible formatting via Ruff

### Testing

- **Unit Tests**: Required for all new functionality
- **Integration Tests**: For cross-platform binary detection
- **Test Coverage**: Aim for high coverage on critical paths
- **Cross-Platform**: Tests must pass on Python 3.8-3.13

## Commit Message Convention

We follow **Conventional Commits** for automated release notes generation.

### Format

```
<type>(<scope>): <description>    ← First line (50-72 chars max)

[optional body]                   ← Detailed explanation (wrap at 72 chars)

[optional footer(s)]              ← Breaking changes, issue references
```

**Important Notes:**
- **First line**: Used by GitHub for auto-generated release notes
- **Body**: Detailed explanation for complex changes (not used in release notes)
- **Footer**: Breaking changes and issue references

### Types

- **feat**: New feature (MINOR version)
- **fix**: Bug fix (PATCH version)
- **docs**: Documentation changes
- **style**: Code formatting (no functional changes)
- **refactor**: Code refactoring
- **perf**: Performance improvements
- **test**: Test-related changes
- **chore**: Build tools or auxiliary tool changes
- **ci**: CI/CD changes

### Examples

**❌ Bad:**
```bash
git commit -m "feat: add async support"
git commit -m "fix: Windows bug"
git commit -m "docs: update readme"
```

**✅ Good First Lines:**
```bash
git commit -m "feat: add async operations with progress callbacks for large archives"
git commit -m "fix: resolve binary path detection on Windows systems with spaces"
git commit -m "docs: add comprehensive migration guide from zipfile to py7zz"
git commit -m "perf: optimize memory usage for large file extraction"
```

**✅ Good Multi-line Commits:**
```bash
git commit -m "feat: add async operations with progress callbacks

This commit introduces comprehensive async support including:
- Progress callback mechanism for real-time updates
- Batch operations for multiple archives
- Memory-efficient streaming for large files
- Cross-platform compatibility testing

The implementation maintains backward compatibility while
providing significant performance improvements for large-scale
operations."

git commit -m "fix: resolve binary path detection on Windows systems with spaces

The previous implementation failed when the 7zz binary path contained
spaces due to incorrect subprocess argument handling. This fix:

- Properly quotes binary paths in subprocess calls
- Adds comprehensive path validation
- Includes test cases for paths with spaces
- Maintains compatibility with existing installations

Fixes #42"
```

### Breaking Changes

Use `BREAKING CHANGE:` in the commit body for major version changes:
```bash
git commit -m "feat!: redesign API for better async support

BREAKING CHANGE: SevenZipFile.extract() now returns async iterator instead of list"
```

### Scope (Optional)

Specify the affected area:
```bash
git commit -m "feat(api): add batch extraction support"
git commit -m "fix(cli): resolve version display format"
git commit -m "docs(readme): add installation troubleshooting"
```

## Pull Request Process

1. **Pre-submission Checklist**
   - [ ] All quality checks pass locally
   - [ ] Tests are added for new functionality
   - [ ] Documentation is updated if needed
   - [ ] Commit messages follow convention
   - [ ] No TODO/FIXME comments left unresolved

2. **PR Description**
   - Clearly describe what changes were made
   - Reference any related issues
   - Include screenshots for UI changes
   - List any breaking changes

3. **Review Process**
   - All CI checks must pass
   - Code review by maintainers
   - Address feedback promptly
   - Squash commits if requested

## Development Environment Details

### Dependencies

- **Runtime**: Python 3.8+ support required
- **Development**: uv for dependency management
- **Testing**: pytest for unit and integration tests
- **Linting**: ruff for code quality
- **Type Checking**: mypy for static analysis

### Project Structure

```
py7zz/
├── py7zz/
│   ├── __init__.py       # Main API exports
│   ├── core.py           # Core 7zz subprocess wrapper
│   ├── cli.py            # CLI tool implementation
│   ├── async_ops.py      # Async operations support
│   ├── updater.py        # Binary download/update logic
│   └── bin/              # Platform-specific binaries
├── tests/                # Test suite
├── docs/                 # Documentation
└── .github/workflows/    # CI/CD configuration
```

### Binary Management

py7zz uses a hybrid approach for 7zz binary distribution:
- **PyPI wheels**: Include bundled binaries for each platform
- **Source installs**: Auto-download binaries on first use
- **Development**: Use `PY7ZZ_BINARY` env var for custom binary paths

## Release Process

Releases are automated through GitHub Actions:
1. **Tag Creation**: Push a version tag (e.g., `v1.0.0`)
2. **Automated Build**: Multi-platform wheels are built
3. **PyPI Publication**: Wheels are published to PyPI
4. **GitHub Release**: Release notes are auto-generated from commits

## Getting Help

- **Issues**: Report bugs or request features via GitHub Issues
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check README.md and code documentation

## Code of Conduct

Please be respectful and professional in all interactions. We follow the standard open-source community guidelines for inclusive collaboration.

## License

By contributing to py7zz, you agree that your contributions will be licensed under the same terms as the project (BSD-3-Clause + LGPL-2.1 for 7-Zip components).
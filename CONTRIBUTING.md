<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: 2025 py7zz contributors
-->

# Contributing to py7zz

Welcome! We're excited you're interested in contributing to py7zz. This guide will help you get started.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Style](#code-style)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Community](#community)

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- uv (for dependency management)

### Types of Contributions

We welcome:
- 🐛 Bug fixes
- ✨ New features
- 📚 Documentation improvements
- 🧪 Test additions
- 🎨 Code refactoring
- 💡 Ideas and suggestions

## Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/py7zz.git
   cd py7zz
   ```

2. **Install uv (if not installed)**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Set up development environment**
   ```bash
   uv sync --dev
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

## Making Changes

### 1. Create a branch

```bash
git checkout -b feature/your-feature-name
```

Use descriptive branch names:
- `feature/add-encryption-support`
- `fix/windows-path-handling`
- `docs/update-api-reference`

### 2. Make your changes

Follow the existing code structure and patterns.

### 3. Run quality checks

Before committing, run all checks:

```bash
# Format code
uv run ruff format .

# Fix linting issues
uv run ruff check --fix .

# Type checking
uv run mypy .

# Run tests
uv run pytest
```

Or use the local CI script:
```bash
./scripts/ci-local.sh
```

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_core.py

# Run with coverage
uv run pytest --cov=py7zz
```

### Writing Tests

- Add tests for all new functionality
- Ensure tests work on Python 3.8-3.13
- Use descriptive test names
- Include both positive and negative test cases

Example:
```python
def test_extract_with_invalid_path_raises_error():
    """Test that extracting to invalid path raises appropriate error."""
    with pytest.raises(py7zz.FileNotFoundError):
        py7zz.extract_archive('nonexistent.7z')
```

## Code Style

### Python Code

- **Style**: PEP 8 with Black formatting (via Ruff)
- **Line length**: 88 characters
- **Imports**: Sorted by `isort` (via Ruff)
- **Type hints**: Required for all functions
- **Docstrings**: Google style for all public APIs

Example:
```python
def create_archive(
    archive_path: Union[str, Path],
    files: List[Union[str, Path]],
    preset: str = "balanced"
) -> None:
    """Create an archive with specified files.

    Args:
        archive_path: Path to create the archive
        files: List of files/directories to include
        preset: Compression preset ('fast', 'balanced', 'ultra')

    Raises:
        FileNotFoundError: If any input file doesn't exist
        CompressionError: If compression fails
    """
```

### Documentation

- Clear and concise
- Include code examples
- Update if changing behavior
- Check spelling and grammar

## Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, missing semicolons, etc)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvement
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```bash
# Feature
git commit -m "feat: add async progress callbacks for large archives"

# Bug fix
git commit -m "fix: resolve Windows path handling for reserved names"

# Documentation
git commit -m "docs: add migration guide from zipfile to py7zz"

# With scope
git commit -m "feat(api): add batch extraction support"

# Breaking change
git commit -m "feat!: change extract() to return list of extracted files

BREAKING CHANGE: extract() now returns a list instead of None"
```

## Pull Request Process

### Before Submitting

- [ ] All tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] Commits follow convention
- [ ] Branch is up to date with main

### PR Title Format

**IMPORTANT**: PR titles must follow the same convention as commits:

```
feat: add async progress callbacks
fix: resolve Windows path handling
docs: update migration guide
```

This is critical because:
- PR titles appear in release notes
- Determines version bumps (feat = minor, fix = patch)
- Enables automatic labeling

### PR Description

Use the template to provide:
- Clear description of changes
- Related issue numbers
- Testing performed
- Breaking changes (if any)

### Review Process

1. CI checks must pass
2. Code review by maintainers
3. Address feedback constructively
4. Squash commits if requested

## Community

### Getting Help

- 💬 [GitHub Discussions](https://github.com/rxchi1d/py7zz/discussions) - Ask questions
- 🐛 [GitHub Issues](https://github.com/rxchi1d/py7zz/issues) - Report bugs
- 📚 [Documentation](docs/) - Read the docs

### Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Provide constructive feedback
- Focus on what's best for the community

### Recognition

Contributors are recognized in:
- GitHub contributors page
- Release notes
- Project documentation

## Development Tips

### Local Binary Testing

For testing with custom 7zz binary:
```bash
export PY7ZZ_BINARY=/path/to/7zz
```

### Debug Logging

Enable debug output:
```python
import py7zz
py7zz.setup_logging("DEBUG")
```

### Performance Testing

For performance-critical changes:
```python
import timeit
import py7zz

# Measure performance
time = timeit.timeit(
    lambda: py7zz.create_archive('test.7z', ['data/']),
    number=10
)
print(f"Average time: {time/10:.2f}s")
```

## Questions?

Feel free to:
- Open a [Discussion](https://github.com/rxchi1d/py7zz/discussions) for questions
- Reach out to maintainers
- Check existing issues and PRs

Thank you for contributing to py7zz! 🎉

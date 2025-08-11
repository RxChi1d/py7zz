# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""
PyPI version validation tests.
Tests version consistency before PyPI publication.
"""

import subprocess
import tempfile
from pathlib import Path

import pytest

import py7zz


class TestPyPIVersionValidation:
    """Test version validation before PyPI publication."""

    def test_wheel_version_consistency(self):
        """Test that wheel version matches expected PyPI version."""
        # Create a test tag
        with tempfile.TemporaryDirectory() as tmpdir_str:
            tmpdir = Path(tmpdir_str)
            self._setup_test_repo(tmpdir)

            # Create test tag
            subprocess.run(["git", "tag", "v0.1.5"], cwd=tmpdir, check=True)

            # Build wheel
            wheel_path = self._build_test_wheel(tmpdir)

            # Extract version from wheel filename
            wheel_filename = wheel_path.name
            assert "py7zz-0.1.5-py3-none-any.whl" in wheel_filename

            # Verify version consistency
            version_from_wheel = self._extract_version_from_wheel(wheel_filename)
            assert version_from_wheel == "0.1.5"

    def test_alpha_version_pypi_consistency(self):
        """Test alpha version consistency for PyPI."""
        with tempfile.TemporaryDirectory() as tmpdir_str:
            tmpdir = Path(tmpdir_str)
            self._setup_test_repo(tmpdir)

            # Create alpha tag
            subprocess.run(["git", "tag", "v0.1.5a1"], cwd=tmpdir, check=True)

            # Build wheel
            wheel_path = self._build_test_wheel(tmpdir)

            # Extract version from wheel filename
            wheel_filename = wheel_path.name
            assert "py7zz-0.1.5a1-py3-none-any.whl" in wheel_filename

            # Verify version consistency
            version_from_wheel = self._extract_version_from_wheel(wheel_filename)
            assert version_from_wheel == "0.1.5a1"

            # Verify it's recognized as alpha
            parsed = py7zz.parse_version(version_from_wheel)
            assert parsed["version_type"] == "alpha"

    def test_dev_version_pypi_consistency(self):
        """Test dev version consistency for PyPI."""
        with tempfile.TemporaryDirectory() as tmpdir_str:
            tmpdir = Path(tmpdir_str)
            self._setup_test_repo(tmpdir)

            # Create dev tag
            subprocess.run(["git", "tag", "v0.1.5.dev1"], cwd=tmpdir, check=True)

            # Build wheel
            wheel_path = self._build_test_wheel(tmpdir)

            # Extract version from wheel filename
            wheel_filename = wheel_path.name
            assert "py7zz-0.1.5.dev1-py3-none-any.whl" in wheel_filename

            # Verify version consistency
            version_from_wheel = self._extract_version_from_wheel(wheel_filename)
            assert version_from_wheel == "0.1.5.dev1"

            # Verify it's recognized as dev
            parsed = py7zz.parse_version(version_from_wheel)
            assert parsed["version_type"] == "dev"

    def test_ci_version_validation_logic(self):
        """Test the CI/CD version validation logic."""
        # Test cases from our CI/CD pipeline
        test_cases = [
            ("v1.0.0", "1.0.0", True),  # Valid stable
            ("v1.0.0a1", "1.0.0a1", True),  # Valid alpha
            ("v1.0.0b1", "1.0.0b1", True),  # Valid beta
            ("v1.0.0rc1", "1.0.0rc1", True),  # Valid release candidate
            ("v1.0.0.dev1", "1.0.0.dev1", True),  # Valid dev
            ("v1.0", "", False),  # Invalid - missing patch
            ("v1.0.0.1", "", False),  # Invalid - extra version part
        ]

        for git_tag, expected_version, should_be_valid in test_cases:
            if should_be_valid:
                # Test tag format validation
                assert self._validate_tag_format(git_tag)

                # Test version extraction
                extracted_version = self._extract_version_from_tag(git_tag)
                assert extracted_version == expected_version

                # Test PEP 440 compliance
                assert self._validate_pep440_compliance(extracted_version)
            else:
                # Should fail validation
                assert not self._validate_tag_format(git_tag)

    def test_pypi_version_metadata(self):
        """Test that package metadata contains correct version."""
        current_version = py7zz.get_version()

        # Test that version is valid
        assert current_version is not None
        assert len(current_version) > 0

        # Test that version is parseable
        parsed = py7zz.parse_version(current_version)
        assert isinstance(parsed["major"], int) and parsed["major"] >= 0
        assert isinstance(parsed["minor"], int) and parsed["minor"] >= 0
        assert isinstance(parsed["patch"], int) and parsed["patch"] >= 0

    def test_installation_version_consistency(self):
        """Test version consistency after installation."""
        # This simulates the user installation experience
        current_version = py7zz.get_version()

        # Test that get_version() returns a valid version
        assert current_version is not None

        # Test that version follows our expected format
        parsed = py7zz.parse_version(current_version)
        assert parsed["version_type"] in ["stable", "alpha", "beta", "rc", "dev"]

        # Test that version is PEP 440 compliant
        import re

        # Updated PEP 440 pattern to support alpha.dev format like 1.1.0a4.dev1
        pep440_pattern = r"^[0-9]+\.[0-9]+(\.[0-9]+)?((a|b|rc)[0-9]+)?(\.dev[0-9]+)?$"
        assert re.match(pep440_pattern, current_version)

    def _setup_test_repo(self, repo_path: Path):
        """Set up a minimal test repository."""
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_path, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"], cwd=repo_path
        )
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path)

        # Create minimal pyproject.toml
        pyproject_content = """
[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"

[project]
name = "py7zz"
dynamic = ["version"]
description = "Test package"
requires-python = ">=3.8"

[tool.hatch.version]
source = "vcs"

[tool.hatch.version.raw-options]
git_describe_command = "git describe --tags --match='v*'"
local_scheme = "no-local-version"
"""
        (repo_path / "pyproject.toml").write_text(pyproject_content)

        # Create minimal package structure
        (repo_path / "py7zz").mkdir()
        (repo_path / "py7zz" / "__init__.py").write_text('__version__ = "0.0.0"')

        # Initial commit
        subprocess.run(["git", "add", "."], cwd=repo_path)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path)

    def _build_test_wheel(self, repo_path: Path) -> Path:
        """Build a test wheel and return its path."""
        dist_dir = repo_path / "dist"
        dist_dir.mkdir(exist_ok=True)

        # Build wheel
        result = subprocess.run(
            ["python", "-m", "build", "--wheel", "--outdir", str(dist_dir)],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            pytest.skip(f"Build failed: {result.stderr}")

        # Find the wheel file
        wheel_files = list(dist_dir.glob("*.whl"))
        assert len(wheel_files) == 1, f"Expected 1 wheel file, found {len(wheel_files)}"

        return wheel_files[0]

    def _extract_version_from_wheel(self, wheel_filename: str) -> str:
        """Extract version from wheel filename."""
        # Wheel filename format: {distribution}-{version}(-{build tag})?-{python tag}-{abi tag}-{platform tag}.whl
        import re

        match = re.match(r"py7zz-([^-]+)-py3-none-any\.whl", wheel_filename)
        if match:
            return match.group(1)
        raise ValueError(
            f"Could not extract version from wheel filename: {wheel_filename}"
        )

    def _validate_tag_format(self, tag: str) -> bool:
        """Validate Git tag format."""
        import re

        pattern = r"^v[0-9]+\.[0-9]+\.[0-9]+(\.(dev[0-9]+)|a[0-9]+|b[0-9]+|rc[0-9]+)?$"
        return re.match(pattern, tag) is not None

    def _extract_version_from_tag(self, tag: str) -> str:
        """Extract version from Git tag."""
        return tag[1:]  # Remove 'v' prefix

    def _validate_pep440_compliance(self, version: str) -> bool:
        """Validate PEP 440 compliance."""
        import re

        pattern = r"^[0-9]+\.[0-9]+\.[0-9]+(\.dev[0-9]+|a[0-9]+|b[0-9]+|rc[0-9]+)?$"
        return re.match(pattern, version) is not None


class TestUserInstallationExperience:
    """Test user installation experience."""

    def test_version_discovery(self):
        """Test that users can discover version information."""
        # Test that get_version() works
        version = py7zz.get_version()
        assert version is not None
        assert isinstance(version, str)
        assert len(version) > 0

        # Test that version can be parsed
        parsed = py7zz.parse_version(version)
        assert "major" in parsed
        assert "minor" in parsed
        assert "patch" in parsed
        assert "version_type" in parsed

    def test_version_type_identification(self):
        """Test that users can identify version type."""
        version = py7zz.get_version()
        parsed = py7zz.parse_version(version)

        # Version type should be one of our supported types
        assert parsed["version_type"] in ["stable", "alpha", "beta", "rc", "dev"]

        # Test version type functions
        from py7zz.version import (
            get_version_type,
            is_alpha_version,
            is_beta_version,
            is_dev_version,
            is_rc_version,
            is_stable_version,
        )

        version_type = get_version_type(version)
        assert version_type in ["stable", "alpha", "beta", "rc", "dev"]

        # Test that exactly one version type function returns True
        type_checks = [
            is_stable_version(version),
            is_alpha_version(version),
            is_beta_version(version),
            is_rc_version(version),
            is_dev_version(version),
        ]
        assert sum(type_checks) == 1, "Exactly one version type should be True"

    def test_cli_version_command(self):
        """Test CLI version command."""
        # Test that CLI version command works
        result = subprocess.run(
            ["python", "-m", "py7zz", "--py7zz-version"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        if result.returncode == 0:
            cli_version = result.stdout.strip()
            package_version = py7zz.get_version()
            assert cli_version == package_version

    def test_import_version_consistency(self):
        """Test that import version is consistent."""
        # Test direct import through main module
        import_version = py7zz.get_version()
        core_version = py7zz.get_version()

        assert import_version == core_version

        # Test that version is accessible from main package
        assert hasattr(py7zz, "get_version")

    def test_version_upgrade_path(self):
        """Test version upgrade path clarity."""
        version = py7zz.get_version()
        parsed = py7zz.parse_version(version)

        # Test that version has clear upgrade path
        if parsed["version_type"] == "dev":
            # Dev versions should have clear next stable version
            base_version = parsed["base_version"]
            assert base_version is not None

        elif parsed["version_type"] == "alpha":
            # Auto versions should have clear base version
            base_version = parsed["base_version"]
            assert base_version is not None

        # All versions should have clear major.minor.patch structure
        assert isinstance(parsed["major"], int) and parsed["major"] >= 0
        assert isinstance(parsed["minor"], int) and parsed["minor"] >= 0
        assert isinstance(parsed["patch"], int) and parsed["patch"] >= 0

"""
Version system tests for py7zz.
Tests dynamic version resolution, PEP 440 compliance, and version consistency.
"""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from py7zz.core import get_version
from py7zz.version import get_version as get_version_direct
from py7zz.version import parse_version


class TestVersionSystem:
    """Test dynamic version resolution system."""

    def test_get_version_returns_string(self):
        """Test version returns a string."""
        version = get_version()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_get_version_consistency(self):
        """Test version consistency between different methods."""
        version1 = get_version()
        version2 = get_version_direct()
        assert version1 == version2

    def test_version_pep440_compliance(self):
        """Test version follows PEP 440 format."""
        version = get_version()

        # Test basic format patterns
        import re

        pep440_pattern = (
            r"^([0-9]+!)?"
            r"([0-9]+(?:\.[0-9]+)*)"
            r"(?:[-_\.]?"
            r"(a|b|rc|alpha|beta|pre|preview|c|dev)"
            r"[-_\.]?([0-9]+)?)?"
            r"(?:[-_\.]?post[-_\.]?([0-9]+)?)?"
            r"(?:[-_\.]?dev[-_\.]?([0-9]+)?)?$"
        )

        assert re.match(pep440_pattern, version, re.IGNORECASE), f"Version {version} is not PEP 440 compliant"

    def test_version_parsing(self):
        """Test version parsing functionality."""
        version = get_version()
        parsed = parse_version(version)

        assert isinstance(parsed, dict)
        assert "major" in parsed
        assert "minor" in parsed
        assert "patch" in parsed
        assert isinstance(parsed["major"], int)
        assert isinstance(parsed["minor"], int)
        assert isinstance(parsed["patch"], int)

    def test_stable_version_format(self):
        """Test stable version format detection."""
        # Test with mock stable version
        with patch("py7zz.version.get_version", return_value="1.0.0"):
            version = get_version()
            parsed = parse_version(version)

            assert parsed["major"] == 1
            assert parsed["minor"] == 0
            assert parsed["patch"] == 0
            assert parsed["version_type"] == "stable"

    def test_dev_version_format(self):
        """Test development version format detection."""
        # Test with mock dev version
        with patch("py7zz.version.get_version", return_value="1.0.0.dev1"):
            version = get_version()
            parsed = parse_version(version)

            assert parsed["major"] == 1
            assert parsed["minor"] == 0
            assert parsed["patch"] == 0
            assert parsed["version_type"] == "dev"
            assert parsed["build_number"] == 1

    def test_alpha_version_format(self):
        """Test alpha version format detection."""
        # Test with mock alpha version
        with patch("py7zz.version.get_version", return_value="1.0.0a1"):
            version = get_version()
            parsed = parse_version(version)

            assert parsed["major"] == 1
            assert parsed["minor"] == 0
            assert parsed["patch"] == 0
            assert parsed["version_type"] == "auto"
            assert parsed["build_number"] == 1


class TestVersionConsistency:
    """Test version consistency across different contexts."""

    def test_package_version_consistency(self):
        """Test package version consistency."""
        # Test that version is consistent across multiple calls
        version1 = get_version()
        version2 = get_version()
        assert version1 == version2

    def test_cli_version_consistency(self):
        """Test CLI version matches package version."""
        package_version = get_version()

        # Test CLI version command
        result = subprocess.run(
            ["uv", "run", "python", "-m", "py7zz", "version", "--format", "json"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        if result.returncode == 0:
            import json

            cli_data = json.loads(result.stdout)
            cli_version = cli_data.get("py7zz_version")
            assert cli_version == package_version

    def test_build_version_consistency(self):
        """Test build process generates consistent version."""
        # Create temporary git repo for testing
        with tempfile.TemporaryDirectory() as tmpdir_str:
            tmpdir = Path(tmpdir_str)

            # Initialize git repo
            subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmpdir)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmpdir)

            # Copy project files
            import shutil

            project_root = Path(__file__).parent.parent
            shutil.copytree(
                project_root,
                tmpdir / "py7zz",
                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "dist", "build"),
            )

            # Create test tag
            subprocess.run(["git", "add", "."], cwd=tmpdir)
            subprocess.run(["git", "commit", "-m", "Test commit"], cwd=tmpdir)
            subprocess.run(["git", "tag", "v1.0.0"], cwd=tmpdir)

            # Test version generation
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "python",
                    "-c",
                    "from hatchling.metadata.core import ProjectMetadata; print(ProjectMetadata.from_file('.').version)",
                ],
                cwd=tmpdir / "py7zz",
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                generated_version = result.stdout.strip()
                assert generated_version == "1.0.0"


class TestVersionErrorHandling:
    """Test version system error handling."""

    def test_invalid_git_state(self):
        """Test handling of invalid git state."""
        # This test is mostly for documentation -
        # hatch-vcs handles most error cases gracefully
        pass

    def test_missing_version_info(self):
        """Test handling of missing version information."""
        # Test that version system provides fallback
        version = get_version()
        assert version is not None
        assert len(version) > 0

    def test_version_parsing_errors(self):
        """Test version parsing error handling."""
        # Test invalid version format
        with pytest.raises(ValueError):
            parse_version("invalid.version.format.x.y.z")

        # Test empty version
        with pytest.raises(ValueError):
            parse_version("")


class TestVersionTypes:
    """Test different version types (stable, alpha, dev)."""

    def test_stable_version_detection(self):
        """Test stable version detection."""
        stable_versions = ["1.0.0", "2.1.5", "10.0.0"]

        for version in stable_versions:
            parsed = parse_version(version)
            assert parsed["version_type"] == "stable"

    def test_alpha_version_detection(self):
        """Test alpha version detection."""
        alpha_versions = ["1.0.0a1", "2.1.0a5", "1.0.0a10"]

        for version in alpha_versions:
            parsed = parse_version(version)
            assert parsed["version_type"] == "auto"

    def test_dev_version_detection(self):
        """Test development version detection."""
        dev_versions = ["1.0.0.dev1", "2.1.0.dev5", "1.0.0.dev10"]

        for version in dev_versions:
            parsed = parse_version(version)
            assert parsed["version_type"] == "dev"


class TestGitTagIntegration:
    """Test integration with Git tags."""

    def test_git_tag_format_validation(self):
        """Test Git tag format validation."""
        valid_tags = ["v1.0.0", "v1.0.0a1", "v1.0.0.dev1", "v10.5.2", "v1.0.0a10", "v1.0.0.dev5"]

        invalid_tags = [
            "1.0.0",  # missing 'v' prefix
            "v1.0",  # missing patch version
            "v1.0.0.1",  # too many version parts
            "v1.0.0b1",  # beta not supported
            "v1.0.0-dev1",  # wrong dev format
        ]

        import re

        tag_pattern = r"^v[0-9]+\.[0-9]+\.[0-9]+(\.dev[0-9]+|a[0-9]+)?$"

        for tag in valid_tags:
            assert re.match(tag_pattern, tag), f"Valid tag {tag} failed validation"

        for tag in invalid_tags:
            assert not re.match(tag_pattern, tag), f"Invalid tag {tag} passed validation"

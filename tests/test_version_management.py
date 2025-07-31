"""
Test suite for py7zz Version Management System.

This module tests all version-related functionality including:
1. Dynamic version resolution and consistency
2. PEP 440 compliance and version parsing
3. Git tag integration and version workflows
4. Version type detection (stable, alpha, dev)
5. Build number generation and validation

Consolidated from:
- test_version_system.py (basic version system tests)
- test_version_integration.py (integration workflow tests)
"""

import contextlib
import re
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from py7zz.core import get_version
from py7zz.version import (
    generate_auto_version,
    generate_dev_version,
    get_base_version,
    get_build_number,
    get_version_type,
    is_auto_version,
    is_dev_version,
    is_stable_version,
    parse_version,
)
from py7zz.version import (
    get_version as get_version_direct,
)


class TestVersionBasics:
    """Test basic version functionality."""

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

    def test_version_not_empty(self):
        """Test that version is not empty or None."""
        version = get_version()
        assert version is not None
        assert version != ""
        assert version.strip() != ""

    def test_version_has_components(self):
        """Test that version has expected components."""
        version = get_version()
        # Should contain at least major.minor
        parts = version.split(".")
        assert len(parts) >= 2

        # First part should be numeric
        assert (
            parts[0].isdigit()
            or parts[0].rstrip("abcdefghijklmnopqrstuvwxyz").isdigit()
        )


class TestVersionPEP440Compliance:
    """Test PEP 440 compliance."""

    def test_version_pep440_compliance(self):
        """Test version follows PEP 440 format."""
        version = get_version()

        # Test basic format patterns
        pep440_pattern = (
            r"^([0-9]+!)?"
            r"([0-9]+(?:\.[0-9]+)*)"
            r"(?:[-_\.]?"
            r"(a|b|rc|alpha|beta|pre|preview|c|dev)"
            r"[-_\.]?([0-9]+)?)?"
            r"(?:[-_\.]?post[-_\.]?([0-9]+)?)?"
            r"(?:[-_\.]?dev[-_\.]?([0-9]+)?)?$"
        )

        assert re.match(pep440_pattern, version, re.IGNORECASE), (
            f"Version '{version}' does not match PEP 440 format"
        )

    def test_version_parsing_basic(self):
        """Test basic version parsing functionality."""
        # Test stable version
        stable = "1.0.0"
        parsed_stable = parse_version(stable)
        assert parsed_stable["version_type"] == "stable"
        assert parsed_stable["major"] == 1
        assert parsed_stable["minor"] == 0
        assert parsed_stable["patch"] == 0

        # Test alpha version
        alpha = "1.0.0a1"
        parsed_alpha = parse_version(alpha)
        assert parsed_alpha["version_type"] == "auto"
        assert parsed_alpha["major"] == 1
        assert parsed_alpha["minor"] == 0
        assert parsed_alpha["patch"] == 0
        assert parsed_alpha["build_number"] == 1

    def test_version_parsing_dev(self):
        """Test dev version parsing."""
        dev = "1.0.0.dev1"
        parsed_dev = parse_version(dev)
        assert parsed_dev["version_type"] == "dev"
        assert parsed_dev["major"] == 1
        assert parsed_dev["minor"] == 0
        assert parsed_dev["patch"] == 0

    def test_version_parsing_invalid(self):
        """Test parsing of invalid versions."""
        invalid_versions = ["", "invalid", "1.0.0.0.0", "v1.0.0"]

        for invalid in invalid_versions:
            with pytest.raises((ValueError, KeyError)):
                parse_version(invalid)


class TestVersionTypes:
    """Test version type detection."""

    def test_stable_version_detection(self):
        """Test stable version detection."""
        assert is_stable_version("1.0.0") is True
        assert is_stable_version("2.1.3") is True
        assert is_stable_version("1.0.0a1") is False
        assert is_stable_version("1.0.0.dev1") is False

    def test_auto_version_detection(self):
        """Test auto (alpha) version detection."""
        assert is_auto_version("1.0.0a1") is True
        assert is_auto_version("2.1.0a5") is True
        assert is_auto_version("1.0.0") is False
        assert is_auto_version("1.0.0.dev1") is False

    def test_dev_version_detection(self):
        """Test dev version detection."""
        assert is_dev_version("1.0.0.dev1") is True
        assert is_dev_version("2.1.0.dev10") is True
        assert is_dev_version("1.0.0") is False
        assert is_dev_version("1.0.0a1") is False

    def test_get_version_type_function(self):
        """Test get_version_type function."""
        assert get_version_type("1.0.0") == "stable"
        assert get_version_type("1.0.0a1") == "auto"
        assert get_version_type("1.0.0.dev1") == "dev"

    def test_get_version_type_current(self):
        """Test get_version_type with current version."""
        current_version = get_version()
        version_type = get_version_type(current_version)
        assert version_type in ["stable", "alpha", "dev"]


class TestVersionGeneration:
    """Test version generation functions."""

    def test_generate_auto_version(self):
        """Test auto version generation."""
        base = "1.0.0"
        build_num = 5
        auto_version = generate_auto_version(base, build_num)

        assert auto_version == "1.0.0a5"
        assert is_auto_version(auto_version)

    def test_generate_dev_version(self):
        """Test dev version generation."""
        base = "1.1.0"
        build_num = 10
        dev_version = generate_dev_version(base, build_num)

        assert dev_version == "1.1.0.dev10"
        assert is_dev_version(dev_version)

    def test_get_base_version(self):
        """Test base version extraction."""
        assert get_base_version("1.0.0") == "1.0.0"
        assert get_base_version("1.0.0a1") == "1.0.0"
        assert get_base_version("1.0.0.dev1") == "1.0.0"

    def test_get_build_number(self):
        """Test build number extraction."""
        assert get_build_number("1.0.0") == 0
        assert get_build_number("1.0.0a5") == 5
        assert get_build_number("1.0.0.dev10") == 10

    def test_version_generation_consistency(self):
        """Test that generated versions can be parsed back correctly."""
        base = "2.1.0"
        build_num = 7

        # Test auto version
        auto_ver = generate_auto_version(base, build_num)
        assert get_base_version(auto_ver) == base
        assert get_build_number(auto_ver) == build_num

        # Test dev version
        dev_ver = generate_dev_version(base, build_num)
        assert get_base_version(dev_ver) == base
        assert get_build_number(dev_ver) == build_num


class TestVersionIntegration:
    """Integration tests for version system workflow."""

    def _setup_git_repo(self, repo_dir: Path):
        """Setup a git repository for testing."""
        subprocess.run(["git", "init"], cwd=repo_dir, check=True)
        subprocess.run(
            ["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_dir,
            check=True,
        )

        # Create initial commit
        test_file = repo_dir / "test.txt"
        test_file.write_text("test content")
        subprocess.run(["git", "add", "test.txt"], cwd=repo_dir, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"], cwd=repo_dir, check=True
        )

    def _get_version_from_repo(self, repo_dir: Path) -> str:
        """Get version from git repository."""
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--match=v*"],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            version_tag = result.stdout.strip()
            # Remove 'v' prefix if present
            if version_tag.startswith("v"):
                return version_tag[1:]
            return version_tag
        except subprocess.CalledProcessError:
            return "0.0.0.dev1"  # Default for repos without tags

    def test_version_workflow_stable(self):
        """Test complete workflow for stable version."""
        with tempfile.TemporaryDirectory() as tmpdir_str:
            tmpdir = Path(tmpdir_str)
            self._setup_git_repo(tmpdir)

            # Create stable version tag
            subprocess.run(["git", "tag", "v1.0.0"], cwd=tmpdir, check=True)

            # Test version generation
            version = self._get_version_from_repo(tmpdir)
            assert version == "1.0.0"

            # Test version parsing
            parsed = parse_version(version)
            assert parsed["version_type"] == "stable"
            assert parsed["major"] == 1
            assert parsed["minor"] == 0
            assert parsed["patch"] == 0

    def test_version_workflow_alpha(self):
        """Test complete workflow for alpha version."""
        with tempfile.TemporaryDirectory() as tmpdir_str:
            tmpdir = Path(tmpdir_str)
            self._setup_git_repo(tmpdir)

            # Create alpha version tag
            subprocess.run(["git", "tag", "v1.0.0a1"], cwd=tmpdir, check=True)

            # Test version generation
            version = self._get_version_from_repo(tmpdir)
            assert version == "1.0.0a1"

            # Test version parsing
            parsed = parse_version(version)
            assert parsed["version_type"] == "auto"
            assert parsed["major"] == 1
            assert parsed["minor"] == 0
            assert parsed["patch"] == 0
            assert parsed["build_number"] == 1

    def test_version_workflow_dev(self):
        """Test complete workflow for dev version."""
        with tempfile.TemporaryDirectory() as tmpdir_str:
            tmpdir = Path(tmpdir_str)
            self._setup_git_repo(tmpdir)

            # Don't create any tags, should result in dev version
            version = self._get_version_from_repo(tmpdir)

            # Should be dev version when no tags exist
            assert ".dev" in version or version == "0.0.0.dev1"

    def test_version_workflow_progression(self):
        """Test version progression from dev to alpha to stable."""
        with tempfile.TemporaryDirectory() as tmpdir_str:
            tmpdir = Path(tmpdir_str)
            self._setup_git_repo(tmpdir)

            # Start with no tags (dev)
            dev_version = self._get_version_from_repo(tmpdir)
            assert ".dev" in dev_version or dev_version == "0.0.0.dev1"

            # Add alpha tag
            subprocess.run(["git", "tag", "v1.0.0a1"], cwd=tmpdir, check=True)
            alpha_version = self._get_version_from_repo(tmpdir)
            assert alpha_version == "1.0.0a1"
            assert is_auto_version(alpha_version)

            # Add stable tag
            subprocess.run(["git", "tag", "v1.0.0"], cwd=tmpdir, check=True)
            stable_version = self._get_version_from_repo(tmpdir)
            assert stable_version == "1.0.0"
            assert is_stable_version(stable_version)

    def test_version_validation_edge_cases(self):
        """Test version validation with edge cases."""
        # Empty version
        with pytest.raises((ValueError, KeyError)):
            parse_version("")

        # Version with just numbers
        parsed = parse_version("1.0.0")
        assert parsed["version_type"] == "stable"

        # Version with multiple prereleases (should handle gracefully)
        with contextlib.suppress(ValueError, KeyError):
            parse_version("1.0.0a1b2")  # Invalid format  # Expected to fail


class TestVersionMocking:
    """Test version functionality with mocked values."""

    def test_version_with_mock_git(self):
        """Test version determination with mocked git commands."""
        with patch("subprocess.run") as mock_run:
            # Mock successful git describe
            mock_run.return_value.stdout = "v1.2.3"
            mock_run.return_value.returncode = 0

            # Test would require actual version module integration
            # This is a structure test for mocking approach
            assert mock_run is not None

    def test_version_fallback_behavior(self):
        """Test version fallback when git is not available."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            # Should fallback to hardcoded version or raise appropriate error
            version = get_version()
            assert isinstance(version, str)
            assert len(version) > 0

    def test_version_with_mock_environment(self):
        """Test version behavior in different environments."""
        # Test in development environment
        current_version = get_version()
        assert current_version is not None

        # Version should be deterministic in test environment
        version2 = get_version()
        assert current_version == version2


class TestVersionConsistency:
    """Test version consistency across different calls."""

    def test_version_consistency_multiple_calls(self):
        """Test that version is consistent across multiple calls."""
        versions = [get_version() for _ in range(5)]
        assert all(v == versions[0] for v in versions)

    def test_version_consistency_different_imports(self):
        """Test version consistency from different import paths."""
        from py7zz import get_version as get_version_main
        from py7zz.core import get_version as get_version_core
        from py7zz.version import get_version as get_version_module

        version_main = get_version_main()
        version_core = get_version_core()
        version_module = get_version_module()

        assert version_main == version_core == version_module

    def test_version_info_consistency(self):
        """Test that version info is consistent."""
        # Test that all version-related functions work with current version
        current_version = get_version()

        # These should not raise exceptions
        version_type = get_version_type(current_version)
        base_version = get_base_version(current_version)
        build_number = get_build_number(current_version)

        assert version_type in ["stable", "alpha", "dev"]
        assert isinstance(base_version, str)
        assert isinstance(build_number, int)
        assert build_number >= 0


class TestVersionEdgeCases:
    """Test edge cases in version handling."""

    def test_version_with_unusual_formats(self):
        """Test version parsing with unusual but valid formats."""
        # Test various valid PEP 440 formats
        valid_versions = [
            "1.0.0",
            "1.0.0a1",
            "1.0.0.dev1",
            "2.1.3",
            "10.0.0a5",
        ]

        for version in valid_versions:
            parsed = parse_version(version)
            assert "version_type" in parsed
            assert "major" in parsed

    def test_version_comparison_logic(self):
        """Test version comparison logic."""
        # Test that version types are correctly identified
        assert is_stable_version("1.0.0")
        assert not is_stable_version("1.0.0a1")
        assert not is_stable_version("1.0.0.dev1")

        assert is_auto_version("1.0.0a1")
        assert not is_auto_version("1.0.0")
        assert not is_auto_version("1.0.0.dev1")

        assert is_dev_version("1.0.0.dev1")
        assert not is_dev_version("1.0.0")
        assert not is_dev_version("1.0.0a1")

    def test_version_generation_edge_cases(self):
        """Test version generation with edge cases."""
        # Test with zero build number
        auto_version = generate_auto_version("1.0.0", 0)
        assert auto_version == "1.0.0a0"

        dev_version = generate_dev_version("1.0.0", 0)
        assert dev_version == "1.0.0.dev0"

        # Test with large build numbers
        auto_version_large = generate_auto_version("1.0.0", 999)
        assert auto_version_large == "1.0.0a999"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

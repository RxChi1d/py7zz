# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""Tests for pinned SHA-256 checksum verification (issue #33).

Covers the ``_pinned`` metadata readers, runtime checksum verification in
``_download``, the deterministic SFX member selection, and consistency
between the shipped ``7zz_version.txt`` and ``7zz_checksums.txt`` files.
"""

import hashlib
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

import py7zz._download as dl
from py7zz._pinned import (
    PINNED_CHECKSUM_FILE,
    read_pinned_7zz_version,
    read_pinned_checksums,
)
from py7zz.updater import UpdateError


class TestPinnedReaders:
    """Test the shared pinned-metadata file readers."""

    def test_read_pinned_version_real_file(self) -> None:
        """Test the shipped version file parses to a dotted version."""
        version = read_pinned_7zz_version()
        assert version is not None
        assert "." in version
        assert version.replace(".", "").isdigit()

    def test_read_pinned_version_missing_returns_none(self) -> None:
        """Test a missing version file returns None (lenient reader)."""
        fake = Path("/nonexistent/py7zz/7zz_version.txt")
        with patch("py7zz._pinned.PINNED_VERSION_FILE", fake):
            assert read_pinned_7zz_version() is None

    def test_read_pinned_version_empty_returns_none(self) -> None:
        """Test an empty version file returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            empty = Path(tmpdir) / "v.txt"
            empty.write_text("  \n", encoding="utf-8")
            with patch("py7zz._pinned.PINNED_VERSION_FILE", empty):
                assert read_pinned_7zz_version() is None

    def test_read_pinned_checksums_parses_sha256sum_format(self) -> None:
        """Test comments and blanks are skipped; digests are lowercased."""
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "sums.txt"
            f.write_text(
                "# comment line\n"
                "\n"
                "ABCDEF0123  asset-one.tar.xz\n"
                "deadbeef  asset-two.exe\n"
                "malformed-line-without-name\n",
                encoding="utf-8",
            )
            with patch("py7zz._pinned.PINNED_CHECKSUM_FILE", f):
                sums = read_pinned_checksums()

        assert sums == {
            "asset-one.tar.xz": "abcdef0123",
            "asset-two.exe": "deadbeef",
        }

    def test_read_pinned_checksums_missing_returns_empty(self) -> None:
        """Test a missing checksum file returns an empty mapping."""
        fake = Path("/nonexistent/py7zz/7zz_checksums.txt")
        with patch("py7zz._pinned.PINNED_CHECKSUM_FILE", fake):
            assert read_pinned_checksums() == {}


class TestShippedChecksumFile:
    """Consistency checks on the real, shipped checksum file."""

    def test_checksum_file_exists_and_parses(self) -> None:
        """Test the shipped file exists and yields valid digests."""
        assert PINNED_CHECKSUM_FILE.exists()
        sums = read_pinned_checksums()
        assert sums, "shipped checksum file must not parse to empty"
        for asset, digest in sums.items():
            assert len(digest) == 64, f"bad digest length for {asset}"
            assert all(c in "0123456789abcdef" for c in digest)

    def test_checksums_cover_all_pinned_version_assets(self) -> None:
        """Test every asset py7zz can download for the pinned version is pinned.

        # Reason: a version bump without a checksum refresh would brick the
        auto-download tier (fail-closed); this catches the desync in CI.
        """
        version = read_pinned_7zz_version()
        assert version is not None
        dotless = version.replace(".", "")
        required = {
            f"7z{dotless}-arm64.exe",
            f"7z{dotless}-linux-arm64.tar.xz",
            f"7z{dotless}-linux-x64.tar.xz",
            f"7z{dotless}-mac.tar.xz",
            f"7z{dotless}-x64.exe",
            "7zr.exe",
        }
        sums = read_pinned_checksums()
        missing = required - set(sums)
        assert not missing, f"checksums missing for: {sorted(missing)}"


class TestVerifyChecksum:
    """Test runtime SHA-256 verification of downloaded assets."""

    def test_matching_checksum_passes(self) -> None:
        """Test a file matching the pinned digest verifies silently."""
        data = b"verified payload"
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "asset"
            f.write_bytes(data)
            with patch(
                "py7zz._download.read_pinned_checksums",
                return_value={"asset.tar.xz": hashlib.sha256(data).hexdigest()},
            ):
                dl.verify_checksum(f, "asset.tar.xz")  # must not raise

    def test_mismatched_checksum_raises(self) -> None:
        """Test a tampered file is rejected with an UpdateError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "asset"
            f.write_bytes(b"tampered payload")
            with patch(
                "py7zz._download.read_pinned_checksums",
                return_value={"asset.tar.xz": "0" * 64},
            ):
                with pytest.raises(UpdateError, match="SHA-256 mismatch"):
                    dl.verify_checksum(f, "asset.tar.xz")

    def test_missing_pinned_entry_fails_closed(self) -> None:
        """Test an asset with no pinned digest is rejected (fail closed)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "asset"
            f.write_bytes(b"data")
            with patch("py7zz._download.read_pinned_checksums", return_value={}):
                with pytest.raises(UpdateError, match="No pinned SHA-256"):
                    dl.verify_checksum(f, "asset.tar.xz")

    def test_unix_extraction_rejects_tampered_archive(self) -> None:
        """Test extract_unix_binary rejects a download whose digest mismatches.

        # Reason: verification must happen BEFORE tarfile touches the bytes;
        the final binary path must never be created.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir) / "2601" / "linux-x64"
            target_dir.mkdir(parents=True)
            binary_path = target_dir / "7zz"

            def fake_download(url: str, dest: Path) -> None:
                dest.write_bytes(b"evil bytes")

            with patch.object(dl, "download_to_file", side_effect=fake_download), patch(
                "py7zz._download.read_pinned_checksums",
                return_value={"7z2601-linux-x64.tar.xz": "0" * 64},
            ):
                with pytest.raises(UpdateError, match="SHA-256 mismatch"):
                    dl.extract_unix_binary(
                        "26.01", "linux", "x64", target_dir, binary_path
                    )

            assert not binary_path.exists()
            # No staging leftovers either.
            assert list(target_dir.iterdir()) == []


class TestFindExtractedMember:
    """Test deterministic SFX member selection (issue #35 item 4)."""

    def test_prefers_exact_top_level_path(self) -> None:
        """Test a top-level member wins over nested duplicates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "7z.exe").write_bytes(b"TOP")
            nested = root / "sub"
            nested.mkdir()
            (nested / "7z.exe").write_bytes(b"NESTED")

            found = dl._find_extracted_member(root, "7z.exe")
            assert found is not None
            assert found.read_bytes() == b"TOP"

    def test_fallback_is_sorted_and_deterministic(self) -> None:
        """Test nested-only duplicates resolve to the lexicographically first."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            for sub in ("zeta", "alpha"):
                d = root / sub
                d.mkdir()
                (d / "7z.exe").write_bytes(sub.encode())

            found = dl._find_extracted_member(root, "7z.exe")
            assert found is not None
            assert found.read_bytes() == b"alpha"

    def test_missing_member_returns_none(self) -> None:
        """Test a member absent from the tree returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            assert dl._find_extracted_member(Path(tmpdir), "7z.exe") is None

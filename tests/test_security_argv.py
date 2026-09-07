# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""
Tests for argument-list hygiene and path validation.

Covers the defenses that keep archive-controlled member names from being parsed
as 7zz switches, keep staged member names inside their temporary directory, and
keep archive passwords out of error messages.
"""

import contextlib
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from py7zz.core import SevenZipFile, find_7z_binary, run_7z
from py7zz.exceptions import SecurityError
from py7zz.security import (
    build_7z_args,
    ensure_within_directory,
    is_within_directory,
    redact_password_args,
    validate_member_path,
)


def assert_positionals_are_shielded(args, archive, names=()):
    """
    Assert that an argument list keeps every positional behind the terminator.

    Args:
        args: Argument list handed to 7zz
        archive: Expected archive path
        names: Member names expected after the archive path
    """
    assert "--" in args, f"missing switch terminator: {args}"
    terminator = args.index("--")

    # Everything between the command and the terminator must be a switch
    for switch in args[1:terminator]:
        assert switch.startswith("-"), f"{switch!r} is not a switch: {args}"

    assert args[terminator + 1] == str(archive)

    positionals = args[terminator + 2 :]
    for name in names:
        assert str(name) in positionals, f"{name!r} missing from {positionals}"


class TestBuild7zArgs:
    """Test the argument assembly helper."""

    def test_places_terminator_between_switches_and_archive(self):
        """Switches come first, then the terminator, then the archive."""
        args = build_7z_args("x", ["-o/out", "-y"], "a.7z")

        assert args == ["x", "-o/out", "-y", "--", "a.7z"]

    def test_member_names_follow_the_archive(self):
        """Member names are placed after the archive path."""
        args = build_7z_args("x", ["-y"], "a.7z", ["-spf", "@list", "ok.txt"])

        assert args == ["x", "-y", "--", "a.7z", "-spf", "@list", "ok.txt"]

    def test_accepts_paths_and_no_names(self):
        """Path objects are stringified and names are optional."""
        args = build_7z_args("l", [], Path("dir/a.7z"))

        assert args == ["l", "--", str(Path("dir/a.7z"))]


class TestValidateMemberPath:
    """Test rejection of member names that escape their destination."""

    @pytest.mark.parametrize(
        "name",
        [
            "../evil.txt",
            "a/../../evil.txt",
            "dir/..",
            "..",
            "/etc/passwd",
            "C:/Windows/System32/evil.dll",
            "D:x",
            "//server/share/evil.txt",
            "\\\\server\\share\\evil.txt",
            "\\windows\\evil.txt",
            "",
            "   ",
        ],
    )
    def test_rejects_escaping_names(self, name):
        """Absolute, drive-qualified and traversing names are refused."""
        with pytest.raises(SecurityError):
            validate_member_path(name)

    @pytest.mark.parametrize(
        "name",
        [
            "a.txt",
            "dir/sub/a.txt",
            "dir\\sub\\a.txt",
            "..hidden.txt",
            "a..b.txt",
            "dir/..hidden/a.txt",
        ],
    )
    def test_accepts_ordinary_names(self, name):
        """Relative names, including ones that merely contain dots, pass."""
        validate_member_path(name)

    def test_error_names_the_parameter(self):
        """The error message identifies the offending parameter."""
        with pytest.raises(SecurityError, match="filename"):
            validate_member_path("../evil.txt", "filename")


class TestDirectoryContainment:
    """Test the resolved-path containment checks."""

    def test_path_inside_base_is_accepted(self, tmp_path):
        """A path below the base directory is inside it."""
        target = tmp_path / "sub" / "a.txt"

        assert is_within_directory(tmp_path, target) is True
        assert ensure_within_directory(tmp_path, target) == target

    def test_base_itself_is_inside(self, tmp_path):
        """The base directory counts as inside itself."""
        assert is_within_directory(tmp_path, tmp_path) is True

    def test_traversal_is_rejected(self, tmp_path):
        """A traversing path resolves outside the base directory."""
        target = tmp_path / ".." / "escaped.txt"

        assert is_within_directory(tmp_path, target) is False
        with pytest.raises(SecurityError):
            ensure_within_directory(tmp_path, target)

    def test_absolute_join_is_rejected(self, tmp_path):
        """Joining an absolute name discards the base and is rejected."""
        target = tmp_path / "/etc/passwd"

        assert is_within_directory(tmp_path, target) is False


class TestRedactPasswordArgs:
    """Test masking of the 7zz password switch."""

    def test_masks_the_password_value(self):
        """The password switch is replaced by a placeholder."""
        args = redact_password_args(["l", "-slt", "-pSuperSecret123", "--", "a.7z"])

        assert args == ["l", "-slt", "-p***", "--", "a.7z"]

    def test_leaves_other_arguments_untouched(self):
        """Other switches, the terminator and names are preserved."""
        original = ["x", "-o/out", "-y", "-mx9", "--", "a.7z", "-spf"]

        assert redact_password_args(original) == original

    def test_keeps_member_names_that_look_like_the_password_switch(self):
        """A member name after the terminator is never mistaken for a password."""
        args = ["x", "-pSecret", "--", "a.7z", "-photo.jpg"]

        assert redact_password_args(args) == ["x", "-p***", "--", "a.7z", "-photo.jpg"]

    def test_leaves_bare_switch_untouched(self):
        """A password switch with no value carries nothing to mask."""
        assert redact_password_args(["t", "-p", "--", "a.7z"]) == [
            "t",
            "-p",
            "--",
            "a.7z",
        ]


class TestRunSevenZipRedaction:
    """Test that a failing 7zz call cannot leak the password."""

    def test_failure_masks_password_without_leaving_a_copy(self):
        """Neither the raised error nor its cause chain holds the password."""
        failure = subprocess.CalledProcessError(
            2, ["/bin/7zz", "l", "-pSuperSecret123", "--", "a.7z"], "", "boom"
        )

        with patch("py7zz.core.find_7z_binary", return_value="/bin/7zz"), patch(
            "py7zz.core.subprocess.run", side_effect=failure
        ):
            with pytest.raises(subprocess.CalledProcessError) as excinfo:
                run_7z(["l", "-pSuperSecret123", "--", "a.7z"])

        rendered = str(excinfo.value)
        cause = excinfo.value.__cause__
        chained = "" if cause is None else str(cause)

        assert "SuperSecret123" not in rendered
        assert "SuperSecret123" not in chained
        assert "-p***" in rendered

        # Reason: repr() and error-reporting tools read .args rather than .cmd,
        # so the masked command has to reach both.
        assert "SuperSecret123" not in repr(excinfo.value)
        assert "SuperSecret123" not in str(excinfo.value.args)


class TestCallSitesShieldPositionals:
    """Test that each 7zz invocation puts positionals behind the terminator."""

    def _archive(self, tmp_path, mode="r"):
        archive = tmp_path / "archive.7z"
        archive.write_bytes(b"stub")
        return SevenZipFile(archive, mode), archive

    def test_extract(self, tmp_path):
        """extract() shields the archive path."""
        sz, archive = self._archive(tmp_path)

        with patch("py7zz.core.run_7z") as mock_run:
            sz.extract(tmp_path / "out")

        assert_positionals_are_shielded(mock_run.call_args[0][0], archive)

    def test_extractall_with_members(self, tmp_path):
        """extractall(members=...) shields the archive and the member names."""
        sz, archive = self._archive(tmp_path)
        members = ["-spf", "ok.txt"]

        with patch("py7zz.core.run_7z") as mock_run:
            sz.extractall(tmp_path / "out", members=members)

        assert_positionals_are_shielded(mock_run.call_args[0][0], archive, members)

    def test_testzip(self, tmp_path):
        """testzip() shields the archive path."""
        sz, archive = self._archive(tmp_path)

        with patch("py7zz.core.run_7z") as mock_run:
            sz.testzip()

        assert_positionals_are_shielded(mock_run.call_args[0][0], archive)

    def test_read(self, tmp_path):
        """read() shields the member name taken from the archive listing."""
        sz, archive = self._archive(tmp_path)
        info = Mock()
        info.filename = "-spf"

        with patch("py7zz.core.run_7z") as mock_run, patch.object(
            SevenZipFile, "infolist", return_value=[info]
        ):
            with pytest.raises(Exception):  # noqa: B017 - extraction result is absent
                sz.read("-spf")

        assert_positionals_are_shielded(mock_run.call_args[0][0], archive, ["-spf"])

    def test_add(self, tmp_path):
        """add() shields the archive path and the source path."""
        source = tmp_path / "payload.txt"
        source.write_text("data")
        archive = tmp_path / "archive.7z"
        sz = SevenZipFile(archive, "w")

        with patch("py7zz.core.run_7z") as mock_run:
            sz.add(source)

        assert_positionals_are_shielded(mock_run.call_args[0][0], archive, [source])

    def test_add_with_arcname(self, tmp_path):
        """add(arcname=...) routes through run_7z with the terminator in place."""
        source = tmp_path / "payload.txt"
        source.write_text("data")
        archive = tmp_path / "archive.7z"
        sz = SevenZipFile(archive, "w")

        with patch("py7zz.core.run_7z") as mock_run:
            sz.add(source, arcname="dir/renamed.txt")

        args = mock_run.call_args[0][0]
        assert_positionals_are_shielded(args, archive.resolve())


class TestWritestrRejectsEscapingNames:
    """Test that staged member names cannot leave the temporary directory."""

    @pytest.mark.parametrize("filename", ["../escape.txt", "/tmp/escape.txt"])
    def test_rejects_escaping_filename(self, tmp_path, filename):
        """An escaping filename is refused before anything is written."""
        sz = SevenZipFile(tmp_path / "archive.7z", "w")

        with patch("py7zz.core.run_7z") as mock_run:
            with pytest.raises(SecurityError):
                sz.writestr(filename, "payload")

        mock_run.assert_not_called()
        assert not (tmp_path.parent / "escape.txt").exists()

    def test_accepts_ordinary_filename(self, tmp_path):
        """An ordinary relative filename is still accepted."""
        sz = SevenZipFile(tmp_path / "archive.7z", "w")

        with patch("py7zz.core.run_7z") as mock_run:
            sz.writestr("dir/ok.txt", "payload")

        mock_run.assert_called_once()


def _binary_or_skip():
    """Return the 7zz binary path, skipping the test when it is unavailable."""
    try:
        return find_7z_binary()
    except Exception:  # pragma: no cover - depends on the install layout
        pytest.skip("7zz binary is not available")


class TestRealArchiveRegressions:
    """End-to-end regressions against a real 7zz binary."""

    def test_switch_named_member_cannot_escape_the_output_directory(self, tmp_path):
        """A member named '-spf' must not be honoured as a 7zz switch."""
        binary = _binary_or_skip()

        victim = tmp_path / "victim" / "owned.txt"
        victim.parent.mkdir()
        victim.write_text("ATTACKER-CONTENT")

        staging = tmp_path / "staging"
        staging.mkdir()
        (staging / "-spf").write_text("")

        archive = tmp_path / "evil.7z"
        # Store the victim under its absolute path, then a member named '-spf'
        subprocess.run(
            [binary, "a", "-spf", str(archive), str(victim)],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [binary, "a", str(archive), "--", "-spf"],
            cwd=str(staging),
            check=True,
            capture_output=True,
        )

        victim.write_text("HOST-CONTENT")

        sz = SevenZipFile(archive, "r")
        for name in sz.namelist():
            # Only the side effect on the victim file matters here
            with contextlib.suppress(Exception):
                sz.read(name)

        assert victim.read_text() == "HOST-CONTENT"

    def test_absolute_member_reads_the_extracted_copy(self, tmp_path):
        """read() must return archived bytes, never the host file's bytes."""
        binary = _binary_or_skip()

        host_file = tmp_path / "host" / "secret.txt"
        host_file.parent.mkdir()
        host_file.write_text("ARCHIVED-BYTES")

        archive = tmp_path / "absolute.7z"
        subprocess.run(
            [binary, "a", "-spf", str(archive), str(host_file)],
            check=True,
            capture_output=True,
        )

        host_file.write_text("HOST-ONLY-BYTES")

        sz = SevenZipFile(archive, "r")
        member = sz.namelist()[0]

        assert sz.read(member) == b"ARCHIVED-BYTES"

# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""Tests for the py7zz CLI entry point."""

import sys
from unittest.mock import Mock, patch

import py7zz.cli as cli


class TestVersionCommand:
    """Test the --version / -V fast path."""

    def test_version_prints_package_and_bundled_versions(self, capsys) -> None:
        """Test --version prints both py7zz and bundled 7zz versions."""
        with patch.object(sys, "argv", ["py7zz", "--version"]):
            cli.main()
        out = capsys.readouterr().out
        assert "py7zz " in out
        assert "7zz   " in out
        # The bundled version comes from the shared pinned-file reader.
        assert "unknown" not in out

    def test_version_uses_shared_pinned_reader(self, capsys) -> None:
        """Test the version command reads via py7zz._pinned (single reader)."""
        with patch.object(sys, "argv", ["py7zz", "-V"]), patch(
            "py7zz._pinned.read_pinned_7zz_version", return_value="99.99"
        ):
            cli.main()
        assert "7zz   99.99 (bundled)" in capsys.readouterr().out


class TestPassThrough:
    """Test the pass-through path to the 7zz binary.

    # Reason: regression guard for the v1.3.0 bug where `import os` lived
    inside the --version branch, making every pass-through invocation fail
    with an unbound-local NameError before reaching the binary.
    """

    def test_posix_passthrough_execs_binary(self) -> None:
        """Test non-version args reach os.execv with the resolved binary."""
        captured = {}

        def fake_execv(path, argv):
            captured["path"] = path
            captured["argv"] = argv

        with patch.object(sys, "argv", ["py7zz", "i"]), patch(
            "py7zz.cli.find_7z_binary", return_value="/fake/7zz"
        ), patch.object(cli.os, "name", "posix"), patch.object(
            cli.os, "execv", side_effect=fake_execv
        ):
            cli.main()

        assert captured["path"] == "/fake/7zz"
        assert captured["argv"] == ["/fake/7zz", "i"]

    def test_windows_passthrough_uses_subprocess(self) -> None:
        """Test the Windows branch runs the binary and exits with its code."""
        with patch.object(sys, "argv", ["py7zz", "i"]), patch(
            "py7zz.cli.find_7z_binary", return_value="C:\\fake\\7zz.exe"
        ), patch.object(cli.os, "name", "nt"), patch(
            "py7zz.cli.subprocess.run", return_value=Mock(returncode=3)
        ) as mock_run, patch.object(cli.sys, "exit") as mock_exit:
            cli.main()

        mock_run.assert_called_once_with(["C:\\fake\\7zz.exe", "i"])
        mock_exit.assert_called_once_with(3)

    def test_passthrough_does_not_raise_unbound_os(self, capsys) -> None:
        """Test pass-through never hits the unbound-local 'os' error."""
        # Reason: force the POSIX branch so the test exercises the same code
        # path on every CI platform; Windows would otherwise spawn a real
        # subprocess against the fake binary path.
        with patch.object(sys, "argv", ["py7zz", "l", "x.7z"]), patch(
            "py7zz.cli.find_7z_binary", return_value="/fake/7zz"
        ), patch.object(cli.os, "name", "posix"), patch.object(cli.os, "execv"):
            cli.main()
        err = capsys.readouterr().err
        assert "local variable 'os'" not in err
        assert "py7zz error" not in err

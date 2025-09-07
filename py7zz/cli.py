# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""
Command Line Interface Module

Directly passes through to the official 7zz binary, ensuring users get complete official 7-Zip functionality.
py7zz's value is in automatic binary management and providing Python API.
"""

import os
import subprocess
import sys

from .core import find_7z_binary

## Intentionally minimal: CLI only exposes --version/-V for version string


def main() -> None:
    """
    Main entry point: Handle py7zz-specific commands or pass through to official 7zz

    This ensures:
    1. Users get complete official 7zz functionality
    2. py7zz-specific commands are handled properly
    3. No need to maintain parameter mapping and feature synchronization
    4. py7zz focuses on Python API and binary management
    """
    try:
        # Handle py7zz-specific minimal commands
        if len(sys.argv) > 1:
            command = sys.argv[1]

            if command in ["--version", "-V"]:
                # Handle quick version command: print only version string
                try:
                    from .version import get_version as _get_version

                    print(_get_version())
                except Exception as _e:
                    print(f"py7zz error: {_e}", file=sys.stderr)
                    sys.exit(1)
                return

        # Get py7zz-managed 7zz binary
        binary_path = find_7z_binary()

        # Direct pass-through of all command line arguments
        cmd = [binary_path] + sys.argv[1:]

        # Use exec to replace current process, ensuring signal handling behavior is consistent with native 7zz
        if os.name == "nt":  # Windows
            # Use subprocess on Windows and wait for result
            result = subprocess.run(cmd)
            sys.exit(result.returncode)
        else:  # Unix-like systems
            # Use execv to replace process on Unix
            os.execv(binary_path, cmd)

    except Exception as e:
        print(f"py7zz error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

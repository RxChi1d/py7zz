"""
Command Line Interface Module

Directly passes through to the official 7zz binary, ensuring users get complete official 7-Zip functionality.
py7zz's value is in automatic binary management and providing Python API.
"""

import json
import os
import subprocess
import sys

from .bundled_info import get_version_info
from .core import find_7z_binary


def print_version_info(format_type: str = "human") -> None:
    """Print version information in specified format."""
    try:
        info = get_version_info()

        if format_type == "json":
            print(json.dumps(info, indent=2))
        else:
            print(f"py7zz version: {info['py7zz_version']}")
            print(f"Bundled 7zz version: {info['bundled_7zz_version']}")
            print(f"Release type: {info['release_type']}")
            print(f"Release date: {info['release_date']}")
            print(f"GitHub tag: {info['github_tag']}")
            print(f"Changelog: {info['changelog_url']}")
    except Exception as e:
        print(f"py7zz error: {e}", file=sys.stderr)
        sys.exit(1)


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
        # Handle py7zz-specific commands
        if len(sys.argv) > 1:
            command = sys.argv[1]

            if command == "version":
                # Handle version command
                format_type = "human"
                if len(sys.argv) > 2 and sys.argv[2] == "--format":
                    if len(sys.argv) > 3:
                        format_type = sys.argv[3]
                    else:
                        print("Error: --format requires a value (human or json)", file=sys.stderr)
                        sys.exit(1)

                print_version_info(format_type)
                return

            elif command in ["--py7zz-version", "-V"]:
                # Handle quick version command
                print_version_info("human")
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

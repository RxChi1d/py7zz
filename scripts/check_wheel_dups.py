#!/usr/bin/env python3

# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors

"""
Wheel Duplicate Filename Checker

This script checks Python wheel (.whl) files for duplicate filenames in local headers,
which can cause PyPI to reject uploads with "Duplicate filename in local headers" error.

The script checks for:
1. Exact duplicate filenames
2. Case-insensitive duplicate filenames (important for cross-platform compatibility)
3. Provides detailed output for debugging

Usage:
    python scripts/check_wheel_dups.py [wheel_files...]
    python scripts/check_wheel_dups.py dist/*.whl
"""

import argparse
import collections
import glob
import sys
import zipfile
from pathlib import Path
from typing import List, Tuple


class Colors:
    """ANSI color codes for terminal output."""

    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    CYAN = "\033[0;36m"
    BOLD = "\033[1m"
    NC = "\033[0m"  # No Color


def print_status(message: str) -> None:
    """Print info message with color."""
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")


def print_success(message: str) -> None:
    """Print success message with color."""
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")


def print_warning(message: str) -> None:
    """Print warning message with color."""
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")


def print_error(message: str) -> None:
    """Print error message with color."""
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")


def print_header(message: str) -> None:
    """Print header message with color."""
    print(f"{Colors.CYAN}=== {message} ==={Colors.NC}")


def check_wheel_duplicates(wheel_path: str) -> Tuple[bool, List[str], List[str], int]:
    """
    Check a wheel file for duplicate filenames.

    Args:
        wheel_path: Path to the wheel file

    Returns:
        Tuple of (has_issues, exact_duplicates, case_duplicates, total_files)
    """
    try:
        with zipfile.ZipFile(wheel_path, "r") as zip_file:
            # Get all filenames from the zip info list
            all_filenames = [info.filename for info in zip_file.infolist()]

        # Check for exact duplicates
        filename_counts = collections.Counter(all_filenames)
        exact_duplicates = [
            filename for filename, count in filename_counts.items() if count > 1
        ]

        # Check for case-insensitive duplicates
        lowercase_counts = collections.Counter(
            filename.lower() for filename in all_filenames
        )
        case_sensitive_duplicates = []

        for lowercase_name, count in lowercase_counts.items():
            if count > 1:
                # Find all original filenames that map to this lowercase version
                matching_originals = [
                    f for f in all_filenames if f.lower() == lowercase_name
                ]
                if len(set(matching_originals)) > 1:  # Different case variations exist
                    case_sensitive_duplicates.append(lowercase_name)

        has_issues = len(exact_duplicates) > 0 or len(case_sensitive_duplicates) > 0

        return (
            has_issues,
            exact_duplicates,
            case_sensitive_duplicates,
            len(all_filenames),
        )

    except zipfile.BadZipFile:
        print_error(f"Invalid or corrupted wheel file: {wheel_path}")
        return True, [], [], 0
    except Exception as e:
        print_error(f"Error reading wheel file {wheel_path}: {e}")
        return True, [], [], 0


def show_wheel_contents(wheel_path: str, show_all: bool = False) -> None:
    """Show contents of a wheel file."""
    try:
        with zipfile.ZipFile(wheel_path, "r") as zip_file:
            filenames = sorted([info.filename for info in zip_file.infolist()])

        print_status(f"Contents of {wheel_path} ({len(filenames)} files):")

        for filename in filenames:
            if show_all or not filename.endswith(
                "/"
            ):  # Skip directories unless showing all
                print(f"  {filename}")

    except Exception as e:
        print_error(f"Error reading wheel contents {wheel_path}: {e}")


def find_wheel_files(patterns: List[str]) -> List[str]:
    """Find wheel files matching the given patterns."""
    wheel_files = []

    for pattern in patterns:
        if "*" in pattern or "?" in pattern:
            # Use glob for patterns
            matches = glob.glob(pattern)
            wheel_files.extend(matches)
        else:
            # Direct file path
            if Path(pattern).exists():
                wheel_files.append(pattern)
            else:
                print_warning(f"File not found: {pattern}")

    # Filter to only .whl files and remove duplicates
    wheel_files = list({f for f in wheel_files if f.endswith(".whl")})

    return sorted(wheel_files)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check Python wheel files for duplicate filenames",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s dist/*.whl                    # Check all wheels in dist/
  %(prog)s dist/mypackage-1.0.0-py3-none-any.whl  # Check specific wheel
  %(prog)s --show-contents dist/*.whl    # Show contents of wheels
  %(prog)s --verbose dist/*.whl          # Detailed output
        """,
    )

    parser.add_argument(
        "wheels",
        nargs="*",
        default=["dist/*.whl"],
        help="Wheel files or patterns to check (default: dist/*.whl)",
    )

    parser.add_argument(
        "--show-contents", action="store_true", help="Show contents of each wheel file"
    )

    parser.add_argument(
        "--show-all-contents",
        action="store_true",
        help="Show all contents including directories",
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Find wheel files
    wheel_files = find_wheel_files(args.wheels)

    if not wheel_files:
        print_error("No wheel files found")
        if args.wheels == ["dist/*.whl"]:
            print_status("Tip: Run 'python -m build' to create wheel files first")
        return 1

    print_header("Wheel Duplicate Filename Checker")
    print_status(f"Checking {len(wheel_files)} wheel file(s)")

    overall_success = True
    total_issues = 0

    for wheel_path in wheel_files:
        print()
        print_status(f"Checking: {wheel_path}")

        # Show contents if requested
        if args.show_contents or args.show_all_contents:
            show_wheel_contents(wheel_path, args.show_all_contents)
            print()

        # Check for duplicates
        has_issues, exact_dups, case_dups, total_files = check_wheel_duplicates(
            wheel_path
        )

        if has_issues:
            overall_success = False
            total_issues += 1

            print_error(f"Issues found in {wheel_path}:")

            if exact_dups:
                print(f"  {Colors.RED}Exact duplicates:{Colors.NC}")
                for dup in exact_dups:
                    print(f"    - {dup}")

            if case_dups:
                print(f"  {Colors.RED}Case-insensitive duplicates:{Colors.NC}")
                for dup in case_dups:
                    # Show the actual filenames that conflict
                    try:
                        with zipfile.ZipFile(wheel_path, "r") as zip_file:
                            all_filenames = [
                                info.filename for info in zip_file.infolist()
                            ]
                            matching = [f for f in all_filenames if f.lower() == dup]
                            print(f"    - {dup}: {matching}")
                    except Exception:
                        print(f"    - {dup}")

        else:
            print_success(f"No duplicate filenames found ({total_files} files)")

        if args.verbose:
            print_status(f"Total files in wheel: {total_files}")

    # Summary
    print()
    print_header("Summary")

    if overall_success:
        print_success(
            f"✅ All {len(wheel_files)} wheel(s) passed duplicate filename checks"
        )
        print_status("Wheels should be acceptable for PyPI upload")
        return 0
    else:
        print_error(f"❌ {total_issues} wheel(s) have duplicate filename issues")
        print_error("These wheels will likely be rejected by PyPI")
        print()
        print_status("How to fix:")
        print("  1. Check your build configuration (pyproject.toml)")
        print("  2. Ensure no files are included via multiple sources")
        print("  3. Remove any conflicting include/force-include directives")
        print("  4. Rebuild wheels after fixing configuration")
        return 1


if __name__ == "__main__":
    sys.exit(main())

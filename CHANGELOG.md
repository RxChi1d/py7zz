<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: 2025 py7zz contributors
-->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.3.0] - 2026-06-06

### Added
- **Source Install Support**: py7zz now works when installed from source (e.g., `pip install git+...`). On first use, the version-pinned 7zz binary is automatically downloaded to `~/.cache/py7zz/` on all supported platforms (Windows x64/ARM64, macOS, Linux x86_64/ARM64). Set `PY7ZZ_NO_AUTODOWNLOAD=1` to opt out in air-gapped or CI environments.

### Fixed
- **Windows Auto-Download**: The Windows auto-download path previously stored the raw SFX installer file instead of extracting the actual `7z.exe` and `7z.dll` binaries, making the cached entry unusable. The binary is now correctly extracted before caching.

## [1.2.0] - 2026-06-06

### Added
- **ARM64 Wheel Support**: Native wheels for Linux ARM64 and Windows ARM64 (Windows ARM64 requires Python 3.11+).
- **7zz Version Detection**: Automatically tracks and reports bundled 7zz version changes in release notes.

### Changed
- **Linux Wheel Platform Tags**: Corrected the x86_64 wheel tag from `manylinux1_x86_64` to the dual `manylinux_2_17_x86_64.manylinux2014_x86_64` form (the new ARM64 wheel uses the matching aarch64 tags). Systems with glibc older than 2.17 are no longer offered the wheel by pip; previously, pip would install the wheel on those systems but the bundled binary would fail at runtime. Each release now verifies the bundled binary's actual glibc requirement against the wheel tag before publishing.
- **Release Note Structure**: Adopted nested "Keep a Changelog" hierarchy for clearer section separation.
- **Category Standardization**: Aligned categories with Conventional Changelog (Angular preset) standards.

### Removed
- **Development Dependencies**: Removed unused `pyyaml` and `zstandard` packages and obsolete documentation.

## [1.2.0a1] - 2026-06-06

### Added
- Pre-release validating the ARM64 release pipeline end to end: native Linux and Windows ARM64 wheels built, verified, and published alongside the existing platforms.

## [1.1.4] - 2026-04-28

### Changed
- **Bundled 7-Zip**: Updated bundled 7zz from 26.00 to 26.01.

## [1.1.3] - 2026-02-16

### Changed
- **Bundled 7-Zip**: Updated bundled 7zz to 26.00.
- **Release Automation**: Tag creation moved to a dedicated owner-triggered workflow for more reliable release runs.

## [1.1.2] - 2025-12-13

### Added
- **Bundled 7zz Version Locking & PR-Only Updates**: Lock bundled 7zz in `py7zz/7zz_version.txt` and add a scheduled check-upstream workflow that opens/refreshes a single PR (no direct push/tag; release remains owner-driven).
- **Repository Guidance**: Document AI attribution rules and required shell tool usage to align with repo standards.

## [1.1.1] - 2025-09-07

### Fixed
- **Filename Listing and Reading with Spaces**: Preserve multiple consecutive spaces and avoid truncation when listing contents; `read()` reliably locates files like `puzzles/puzzle 10.txt`.
- **Robust Listing Parser**: Accept minimal `-slt` outputs without separators, improving reliability of `infolist()` and `open()` across environments.

### Changed
- **List Methods Consistency**: `namelist()` and `getnames()` return files only (directories excluded) for consistency with `zipfile.ZipFile`; both methods now return the same results.
- **CLI Version Command**: Standardized to `--version`/`-V` and now prints only the version string (no extra fields).

### Security
- **Sensitive Data Protection**: Debug logging avoids exposing passwords by masking command arguments when a password is provided.

### Removed
- **CLI Subcommand**: Removed `py7zz version` subcommand and non-standard fields (release type, GitHub tag/changelog link) from CLI output.

## [1.1.0] - 2025-08-10

### Fixed
- **Critical Package Distribution Issue**: Resolved PyPI packages being non-functional due to missing binaries (wheels were only 86KB instead of required multi-MB with 7zz executables)
- **Version Information Display**: Fixed "Bundled 7zz version: unknown" issue by implementing intelligent auto-detection system
- **Python 3.8 Compatibility**: Resolved circular dependency causing infinite recursion and test failures on older Python versions
- **Cross-Platform Binary Support**: Enhanced macOS universal2 and Windows executable packaging with proper dependency inclusion

### Added
- **Smart Version Detection System**: Zero-maintenance version detection that automatically identifies bundled 7zz version without manual registry updates
- **Streamlined CLI Interface**: Simplified `py7zz -V` output focusing on essential version information (py7zz version and bundled 7zz version only)
- **Comprehensive License Compliance**: Full REUSE specification compliance with automated license scanning and SBOM generation
- **Enhanced API Design**: Improved configuration validation and error handling for better developer experience

### Changed
- **Simplified User Experience**: CLI version output reduced from verbose 6-line format to clean 2-line essential information display
- **Robust Error Handling**: Enhanced graceful degradation when version detection or binary operations fail
- **Modernized Development Workflow**: Integrated pre-commit hooks, automated code quality checks, and streamlined CI/CD pipeline

## [1.0.1] - 2025-08-08

### Fixed
- **Critical Fixes**: Various stability and compatibility improvements

## [1.0.0] - 2025-08-01

### Added
- **Windows Filename Compatibility**: Automatic sanitization of problematic filenames during archive operations, ensuring cross-platform compatibility
- **Enhanced Security Features**: Built-in protection against ZIP bombs and malicious archives with configurable security limits
- **Industry-Standard API Compatibility**: Comprehensive compatibility layer providing drop-in replacement functionality for `zipfile` and `tarfile`
- **Advanced Async Operations**: Enhanced asynchronous archive operations with progress callbacks and better error handling
- **Production-Ready Architecture**: Redesigned core architecture for improved performance, reliability, and maintainability

### Changed
- **Version Management**: Upgraded to automated PEP 440 compliant version management system
- **Documentation Structure**: Complete documentation overhaul following Google style guidelines for better clarity and navigation
- **API Architecture**: Redesigned internal API structure for better performance and future extensibility
- **Error Handling**: Improved exception hierarchy with more specific error types for better debugging

### Fixed
- **Cross-Platform Compatibility**: Resolved Windows-specific issues with filename handling and path operations
- **Python Version Support**: Fixed compatibility issues across Python 3.8+ versions
- **Archive Reliability**: Improved stability and error handling for various archive formats and edge cases

## [1.0.0b2] - 2025-07-31

### Added
- Comprehensive testing and validation improvements
- Enhanced stability based on beta1 user feedback

### Fixed
- Minor bugs and compatibility issues identified in beta testing

## [1.0.0b1] - 2025-07-31

### Added
- Feature-complete beta release for user testing
- All major functionality implemented and ready for validation

## [1.0.0a1] - 2025-07-XX

### Added
- Initial alpha release for early adopters and testing
- Core archive operations and cross-platform 7zz integration
- Basic API implementation with fundamental features

## [0.1.1] - 2025-07-XX

### Added
- **Python 3.13 Support**: Extended compatibility to include Python 3.13
- **Release Automation**: Comprehensive GitHub Release automation with auto-generated release notes
- **Contributing Guidelines**: Detailed contributing documentation and GitHub templates

### Fixed
- **Python Compatibility**: Resolved compatibility issues across different Python versions
- **CI/CD Pipeline**: Improved workflow reliability and test coverage
- **Documentation**: Fixed README badges and improved project documentation

### Changed
- **Development Workflow**: Streamlined development process with industry-standard tooling
- **Testing Infrastructure**: Enhanced test coverage and dynamic version system support

## [0.1.0] - 2025-07-XX

### Added
- **Initial Release**: First stable release of py7zz
- **Cross-Platform Support**: Native support for macOS, Linux, and Windows platforms
- **7-Zip Integration**: Bundled 7zz binary for seamless archive operations
- **Python API**: Comprehensive Python interface for archive manipulation

[Unreleased]: https://github.com/rxchi1d/py7zz/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/rxchi1d/py7zz/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/rxchi1d/py7zz/compare/v1.1.4...v1.2.0
[1.2.0a1]: https://github.com/rxchi1d/py7zz/compare/v1.1.4...v1.2.0a1
[1.1.4]: https://github.com/rxchi1d/py7zz/compare/v1.1.3...v1.1.4
[1.1.3]: https://github.com/rxchi1d/py7zz/compare/v1.1.2...v1.1.3
[1.1.2]: https://github.com/rxchi1d/py7zz/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/rxchi1d/py7zz/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/rxchi1d/py7zz/compare/v1.0.0...v1.1.0
[1.0.1]: https://github.com/rxchi1d/py7zz/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/rxchi1d/py7zz/compare/v0.1.1...v1.0.0
[1.0.0b2]: https://github.com/rxchi1d/py7zz/compare/v1.0.0b1...v1.0.0b2
[1.0.0b1]: https://github.com/rxchi1d/py7zz/compare/v1.0.0a1...v1.0.0b1
[1.0.0a1]: https://github.com/rxchi1d/py7zz/compare/v0.1.1...v1.0.0a1
[0.1.1]: https://github.com/rxchi1d/py7zz/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/rxchi1d/py7zz/releases/tag/v0.1.0

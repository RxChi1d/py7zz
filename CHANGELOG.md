<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: 2025 py7zz contributors
-->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **7zz Version Detection**: Automatically tracks and reports bundled 7zz version changes in release notes.

### Changed
- **Release Note Structure**: Adopted nested "Keep a Changelog" hierarchy for clearer section separation.
- **Category Standardization**: Aligned categories with Conventional Changelog (Angular preset) standards.

### Removed
- **Development Dependencies**: Removed unused `pyyaml` and `zstandard` packages and obsolete documentation.

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

[Unreleased]: https://github.com/rxchi1d/py7zz/compare/v1.1.2...HEAD
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

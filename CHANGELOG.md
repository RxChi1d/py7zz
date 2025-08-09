<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: 2025 py7zz contributors
-->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **PyPI Upload Issues**: Fixed "Duplicate filename in local headers" error preventing wheel uploads
- **Platform-Specific Wheels**: Replaced macOS universal2 binaries with separate ARM64 and x86_64 wheels
- **Windows Functionality**: Ensured 7z.dll inclusion for complete format support

### Added
- **Duplicate Detection**: Comprehensive wheel filename checking prevents PyPI rejection
- **TestPyPI Validation**: Two-stage upload process validates packages before production
- **Enhanced CI/CD**: Multi-platform build matrix for optimized platform-specific wheels
- **Binary Management**: Unified download script for 7zz binaries across all platforms

### Changed
- **Release Process**: Updated GitHub Actions release workflow for separate platform builds
- **File Structure**: Streamlined binary packaging reduces wheel complexity
- **Release Strategy**: Automated TestPyPI-first workflow ensures release quality

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

[Unreleased]: https://github.com/rxchi1d/py7zz/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/rxchi1d/py7zz/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/rxchi1d/py7zz/compare/v0.1.1...v1.0.0
[1.0.0b2]: https://github.com/rxchi1d/py7zz/compare/v1.0.0b1...v1.0.0b2
[1.0.0b1]: https://github.com/rxchi1d/py7zz/compare/v1.0.0a1...v1.0.0b1
[1.0.0a1]: https://github.com/rxchi1d/py7zz/compare/v0.1.1...v1.0.0a1
[0.1.1]: https://github.com/rxchi1d/py7zz/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/rxchi1d/py7zz/releases/tag/v0.1.0

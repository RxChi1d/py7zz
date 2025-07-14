# Binary Directory

This directory contains platform-specific 7zz binaries for distribution.

## Structure

- `macos/` - macOS binaries (x86_64 and arm64)
- `linux/` - Linux binaries (x86_64 and arm64)  
- `windows/` - Windows binaries (x86_64)

## Manual Download Instructions

For M1 milestone, binaries need to be manually downloaded from:
https://github.com/ip7z/7zip/releases

### macOS
Download `7z*-mac.tar.xz` and extract `7zz` to `macos/`

### Linux
Download `7z*-linux-x64.tar.xz` and extract `7zz` to `linux/`

### Windows
Download `7z*-x64.exe` and extract `7zz.exe` to `windows/`

## Future Implementation
The updater module (M3) will automate this process via GitHub API.
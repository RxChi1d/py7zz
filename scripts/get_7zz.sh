#!/usr/bin/env bash

# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors

# Universal 7zz binary downloader for py7zz
# Downloads 7zz binaries for different platforms and architectures
# Supports: macOS (arm64, x86_64, universal2), Linux (x86_64), Windows (x64)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1" >&2
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" >&2
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" >&2
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

print_header() {
    echo -e "${CYAN}=== $1 ===${NC}" >&2
}

# Default values
SEVEN_ZIP_VERSION="" 
BASE_URL="https://7-zip.org/a"
PLATFORM=""
ARCH=""
OUTPUT_DIR="py7zz/bin"
BUILD_DIR="build"
VERSION_FILE="py7zz/7zz_version.txt"

# Modes
MODE_DOWNLOAD="download"
MODE_DETECT_ONLY="detect"
MODE_UPDATE_CONFIG="update"
MODE_GET_CURRENT="get_current"
CURRENT_MODE="$MODE_DOWNLOAD"

# Show help
show_help() {
    cat << EOF
7zz Binary Downloader for py7zz

Usage: $0 [OPTIONS]

Options:
  --os, --platform OS    Target OS: macos, linux, windows
  --arch ARCH            Target architecture: universal2, x86_64
  --version VERSION      Specific 7-Zip version to download (overrides file)
  --output DIR           Output directory (default: $OUTPUT_DIR)
  --build-dir DIR        Build directory for temporary files (default: $BUILD_DIR)
  
  --detect-latest        Detect latest version from website and exit (prints version)
  --get-current          Print currently configured version from file and exit
  --update-config        Detect latest version, update configuration file, and proceed
  
  --help, -h             Show this help message

Default Behavior:
  Reads version from $VERSION_FILE and downloads that version.

Supported combinations:
  macOS:   universal2 (official 7-Zip distribution supports both ARM64 and x86_64)
  Linux:   x86_64
  Windows: x86_64 (includes 7z.exe + 7z.dll for complete functionality)
EOF
}

# Auto-detect platform and architecture
auto_detect_platform() {
    local os_name=$(uname -s)
    local arch_name=$(uname -m)

    case "$os_name" in
        Darwin)
            PLATFORM="macos"
            ARCH="universal2"  # 7-Zip only provides universal2 for macOS
            ;;
        Linux)
            PLATFORM="linux"
            case "$arch_name" in
                x86_64) ARCH="x86_64" ;;
                *) ARCH="x86_64" ;;  # Default fallback
            esac
            ;;
        CYGWIN*|MINGW*|MSYS*)
            PLATFORM="windows"
            ARCH="x64"
            ;;
        *)
            print_error "Unsupported platform: $os_name"
            exit 1
            ;;
    esac

    print_status "Auto-detected: $PLATFORM $ARCH"
}

# Auto-detect latest 7-Zip version from website
detect_latest_version_online() {
    print_status "Detecting latest 7-Zip version from official website..."

    local download_page
    if ! download_page=$(curl -s --max-time 10 "https://7-zip.org/download.html"); then
        print_error "Failed to fetch 7-Zip download page"
        return 1
    fi

    # Extract version from "Download 7-Zip XX.XX" pattern
    local version
    version=$(echo "$download_page" | grep -i "Download 7-Zip" | grep -o "[0-9]\+\.[0-9]\+" | head -1)

    if [ -z "$version" ]; then
        print_error "Could not detect 7-Zip version from download page"
        return 1
    fi

    echo "$version"
}

# Read version from local file
read_version_file() {
    if [ -f "$VERSION_FILE" ]; then
        cat "$VERSION_FILE" | tr -d '[:space:]'
    else
        return 1
    fi
}

# Write version to local file
write_version_file() {
    local version="$1"
    mkdir -p "$(dirname "$VERSION_FILE")"
    echo "$version" > "$VERSION_FILE"
    print_success "Updated configuration file: $VERSION_FILE -> $version"
}

# Download and extract 7zz for macOS universal2
download_macos_universal2() {
    local version_str="${SEVEN_ZIP_VERSION//./}"
    local url="${BASE_URL}/7z${version_str}-mac.tar.xz"
    local archive="${BUILD_DIR}/macos/7z-mac-universal2.tar.xz"
    local extract_dir="${BUILD_DIR}/macos/universal2"

    mkdir -p "$extract_dir"

    print_status "Downloading macOS universal2 from: $url"
    if ! curl -fsSL "$url" -o "$archive"; then
        print_error "Failed to download macOS universal2 version"
        return 1
    fi

    print_status "Extracting macOS universal2..."
    if ! tar -xf "$archive" -C "$extract_dir"; then
        print_error "Failed to extract macOS universal2 archive"
        return 1
    fi

    # Find the 7zz binary
    local binary=$(find "$extract_dir" -name "7zz" -type f | head -n 1)
    if [ -z "$binary" ]; then
        print_error "7zz binary not found in universal2 archive"
        return 1
    fi

    echo "$binary"
}

# Download and extract 7zz for Linux
download_linux() {
    local version_str="${SEVEN_ZIP_VERSION//./}"
    local url="${BASE_URL}/7z${version_str}-linux-x64.tar.xz"
    local archive="${BUILD_DIR}/linux/7z-linux-x64.tar.xz"
    local extract_dir="${BUILD_DIR}/linux/x86_64"

    mkdir -p "$extract_dir"

    print_status "Downloading Linux x86_64 from: $url"
    if ! curl -fsSL "$url" -o "$archive"; then
        print_error "Failed to download Linux x86_64 version"
        return 1
    fi

    print_status "Extracting Linux x86_64..."
    if ! tar -xf "$archive" -C "$extract_dir"; then
        print_error "Failed to extract Linux archive"
        return 1
    fi

    # Find the 7zz binary
    local binary=$(find "$extract_dir" -name "7zz" -type f | head -n 1)
    if [ -z "$binary" ]; then
        print_error "7zz binary not found in Linux archive"
        return 1
    fi

    echo "$binary"
}

# Download and extract 7zz for Windows
download_windows() {
    local version_str="${SEVEN_ZIP_VERSION//./}"
    local url="${BASE_URL}/7z${version_str}-x64.exe"
    local archive="${BUILD_DIR}/windows/7z-windows-x64.exe"
    local extract_dir="${BUILD_DIR}/windows/x64"

    mkdir -p "$extract_dir"

    print_status "Downloading Windows x64 from: $url"
    if ! curl -fsSL "$url" -o "$archive"; then
        print_error "Failed to download Windows x64 version"
        return 1
    fi

    print_status "Extracting Windows x64..."

    # Try different extraction methods
    if command -v 7z &> /dev/null; then
        print_status "Using 7z to extract Windows installer..."
        if ! 7z x "$archive" -o"$extract_dir" -y >&2; then
            print_error "Failed to extract Windows archive with 7z"
            return 1
        fi
    elif command -v unzip &> /dev/null; then
        print_status "Using unzip to extract Windows installer..."
        # Some 7-Zip installers can be extracted as ZIP
        if ! unzip -q "$archive" -d "$extract_dir" 2>/dev/null; then
            print_error "Failed to extract Windows archive with unzip"
            return 1
        fi
    else
        print_error "No suitable extraction tool found for Windows archive"
        print_error "Please install 7z or unzip"
        return 1
    fi

    # Find required files: Windows installer contains 7z.exe (not 7zz.exe)
    local exe_binary=$(find "$extract_dir" -name "7z.exe" -type f | head -n 1)
    local dll_file=$(find "$extract_dir" -name "7z.dll" -type f | head -n 1)

    if [ -z "$exe_binary" ]; then
        print_error "7z.exe not found in Windows installer"
        return 1
    fi

    print_status "Found Windows binary: $(basename "$exe_binary")"

    if [ -z "$dll_file" ]; then
        print_warning "7z.dll not found - Windows functionality may be limited"
    fi

    # Return both files separated by space
    echo "$exe_binary $dll_file"
}

# Main download function
download_7zz() {
    local output_file=""

    print_header "Downloading 7-Zip $SEVEN_ZIP_VERSION for $PLATFORM $ARCH"

    # Clean and create build directory
    rm -rf "$BUILD_DIR"
    mkdir -p "$BUILD_DIR"

    case "$PLATFORM" in
        macos)
            case "$ARCH" in
                universal2)
                    local binary=$(download_macos_universal2)
                    if [ -z "$binary" ]; then
                        print_error "Failed to download macOS universal2 binary"
                        return 1
                    fi

                    output_file="${OUTPUT_DIR}/7zz"
                    mkdir -p "$OUTPUT_DIR"
                    cp "$binary" "$output_file"
                    chmod +x "$output_file"
                    ;;
                *)
                    print_error "Unsupported macOS architecture: $ARCH"
                    return 1
                    ;;
            esac
            ;;
        linux)
            case "$ARCH" in
                x86_64)
                    local binary=$(download_linux)
                    if [ -z "$binary" ]; then
                        print_error "Failed to download Linux binary"
                        return 1
                    fi

                    output_file="${OUTPUT_DIR}/7zz"
                    mkdir -p "$OUTPUT_DIR"
                    cp "$binary" "$output_file"
                    chmod +x "$output_file"
                    ;;
                *)
                    print_error "Unsupported Linux architecture: $ARCH"
                    return 1
                    ;;
            esac
            ;;
        windows)
            case "$ARCH" in
                x86_64)
                    local files=$(download_windows)
                    if [ -z "$files" ]; then
                        print_error "Failed to download Windows files"
                        return 1
                    fi

                    local exe_file=$(echo $files | cut -d' ' -f1)
                    local dll_file=$(echo $files | cut -d' ' -f2)

                    mkdir -p "$OUTPUT_DIR"

                    output_file="${OUTPUT_DIR}/7zz.exe"
                    cp "$exe_file" "$output_file"
                    print_status "Copied $(basename "$exe_file") as 7zz.exe"

                    if [ -n "$dll_file" ] && [ "$dll_file" != "null" ] && [ -f "$dll_file" ]; then
                        cp "$dll_file" "${OUTPUT_DIR}/7z.dll"
                        print_status "Copied 7z.dll for complete Windows functionality"
                    fi
                    ;;
                *)
                    print_error "Unsupported Windows architecture: $ARCH"
                    return 1
                    ;;
            esac
            ;;
        *)
            print_error "Unsupported platform: $PLATFORM"
            return 1
            ;;
    esac

    if [ -z "$output_file" ]; then
        print_error "No output file generated"
        return 1
    fi

    # Verify the binary
    print_status "Binary information:"
    file "$output_file" >&2 || true
    ls -lh "$output_file" >&2

    # Test the binary
    print_status "Testing binary..."
    if "$output_file" --help >/dev/null 2>&1; then
        print_success "Binary test successful"
    else
        print_warning "Binary test failed - may need different dependencies or signing"
    fi

    print_success "7zz binary ready at: $output_file"

    # Clean up
    print_status "Cleaning up temporary files..."
    rm -rf "$BUILD_DIR"

    return 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --platform|--os)
            PLATFORM="$2"
            shift 2
            ;;
        --arch)
            ARCH="$2"
            shift 2
            ;;
        --version)
            SEVEN_ZIP_VERSION="$2"
            shift 2
            ;;
        --detect-latest|--detect-version) # Keep detect-version for partial back-compat (though behavior changed to pure detect)
            CURRENT_MODE="$MODE_DETECT_ONLY"
            shift
            ;;
        --get-current)
            CURRENT_MODE="$MODE_GET_CURRENT"
            shift
            ;;
        --update-config)
            CURRENT_MODE="$MODE_UPDATE_CONFIG"
            shift
            ;;
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --build-dir)
            BUILD_DIR="$2"
            shift 2
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# === MODE EXECUTION ===

# 1. Detect Only Mode
if [ "$CURRENT_MODE" == "$MODE_DETECT_ONLY" ]; then
    if detected_version=$(detect_latest_version_online); then
        echo "$detected_version"
        exit 0
    else
        print_error "Version detection failed"
        exit 1
    fi
fi

# 2. Get Current Mode
if [ "$CURRENT_MODE" == "$MODE_GET_CURRENT" ]; then
    if current_version=$(read_version_file); then
        echo "$current_version"
        exit 0
    else
        print_error "Configuration file not found: $VERSION_FILE"
        exit 1
    fi
fi

# 3. Update Config Mode
if [ "$CURRENT_MODE" == "$MODE_UPDATE_CONFIG" ]; then
    print_status "Checking for updates..."
    if detected_version=$(detect_latest_version_online); then
        print_status "Detected version: $detected_version"
        write_version_file "$detected_version"
        
        # Set version for download
        SEVEN_ZIP_VERSION="$detected_version"
        # Continue to download to verify it works
        print_status "Proceeding to verify download..."
    else
        print_error "Version detection failed"
        exit 1
    fi
fi

# 4. Download Mode (Default)
if [ -z "$SEVEN_ZIP_VERSION" ]; then
    # Try to read from file first
    print_status "Checking configured version..."
    if file_version=$(read_version_file); then
        SEVEN_ZIP_VERSION="$file_version"
        print_success "Using configured version: $SEVEN_ZIP_VERSION"
    else
        print_warning "Configuration file not found. Falling back to auto-detection..."
        if detected_version=$(detect_latest_version_online); then
            SEVEN_ZIP_VERSION="$detected_version"
            print_success "Auto-detected version: $SEVEN_ZIP_VERSION"
        else
            print_error "Could not determine version. Please specify --version or create $VERSION_FILE"
            exit 1
        fi
    fi
fi

# Auto-detect platform if not specified
if [ -z "$PLATFORM" ] || [ -z "$ARCH" ]; then
    print_status "Auto-detecting platform and architecture..."
    auto_detect_platform
fi

# Main execution
print_header "7zz Binary Downloader"
print_status "Platform: $PLATFORM"
print_status "Architecture: $ARCH"
print_status "Version: $SEVEN_ZIP_VERSION"
print_status "Output directory: $OUTPUT_DIR"

download_7zz
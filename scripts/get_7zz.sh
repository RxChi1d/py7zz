#!/usr/bin/env bash

# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors

# Universal 7zz binary downloader for py7zz
# Downloads 7zz binaries for different platforms and architectures
# Supported combinations:
#   macOS:   universal2 (arm64/x86_64 are accepted aliases; the universal2
#            binary covers both)
#   Linux:   x86_64, arm64
#   Windows: x86_64, arm64

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
CHECKSUM_FILE="py7zz/7zz_checksums.txt"
# Canonical source for checksum refresh; byte-identical to the 7-zip.org
# mirrors used by BASE_URL (verified), and matches the runtime download URLs.
GITHUB_RELEASES_URL="https://github.com/ip7z/7zip/releases/download"

# Modes
MODE_DOWNLOAD="download"
MODE_DETECT_ONLY="detect"
MODE_UPDATE_CONFIG="update"
MODE_GET_CURRENT="get_current"
MODE_REFRESH_CHECKSUMS="refresh_checksums"
CURRENT_MODE="$MODE_DOWNLOAD"

# Show help
show_help() {
    cat << EOF
7zz Binary Downloader for py7zz

Usage: $0 [OPTIONS]

Options:
  --os, --platform OS    Target OS: macos, linux, windows
  --arch ARCH            Target architecture: universal2, x86_64, arm64
                         (aliases: aarch64/ARM64 -> arm64; amd64/x64 -> x86_64)
  --version VERSION      Specific 7-Zip version to download (overrides file)
  --output DIR           Output directory (default: $OUTPUT_DIR)
  --build-dir DIR        Build directory for temporary files (default: $BUILD_DIR)

  --detect-latest        Detect latest version from website and exit (prints version)
  --get-current          Print currently configured version from file and exit
  --update-config        Detect latest version, update configuration file, and proceed
  --refresh-checksums    Download all release assets for the configured (or
                         --version) 7-Zip version and rewrite $CHECKSUM_FILE

  --help, -h             Show this help message

Default Behavior:
  Reads version from $VERSION_FILE and downloads that version.

Supported combinations:
  macOS:   universal2 (arm64/x86_64 accepted as aliases; the universal2 binary
           covers both architectures)
  Linux:   x86_64, arm64
  Windows: x86_64, arm64 (includes 7z.exe + 7z.dll for complete functionality)
EOF
}

# Normalize an architecture string to one of: arm64, x86_64, universal2.
#
# Accepts the common spellings emitted by 'uname -m' and user input across
# platforms and maps them onto py7zz's canonical names. Unknown values are
# echoed back unchanged so callers can detect and reject them explicitly.
#
# Args:
#   $1: Raw architecture string (e.g. "aarch64", "AMD64", "arm64").
#
# Outputs:
#   The normalized architecture on stdout.
normalize_arch() {
    local raw="$1"
    case "$raw" in
        # Reason: 'uname -m' and CI inputs use several arm64 spellings.
        aarch64|arm64|ARM64|Arm64) echo "arm64" ;;
        # Reason: x86_64 appears as amd64/x64 on Windows and some toolchains.
        x86_64|amd64|AMD64|x64|X64) echo "x86_64" ;;
        # universal2 is a macOS-only passthrough; covers both architectures.
        universal2) echo "universal2" ;;
        # Unknown value: echo back unchanged so the caller can reject it.
        *) echo "$raw" ;;
    esac
}

# Compute the SHA-256 digest of a file, portably across macOS, Linux, and
# Git Bash on Windows.
#
# Args:
#   $1: File path.
#
# Outputs:
#   The lowercase hex digest on stdout.
compute_sha256() {
    local file="$1"
    if command -v sha256sum &> /dev/null; then
        sha256sum "$file" | awk '{print $1}'
    elif command -v shasum &> /dev/null; then
        shasum -a 256 "$file" | awk '{print $1}'
    else
        print_error "No SHA-256 tool found (need sha256sum or shasum)"
        return 1
    fi
}

# Verify a downloaded asset against the pinned checksum file.
#
# Fails closed: a missing checksum entry is treated as an error, the same as
# a digest mismatch. This mirrors the runtime verification in
# py7zz/_download.py so build-time and runtime share one trust anchor.
#
# Args:
#   $1: Downloaded file path.
#   $2: Release asset name to look up in $CHECKSUM_FILE.
verify_asset_checksum() {
    local file="$1"
    local asset_name="$2"

    if [ ! -f "$CHECKSUM_FILE" ]; then
        print_error "Checksum file not found: $CHECKSUM_FILE"
        return 1
    fi

    # Exact-match lookup on the asset-name column; '#' comments are skipped.
    local expected
    expected=$(awk -v name="$asset_name" '$1 !~ /^#/ && $2 == name {print $1; exit}' "$CHECKSUM_FILE")
    if [ -z "$expected" ]; then
        print_error "No pinned SHA-256 checksum for $asset_name in $CHECKSUM_FILE"
        print_error "Run '$0 --refresh-checksums' after bumping the 7zz version."
        return 1
    fi

    local actual
    if ! actual=$(compute_sha256 "$file"); then
        return 1
    fi

    if [ "$actual" != "$expected" ]; then
        print_error "SHA-256 mismatch for $asset_name: expected $expected, got $actual"
        print_error "The download may be corrupted or tampered with; refusing to use it."
        return 1
    fi

    print_status "Checksum verified for $asset_name"
}

# Regenerate the pinned checksum file for one 7-Zip version.
#
# Downloads every release asset py7zz can consume (all platform binaries plus
# the 7zr.exe runtime bootstrap) from the canonical GitHub release and writes
# their SHA-256 digests to $CHECKSUM_FILE in sha256sum format.
#
# Args:
#   $1: Dotted 7-Zip version (e.g. "26.01").
refresh_checksums() {
    local version="$1"
    local dotless="${version//./}"
    local assets=(
        "7z${dotless}-arm64.exe"
        "7z${dotless}-linux-arm64.tar.xz"
        "7z${dotless}-linux-x64.tar.xz"
        "7z${dotless}-mac.tar.xz"
        "7z${dotless}-x64.exe"
        "7zr.exe"
    )

    local tmpdir
    tmpdir=$(mktemp -d)
    local out="${tmpdir}/7zz_checksums.txt"

    {
        echo "# SHA-256 checksums for the pinned 7-Zip ${version} release assets."
        echo "# Source: https://github.com/ip7z/7zip/releases/tag/${version}"
        echo "# (byte-identical to the https://7-zip.org/a/ mirrors)"
        echo "# Regenerate with: ./scripts/get_7zz.sh --refresh-checksums"
    } > "$out"

    local asset digest
    for asset in "${assets[@]}"; do
        local url="${GITHUB_RELEASES_URL}/${version}/${asset}"
        print_status "Downloading ${asset} for checksum..."
        if ! curl -fsSL "$url" -o "${tmpdir}/${asset}"; then
            print_error "Failed to download $url"
            rm -rf "$tmpdir"
            return 1
        fi
        if ! digest=$(compute_sha256 "${tmpdir}/${asset}"); then
            rm -rf "$tmpdir"
            return 1
        fi
        echo "${digest}  ${asset}" >> "$out"
    done

    cp "$out" "$CHECKSUM_FILE"
    rm -rf "$tmpdir"
    print_success "Updated $CHECKSUM_FILE for 7-Zip $version"
}

# Auto-detect platform and architecture
auto_detect_platform() {
    local os_name
    local arch_name
    os_name=$(uname -s)
    arch_name=$(uname -m)

    # Normalize the detected architecture up front so every branch works with
    # py7zz's canonical names (arm64 / x86_64 / universal2).
    local norm_arch
    norm_arch=$(normalize_arch "$arch_name")

    case "$os_name" in
        Darwin)
            PLATFORM="macos"
            # 7-Zip only ships a universal2 binary for macOS; the detected
            # architecture is irrelevant because universal2 covers both.
            ARCH="universal2"
            ;;
        Linux)
            PLATFORM="linux"
            case "$norm_arch" in
                x86_64|arm64) ARCH="$norm_arch" ;;
                *)
                    # Reason: silently defaulting to x86_64 would download the
                    # wrong binary on unsupported architectures.
                    print_error "Unsupported Linux architecture: $arch_name"
                    exit 1
                    ;;
            esac
            ;;
        CYGWIN*|MINGW*|MSYS*)
            PLATFORM="windows"
            case "$norm_arch" in
                x86_64|arm64) ARCH="$norm_arch" ;;
                *)
                    print_error "Unsupported Windows architecture: $arch_name"
                    exit 1
                    ;;
            esac
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

    if ! verify_asset_checksum "$archive" "7z${version_str}-mac.tar.xz"; then
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
#
# Args:
#   $1: Target architecture (x86_64 or arm64).
download_linux() {
    local target_arch="$1"
    local version_str="${SEVEN_ZIP_VERSION//./}"

    # Map py7zz's canonical architecture onto 7-Zip's asset suffix.
    local asset_arch
    case "$target_arch" in
        x86_64) asset_arch="x64" ;;
        arm64) asset_arch="arm64" ;;
        *)
            print_error "Unsupported Linux architecture: $target_arch"
            return 1
            ;;
    esac

    local url="${BASE_URL}/7z${version_str}-linux-${asset_arch}.tar.xz"
    local archive="${BUILD_DIR}/linux/7z-linux-${asset_arch}.tar.xz"
    local extract_dir="${BUILD_DIR}/linux/${target_arch}"

    mkdir -p "$extract_dir"

    print_status "Downloading Linux ${target_arch} from: $url"
    if ! curl -fsSL "$url" -o "$archive"; then
        print_error "Failed to download Linux ${target_arch} version"
        return 1
    fi

    if ! verify_asset_checksum "$archive" "7z${version_str}-linux-${asset_arch}.tar.xz"; then
        return 1
    fi

    print_status "Extracting Linux ${target_arch}..."
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
#
# Args:
#   $1: Target architecture (x86_64 or arm64).
download_windows() {
    local target_arch="$1"
    local version_str="${SEVEN_ZIP_VERSION//./}"

    # Map py7zz's canonical architecture onto 7-Zip's installer suffix.
    local asset_arch
    case "$target_arch" in
        x86_64) asset_arch="x64" ;;
        arm64) asset_arch="arm64" ;;
        *)
            print_error "Unsupported Windows architecture: $target_arch"
            return 1
            ;;
    esac

    local url="${BASE_URL}/7z${version_str}-${asset_arch}.exe"
    local archive="${BUILD_DIR}/windows/7z-windows-${asset_arch}.exe"
    local extract_dir="${BUILD_DIR}/windows/${target_arch}"

    mkdir -p "$extract_dir"

    print_status "Downloading Windows ${target_arch} from: $url"
    if ! curl -fsSL "$url" -o "$archive"; then
        print_error "Failed to download Windows ${target_arch} version"
        return 1
    fi

    if ! verify_asset_checksum "$archive" "7z${version_str}-${asset_arch}.exe"; then
        return 1
    fi

    print_status "Extracting Windows ${target_arch}..."

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
        # Reason: 7z.exe cannot run without 7z.dll, so a missing DLL is a hard
        # failure rather than a warning. The caller must propagate this.
        print_error "7z.dll not found in Windows installer - cannot continue"
        return 1
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

    # Declared here so they can be assigned separately from declaration below.
    # Reason: 'local var=$(fn)' swallows the function's exit status, so each
    # download result is captured on its own line to preserve set -e semantics.
    local binary=""
    local files=""

    case "$PLATFORM" in
        macos)
            case "$ARCH" in
                universal2)
                    binary=$(download_macos_universal2)
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
                x86_64|arm64)
                    binary=$(download_linux "$ARCH")
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
                x86_64|arm64)
                    files=$(download_windows "$ARCH")
                    if [ -z "$files" ]; then
                        print_error "Failed to download Windows files"
                        return 1
                    fi

                    local exe_file
                    local dll_file
                    exe_file=$(echo "$files" | cut -d' ' -f1)
                    dll_file=$(echo "$files" | cut -d' ' -f2)

                    mkdir -p "$OUTPUT_DIR"

                    output_file="${OUTPUT_DIR}/7zz.exe"
                    cp "$exe_file" "$output_file"
                    print_status "Copied $(basename "$exe_file") as 7zz.exe"

                    # download_windows guarantees a non-empty dll path on success,
                    # so a missing file here is a hard failure.
                    if [ -n "$dll_file" ] && [ -f "$dll_file" ]; then
                        cp "$dll_file" "${OUTPUT_DIR}/7z.dll"
                        print_status "Copied 7z.dll for complete Windows functionality"
                    else
                        print_error "7z.dll missing after extraction - cannot continue"
                        return 1
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
        --refresh-checksums)
            CURRENT_MODE="$MODE_REFRESH_CHECKSUMS"
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

# 3. Refresh Checksums Mode
if [ "$CURRENT_MODE" == "$MODE_REFRESH_CHECKSUMS" ]; then
    if [ -z "$SEVEN_ZIP_VERSION" ]; then
        if ! SEVEN_ZIP_VERSION=$(read_version_file); then
            print_error "Configuration file not found: $VERSION_FILE (or pass --version)"
            exit 1
        fi
    fi
    if refresh_checksums "$SEVEN_ZIP_VERSION"; then
        exit 0
    else
        print_error "Checksum refresh failed"
        exit 1
    fi
fi

# 4. Update Config Mode
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

# 5. Download Mode (Default)
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

# Normalize the architecture for both user-supplied and auto-detected values.
# Auto-detection already normalizes, so this is idempotent there; it primarily
# canonicalizes user input such as aarch64/AMD64/x64.
if [ -n "$ARCH" ]; then
    ARCH=$(normalize_arch "$ARCH")
fi

# macOS ships only a universal2 binary. If the user explicitly requested
# arm64/x86_64 for macOS, accept it but force universal2 and explain why.
if [ "$PLATFORM" == "macos" ] && [ "$ARCH" != "universal2" ]; then
    case "$ARCH" in
        arm64|x86_64)
            print_status "macOS provides a single universal2 binary covering both arm64 and x86_64; using universal2 instead of '$ARCH'."
            ARCH="universal2"
            ;;
        *)
            print_error "Unsupported macOS architecture: $ARCH"
            exit 1
            ;;
    esac
fi

# Main execution
print_header "7zz Binary Downloader"
print_status "Platform: $PLATFORM"
print_status "Architecture: $ARCH"
print_status "Version: $SEVEN_ZIP_VERSION"
print_status "Output directory: $OUTPUT_DIR"

download_7zz

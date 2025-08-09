#!/bin/bash

# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors

# Complete CI workflow simulation for local testing
# This script runs all CI checks locally to minimize remote CI failures

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_section() {
    echo -e "${CYAN}[SECTION]${NC} $1"
}

print_header() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${WHITE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
}

# Function to check if we're in the right directory
check_project_root() {
    if [[ ! -f "pyproject.toml" || ! -d "py7zz" ]]; then
        print_error "This script must be run from the project root directory"
        print_error "Expected: pyproject.toml and py7zz/ directory"
        exit 1
    fi

    if [[ ! -f "scripts/quick-check.sh" ]]; then
        print_error "quick-check.sh script not found. Please ensure it exists in scripts/"
        exit 1
    fi
}

# Function to set up test environment (PY7ZZ_BINARY handling)
setup_test_environment() {
    print_section "Setting up Test Environment"

    # Set up 7zz binary for testing if not already set
    if [ -z "$PY7ZZ_BINARY" ]; then
        print_status "Searching for 7zz/7z binary for testing..."

        # Try to find 7zz in common locations
        if command -v 7zz &> /dev/null; then
            export PY7ZZ_BINARY=$(which 7zz)
            print_success "Auto-detected 7zz binary: $PY7ZZ_BINARY"
        elif command -v 7z &> /dev/null; then
            export PY7ZZ_BINARY=$(which 7z)
            print_success "Auto-detected 7z binary: $PY7ZZ_BINARY"
        else
            print_warning "System 7zz/7z binary not found, some tests may fail"
            print_warning "Hint: Set PY7ZZ_BINARY environment variable to point to your 7zz binary"
            print_warning "Or install 7-Zip: brew install 7-zip (macOS) or apt install 7zip (Ubuntu)"
        fi
    else
        # Ensure environment variable is exported for child processes
        export PY7ZZ_BINARY="$PY7ZZ_BINARY"
        print_success "Using predefined PY7ZZ_BINARY: $PY7ZZ_BINARY"
    fi

    print_success "Test environment setup complete"
}

# Function to run REUSE compliance check
run_reuse_check() {
    print_section "Running REUSE Compliance Check"

    print_status "Checking REUSE compliance..."

    if command -v reuse &> /dev/null; then
        if reuse lint; then
            print_success "REUSE compliance check passed"
        else
            print_error "REUSE compliance check failed"
            return 1
        fi
    else
        print_status "Installing reuse temporarily..."
        if uv run --with reuse reuse lint; then
            print_success "REUSE compliance check passed"
        else
            print_error "REUSE compliance check failed"
            return 1
        fi
    fi
}

# Function to run build verification
run_build_verification() {
    print_section "Running Build Verification"

    print_status "Building wheel and sdist..."

    # Clean previous builds
    rm -rf dist/ build/ *.egg-info/

    if uv run python -m build; then
        print_success "Build completed successfully"
    else
        print_error "Build failed"
        return 1
    fi

    print_status "Verifying license files in packages..."

    # Check wheel contents
    local wheel_file=$(ls dist/*.whl 2>/dev/null | head -n1)
    if [ -n "$wheel_file" ]; then
        print_status "Checking wheel: $wheel_file"
        if uv run python -c "
import zipfile
import sys
z = zipfile.ZipFile('$wheel_file')
required_files = ['LICENSE', 'THIRD_PARTY_NOTICES.md', 'LICENSES/LicenseRef-7zip.txt']
missing = [f for f in required_files if f not in z.namelist()]
if missing:
    print(f'❌ Missing files in wheel: {missing}')
    sys.exit(1)
else:
    print('✅ All required license files found in wheel')
"; then
            print_success "Wheel verification passed"
        else
            print_error "Wheel verification failed"
            return 1
        fi
    else
        print_error "No wheel file found"
        return 1
    fi

    # Check sdist contents
    local sdist_file=$(ls dist/*.tar.gz 2>/dev/null | head -n1)
    if [ -n "$sdist_file" ]; then
        print_status "Checking sdist: $sdist_file"
        if uv run python -c "
import tarfile
import sys
t = tarfile.open('$sdist_file')
names = t.getnames()
required_patterns = ['LICENSE', 'THIRD_PARTY_NOTICES.md', 'LICENSES/LicenseRef-7zip.txt']
missing = [p for p in required_patterns if not any(p in name for name in names)]
if missing:
    print(f'❌ Missing files in sdist: {missing}')
    sys.exit(1)
else:
    print('✅ All required license files found in sdist')
"; then
            print_success "Sdist verification passed"
        else
            print_error "Sdist verification failed"
            return 1
        fi
    else
        print_error "No sdist file found"
        return 1
    fi
}

# Function to run comprehensive tests
run_comprehensive_tests() {
    print_section "Running Comprehensive Tests"

    print_status "Running pytest with detailed output..."

    local pytest_cmd="uv run pytest -v --tb=short"

    if [ -n "$PY7ZZ_BINARY" ]; then
        print_status "Test environment: PY7ZZ_BINARY=$PY7ZZ_BINARY"
        echo -e "${PURPLE}Command: $pytest_cmd${NC}"

        if $pytest_cmd; then
            print_success "All tests passed with 7zz binary available"
        else
            print_error "Some tests failed - please fix test errors"
            return 1
        fi
    else
        print_warning "Running tests without 7zz binary (some tests may be skipped)"
        echo -e "${PURPLE}Command: $pytest_cmd${NC}"

        if $pytest_cmd; then
            print_success "Tests completed (some may have been skipped due to missing 7zz)"
        else
            print_error "Some tests failed - please fix test errors"
            return 1
        fi
    fi
}

# Function to clean up temporary files
cleanup_temp_files() {
    print_status "Cleaning up temporary files..."

    # Remove test artifacts and caches
    rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/
    rm -f .coverage
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

    print_success "Cleanup completed"
}

# Function to display CI simulation summary
display_summary() {
    local exit_code=$1
    local execution_time=$2

    echo
    print_header "CI Workflow Simulation Summary"

    if [[ $exit_code -eq 0 ]]; then
        print_success "🎉 All CI checks passed locally!"
        echo
        echo "Your code is ready to push to remote repository."
        echo "The remote CI should pass without issues."
        echo
        echo "Next steps:"
        echo "  • git add ."
        echo "  • git commit -m \"your commit message\""
        echo "  • git push origin $(git branch --show-current)"
    else
        print_error "❌ Some CI checks failed!"
        echo
        echo "Please fix the issues above before pushing to remote."
        echo "This will help avoid failed CI runs on the remote repository."
        echo
        echo "Troubleshooting tips:"
        echo "  • Review error messages above"
        echo "  • Run 'scripts/quick-check.sh' for faster feedback"
        echo "  • Check test failures with 'uv run pytest -v'"
    fi

    echo
    print_status "Total execution time: ${execution_time} seconds"
    print_header "End of CI Simulation"
}

# Function to show help
show_help() {
    echo "CI Local - Complete CI workflow simulation for py7zz"
    echo
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  --quick-only    Run only quick checks (equivalent to quick-check.sh)"
    echo "  --no-cleanup    Skip cleanup of temporary files and caches"
    echo "  --help, -h      Show this help message"
    echo
    echo "This script simulates the complete CI workflow locally, including:"
    echo "  1. Quick checks (formatting, linting, type checking)"
    echo "  2. REUSE compliance check"
    echo "  3. Build verification (wheel/sdist with license files)"
    echo "  4. Test environment setup (PY7ZZ_BINARY detection)"
    echo "  5. Comprehensive testing with pytest"
    echo "  6. Cleanup of temporary files and caches"
    echo
    echo "Environment variables:"
    echo "  PY7ZZ_BINARY    Path to 7zz binary for testing (auto-detected if not set)"
    echo
    echo "Examples:"
    echo "  $0                    # Run full CI simulation"
    echo "  $0 --quick-only      # Run only format/lint/type checks"
    echo "  $0 --no-cleanup      # Keep temporary files after execution"
    echo
    echo "The script helps catch issues before pushing to the repository,"
    echo "reducing failed CI runs and improving development efficiency."
}

# Main execution
main() {
    local quick_only=false
    local no_cleanup=false
    local start_time=$(date +%s)

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --quick-only)
                quick_only=true
                shift
                ;;
            --no-cleanup)
                no_cleanup=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo
                show_help
                exit 1
                ;;
        esac
    done

    print_header "py7zz Local CI Simulation Started"
    echo -e "${WHITE}Simulating GitHub Actions workflow locally${NC}"
    echo

    check_project_root

    local exit_code=0

    # Step 1: Run quick checks (delegate to quick-check.sh)
    print_section "Step 1: Quick Checks (Format, Lint, Type)"
    chmod +x scripts/quick-check.sh
    if ./scripts/quick-check.sh; then
        print_success "Quick checks completed successfully"
    else
        print_error "Quick checks failed"
        exit_code=1
        # Continue with other checks for full report
    fi

    # If only quick checks requested, exit here
    if [[ "$quick_only" == true ]]; then
        local end_time=$(date +%s)
        local execution_time=$((end_time - start_time))
        display_summary $exit_code $execution_time
        exit $exit_code
    fi

    echo

    # Step 2: REUSE compliance check
    run_reuse_check || exit_code=1

    echo

    # Step 3: Build verification
    run_build_verification || exit_code=1

    echo

    # Step 4: Set up test environment
    setup_test_environment || exit_code=1

    echo

    # Step 5: Comprehensive testing
    run_comprehensive_tests || exit_code=1

    echo

    # Step 6: Cleanup (unless disabled)
    if [[ "$no_cleanup" != true ]]; then
        cleanup_temp_files
    else
        print_status "Skipping cleanup (--no-cleanup flag used)"
    fi

    # Calculate execution time
    local end_time=$(date +%s)
    local execution_time=$((end_time - start_time))

    # Display final summary
    display_summary $exit_code $execution_time

    exit $exit_code
}

# Run main function with all arguments
main "$@"

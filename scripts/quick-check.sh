#!/bin/bash

# Quick CI checks for local development
# This script performs lightweight checks that can be run frequently during development

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Function to check if we're in the right directory
check_project_root() {
    if [[ ! -f "pyproject.toml" || ! -d "py7zz" ]]; then
        print_error "This script must be run from the project root directory"
        print_error "Expected: pyproject.toml and py7zz/ directory"
        exit 1
    fi
}

# Function to ensure uv environment is set up
setup_environment() {
    print_status "Setting up development environment..."

    if ! command -v uv &> /dev/null; then
        print_error "uv is not installed. Please install uv first."
        print_error "Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi

    # Ensure dependencies are installed
    print_status "Syncing development dependencies..."
    uv sync --dev

    print_status "Installing package in editable mode..."
    uv pip install -e .

    print_success "Environment setup complete"
}

# Function to run code formatting checks
check_formatting() {
    print_status "Checking code formatting with ruff..."

    # Check formatting
    if uv run ruff format --check --diff .; then
        print_success "Code formatting is correct"
    else
        print_warning "Code formatting issues found"
        print_status "Auto-fixing formatting..."
        if uv run ruff format .; then
            print_warning "Code has been auto-formatted. Please review changes and commit again."
            return 1
        else
            print_error "Auto-formatting failed"
            return 1
        fi
    fi
}

# Function to run linting
check_linting() {
    print_status "Running linting checks with ruff..."

    if uv run ruff check .; then
        print_success "Linting checks passed"
    else
        print_warning "Linting issues found"
        print_status "Attempting auto-fix..."
        if uv run ruff check --fix .; then
            print_warning "Linting issues have been auto-fixed. Please review changes and commit again."
            return 1
        else
            print_error "Auto-fix failed. Please fix linting issues manually."
            return 1
        fi
    fi
}

# Function to run type checking
check_types() {
    print_status "Running type checking with mypy..."

    # Temporarily uninstall editable package to avoid path conflicts
    uv pip uninstall py7zz > /dev/null 2>&1 || true

    if uv run mypy .; then
        print_success "Type checking passed"
        # Reinstall editable package
        uv pip install -e . > /dev/null 2>&1
    else
        print_error "Type checking failed"
        # Reinstall editable package even on failure
        uv pip install -e . > /dev/null 2>&1
        return 1
    fi
}

# Main execution
main() {
    local start_time=$(date +%s)

    echo "=========================================="
    echo "  Quick CI Checks for Local Development"
    echo "=========================================="
    echo

    check_project_root

    local exit_code=0

    # Run checks
    setup_environment || exit_code=1
    echo
    check_formatting || exit_code=1
    echo
    check_linting || exit_code=1
    echo
    check_types || exit_code=1

    # Calculate execution time
    local end_time=$(date +%s)
    local execution_time=$((end_time - start_time))

    echo
    echo "=========================================="
    if [[ $exit_code -eq 0 ]]; then
        print_success "All quick checks passed! ✅"
        echo "Your code is ready for more comprehensive testing."
        echo
        echo "Next steps:"
        echo "  • Run 'scripts/ci-local.sh' for complete CI simulation"
        echo "  • Or run 'uv run pytest' for testing"
    else
        print_error "Some checks failed! ❌"
        echo "Please fix the issues above before pushing to remote."
        echo
        echo "Tip: Many issues were auto-fixed. Review changes with 'git diff'"
    fi
    echo
    print_status "Execution time: ${execution_time} seconds"
    echo "=========================================="

    exit $exit_code
}

# Run main function
main "$@"
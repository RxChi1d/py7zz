#!/bin/bash

# py7zz Format and Lint Checks
# Fast format and lint checks suitable for pre-commit hooks
# For complete CI checks, use scripts/ci-local.sh

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${CYAN}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "Please run this script in the project root directory (should contain pyproject.toml)"
    exit 1
fi

echo -e "${WHITE}Running format and lint checks...${NC}"
echo ""

# Ruff format check (fast)
print_step "Running ruff format check..."
echo -e "${PURPLE}Command: uv run ruff format --check --diff .${NC}"
if uv run ruff format --check --diff .; then
    print_success "ruff format check passed"
else
    print_error "ruff format check failed - code format does not meet standards"
    echo -e "${YELLOW}Auto-fixing: running 'uv run ruff format .'${NC}"
    if uv run ruff format .; then
        print_warning "Code has been auto-formatted. Please review changes and commit again."
        exit 1
    else
        print_error "Auto-formatting failed"
        exit 1
    fi
fi

# Ruff check (fast)
print_step "Running ruff check..."
echo -e "${PURPLE}Command: uv run ruff check .${NC}"
if uv run ruff check .; then
    print_success "ruff check passed"
else
    print_error "ruff check failed - attempting auto-fix"
    echo -e "${YELLOW}Auto-fixing: running 'uv run ruff check --fix .'${NC}"
    if uv run ruff check --fix .; then
        print_warning "Code issues have been auto-fixed. Please review changes and commit again."
        exit 1
    else
        print_error "Auto-fix failed - please fix code style issues manually"
        exit 1
    fi
fi

echo ""
print_success "All format and lint checks passed! ✨"
echo -e "${GREEN}Safe to commit.${NC}"

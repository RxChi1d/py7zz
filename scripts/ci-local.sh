#!/bin/bash

# py7zz Local CI Simulation Script
# Local version of GitHub Actions CI workflow simulation
# Keeps exactly consistent with .github/workflows/ci.yml

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${WHITE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
}

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

# Start time for performance tracking
start_time=$(date +%s)

print_header "py7zz Local CI Check Started"
echo -e "${WHITE}Simulating GitHub Actions workflow: .github/workflows/ci.yml${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "Please run this script in the project root directory (should contain pyproject.toml)"
    exit 1
fi

# Set up 7zz binary for testing if not already set
if [ -z "$PY7ZZ_BINARY" ]; then
    # Try to find 7zz in common locations
    if command -v 7zz &> /dev/null; then
        export PY7ZZ_BINARY=$(which 7zz)
        print_warning "Auto-detected and set test 7zz binary: $PY7ZZ_BINARY"
    elif command -v 7z &> /dev/null; then
        export PY7ZZ_BINARY=$(which 7z)
        print_warning "Auto-detected and set test 7z binary: $PY7ZZ_BINARY"
    else
        print_warning "System 7zz/7z binary not found, some tests may fail"
        print_warning "Hint: Set PY7ZZ_BINARY environment variable to point to your 7zz binary"
        print_warning "Or install 7-Zip: brew install 7-zip (macOS) or apt install 7zip (Ubuntu)"
    fi
else
    # Ensure environment variable is exported for child processes
    export PY7ZZ_BINARY="$PY7ZZ_BINARY"
    print_warning "Using predefined PY7ZZ_BINARY: $PY7ZZ_BINARY"
fi

# Phase 1: Environment Check
print_header "Phase 1: Environment Check"

print_step "Checking Python..."
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version)
    print_success "Python installed: $python_version"
else
    print_error "Python 3 not installed"
    exit 1
fi

print_step "Checking uv package manager..."
if command -v uv &> /dev/null; then
    uv_version=$(uv --version)
    print_success "uv installed: $uv_version"
else
    print_error "uv not installed, please run: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

print_step "Checking virtual environment..."
if [ -d ".venv" ]; then
    print_success "Virtual environment exists: .venv/"
else
    print_warning "Virtual environment does not exist, creating new virtual environment"
    uv venv
fi

echo ""

# Phase 2: Dependencies Installation
print_header "Phase 2: Dependencies Installation (CI Simulation)"

print_step "Syncing development dependencies (uv sync --dev)..."
if uv sync --dev; then
    print_success "Development dependencies sync completed"
else
    print_error "Dependencies sync failed"
    exit 1
fi

print_step "Installing local package (uv pip install -e .)..."
if uv pip install -e .; then
    print_success "Local package installation completed"
else
    print_error "Local package installation failed"
    exit 1
fi

echo ""

# Phase 3: Lint Checks (exactly matching CI)
print_header "Phase 3: Code Style Checks (Lint Job)"

print_step "Running ruff check (exactly matching CI)..."
echo -e "${PURPLE}Command: uv run ruff check . --output-format=github${NC}"
if uv run ruff check . --output-format=github; then
    print_success "ruff check passed"
else
    print_error "ruff check failed - please fix code style issues"
    echo -e "${YELLOW}Suggestion: run 'uv run ruff check --fix .' for auto-fix${NC}"
    exit 1
fi

print_step "Running ruff format check (exactly matching CI)..."
echo -e "${PURPLE}Command: uv run ruff format --check --diff .${NC}"
if uv run ruff format --check --diff .; then
    print_success "ruff format check passed"
else
    print_error "ruff format check failed - code format does not meet standards"
    echo -e "${YELLOW}Suggestion: run 'uv run ruff format .' for auto-formatting${NC}"
    exit 1
fi

echo ""

# Phase 4: Test Checks (exactly matching CI)
print_header "Phase 4: Testing and Type Checks (Test Job)"

print_step "Running pytest (exactly matching CI)..."
if [ -n "$PY7ZZ_BINARY" ]; then
    echo -e "${PURPLE}Command: uv run pytest -v --tb=short (with PY7ZZ_BINARY=$PY7ZZ_BINARY)${NC}"
    if uv run pytest -v --tb=short; then
        print_success "pytest tests passed"
    else
        print_error "pytest tests failed - please fix test errors"
        exit 1
    fi
else
    echo -e "${PURPLE}Command: uv run pytest -v --tb=short${NC}"
    if uv run pytest -v --tb=short; then
        print_success "pytest tests passed"
    else
        print_error "pytest tests failed - please fix test errors"
        exit 1
    fi
fi

print_step "Running mypy type check (exactly matching CI)..."
echo -e "${PURPLE}Command: uv run mypy .${NC}"
if uv run mypy .; then
    print_success "mypy type check passed"
else
    print_error "mypy type check failed - please fix type errors"
    exit 1
fi

echo ""

# Calculate execution time
end_time=$(date +%s)
execution_time=$((end_time - start_time))

# Final Success Report
print_header "🎉 Local CI Check Completed"
echo -e "${GREEN}✅ All check items passed!${NC}"
echo ""
echo -e "${WHITE}Check Results Summary:${NC}"
echo -e "  ${GREEN}✅${NC} Environment Check"
echo -e "  ${GREEN}✅${NC} Dependencies Installation"
echo -e "  ${GREEN}✅${NC} ruff check (Code Style)"
echo -e "  ${GREEN}✅${NC} ruff format check (Code Format)"
echo -e "  ${GREEN}✅${NC} pytest (Unit Tests)"
echo -e "  ${GREEN}✅${NC} mypy (Type Check)"
echo ""
echo -e "${CYAN}Execution Time: ${execution_time} seconds${NC}"
echo -e "${GREEN}🚀 Safe to commit and push to GitHub!${NC}"
echo ""
echo -e "${WHITE}Suggested commit workflow:${NC}"
echo -e "  git add ."
echo -e "  git commit -m \"your commit message\""
echo -e "  git push origin <branch-name>"
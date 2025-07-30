#!/bin/bash

# py7zz Local CI Simulation Script
# 模擬 GitHub Actions CI workflow 的本地版本
# 與 .github/workflows/ci.yml 保持完全一致

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

print_header "py7zz 本地 CI 檢查開始"
echo -e "${WHITE}模擬 GitHub Actions workflow: .github/workflows/ci.yml${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "請在專案根目錄執行此腳本 (應包含 pyproject.toml)"
    exit 1
fi

# Phase 1: Environment Check
print_header "階段 1: 環境檢查"

print_step "檢查 Python..."
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version)
    print_success "Python 已安裝: $python_version"
else
    print_error "Python 3 未安裝"
    exit 1
fi

print_step "檢查 uv 套件管理器..."
if command -v uv &> /dev/null; then
    uv_version=$(uv --version)
    print_success "uv 已安裝: $uv_version"
else
    print_error "uv 未安裝，請執行: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

print_step "檢查虛擬環境..."
if [ -d ".venv" ]; then
    print_success "虛擬環境已存在: .venv/"
else
    print_warning "虛擬環境不存在，將建立新的虛擬環境"
    uv venv
fi

echo ""

# Phase 2: Dependencies Installation
print_header "階段 2: 安裝依賴 (模擬 CI)"

print_step "同步開發依賴 (uv sync --dev)..."
if uv sync --dev; then
    print_success "開發依賴同步完成"
else
    print_error "依賴同步失敗"
    exit 1
fi

print_step "安裝本地套件 (uv pip install -e .)..."
if uv pip install -e .; then
    print_success "本地套件安裝完成"
else
    print_error "本地套件安裝失敗"
    exit 1
fi

echo ""

# Phase 3: Lint Checks (exactly matching CI)
print_header "階段 3: 程式碼風格檢查 (Lint Job)"

print_step "執行 ruff check (與 CI 完全一致)..."
echo -e "${PURPLE}命令: uv run ruff check . --output-format=github${NC}"
if uv run ruff check . --output-format=github; then
    print_success "ruff check 通過"
else
    print_error "ruff check 失敗 - 請修正程式碼風格問題"
    echo -e "${YELLOW}建議執行: uv run ruff check --fix . 自動修正${NC}"
    exit 1
fi

print_step "執行 ruff format check (與 CI 完全一致)..."
echo -e "${PURPLE}命令: uv run ruff format --check --diff .${NC}"
if uv run ruff format --check --diff .; then
    print_success "ruff format check 通過"
else
    print_error "ruff format check 失敗 - 程式碼格式不符合標準"
    echo -e "${YELLOW}建議執行: uv run ruff format . 自動格式化${NC}"
    exit 1
fi

echo ""

# Phase 4: Test Checks (exactly matching CI)
print_header "階段 4: 測試與類型檢查 (Test Job)"

print_step "執行 pytest (與 CI 完全一致)..."
echo -e "${PURPLE}命令: uv run pytest -v --tb=short${NC}"
if uv run pytest -v --tb=short; then
    print_success "pytest 測試通過"
else
    print_error "pytest 測試失敗 - 請修正測試錯誤"
    exit 1
fi

print_step "執行 mypy 類型檢查 (與 CI 完全一致)..."
echo -e "${PURPLE}命令: uv run mypy .${NC}"
if uv run mypy .; then
    print_success "mypy 類型檢查通過"
else
    print_error "mypy 類型檢查失敗 - 請修正類型錯誤"
    exit 1
fi

echo ""

# Calculate execution time
end_time=$(date +%s)
execution_time=$((end_time - start_time))

# Final Success Report
print_header "🎉 本地 CI 檢查完成"
echo -e "${GREEN}✅ 所有檢查項目通過！${NC}"
echo ""
echo -e "${WHITE}檢查結果摘要:${NC}"
echo -e "  ${GREEN}✅${NC} 環境檢查"
echo -e "  ${GREEN}✅${NC} 依賴安裝"
echo -e "  ${GREEN}✅${NC} ruff check (程式碼風格)"
echo -e "  ${GREEN}✅${NC} ruff format check (程式碼格式)"
echo -e "  ${GREEN}✅${NC} pytest (單元測試)"
echo -e "  ${GREEN}✅${NC} mypy (類型檢查)"
echo ""
echo -e "${CYAN}執行時間: ${execution_time} 秒${NC}"
echo -e "${GREEN}🚀 可以安全地提交和推送到 GitHub！${NC}"
echo ""
echo -e "${WHITE}建議的提交工作流程:${NC}"
echo -e "  git add ."
echo -e "  git commit -m \"your commit message\""
echo -e "  git push origin <branch-name>"
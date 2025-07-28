# CLAUDE.md

此檔案提供 Claude Code (claude.ai/code) 在此儲存庫中工作時的指引。

## 語言規則

**重要：請嚴格遵循以下語言規則**

1. **Claude.md 內容**：使用zh-tw
2. **與 Claude 對話**：使用zh-tw
3. **程式碼註解**：使用en
4. **函數/變數命名**：使用en
5. **Git commit 訊息**：使用en
6. **文件字串 (docstrings)**：使用en

## 專案概述

py7zz 是一個 Python 套件，封裝了官方的 7zz CLI 工具，跨平台（macOS、Debian 系 Linux、Windows x64）提供一致的物件導向程式介面，並具備自動更新機制。專案遵循「Vibe Coding」工作流程，強調快速迭代、CI/CD 整合以及強制程式碼格式化。

**Python 支援版本**：Python 3.8+ (包含 Python 3.13)

**專案願景**：讓使用者「pip install py7zz」後，立即能夠通過跨平台統一的Python API接口或py7zz CLI工具壓縮/解壓縮數十種格式，無需預先安裝 7-Zip，wheel 套件包含平台特定的 7zz 二進位檔案。

## 開發命令

### 環境設定
```bash
source .venv/bin/activate  # 啟動虛擬環境（直接使用工具時必須）

# 設定開發二進位檔案路徑（開發用，可選）
export PY7ZZ_BINARY=/opt/homebrew/bin/7zz  # macOS with Homebrew
# export PY7ZZ_BINARY=/usr/bin/7zz         # Linux systems
# export PY7ZZ_BINARY=/path/to/7zz.exe     # Windows systems
```

### 安裝方法

py7zz 支援多種安裝方法以滿足不同使用情境：

#### 1. 正式版安裝（推薦）
```bash
pip install py7zz
```
- 包含綁定的 7zz 二進位檔案以確保版本一致性
- 無需額外設定
- 自動二進位檔案偵測和版本配對

#### 2. 開發版安裝（從原始碼）
```bash
# 複製儲存庫並以可編輯模式安裝
git clone https://github.com/rxchi1d/py7zz.git
cd py7zz
pip install -e .
```
- 首次使用時自動下載正確的 7zz 二進位檔案
- 快取於 ~/.cache/py7zz/ 以供離線使用
- 確保版本一致性而不依賴系統

#### 3. 直接 GitHub 安裝
```bash
# 安裝最新開發版本
pip install git+https://github.com/rxchi1d/py7zz.git
```
- 直接從 GitHub 儲存庫安裝
- 首次使用時自動下載正確的 7zz 二進位檔案
- 無需本地 git 複製或系統 7zz

#### 二進位檔案發現順序（混合方法）
py7zz 依下列順序尋找 7zz 二進位檔案：
1. **PY7ZZ_BINARY** 環境變數（僅開發/測試用）
2. **綁定二進位檔案**（PyPI wheel 套件）
3. **自動下載二進位檔案**（原始碼安裝 - 快取於 ~/.cache/py7zz/）

**主要特色：**
- **隔離性**：永不使用系統 7zz 以避免衝突
- **版本一致性**：每個 py7zz 版本都與特定 7zz 版本配對
- **自動化**：原始碼安裝首次使用時自動下載正確二進位檔案
- **快取**：下載的二進位檔案快取以供離線使用

這確保了所有安裝方法的可靠性、隔離性和版本一致性。

### 依賴管理
**重要**：所有依賴必須透過 `uv add` 命令管理。禁止手動編輯 `pyproject.toml` 或使用 `uv pip install`。

```bash
# 執行期依賴
uv add requests rich typer packaging

# 開發依賴
uv add --dev pytest ruff mypy
```

### 核心開發循環
```bash
# 使用 uv（推薦）
uv run ruff check --fix .   # 風格檢查並自動修正
uv run ruff format .        # 格式化程式碼
uv run mypy .               # 類型檢查
uv run pytest              # 執行單元測試

# 或使用傳統命令（需要啟動虛擬環境）
source .venv/bin/activate
ruff check --fix .
ruff format .
mypy .
pytest
```

**注意**：完整的程式碼品質檢查會在 GitHub Actions 中執行，確保 PR 合併前的程式碼品質。

### 完整開發工作流程範例
```bash
# 1. 啟動開發環境
source .venv/bin/activate

# 2. 開發程式碼...

# 3. 執行完整質檢流程（與 CI 一致）
uv run ruff format .        # 格式化程式碼
uv run ruff check --fix .   # 檢查並修正程式碼風格（包含 SIM 規則）
uv run mypy .               # 類型檢查
uv run pytest              # 執行完整測試套件

# 4. 確認所有檢查通過後才提交
git add .
git commit -m "feat: add new feature"

# 5. 推送前再次確認 CI 會通過
git push origin <branch-name>
```

## 架構

### 專案結構
```
py7zz/
├── __init__.py            # 匯出 SevenZipFile, get_version
├── core.py                # subprocess 膠合、banner 解析
├── cli.py                 # CLI 工具入口點
├── async_ops.py           # 異步操作支援
├── bin/                   # 二進位檔案目錄
│   └── 7zz[.exe]         # 平台特定二進位檔案（每個 wheel 只包含一個）
├── updater.py             # GitHub API 整合及原始碼安裝的自動下載
├── bundled_info.py        # 版本註冊表和二進位檔案資訊
├── pyproject.toml         # build-system = "hatchling"
├── README.md
├── CLAUDE.md              # Claude Code 工作指引
├── tests/                 # 測試套件
│   ├── test_*.py         # 各種測試模組
│   └── __init__.py
└── .github/workflows/
    ├── ci.yml             # push/PR 時的 lint+test (Python 3.8-3.13)
    ├── build.yml          # tag push 時的 wheel 矩陣建置
    └── watch_release.yml  # 夜間建置自動化
```

### 核心元件
- **SevenZipFile**：主要 API 類別，類似 zipfile 介面
- **core.run_7z()**：7zz CLI 執行的 subprocess 包裝器
- **AsyncSevenZipFile**：異步操作支援，具進度報告功能
- **CLI 工具**：py7zz 命令行工具，提供直接 7zz 操作
- **二進位檔案解析**：具隔離性和版本一致性的混合方法
- **版本一致性**：每個 py7zz 版本都與特定 7zz 版本配對以確保穩定性
- **三層版本控制**：Release（穩定）、Auto（基本穩定）、Dev（不穩定）

### API 設計

py7zz 遵循**分層 API 設計**以服務不同使用者需求和技能水準：

1. **簡單函數 API**：一行解決方案（80% 使用情境）
2. **相容性 API**：類似 zipfile.ZipFile 介面（遷移使用者）
3. **進階控制 API**：細粒度控制與自訂組態（進階使用者）
4. **異步 API**：非阻塞操作與進度報告（大型檔案處理）
5. **原生 7zz API**：直接 7zz 命令存取（專家使用者）

#### 設計原則
1. **漸進複雜性**：簡單 → 標準 → 進階 → 專家
2. **智慧預設值**：根據使用模式自動最佳設定
3. **格式透明性**：從檔案副檔名自動偵測格式
4. **遷移友善**：從 zipfile/tarfile 最少程式碼變更
5. **錯誤處理**：清晰、可執行的錯誤訊息

## CI/CD 流水線

### GitHub Actions 工作流程
1. **ci.yml**：push/PR 時執行 - 執行 ruff、pytest、mypy（PR 閘道）
   - 測試 Python 版本：3.8, 3.9, 3.10, 3.11, 3.12, 3.13
2. **build.yml**：tag push 時觸發 - 使用矩陣建置為所有平台建置 wheel
3. **watch_release.yml**：夜間建置自動化（目前手動觸發）

### 三層版本系統（PEP 440 規範）
- **🟢 Release**（`1.0.0`）：穩定、手動發布、生產就緒
  - **Release Notes**：Release Drafter 生成的專業分類 release notes
  - **來源**：合併到 main 分支的 PR
- **🟡 Auto**（`1.0.0a1`）：基本穩定、7zz 更新時自動發布
  - **Release Notes**：GitHub 原生自動生成（基於 commit 訊息）
  - **來源**：feature branch 上的 commit 記錄
- **🔴 Dev**（`1.1.0.dev1`）：不穩定、手動發布以測試新功能
  - **Release Notes**：GitHub 原生自動生成（基於 commit 訊息）
  - **來源**：feature branch 上的 commit 記錄

### 程式碼品質要求
- **Ruff**：強制程式碼風格，line-length=88、select=["E", "F", "I", "UP", "B", "C4", "SIM"]
- **MyPy**：所有程式碼都需要類型檢查，target-version=py38
- **Pytest**：合併前單元測試必須通過
- **CI 必須通過**：所有程式碼必須通過 GitHub Actions 中的完整檢查
- **Python 版本相容性**：所有程式碼必須在 Python 3.8-3.13 上通過測試
- **提交前驗證**：必須執行完整的本地質檢流程

## 程式碼提交前檢查清單

在提交程式碼前，請確保：
- [ ] `uv run ruff format .` 執行成功，程式碼格式化完成
- [ ] `uv run ruff check --fix .` 無錯誤，所有 lint 規則通過（包含 SIM 簡化規則）
- [ ] `uv run mypy .` 無錯誤，所有類型檢查通過
- [ ] `uv run pytest` 全部測試通過，無失敗案例
- [ ] 所有修改都經過適當測試（單元測試、整合測試）
- [ ] 相關文件已同步更新（README.md、CLAUDE.md、docstrings）
- [ ] 程式碼符合專案架構和設計原則
- [ ] 沒有遺留的 TODO 或 FIXME 註解（除非有計劃處理）
- [ ] 提交訊息遵循約定格式（詳見「提交訊息規範」）

**重要**：只有在所有檢查項目都通過後，才能提交程式碼到儲存庫。這確保了程式碼品質並避免 CI 失敗。

## 提交訊息規範

py7zz 遵循**約定式提交**（Conventional Commits）規範，確保自動生成的 Release Notes 品質良好。

### 格式要求

```
<type>(<scope>): <description>    ← 第一行（50-72 字符）

[optional body]                   ← 詳細說明（72 字符換行）

[optional footer(s)]              ← 破壞性變更、問題參考
```

**重要說明**：
- **第一行**：GitHub 自動生成 release notes 使用
- **內容主體**：複雜變更的詳細解釋（不會出現在 release notes 中）
- **腳註**：破壞性變更和問題參考

### 提交類型

- **feat**: 新功能（對應 MINOR 版本）
- **fix**: 錯誤修復（對應 PATCH 版本）
- **docs**: 文件變更
- **style**: 代碼格式（不影響功能）
- **refactor**: 重構代碼
- **perf**: 性能優化
- **test**: 測試相關
- **chore**: 建置或工具變更
- **ci**: CI/CD 相關

### 描述寫法

**❌ 不好的範例**：
```bash
git commit -m "feat: add async support"
git commit -m "fix: Windows bug"
git commit -m "docs: update readme"
```

**✅ 好的範例**：
```bash
# 單行 commit（簡單變更）
git commit -m "feat: add async operations with progress callbacks for large archives"
git commit -m "fix: resolve binary path detection on Windows systems with spaces"
git commit -m "docs: add comprehensive migration guide from zipfile to py7zz"

# 多行 commit（複雜變更）
git commit -m "feat: add async operations with progress callbacks

This commit introduces comprehensive async support including:
- Progress callback mechanism for real-time updates
- Batch operations for multiple archives
- Memory-efficient streaming for large files
- Cross-platform compatibility testing

The implementation maintains backward compatibility while
providing significant performance improvements for large-scale
operations."

git commit -m "fix: resolve binary path detection on Windows systems with spaces

The previous implementation failed when the 7zz binary path contained
spaces due to incorrect subprocess argument handling. This fix:

- Properly quotes binary paths in subprocess calls
- Adds comprehensive path validation
- Includes test cases for paths with spaces
- Maintains compatibility with existing installations

Fixes #42"
```

### 重大變更

使用 `BREAKING CHANGE:` 標記（對應 MAJOR 版本）：
```bash
git commit -m "feat!: redesign API for better async support

BREAKING CHANGE: SevenZipFile.extract() now returns async iterator instead of list"
```

### 作用域（可選）

指定影響範圍：
```bash
git commit -m "feat(api): add batch extraction support"
git commit -m "fix(cli): resolve version display format"
git commit -m "docs(readme): add installation troubleshooting"
```

### 為什麼重要

1. **自動化 Release Notes**：Release Drafter 基於 PR 標題生成分類的 release notes
2. **版本控制**：工具可自動判斷版本號變更（feat = minor, fix = patch）
3. **可追蹤性**：清楚了解每次變更的目的和影響
4. **團隊協作**：一致的格式提高可讀性

### PR 標題規範

**重要**：PR 標題必須遵循相同的約定式提交格式，因為：
- PR 標題會直接出現在 release notes 中
- Release Drafter 根據 PR 標題自動分類和標籤
- 語義化版本控制依賴 PR 標題判斷版本類型

```bash
# PR 標題範例
feat: add async operations with progress callbacks
fix: resolve binary path detection on Windows systems
docs: add comprehensive migration guide from zipfile
perf: optimize memory usage for large file extraction
```

### 建立 Pull Request 規範

**重要**：建立 PR 時必須遵循以下規範：

1. **PR 標題格式**：
   - 必須遵循約定式提交格式：`<type>(<scope>): <description>`
   - 範例：`feat: add async operations with progress callbacks`

2. **PR 內容格式**：
   - 參考 `.github/pull_request_template.md` 中的模板
   - 包含完整的變更說明、測試資訊、檢查清單

3. **PR 標籤**：
   - 根據 PR 標題自動分類（Release Drafter 自動處理）
   - 確保選擇正確的變更類型

4. **PR 描述要求**：
   - 清楚描述變更內容和原因
   - 列出相關的測試項目
   - 確認所有檢查清單項目

**模板位置**：`.github/pull_request_template.md`

### 檢查清單

提交前確認：
- [ ] 使用正確的 type 前綴
- [ ] 描述清楚具體做了什麼
- [ ] 使用現在式動詞（"add" 而非 "added"）
- [ ] 首字母小寫
- [ ] 不超過 72 字符
- [ ] 描述「做了什麼」而非「怎麼做」

## 開發注意事項

- **依賴管理**：專用 `uv` 進行依賴管理和虛擬環境
- **Python 版本相容性**：支援 Python 3.8+ (包含 Python 3.13)
- **二進位檔案發布**：包含從 GitHub 發布下載的平台特定 7zz 執行檔
- **自動建置**：偵測到新 7zz 發布時自動建立夜間建置
- **跨平台相容性**：macOS、Debian 系 Linux、Windows x64
- **授權條款**：BSD-3 + LGPL 2.1（保留 7-Zip 授權條款）
- **異步支援**：提供完整的異步操作 API 與進度報告
- **Windows 檔案名稱相容性**：自動處理 Windows 檔案名稱限制，包含無效字符替換和保留名稱處理

## 建置系統

### 二進位檔案發布
- CI 下載平台特定資產（`7z{ver}-{os}-{arch}.tar.xz`）
- 驗證 SHA256 校驗和
- 解壓縮至 `bin/7zz[.exe]`
- 打包於 wheel 中發布

### 版本管理
- 採用 PEP 440 規範，確保 PyPI 和 GitHub Release 版本一致
- 每個 py7zz 版本都與特定 7zz 版本配對以確保一致性
- 版本資訊透過 bundled_info.py 的 VERSION_REGISTRY 追蹤
- 無執行時自動更新 - 使用者必須升級整個 py7zz 套件
- 夜間建置可用於在正式發布前測試新 7zz 發布
- 正式發布需要手動測試和核准

## 里程碑

專案遵循結構化開發計劃：
- **M1** ✅：儲存庫設定、基本 API、手動二進位檔案下載
- **M2** ✅：跨平台 wheel 建置、CI 設定
- **M3** ✅：GitHub API 整合、夜間建置自動化
- **M4** ✅：非同步操作、進度報告
- **M5** ✅：文件、類型提示、PyPI 發布
  - [x] 為 zipfile/tarfile 使用者建立 MIGRATION.md
  - [x] 將遷移指南連結加入 README.md
  - [x] 完成 API 文件和範例
  - [x] 完成類型提示和文件字串
  - [x] 準備 PyPI 發布

## 二進位檔案管理與安裝策略

### 混合二進位檔案發布方法

py7zz 實作混合方法以確保**隔離性**和**版本一致性**：

#### 設計原則
1. **永不使用系統 7zz** - 避免版本衝突並確保可重現行為
2. **版本配對** - 每個 py7zz 版本都與特定 7zz 版本配對
3. **自動處理** - 使用者無需手動安裝或設定 7zz
4. **離線能力** - 下載的二進位檔案快取以供離線使用

#### 實作策略

**PyPI Wheel 發布（生產環境）**：
- 使用 GitHub Actions 從 https://github.com/ip7z/7zip/releases 下載 7zz 二進位檔案
- 將平台特定二進位檔案嵌入 wheel 套件
- 使用者透過 `pip install py7zz` 取得綁定二進位檔案
- 安裝後無需網路連線

**原始碼安裝（開發環境）**：
- git 儲存庫中 `py7zz/bin/` 目錄為空
- 透過 `updater.py` 首次使用時自動下載正確 7zz 二進位檔案
- 快取於 `~/.cache/py7zz/{version}/` 目錄
- 僅首次使用時需要網路連線

#### 二進位檔案發現優先順序
```python
def find_7z_binary() -> str:
    # 1. 環境變數（僅開發/測試用）
    if PY7ZZ_BINARY and exists: return PY7ZZ_BINARY
    
    # 2. 綁定二進位檔案（PyPI wheel 套件）
    if bundled_binary and exists: return bundled_binary
    
    # 3. 自動下載二進位檔案（原始碼安裝）
    if auto_download_successful: return cached_binary
    
    # 4. 錯誤 - 無系統備援
    raise RuntimeError("7zz binary not found")
```

#### 版本一致性機制
- `version.py` 定義：`__version__ = "1.0.0"` (PEP 440 規範)
- `bundled_info.py` 的 `VERSION_REGISTRY` 追蹤 7zz 版本對應關係
- 自動下載使用 `get_bundled_7zz_version()` 確保正確二進位檔案版本
- 資產命名：`24.07` → `2407` 用於 GitHub 發布 URL

#### 快取管理
- 位置：`~/.cache/py7zz/{version}/7zz[.exe]`
- 透過 `updater.cleanup_old_versions()` 自動清理
- 跨 py7zz 重新安裝保留
- 從 tar.xz/exe 檔案進行平台特定二進位檔案解壓縮

### 設定要求

#### pyproject.toml 二進位檔案包含
```toml
[tool.hatch.build.targets.wheel]
packages = ["py7zz"]
include = [
    "py7zz/bin/**/*",
]

[tool.hatch.build.targets.wheel.force-include]
"py7zz/bin" = "py7zz/bin"
```

#### GitHub Actions 二進位檔案下載
- 從 GitHub 發布下載平台特定 7zz 二進位檔案
- 支援 Linux、macOS（x64/arm64）、Windows 平台
- 驗證二進位檔案可執行性

#### 錯誤處理與備援
- 無系統 7zz 備援，確保版本一致性
- 提供清晰的錯誤訊息和解決方案
- 支援環境變數覆蓋（開發用）

### 測試要求

#### 安裝方法測試
- 測試使用綁定二進位檔案的 PyPI wheel 安裝
- 測試使用自動下載的原始碼安裝
- 測試環境變數覆蓋
- 測試快取填充後的離線功能
- 測試跨安裝方法的版本一致性

#### 二進位檔案驗證
- 驗證二進位檔案可執行性：`7zz --help`
- 驗證版本匹配：解析輸出的版本字串
- 驗證平台相容性：正確架構
- 驗證跨會話快取持久性

## CLI 工具

py7zz 提供 CLI 工具以支援版本查詢和直接 7zz 操作：

### 版本查詢
```bash
# 查詢詳細版本資訊
py7zz version

# JSON 格式輸出
py7zz version --format json

# 快速版本查詢
py7zz --py7zz-version
py7zz -V
```

### 直接 7zz 操作
```bash
# 直接傳遞給 7zz 二進位檔案
py7zz a archive.7z files/
py7zz x archive.7z
py7zz l archive.7z
```

**注意**：CLI 入口點從 `7zz` 改為 `py7zz` 以避免與系統 7zz 命令衝突。

此混合方法確保 py7zz 在所有安裝方法中都能可靠運作，同時維護嚴格的版本控制和系統隔離。

## Windows 檔案名稱相容性

py7zz 提供自動的 Windows 檔案名稱相容性處理，解決從 Unix 系統建立的封存檔在 Windows 上解壓縮時的檔名問題。

### 功能特色

**自動偵測和重試機制**：
- 先嘗試直接解壓縮
- 若因檔名問題失敗，自動使用淨化檔名重試
- 提供詳細的日誌記錄每個重新命名的檔案

**檔案名稱淨化規則**：
- **無效字符替換**：將 `< > : " | ? *` 及控制字符替換為 `_`
- **保留名稱處理**：Windows 保留名稱（CON, PRN, AUX, NUL, COM1-9, LPT1-9）加上 `_file` 後綴
- **長度限制**：檔名超過 255 字符時截短並加上 MD5 hash 確保唯一性
- **尾隨字符移除**：移除檔名結尾的空格和句點
- **目錄遍歷防護**：防止 `../` 等路徑遍歷攻擊
- **唯一性保證**：確保淨化後的檔名不會產生衝突

### 使用方式

功能完全自動化，用戶無需額外設定：

```python
import py7zz

# 自動處理有問題的檔名
py7zz.extract_archive("unix-created-archive.7z", "output/")

# 使用 SevenZipFile 類別
with py7zz.SevenZipFile("problematic-names.zip") as sz:
    sz.extract("output/")  # 自動淨化檔名
```

### 日誌控制

用戶可控制檔名相容性警告的顯示：

```python
import py7zz

# 啟用詳細日誌（預設）
py7zz.setup_logging("INFO")

# 停用檔名警告
py7zz.disable_warnings()

# 啟用除錯日誌
py7zz.enable_debug_logging()
```

### 檔名轉換範例

| 原始檔名 | 淨化後檔名 | 原因 |
|---------|-----------|------|
| `file:name.txt` | `file_name.txt` | 無效字符 `:` |
| `CON.txt` | `CON_file.txt` | Windows 保留名稱 |
| `file<>name.zip` | `file___name.zip` | 多個無效字符 |
| `very-long-filename...` | `very-long-fil_a1b2c3d4.txt` | 超長檔名截短+hash |
| `filename ` | `filename` | 移除尾隨空格 |

### 錯誤處理

**FilenameCompatibilityError**：當檔名相容性處理失敗時拋出
**ExtractionError**：包含原始錯誤訊息和淨化錯誤的詳細資訊

### 非 Windows 系統

在非 Windows 系統上，此功能自動停用以避免不必要的效能開銷。

### 安全考量

- **路徑遍歷防護**：防止惡意封存檔案寫入系統目錄外
- **檔名長度限制**：防止過長檔名造成系統問題
- **字符安全性**：移除可能導致系統問題的控制字符
# CLAUDE.md

此檔案提供 Claude Code (claude.ai/code) 在此儲存庫中工作時的指引。

## 語言規則

**重要：請嚴格遵循以下語言規則**

1. **Claude.md 內容**：使用zh-tw
2. **對話語言**：使用zh-tw
3. **程式碼註解**：使用en
4. **函數/變數命名**：使用en
5. **Git commit 訊息**：使用en
6. **文件字串 (docstrings)**：使用en
7. **專案文檔**：使用en

## 撰寫風格與格式
- 程式碼（python, bash, etc.）、配置檔案 (yaml, poml, etc.)：遵循 ruff 規範。如果有不同會在後續 `uv run ruff check .`檢查出異常。
- 專案文檔、說明文字、文件模板：遵循 Google 風格。
- Commit與PR訊息：遵循 Convential Commit 格式與 Google 風格/格式。
- Changelog: 遵循 Keep a Changelog 格式。

## 專案概述

py7zz 是一個 Python 套件，封裝了官方的 7zz CLI 二進位檔案 (7-Zip) ，提供跨平台（macOS、Debian 系 Linux、Windows x64）提供一致的 Python API與命令接口。無需預先安裝 7-Zip，wheel 套件包含平台特定的 7zz 。

**Python 支援版本**：Python >= 3.8
**Python 套件管理工具**：uv
**uv 管理的虛擬環境**：`.venv/`

### 核心開發循環

⚠️ **重要**：每次commit前**必須**執行完整的品質檢查流程 (`scripts/ci-local.sh`)，並通過所有檢測。

開發過程中也可以使用以下命令做基本的檢查與測試：
```bash
# 使用 uv（推薦）- 按照 CI 執行順序
uv run ruff format .        # 1. 格式化程式碼
uv run ruff check --fix .   # 2. 風格檢查並自動修正
uv run mypy .               # 3. 類型檢查
uv run pytest              # 4. 執行單元測試
```

## commit 訊息規範

- 格式：遵循 **Conventional Commits** 規範。
- 風格：Google 風格。

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
**風格**：Google 風格。


## 文件撰寫與可解釋性
- **當新增功能、依賴變更或安裝步驟修改時，請更新 `README.md`。**
- **為不明顯的程式碼加上註解，並確保所有內容中階開發者都能理解。**
- 撰寫複雜邏輯時，**請加入行內 `# Reason:` 註解，說明「為什麼」這麼做，而不只是「做了什麼」。**

## AI 行為規範
- **絕不假設缺漏的上下文，如有疑問務必提出問題確認。**
- **嚴禁臆造不存在的函式或套件** —— 只能使用已知、驗證過的 Python 套件。
- **在程式碼或測試中引用檔案路徑或模組名稱前，務必確認其存在。**
- **除非有明確指示，或任務需求（見 `TASK.md`），**否則**不得刪除或覆蓋現有程式碼。**
- **需要分析或拆解問題，通過 sequential thinking 進行更深度思考**
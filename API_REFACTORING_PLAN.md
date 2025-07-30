# py7zz API 重構計劃

## 概述

基於對現有 API 的全面審核，py7zz 目前存在以下主要問題：

1. **缺乏業界標準對標**：API 設計未與 zipfile/tarfile 標準一致
2. **功能概念混淆**：某些 API 混合了不同層級的功能
3. **命名不一致**：API 命名未遵循 Python 標準庫慣例
4. **缺少關鍵 API**：缺少業界標準的 `infolist()` 等重要方法
5. **API 增殖**：存在功能重疊但命名不同的 API

## 當前 API 審核結果

### Layer 1: Simple Function API (簡單函數 API)

**位置**：`py7zz/simple.py`

#### 現有 API：
1. `create_archive(archive_path, files, preset="balanced", password=None)`
2. `extract_archive(archive_path, output_dir=".", overwrite=True)`
3. `list_archive(archive_path)` → `List[str]`
4. `compress_file(input_path, output_path=None, preset="balanced")`
5. `compress_directory(input_dir, output_path=None, preset="balanced")`
6. `get_archive_info(archive_path)` → `Dict[str, Any]`
7. `test_archive(archive_path)` → `bool`

#### 問題分析：
- ✅ **保留**：`create_archive()` - 符合簡單 API 設計原則
- ✅ **保留**：`extract_archive()` - 符合簡單 API 設計原則
- ❌ **問題**：`list_archive()` - 與 Layer 2 的 `namelist()` 功能重複
- ✅ **保留**：`compress_file()` - 單檔案快捷方式有獨立價值
- ✅ **保留**：`compress_directory()` - 目錄快捷方式有獨立價值
- ❌ **重大問題**：`get_archive_info()` - 混合了檔案清單與封存統計功能
- ✅ **保留**：`test_archive()` - 符合簡單 API 設計原則

#### Async 版本：
8. `create_archive_async()` - 可選匯入
9. `extract_archive_async()`
10. `compress_file_async()`
11. `compress_directory_async()`

### Layer 2: Object-Oriented API (物件導向 API)

**位置**：`py7zz/core.py` - `SevenZipFile` 類別

#### 現有 API：
1. `SevenZipFile.__init__(file, mode, level, preset, config)`
2. `SevenZipFile.add(name, arcname=None)`
3. `SevenZipFile.extract(path=".", overwrite=False)`
4. `SevenZipFile.list_contents()` → `List[str]`

#### zipfile/tarfile 兼容方法：
5. `SevenZipFile.namelist()` → `List[str]` (調用 `list_contents()`)
6. `SevenZipFile.getnames()` → `List[str]` (調用 `list_contents()`)
7. `SevenZipFile.extractall(path=".", members=None)`
8. `SevenZipFile.read(name)` → `bytes`
9. `SevenZipFile.writestr(filename, data)`
10. `SevenZipFile.testzip()` → `Optional[str]`
11. `SevenZipFile.close()`
12. `SevenZipFile.__iter__()` → `Iterator[str]`
13. `SevenZipFile.__contains__(name)` → `bool`

#### 問題分析：
- ❌ **重大問題**：缺少業界標準的 `infolist()` 方法
- ❌ **重大問題**：缺少 `getinfo(name)` 方法
- ❌ **重大問題**：缺少檔案資訊類別 (如 `ZipInfo`、`TarInfo` 對等)
- ❌ **命名問題**：`list_contents()` 應為內部方法，不應暴露
- ❌ **功能問題**：`extractall()` 的 `members` 參數未實作
- ❌ **問題**：`add()` 的 `arcname` 參數未實作

### Layer 3: Advanced Configuration API

**位置**：`py7zz/config.py`

#### 現有 API：
1. `Config` 類別 - 進階壓縮設定
2. `Presets` 類別 - 預設配置
3. `create_custom_config(**kwargs)` → `Config`
4. `get_recommended_preset(use_case)` → `str`

#### 問題分析：
- ✅ **保留**：設計良好，符合進階用戶需求

### Layer 4: Async Operations API

**位置**：`py7zz/async_ops.py`

#### 現有 API：
1. `AsyncSevenZipFile` 類別
2. `ProgressInfo` 類別
3. `compress_async()`
4. `extract_async()`
5. `batch_compress_async()`
6. `batch_extract_async()`

#### 問題分析：
- ❌ **重大問題**：`AsyncSevenZipFile` 缺少與 `SevenZipFile` 對等的業界標準方法
- ❌ **問題**：異步 API 與同步 API 不一致

### 其他模組：

#### 版本資訊 API (`py7zz/version.py`, `py7zz/bundled_info.py`)
- ✅ **保留**：設計良好

#### 錯誤處理 (`py7zz/exceptions.py`)
- ✅ **保留**：設計良好

#### 日誌配置 (`py7zz/logging_config.py`)
- ✅ **保留**：設計良好

#### CLI 工具 (`py7zz/cli.py`)
- ✅ **保留**：設計良好

## 重構計劃

### 階段 1：業界標準對標 (高優先級)

#### 1.1 新增缺失的業界標準 API

**新增 `ArchiveInfo` 類別** (`py7zz/archive_info.py`)：
```python
class ArchiveInfo:
    """Archive member information, similar to zipfile.ZipInfo and tarfile.TarInfo"""
    def __init__(self, filename: str):
        self.filename = filename
        self.date_time: Optional[tuple] = None
        self.compress_type: Optional[str] = None
        self.comment: str = ""
        self.extra: bytes = b""
        self.create_system: int = 0
        self.create_version: int = 0
        self.extract_version: int = 0
        self.reserved: int = 0
        self.flag_bits: int = 0
        self.volume: int = 0
        self.internal_attr: int = 0
        self.external_attr: int = 0
        self.header_offset: int = 0
        self.CRC: int = 0
        self.compress_size: int = 0
        self.file_size: int = 0
```

**修改 `SevenZipFile` 類別**：
```python
class SevenZipFile:
    def infolist(self) -> List[ArchiveInfo]:
        """Return list of ArchiveInfo objects (業界標準)"""
        
    def getinfo(self, name: str) -> ArchiveInfo:
        """Return ArchiveInfo for given member (業界標準)"""
        
    def _get_detailed_info(self) -> List[ArchiveInfo]:
        """Internal method to parse 7zz -slt output for detailed info"""
```

#### 1.2 修復現有問題

**修復 `get_archive_info()` 功能混淆**：
```python
# OLD - 混合了檔案清單與統計資訊
def get_archive_info(archive_path) -> Dict[str, Any]:
    return {
        "file_count": len(files),      # 統計資訊
        "compressed_size": size,       # 統計資訊  
        "files": files,               # 檔案清單 - 不應在此
        "format": format,             # 統計資訊
        "path": path,                 # 統計資訊
    }

# NEW - 分離功能
def get_archive_info(archive_path) -> Dict[str, Any]:
    """Get archive statistics only (純統計資訊)"""
    return {
        "file_count": int,
        "compressed_size": int,
        "uncompressed_size": int,  # 新增
        "compression_ratio": float, # 新增
        "format": str,
        "path": str,
        "created": datetime,        # 新增
        "modified": datetime,       # 新增
    }
```

**解決 API 重複問題**：
- 移除 `list_archive()` - 功能由 `SevenZipFile.namelist()` 提供
- 將 `list_contents()` 設為私有方法 `_list_contents()`

### 階段 2：API 命名標準化 (中優先級)

#### 2.1 統一命名慣例

**保持與 zipfile 一致**：
- ✅ `namelist()` - 已存在
- ✅ `extractall()` - 已存在，需完善 `members` 參數
- ✅ `read()` - 已存在
- ✅ `testzip()` - 已存在
- ❌ `infolist()` - 需新增
- ❌ `getinfo()` - 需新增

**保持與 tarfile 相容**：
- ✅ `getnames()` - 已存在，應調用 `namelist()`
- ❌ `getmembers()` - 需新增，應調用 `infolist()`
- ❌ `getmember()` - 需新增，應調用 `getinfo()`

#### 2.2 方法簽名標準化

**統一參數命名**：
```python
# 當前不一致的命名
SevenZipFile.extract(path=".")        # 使用 'path'
extract_archive(archive_path, output_dir=".")  # 使用 'output_dir'

# 標準化後
SevenZipFile.extractall(path=".")     # 與 zipfile 一致
extract_archive(archive_path, path=".") # 保持參數名一致
```

### 階段 3：功能完善 (中優先級)

#### 3.1 實作未完成功能

**完善 `extractall()` 方法**：
```python
def extractall(self, path=".", members=None):
    """完整實作 members 參數以支援選擇性解壓縮"""
```

**完善 `add()` 方法**：
```python  
def add(self, name, arcname=None):
    """完整實作 arcname 參數以支援自訂封存內路徑"""
```

#### 3.2 異步 API 一致性

**標準化 `AsyncSevenZipFile`**：
```python
class AsyncSevenZipFile:
    async def infolist(self) -> List[ArchiveInfo]: ...
    async def getinfo(self, name: str) -> ArchiveInfo: ...
    async def namelist(self) -> List[str]: ...
    # ... 其他與 SevenZipFile 對等的方法
```

### 階段 4：向後相容性 (低優先級)

#### 4.1 已廢棄 API 的處理

**標記為已廢棄但保留**：
```python
def list_archive(archive_path) -> List[str]:
    """
    List archive contents.
    
    .. deprecated:: 2.0.0
        Use SevenZipFile.namelist() instead for better zipfile compatibility.
    """
    warnings.warn("list_archive is deprecated, use SevenZipFile.namelist()", 
                  DeprecationWarning, stacklevel=2)
    with SevenZipFile(archive_path, 'r') as sz:
        return sz.namelist()
```

**私有化內部方法**：
```python
class SevenZipFile: 
    def _list_contents(self) -> List[str]:  # 改為私有
        """Internal method for listing contents"""
        
    def namelist(self) -> List[str]:
        """Public API that calls _list_contents()"""
        return self._list_contents()
```

## 實作優先級

### 高優先級 (必須實作)
1. ✅ 新增 `ArchiveInfo` 類別
2. ✅ 新增 `SevenZipFile.infolist()` 方法  
3. ✅ 新增 `SevenZipFile.getinfo()` 方法
4. ✅ 修復 `get_archive_info()` 功能混淆
5. ✅ 新增詳細資訊解析 (`-slt` 輸出解析)

### 中優先級 (建議實作)
1. ⚠️ 完善 `extractall(members=...)` 參數
2. ⚠️ 完善 `add(arcname=...)` 參數  
3. ⚠️ 標準化異步 API
4. ⚠️ 移除/私有化重複 API

### 低優先級 (可選實作)
1. 🔄 向後相容性警告
2. 🔄 API 文檔更新
3. 🔄 遷移指南更新

## 實作策略

### 1. 漸進式重構
- 新增 API 而不立即移除舊 API
- 使用 deprecation warnings 標記舊 API
- 在主要版本更新時移除廢棄 API

### 2. 測試優先
- 為每個新 API 編寫測試
- 確保與 zipfile/tarfile 行為一致
- 測試向後相容性

### 3. 文檔同步更新
- 更新 API 文檔
- 更新遷移指南
- 更新範例程式碼

## 預期效果

### 對使用者的好處
1. **更好的遷移體驗**：與 zipfile/tarfile 更一致的 API
2. **更完整的功能**：支援檔案詳細資訊查詢
3. **更清晰的設計**：分離的功能，避免概念混淆
4. **更好的類型支援**：明確的回傳類型

### 對專案的好處  
1. **符合業界標準**：與 Python 標準庫設計原則一致
2. **更好的可維護性**：清晰的 API 邊界
3. **更強的競爭力**：完整的功能對標
4. **更好的用戶接受度**：符合用戶預期的 API 設計

## 風險評估

### 低風險
- 新增 API：向後相容，不影響現有程式碼
- 私有化內部方法：透過 deprecation 警告漸進移除

### 中風險  
- 修改 `get_archive_info()` 回傳格式：可能影響依賴特定格式的程式碼
- 解決方案：提供新方法名，保留舊方法但加入 deprecation 警告

### 高風險
- 無：本重構計劃主要是新增功能，不直接破壞現有 API

## 結論

此重構計劃旨在將 py7zz 從一個功能性的 7zz 包裝器升級為一個符合業界標準、設計良好的檔案封存庫。通過對標 zipfile 和 tarfile 的設計原則，py7zz 將能提供更好的使用者體驗和更強的功能完整性。

重構將採用漸進式方法，確保向後相容性的同時提供現代化的 API 設計。這將使 py7zz 成為 Python 生態系統中檔案封存操作的首選解決方案。
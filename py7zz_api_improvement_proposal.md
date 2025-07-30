# py7zz API Improvement Proposal

## 概述

本提案旨在全面改進py7zz的API設計，確保各層級間的一致性、完整性和易用性。基於對現有架構的分析，制定完整的標準化計劃。

## 當前API架構分析

### 現有分層架構
1. **Layer 1 - 簡單函數API** (simple.py) - 一行解決方案
2. **Layer 2 - 物件導向API** (core.py) - zipfile/tarfile相容介面  
3. **Layer 3 - 進階控制API** (config.py, compression.py) - 細粒度控制
4. **Layer 4 - 異步API** (async_ops.py) - 非阻塞操作
5. **Layer 5 - 專家API** (run_7z) - 直接7zz存取

### 發現的問題

#### 1. API一致性問題
- **參數命名不統一**：
  - `extract_archive(output_dir)` vs `SevenZipFile.extract(path)`
  - `compress_file(output_path)` vs `create_archive(archive_path)`
- **錯誤處理不一致**：
  - 部分函數拋出`FileNotFoundError`，部分拋出`RuntimeError`
  - 異常訊息格式不統一

#### 2. 功能完整性缺失
- **SevenZipFile缺少標準方法**：
  - 缺少`readall()`, `open()`等zipfile標準方法
  - 缺少完整的上下文管理器支援
- **簡單API缺少便利函數**：
  - 缺少`copy_archive()`, `merge_archives()`等常用操作
  - 批量操作支援不足

#### 3. 配置系統限制
- **預設值管理**：
  - 缺少全域默認配置
  - 無法持久化用戶偏好設定
- **動態配置**：
  - 無法根據檔案類型自動選擇最佳配置
  - 缺少智能預設值推薦

#### 4. 文件和測試覆蓋
- **API文件不完整**：部分新增方法缺少文件
- **測試覆蓋不全面**：某些邊緣情況未測試
- **範例程式碼過時**：部分範例使用舊的API

## 改進計劃

### Phase 6.1 - API標準化設計原則

#### 核心設計原則
1. **一致性優先**：
   - 統一參數命名規範
   - 統一錯誤處理機制
   - 統一返回值格式

2. **向後相容性**：
   - 保持現有API不變
   - 新增方法而非替換
   - 提供遷移路徑

3. **漸進複雜性**：
   - Layer 1: 零配置，一行解決
   - Layer 2: 標準配置，物件導向
   - Layer 3: 高級配置，專家控制
   - Layer 4: 異步操作，大規模處理
   - Layer 5: 直接控制，最大靈活性

#### 命名規範標準化
```python
# 統一參數命名
archive_path: str           # 壓縮檔路徑
source_path: str            # 來源檔/目錄路徑  
output_dir: str             # 輸出目錄
target_path: str            # 目標路徑
file_list: List[str]        # 檔案清單
member_list: List[str]      # 成員清單
preset: str                 # 預設配置名稱
config: Config              # 詳細配置對象
progress_callback: Callable # 進度回調函數
overwrite: bool = True      # 是否覆寫
create_dirs: bool = True    # 是否建立目錄
```

### Phase 6.2 - Layer 1 簡單函數API增強

#### 新增便利函數
```python
# 批量操作
def batch_create_archives(operations: List[Tuple[str, List[str]]], **kwargs) -> None
def batch_extract_archives(archives: List[str], output_dir: str, **kwargs) -> None

# 檔案操作
def copy_archive(source: str, target: str, **kwargs) -> None  
def merge_archives(archives: List[str], output: str, **kwargs) -> None
def split_archive(archive: str, part_size: str, **kwargs) -> List[str]

# 資訊查詢  
def get_compression_ratio(archive_path: str) -> float
def get_archive_format(archive_path: str) -> str
def compare_archives(archive1: str, archive2: str) -> bool

# 轉換操作
def convert_archive_format(source: str, target: str, target_format: str, **kwargs) -> None
def recompress_archive(archive_path: str, new_preset: str, **kwargs) -> None
```

#### 參數標準化
```python
# 統一所有簡單API的參數格式
def create_archive(
    archive_path: str,
    source_paths: List[str], 
    preset: str = "balanced",
    config: Optional[Config] = None,
    progress_callback: Optional[Callable] = None,
    overwrite: bool = True
) -> None

def extract_archive(
    archive_path: str,
    output_dir: str = ".",
    member_list: Optional[List[str]] = None,
    overwrite: bool = True,
    create_dirs: bool = True,
    progress_callback: Optional[Callable] = None
) -> None
```

### Phase 6.3 - Layer 2 核心API完善

#### SevenZipFile標準化
```python
class SevenZipFile:
    # 新增zipfile相容方法
    def open(self, name: str, mode: str = "r") -> BinaryIO
    def readall(self) -> bytes  
    def setpassword(self, pwd: bytes) -> None
    def comment(self) -> bytes
    def setcomment(self, comment: bytes) -> None
    
    # 新增tarfile相容方法  
    def getnames(self) -> List[str]
    def getmembers(self) -> List[ArchiveInfo]
    def getmember(self, name: str) -> ArchiveInfo
    def gettarinfo(self, name: str) -> ArchiveInfo
    
    # 新增便利方法
    def copy_member(self, member: str, target_archive: 'SevenZipFile') -> None
    def rename_member(self, old_name: str, new_name: str) -> None
    def delete_member(self, name: str) -> None
    
    # 增強現有方法
    def extract(
        self, 
        output_dir: str = ".", 
        member_list: Optional[List[str]] = None,
        progress_callback: Optional[Callable] = None
    ) -> None
    
    def add(
        self, 
        source_path: str, 
        arcname: Optional[str] = None,
        recursive: bool = True,
        filter_func: Optional[Callable] = None
    ) -> None
```

### Phase 6.4 - Layer 3 進階配置系統

#### 配置系統增強
```python
@dataclass
class AdvancedConfig(Config):
    # 自動配置
    auto_detect_format: bool = True
    auto_optimize_settings: bool = True
    
    # 檔案過濾
    include_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    
    # 性能調優  
    io_buffer_size: str = "1m"
    temp_dir: Optional[str] = None
    
    # 驗證設定
    verify_after_create: bool = False
    checksum_algorithm: str = "crc32"

# 全域配置管理
class GlobalConfig:
    @classmethod
    def set_default_preset(cls, preset: str) -> None
    
    @classmethod  
    def get_default_preset(cls) -> str
    
    @classmethod
    def load_user_config(cls, config_path: str) -> None
    
    @classmethod
    def save_user_config(cls, config_path: str) -> None

# 智能預設值推薦
class PresetRecommender:
    @staticmethod
    def recommend_for_content(file_paths: List[str]) -> str
    
    @staticmethod
    def recommend_for_size(total_size: int) -> str
    
    @staticmethod
    def recommend_for_usage(usage_type: str) -> str  # "backup", "distribution", "storage"
```

### Phase 6.5 - 統一異常處理系統

#### 異常層次結構重新設計
```python
# 基礎異常類別
class Py7zzError(Exception):
    def __init__(self, message: str, error_code: Optional[int] = None, context: Optional[Dict] = None)

# 具體異常類別  
class ValidationError(Py7zzError):
    """輸入驗證錯誤"""
    
class OperationError(Py7zzError): 
    """操作執行錯誤"""
    
class CompatibilityError(Py7zzError):
    """相容性錯誤"""

# 統一錯誤處理裝飾器
def handle_7z_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except subprocess.CalledProcessError as e:
            # 統一轉換為py7zz異常
            raise OperationError(f"7z operation failed: {e.stderr}", e.returncode)
        except FileNotFoundError as e:
            raise ValidationError(f"File not found: {e.filename}")
    return wrapper
```

### Phase 6.6 - 文件和測試標準化

#### API文件結構  
```
docs/api/
├── overview.md              # API概述和設計理念
├── quickstart.md           # 快速開始指南  
├── layer1-simple.md        # Layer 1 簡單函數API
├── layer2-oop.md           # Layer 2 物件導向API
├── layer3-advanced.md      # Layer 3 進階配置API
├── layer4-async.md         # Layer 4 異步操作API
├── layer5-expert.md        # Layer 5 專家級API
├── error-handling.md       # 錯誤處理指南
├── migration-guide.md      # 遷移指南
└── examples/               # 完整範例程式碼
    ├── basic-usage.py
    ├── advanced-config.py
    ├── async-operations.py
    └── batch-processing.py
```

#### 測試架構標準化
```
tests/api/
├── test_layer1_simple.py       # Layer 1 測試
├── test_layer2_oop.py          # Layer 2 測試  
├── test_layer3_advanced.py     # Layer 3 測試
├── test_layer4_async.py        # Layer 4 測試
├── test_layer5_expert.py       # Layer 5 測試
├── test_error_handling.py      # 錯誤處理測試
├── test_compatibility.py       # 相容性測試
└── integration/                # 整合測試
    ├── test_full_workflow.py
    ├── test_cross_platform.py
    └── test_performance.py
```

## 實施時程

### Week 1: API設計標準化
- [ ] 完成API設計規範文件
- [ ] 制定命名規範和錯誤處理標準
- [ ] 設計統一的參數和返回值格式

### Week 2: Layer 1 & 2 增強  
- [ ] 實現簡單API的新便利函數
- [ ] 完善SevenZipFile的標準方法
- [ ] 標準化所有參數命名

### Week 3: Layer 3 & 配置系統
- [ ] 增強配置系統和預設值管理
- [ ] 實現智能配置推薦
- [ ] 建立全域配置管理

### Week 4: 測試和文件
- [ ] 編寫完整的測試套件
- [ ] 更新所有API文件
- [ ] 建立遷移指南和範例

### Week 5: 整合和驗證
- [ ] 執行完整的整合測試
- [ ] 性能基準測試
- [ ] 最終品質保證

## 成功指標

1. **API一致性**：100%的參數命名符合標準
2. **功能完整性**：所有標準zipfile/tarfile方法已實現  
3. **測試覆蓋率**：達到95%以上的程式碼覆蓋率
4. **文件完整性**：所有公共API都有完整文件
5. **性能維持**：改進後性能不低於原版本
6. **向後相容**：現有程式碼無需修改即可運行

## 風險評估

1. **向後相容性**：通過保留舊API並逐步過渡來降低風險
2. **性能影響**：通過基準測試確保性能不下降  
3. **複雜性增加**：通過清晰的分層設計和文件來管理複雜性
4. **測試覆蓋**：通過自動化測試確保品質

## 結論

這個全面的API改進計劃將使py7zz成為一個更加完整、一致和易用的Python壓縮庫。通過分階段實施和嚴格的品質控制，我們可以在保持向後相容性的同時，大幅提升API的專業性和易用性。
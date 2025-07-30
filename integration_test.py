#!/usr/bin/env python3
"""
階段6-整合驗證：完整的API整合測試腳本

本腳本執行完整的py7zz API整合測試，驗證所有新增功能的正確性和相互協作。
"""

import sys


def test_api_availability():
    """測試所有新增API的可用性"""
    print("🔍 測試 API 可用性...")

    import py7zz

    # Layer 1 進階函數
    layer1_functions = [
        "batch_create_archives",
        "batch_extract_archives",
        "copy_archive",
        "get_compression_ratio",
        "get_archive_format",
        "compare_archives",
        "convert_archive_format",
        "recompress_archive",
    ]

    for func_name in layer1_functions:
        assert hasattr(py7zz, func_name), f"❌ 缺少函數: {func_name}"
        assert callable(getattr(py7zz, func_name)), f"❌ {func_name} 不可調用"

    # Layer 2 增強方法 - SevenZipFile
    with py7zz.SevenZipFile("dummy.7z", "w") as sz:
        layer2_methods = [
            "open",
            "readall",
            "setpassword",
            "comment",
            "setcomment",
            "copy_member",
            "filter_members",
            "get_member_size",
            "get_member_compressed_size",
        ]

        for method_name in layer2_methods:
            assert hasattr(sz, method_name), f"❌ SevenZipFile 缺少方法: {method_name}"

    # Layer 3 全域配置
    assert hasattr(py7zz, "GlobalConfig"), "❌ 缺少 GlobalConfig 類別"
    assert hasattr(py7zz, "PresetRecommender"), "❌ 缺少 PresetRecommender 類別"

    # 統一異常處理
    exception_classes = [
        "ValidationError",
        "OperationError",
        "CompatibilityError",
        "handle_7z_errors",
        "handle_file_errors",
        "handle_validation_errors",
        "classify_error_type",
        "get_error_suggestions",
    ]

    for exc_name in exception_classes:
        assert hasattr(py7zz, exc_name), f"❌ 缺少異常類別/函數: {exc_name}"

    print("✅ 所有 API 都可用")


def test_basic_functionality():
    """測試基本功能正常工作"""
    print("🧪 測試基本功能...")

    import py7zz

    # 測試批次操作（空列表）
    try:
        py7zz.batch_create_archives([])
        py7zz.batch_extract_archives([], "output/")
        print("✅ 批次操作基本功能正常")
    except Exception as e:
        print(f"❌ 批次操作測試失敗: {e}")
        return False

    # 測試異常處理
    try:

        @py7zz.handle_validation_errors
        def test_decorated_function():
            pass

        test_decorated_function()  # 應該正常執行
        print("✅ 異常處理裝飾器正常")
    except Exception as e:
        print(f"❌ 異常處理測試失敗: {e}")
        return False

    # 測試配置系統
    try:
        current_preset = py7zz.GlobalConfig.get_default_preset()
        print(f"✅ 當前預設預設: {current_preset}")
    except Exception as e:
        print(f"❌ 配置系統測試失敗: {e}")
        return False

    return True


def test_error_handling():
    """測試錯誤處理機制"""
    print("🛡️ 測試錯誤處理機制...")

    import py7zz

    # 測試對不存在檔案的錯誤處理
    try:
        py7zz.get_compression_ratio("nonexistent.7z")
        print("❌ 應該拋出異常但沒有")
        return False
    except py7zz.FileNotFoundError:
        print("✅ 正確處理不存在檔案的錯誤")
    except Exception as e:
        print(f"❌ 意外的異常類型: {type(e).__name__}: {e}")
        return False

    # 測試異常增強功能
    try:
        error = py7zz.ValidationError("測試錯誤", parameter="test_param")
        error.add_context("operation", "test")
        error.add_suggestion("檢查參數")

        info = error.get_detailed_info()
        assert "parameter" in info["context"]
        assert "operation" in info["context"]
        assert len(info["suggestions"]) >= 1
        print("✅ 異常增強功能正常")
    except Exception as e:
        print(f"❌ 異常增強功能測試失敗: {e}")
        return False

    return True


def test_configuration_system():
    """測試配置系統"""
    print("⚙️ 測試配置系統...")

    import py7zz

    try:
        # 測試預設管理
        original_preset = py7zz.GlobalConfig.get_default_preset()
        py7zz.GlobalConfig.set_default_preset("ultra")
        assert py7zz.GlobalConfig.get_default_preset() == "ultra"
        py7zz.GlobalConfig.set_default_preset(original_preset)  # 恢復原始狀態

        print("✅ 配置系統基本功能正常")
    except Exception as e:
        print(f"❌ 配置系統測試失敗: {e}")
        return False

    try:
        # 測試預設推薦
        for usage in ["backup", "storage", "distribution", "temporary"]:
            recommendation = py7zz.PresetRecommender.recommend_for_usage(usage)
            assert recommendation in [
                "fast",
                "balanced",
                "backup",
                "ultra",
                "secure",
                "compatibility",
            ]

        print("✅ 預設推薦系統正常")
    except Exception as e:
        print(f"❌ 預設推薦測試失敗: {e}")
        return False

    return True


def test_compatibility():
    """測試向後相容性"""
    print("🔄 測試向後相容性...")

    import py7zz

    try:
        # 測試基本API仍然可用
        basic_functions = [
            "create_archive",
            "extract_archive",
            "test_archive",
            "get_archive_info",
        ]

        for func_name in basic_functions:
            assert hasattr(py7zz, func_name), f"❌ 基本函數 {func_name} 不見了"
            assert callable(getattr(py7zz, func_name)), f"❌ {func_name} 不可調用"

        # 測試SevenZipFile基本方法
        with py7zz.SevenZipFile("dummy.7z", "w") as sz:
            basic_methods = ["add", "writestr", "close"]
            for method_name in basic_methods:
                assert hasattr(sz, method_name), (
                    f"❌ SevenZipFile 基本方法 {method_name} 不見了"
                )

        print("✅ 向後相容性測試通過")
        return True
    except Exception as e:
        print(f"❌ 向後相容性測試失敗: {e}")
        return False


def test_version_consistency():
    """測試版本一致性"""
    print("📋 測試版本一致性...")

    import py7zz

    try:
        # 測試版本函數可用
        version = py7zz.get_version()
        bundled_version = py7zz.get_bundled_7zz_version()
        version_info = py7zz.get_version_info()

        assert isinstance(version, str) and version, "❌ get_version() 應該返回非空字串"
        assert isinstance(bundled_version, str) and bundled_version, (
            "❌ get_bundled_7zz_version() 應該返回非空字串"
        )
        assert isinstance(version_info, dict), "❌ get_version_info() 應該返回字典"

        print(f"✅ 版本資訊正常 - py7zz: {version}, 7zz: {bundled_version}")
        return True
    except Exception as e:
        print(f"❌ 版本一致性測試失敗: {e}")
        return False


def run_integration_tests():
    """執行完整的整合測試"""
    print("🚀 開始執行 py7zz API 整合驗證測試")
    print("=" * 60)

    tests = [
        test_api_availability,
        test_basic_functionality,
        test_error_handling,
        test_configuration_system,
        test_compatibility,
        test_version_consistency,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            result = test_func()
            if result is not False:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ 測試 {test_func.__name__} 異常失敗: {e}")
            failed += 1
        print()  # 空行分隔

    print("=" * 60)
    print(f"📊 整合測試完成: {passed} 通過, {failed} 失敗")

    if failed == 0:
        print("🎉 所有整合測試通過！py7zz API 整合性驗證成功")
        return True
    else:
        print("⚠️  部分整合測試失敗，需要檢查相關功能")
        return False


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)

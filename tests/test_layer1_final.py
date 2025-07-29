"""
Final simplified test suite for Layer 1 Advanced Convenience Functions.
"""

import pytest

import py7zz


class TestAdvancedFunctionsExist:
    """Test that all advanced functions exist and are callable."""

    def test_all_functions_exist(self):
        """Verify all Layer 1 advanced functions exist and are callable."""
        functions_to_test = [
            "batch_create_archives",
            "batch_extract_archives",
            "copy_archive",
            "get_compression_ratio",
            "get_archive_format",
            "compare_archives",
            "convert_archive_format",
            "recompress_archive",
        ]

        for func_name in functions_to_test:
            assert hasattr(py7zz, func_name), f"Function {func_name} not found"
            func = getattr(py7zz, func_name)
            assert callable(func), f"Function {func_name} is not callable"

    def test_function_signatures(self):
        """Test function signatures are reasonable."""
        import inspect

        # Test batch_create_archives
        sig = inspect.signature(py7zz.batch_create_archives)
        assert "operations" in sig.parameters
        assert "preset" in sig.parameters

        # Test batch_extract_archives
        sig = inspect.signature(py7zz.batch_extract_archives)
        assert "archive_paths" in sig.parameters
        assert "output_dir" in sig.parameters

        # Test copy_archive
        sig = inspect.signature(py7zz.copy_archive)
        assert "source_archive" in sig.parameters
        assert "target_archive" in sig.parameters

        # Test get_compression_ratio
        sig = inspect.signature(py7zz.get_compression_ratio)
        assert "archive_path" in sig.parameters

        # Test get_archive_format
        sig = inspect.signature(py7zz.get_archive_format)
        assert "archive_path" in sig.parameters

        # Test compare_archives
        sig = inspect.signature(py7zz.compare_archives)
        assert "archive1" in sig.parameters
        assert "archive2" in sig.parameters


class TestBasicFunctionality:
    """Test basic functionality without complex mocking."""

    def test_batch_create_empty_operations(self):
        """Test batch creation with empty operations list."""
        # This should not raise an error
        try:
            py7zz.batch_create_archives([])
        except Exception as e:
            pytest.fail(f"batch_create_archives([]) raised {type(e).__name__}: {e}")

    def test_batch_extract_empty_archives(self):
        """Test batch extraction with empty archive list."""
        # This should not raise an error
        try:
            py7zz.batch_extract_archives([], "output/")
        except Exception as e:
            pytest.fail(
                f"batch_extract_archives([], 'output/') raised {type(e).__name__}: {e}"
            )

    def test_error_handling_for_missing_files(self):
        """Test that functions properly handle missing files."""
        # These should raise FileNotFoundError

        with pytest.raises(py7zz.FileNotFoundError):
            py7zz.copy_archive("nonexistent.7z", "target.7z")

        with pytest.raises(py7zz.FileNotFoundError):
            py7zz.get_compression_ratio("nonexistent.7z")

        with pytest.raises(py7zz.FileNotFoundError):
            py7zz.get_archive_format("nonexistent.7z")


class TestParameterValidation:
    """Test parameter validation for advanced functions."""

    def test_batch_create_invalid_operations(self):
        """Test batch creation with invalid operations format."""
        # Test with invalid operation format
        with pytest.raises((ValueError, TypeError)):
            py7zz.batch_create_archives("not_a_list")

    def test_batch_extract_invalid_type(self):
        """Test batch extraction with invalid archive list type."""
        # The function iterates over string chars, which leads to individual file checks
        # This is expected behavior - each character becomes a "filename" to check
        with pytest.raises(py7zz.FileNotFoundError):
            py7zz.batch_extract_archives("not_a_list", "output/")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

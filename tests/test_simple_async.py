"""
Tests for async simple API functions.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Import async functions if available
try:
    from py7zz.simple import (
        compress_directory_async,
        compress_file_async,
        create_archive_async,
        extract_archive_async,
    )
    async_available = True
except ImportError:
    async_available = False

from py7zz.async_ops import ProgressInfo
from py7zz.exceptions import FileNotFoundError


@pytest.mark.skipif(not async_available, reason="Async operations not available")
class TestSimpleAsyncAPI:
    """Test simple async API functions."""
    
    @pytest.mark.asyncio
    async def test_create_archive_async_file_not_found(self):
        """Test create_archive_async with non-existent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = Path(tmpdir) / "test.7z"
            nonexistent_file = Path(tmpdir) / "nonexistent.txt"
            
            with pytest.raises(FileNotFoundError):
                await create_archive_async(archive_path, [nonexistent_file])
    
    @pytest.mark.asyncio
    async def test_extract_archive_async_not_found(self):
        """Test extract_archive_async with non-existent archive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent_archive = Path(tmpdir) / "nonexistent.7z"
            
            with pytest.raises(FileNotFoundError):
                await extract_archive_async(nonexistent_archive, tmpdir)
    
    @pytest.mark.asyncio
    async def test_compress_file_async_not_found(self):
        """Test compress_file_async with non-existent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent_file = Path(tmpdir) / "nonexistent.txt"
            
            with pytest.raises(FileNotFoundError):
                await compress_file_async(nonexistent_file)
    
    @pytest.mark.asyncio
    async def test_compress_directory_async_not_found(self):
        """Test compress_directory_async with non-existent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent_dir = Path(tmpdir) / "nonexistent"
            
            with pytest.raises(FileNotFoundError):
                await compress_directory_async(nonexistent_dir)
    
    @pytest.mark.asyncio
    async def test_compress_directory_async_not_directory(self):
        """Test compress_directory_async with file instead of directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")
            
            with pytest.raises(ValueError, match="Path is not a directory"):
                await compress_directory_async(test_file)
    
    @pytest.mark.asyncio
    async def test_create_archive_async_with_progress(self):
        """Test create_archive_async with progress callback."""
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = Path(tmpdir) / "test.7z"
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")
            
            progress_calls = []
            
            def progress_callback(info):
                progress_calls.append(info)
                assert isinstance(info, ProgressInfo)
            
            with patch('py7zz.simple._compress_async') as mock_compress:
                mock_compress.return_value = None
                
                await create_archive_async(
                    archive_path, 
                    [test_file], 
                    progress_callback=progress_callback
                )
                
                # Verify _compress_async was called with correct arguments
                mock_compress.assert_called_once_with(
                    archive_path, 
                    [test_file], 
                    progress_callback
                )
    
    @pytest.mark.asyncio
    async def test_extract_archive_async_with_progress(self):
        """Test extract_archive_async with progress callback."""
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = Path(tmpdir) / "test.7z"
            
            progress_calls = []
            
            def progress_callback(info):
                progress_calls.append(info)
                assert isinstance(info, ProgressInfo)
            
            with patch('py7zz.simple._extract_async') as mock_extract, \
                 patch('pathlib.Path.exists', return_value=True):
                mock_extract.return_value = None
                
                await extract_archive_async(
                    archive_path, 
                    tmpdir, 
                    progress_callback=progress_callback
                )
                
                # Verify _extract_async was called with correct arguments
                mock_extract.assert_called_once_with(
                    archive_path, 
                    tmpdir, 
                    True,  # overwrite default
                    progress_callback
                )
    
    @pytest.mark.asyncio
    async def test_compress_file_async_with_auto_output(self):
        """Test compress_file_async with auto-generated output path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")
            
            with patch('py7zz.simple.create_archive_async') as mock_create:
                mock_create.return_value = None
                
                result = await compress_file_async(test_file)
                
                # Verify result is correct path
                expected_path = test_file.with_suffix(test_file.suffix + ".7z")
                assert result == expected_path
                
                # Verify create_archive_async was called
                mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_compress_file_async_with_custom_output(self):
        """Test compress_file_async with custom output path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")
            output_path = Path(tmpdir) / "custom.7z"
            
            with patch('py7zz.simple.create_archive_async') as mock_create:
                mock_create.return_value = None
                
                result = await compress_file_async(test_file, output_path)
                
                # Verify result is correct path
                assert result == output_path
                
                # Verify create_archive_async was called with correct arguments
                mock_create.assert_called_once_with(
                    output_path, 
                    [test_file], 
                    preset="balanced", 
                    progress_callback=None
                )
    
    @pytest.mark.asyncio
    async def test_compress_directory_async_with_auto_output(self):
        """Test compress_directory_async with auto-generated output path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "test_dir"
            test_dir.mkdir()
            (test_dir / "file.txt").write_text("content")
            
            with patch('py7zz.simple.create_archive_async') as mock_create:
                mock_create.return_value = None
                
                result = await compress_directory_async(test_dir)
                
                # Verify result is correct path
                expected_path = test_dir.with_suffix(".7z")
                assert result == expected_path
                
                # Verify create_archive_async was called
                mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_compress_directory_async_with_custom_output(self):
        """Test compress_directory_async with custom output path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "test_dir"
            test_dir.mkdir()
            (test_dir / "file.txt").write_text("content")
            output_path = Path(tmpdir) / "custom.7z"
            
            with patch('py7zz.simple.create_archive_async') as mock_create:
                mock_create.return_value = None
                
                result = await compress_directory_async(test_dir, output_path)
                
                # Verify result is correct path
                assert result == output_path
                
                # Verify create_archive_async was called with correct arguments
                mock_create.assert_called_once_with(
                    output_path, 
                    [test_dir], 
                    preset="balanced", 
                    progress_callback=None
                )
    
    @pytest.mark.asyncio
    async def test_preset_handling(self):
        """Test preset parameter handling in async functions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")
            
            with patch('py7zz.simple.create_archive_async') as mock_create:
                mock_create.return_value = None
                
                # Test different presets
                for preset in ["fast", "balanced", "backup", "ultra"]:
                    await compress_file_async(test_file, preset=preset)
                    
                    # Verify correct preset was passed
                    call_args = mock_create.call_args
                    assert call_args[1]["preset"] == preset
    
    @pytest.mark.asyncio
    async def test_overwrite_parameter(self):
        """Test overwrite parameter in extract_archive_async."""
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = Path(tmpdir) / "test.7z"
            
            with patch('py7zz.simple._extract_async') as mock_extract, \
                 patch('pathlib.Path.exists', return_value=True):
                mock_extract.return_value = None
                
                # Test with overwrite=True (default)
                await extract_archive_async(archive_path, tmpdir)
                mock_extract.assert_called_with(archive_path, tmpdir, True, None)
                
                # Test with overwrite=False
                await extract_archive_async(archive_path, tmpdir, overwrite=False)
                mock_extract.assert_called_with(archive_path, tmpdir, False, None)


@pytest.mark.skipif(async_available, reason="Async operations are available")
class TestAsyncNotAvailable:
    """Test behavior when async operations are not available."""
    
    def test_async_functions_not_imported(self):
        """Test that async functions are not imported when not available."""
        # This test runs only when async operations are not available
        # It verifies that the import fails gracefully
        with pytest.raises(ImportError):
            pass
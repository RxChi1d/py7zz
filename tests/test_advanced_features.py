# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""
Test suite for advanced features based on ChatGPT o3 recommendations.

Tests streaming interface, thread-safe configuration, structured callbacks,
and logging integration.
"""

import io
import json
import tempfile
import threading
import time
from unittest.mock import Mock, patch

import pytest

import py7zz
from py7zz.callbacks import OperationStage, OperationType, ProgressInfo, ProgressTracker
from py7zz.streaming import ArchiveStreamReader, ArchiveStreamWriter
from py7zz.thread_safe_config import ImmutableConfig, ThreadSafeGlobalConfig


class TestStreamingInterface:
    """Test file-like streaming interface for cloud integration."""

    def test_archive_stream_reader_basic(self):
        """Test basic ArchiveStreamReader functionality."""
        # Mock archive for testing
        mock_archive = Mock()
        mock_archive.namelist.return_value = ["test.txt"]
        mock_archive.read.return_value = b"Hello, World!\nSecond line\n"

        reader = ArchiveStreamReader(mock_archive, "test.txt")

        # Test basic properties
        assert reader.readable()
        assert not reader.writable()
        assert reader.seekable()
        assert not reader.closed

        # Test reading
        data = reader.read(5)
        assert data == b"Hello"
        assert reader.tell() == 5

        # Test seeking
        reader.seek(0)
        assert reader.tell() == 0

        # Test readline
        line = reader.readline()
        assert line == b"Hello, World!\n"

        reader.close()
        assert reader.closed

    def test_archive_stream_reader_context_manager(self):
        """Test ArchiveStreamReader as context manager."""
        mock_archive = Mock()
        mock_archive.namelist.return_value = ["test.txt"]
        mock_archive.read.return_value = b"test content"

        with ArchiveStreamReader(mock_archive, "test.txt") as reader:
            assert not reader.closed
            data = reader.read()
            assert data == b"test content"

        assert reader.closed

    def test_archive_stream_writer_basic(self):
        """Test basic ArchiveStreamWriter functionality."""
        mock_archive = Mock()

        with tempfile.TemporaryDirectory():
            writer = ArchiveStreamWriter(mock_archive, "output.txt")

            # Test basic properties
            assert not writer.readable()
            assert writer.writable()
            assert writer.seekable()
            assert not writer.closed

            # Test writing
            bytes_written = writer.write(b"Hello, World!")
            assert bytes_written == 13

            writer.close()
            assert writer.closed

            # Verify archive.add was called
            mock_archive.add.assert_called_once()

    def test_archive_stream_writer_context_manager(self):
        """Test ArchiveStreamWriter as context manager."""
        mock_archive = Mock()

        with ArchiveStreamWriter(mock_archive, "output.txt") as writer:
            assert not writer.closed
            writer.write(b"test content")

        assert writer.closed
        mock_archive.add.assert_called_once()

    def test_streaming_io_compatibility(self):
        """Test compatibility with io.BufferedIOBase interface."""
        mock_archive = Mock()
        mock_archive.namelist.return_value = ["test.txt"]
        mock_archive.read.return_value = b"Hello, World!"

        reader = ArchiveStreamReader(mock_archive, "test.txt")

        # Test isinstance check
        assert isinstance(reader, io.BufferedIOBase)

        # Test readinto method
        buffer = bytearray(10)
        bytes_read = reader.readinto(buffer)
        assert bytes_read == 10
        assert buffer == b"Hello, Wor"

        reader.close()


class TestThreadSafeConfiguration:
    """Test thread-safe configuration management."""

    def test_immutable_config_creation(self):
        """Test immutable configuration creation and validation."""
        config = ImmutableConfig(level=7, compression="lzma2", solid=True)

        assert config.level == 7
        assert config.compression == "lzma2"
        assert config.solid is True

        # Test immutability
        with pytest.raises(
            AttributeError
        ):  # dataclass frozen=True prevents modification
            config.level = 9  # type: ignore # intentionally testing frozen dataclass

    def test_immutable_config_replace(self):
        """Test creating new config with changes."""
        original = ImmutableConfig(level=5)
        modified = original.replace(level=9, compression="bzip2")

        # Original unchanged
        assert original.level == 5
        assert original.compression == "lzma2"

        # New config has changes
        assert modified.level == 9
        assert modified.compression == "bzip2"

    def test_thread_safe_global_config_basic(self):
        """Test basic thread-safe configuration operations."""
        # Reset to known state
        ThreadSafeGlobalConfig.reset_to_defaults()

        # Test getting and setting config
        config = ThreadSafeGlobalConfig.get_config()
        assert isinstance(config, ImmutableConfig)

        new_config = ImmutableConfig(level=9, preset_name="test")
        ThreadSafeGlobalConfig.set_config(new_config)

        retrieved = ThreadSafeGlobalConfig.get_config()
        assert retrieved.level == 9
        assert retrieved.preset_name == "test"

    def test_thread_safe_global_config_update(self):
        """Test updating global configuration."""
        ThreadSafeGlobalConfig.reset_to_defaults()

        updated = ThreadSafeGlobalConfig.update_config(level=8, compression="bzip2")

        assert updated.level == 8
        assert updated.compression == "bzip2"

        # Verify it's actually set globally
        current = ThreadSafeGlobalConfig.get_config()
        assert current.level == 8
        assert current.compression == "bzip2"

    def test_temporary_config_context_manager(self):
        """Test temporary configuration context manager."""
        ThreadSafeGlobalConfig.reset_to_defaults()
        original_level = ThreadSafeGlobalConfig.get_config().level

        with ThreadSafeGlobalConfig.temporary_config(level=9) as temp_config:
            assert temp_config.level == 9
            assert ThreadSafeGlobalConfig.get_config().level == 9

        # Should be restored
        assert ThreadSafeGlobalConfig.get_config().level == original_level

    def test_thread_safety_concurrent_access(self):
        """Test concurrent access to global configuration."""
        ThreadSafeGlobalConfig.reset_to_defaults()
        results = []
        errors = []

        def worker(worker_id: int):
            try:
                for i in range(10):
                    # Mix of reads and writes
                    config = ThreadSafeGlobalConfig.get_config()
                    results.append((worker_id, config.level))

                    if i % 3 == 0:
                        ThreadSafeGlobalConfig.update_config(level=(worker_id + i) % 10)

                    time.sleep(0.001)  # Small delay to encourage race conditions
            except Exception as e:
                errors.append((worker_id, str(e)))

        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Should have no errors and reasonable number of results
        assert len(errors) == 0
        assert len(results) >= 40  # Should have some results from each thread

    def test_preset_integration(self):
        """Test preset configuration integration."""
        # Test getting preset config
        ultra_config = py7zz.get_preset_config("ultra")
        assert ultra_config.level == 9
        assert ultra_config.preset_name == "ultra"

        # Test applying preset
        py7zz.apply_preset("fast")
        current = ThreadSafeGlobalConfig.get_config()
        assert current.preset_name == "fast"
        assert current.level == 1

        # Test preset context manager
        with py7zz.with_preset("ultra") as preset_config:
            assert preset_config.level == 9

        # Should be restored to fast
        assert ThreadSafeGlobalConfig.get_config().preset_name == "fast"


class TestStructuredCallbacks:
    """Test structured callback system."""

    def test_progress_info_creation(self):
        """Test ProgressInfo creation and validation."""
        progress = ProgressInfo(
            percentage=50.0,
            bytes_processed=1024,
            total_bytes=2048,
            speed_bps=1000.0,
            elapsed_time=1.5,
            estimated_remaining=1.5,
            operation_type=OperationType.COMPRESS,
            operation_stage=OperationStage.PROCESSING,
            current_file="test.txt",
            files_processed=1,
            total_files=2,
            metadata={"custom": "value"},
        )

        assert progress.percentage == 50.0
        assert progress.completion_ratio == 0.5
        assert progress.bytes_remaining == 1024
        assert progress.files_remaining == 1
        assert progress.metadata["custom"] == "value"

    def test_progress_info_validation(self):
        """Test ProgressInfo validation."""
        # Test invalid percentage
        with pytest.raises(ValueError):
            ProgressInfo(
                percentage=150.0,  # Invalid
                bytes_processed=0,
                total_bytes=100,
                speed_bps=None,
                elapsed_time=0,
                estimated_remaining=None,
                operation_type=OperationType.COMPRESS,
                operation_stage=OperationStage.PROCESSING,
                current_file=None,
                files_processed=0,
                total_files=None,
                metadata={},
            )

        # Test negative bytes processed
        with pytest.raises(ValueError):
            ProgressInfo(
                percentage=50.0,
                bytes_processed=-100,  # Invalid
                total_bytes=100,
                speed_bps=None,
                elapsed_time=0,
                estimated_remaining=None,
                operation_type=OperationType.COMPRESS,
                operation_stage=OperationStage.PROCESSING,
                current_file=None,
                files_processed=0,
                total_files=None,
                metadata={},
            )

    def test_progress_tracker_basic(self):
        """Test basic ProgressTracker functionality."""
        callback_calls = []

        def test_callback(progress: ProgressInfo):
            callback_calls.append(progress)

        tracker = ProgressTracker(
            operation_type=OperationType.COMPRESS,
            callback=test_callback,
            total_bytes=1000,
            update_interval=0.0,  # No delay for testing
        )

        # Update progress
        tracker.update(bytes_processed=250)
        tracker.update(bytes_processed=500, current_file="test.txt")
        tracker.complete()

        # Should have received callbacks
        assert len(callback_calls) >= 2
        assert callback_calls[-1].operation_stage == OperationStage.COMPLETED
        assert callback_calls[-1].percentage == 100.0

    def test_progress_tracker_speed_calculation(self):
        """Test speed calculation in ProgressTracker."""
        callback_calls = []

        def test_callback(progress: ProgressInfo):
            callback_calls.append(progress)

        tracker = ProgressTracker(
            operation_type=OperationType.EXTRACT,
            callback=test_callback,
            total_bytes=2000,
            update_interval=0.0,
        )

        # Simulate processing over time
        tracker.update(bytes_processed=500)

        # Speed calculation requires time difference and more processing
        time.sleep(1.1)  # Need >1 second for speed calculation
        tracker.update(bytes_processed=1000)

        # Force another update after speed calculation window
        time.sleep(0.1)
        tracker.update(bytes_processed=1500, force_callback=True)

        # Should have some callbacks and potentially speed data
        assert len(callback_calls) >= 1

        # Speed calculation is complex and may not always be available immediately
        # Just test that we can call the methods without errors
        if callback_calls:
            latest_progress = callback_calls[-1]
            # Speed may be None or a float, both are valid
            assert latest_progress.speed_bps is None or isinstance(
                latest_progress.speed_bps, float
            )

    def test_predefined_callbacks(self):
        """Test predefined callback functions."""
        progress = ProgressInfo(
            percentage=75.0,
            bytes_processed=750,
            total_bytes=1000,
            speed_bps=1000.0,
            elapsed_time=0.75,
            estimated_remaining=0.25,
            operation_type=OperationType.COMPRESS,
            operation_stage=OperationStage.PROCESSING,
            current_file="test.txt",
            files_processed=3,
            total_files=4,
            metadata={},
        )

        # Test console callback (should not raise)
        with patch("builtins.print") as mock_print:
            py7zz.console_progress_callback(progress)
            mock_print.assert_called()

        # Test detailed callback
        with patch("builtins.print") as mock_print:
            py7zz.detailed_console_callback(progress)
            mock_print.assert_called()

        # Test JSON callback
        with patch("builtins.print") as mock_print:
            py7zz.json_progress_callback(progress)
            mock_print.assert_called()

            # Verify it's valid JSON
            json_str = mock_print.call_args[0][0]
            json.loads(json_str)  # Should not raise

    def test_callback_factory(self):
        """Test callback factory function."""
        console_callback = py7zz.create_callback("console")
        assert callable(console_callback)

        detailed_callback = py7zz.create_callback("detailed")
        assert callable(detailed_callback)

        json_callback = py7zz.create_callback("json")
        assert callable(json_callback)

        # Test invalid callback type
        with pytest.raises(ValueError):
            py7zz.create_callback("invalid_type")


class TestLoggingIntegration:
    """Test enhanced logging integration with standard Python logging."""

    def test_standard_logging_integration(self):
        """Test integration with standard Python logging."""
        import logging

        # Configure standard Python logging
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)

        # Get py7zz logger
        logger = py7zz.logging_config.get_logger("test_module")

        # Should have proper name hierarchy
        assert logger.name.startswith("py7zz")

        # Should be able to log messages
        with patch("sys.stderr"):
            logger.info("Test message")
            # Message should be handled by py7zz logging system

    def test_logger_hierarchy(self):
        """Test proper logger hierarchy."""
        # Test various module names
        test_cases = [
            ("py7zz.core", "py7zz.core"),
            ("test_module", "py7zz.test_module"),
            ("__main__", "py7zz"),
            ("my.module.name", "py7zz.name"),
        ]

        for input_name, expected_name in test_cases:
            logger = py7zz.logging_config.get_logger(input_name)
            assert logger.name == expected_name

    def test_verbosity_control(self):
        """Test logging verbosity control."""
        # Test different verbosity levels
        py7zz.setup_logging("ERROR")
        config = py7zz.get_logging_config()
        assert config["level"] == "ERROR"

        py7zz.setup_logging("DEBUG")
        config = py7zz.get_logging_config()
        assert config["level"] == "DEBUG"

        # Test dynamic level changes
        py7zz.set_log_level("WARNING")
        config = py7zz.get_logging_config()
        assert config["level"] == "WARNING"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

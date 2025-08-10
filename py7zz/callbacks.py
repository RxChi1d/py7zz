# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""
Structured callback system for py7zz progress reporting.

Provides extensible callback interfaces with structured parameters
for progress monitoring, error handling, and operation feedback.
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol

from .logging_config import get_logger

logger = get_logger(__name__)


class OperationType(Enum):
    """Types of operations that can be monitored."""

    COMPRESS = "compress"
    EXTRACT = "extract"
    TEST = "test"
    LIST = "list"
    ADD = "add"
    DELETE = "delete"
    UPDATE = "update"


class OperationStage(Enum):
    """Stages of an operation lifecycle."""

    STARTING = "starting"
    ANALYZING = "analyzing"
    PROCESSING = "processing"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class ProgressInfo:
    """
    Structured progress information for operations.

    Provides comprehensive progress data in a structured format
    that's extensible for future enhancements.
    """

    # Core progress metrics
    percentage: float  # Progress as percentage (0.0 - 100.0)
    bytes_processed: int  # Number of bytes processed
    total_bytes: Optional[int]  # Total bytes to process (None if unknown)

    # Speed and timing
    speed_bps: Optional[float]  # Processing speed in bytes per second
    elapsed_time: float  # Elapsed time in seconds
    estimated_remaining: Optional[float]  # Estimated remaining time in seconds

    # Operation context
    operation_type: OperationType  # Type of operation
    operation_stage: OperationStage  # Current stage of operation
    current_file: Optional[str]  # Currently processing file

    # File-level progress
    files_processed: int  # Number of files completed
    total_files: Optional[int]  # Total number of files (None if unknown)

    # Additional metadata
    metadata: Dict[str, Any]  # Extensible metadata dictionary

    def __post_init__(self) -> None:
        """Validate progress info after initialization."""
        if not 0.0 <= self.percentage <= 100.0:
            raise ValueError(f"Percentage must be 0.0-100.0, got {self.percentage}")

        if self.bytes_processed < 0:
            raise ValueError(
                f"Bytes processed must be non-negative, got {self.bytes_processed}"
            )

        if self.total_bytes is not None and self.total_bytes < self.bytes_processed:
            raise ValueError("Total bytes cannot be less than bytes processed")

        if self.elapsed_time < 0:
            raise ValueError(
                f"Elapsed time must be non-negative, got {self.elapsed_time}"
            )

    @property
    def completion_ratio(self) -> float:
        """Get completion ratio (0.0 - 1.0)."""
        return self.percentage / 100.0

    @property
    def bytes_remaining(self) -> Optional[int]:
        """Get remaining bytes to process."""
        if self.total_bytes is not None:
            return max(0, self.total_bytes - self.bytes_processed)
        return None

    @property
    def files_remaining(self) -> Optional[int]:
        """Get remaining files to process."""
        if self.total_files is not None:
            return max(0, self.total_files - self.files_processed)
        return None

    def format_speed(self) -> str:
        """Format processing speed as human-readable string."""
        if self.speed_bps is None:
            return "Unknown"

        if self.speed_bps < 1024:
            return f"{self.speed_bps:.1f} B/s"
        elif self.speed_bps < 1024 * 1024:
            return f"{self.speed_bps / 1024:.1f} KB/s"
        elif self.speed_bps < 1024 * 1024 * 1024:
            return f"{self.speed_bps / (1024 * 1024):.1f} MB/s"
        else:
            return f"{self.speed_bps / (1024 * 1024 * 1024):.1f} GB/s"

    def format_time(self, seconds: Optional[float]) -> str:
        """Format time duration as human-readable string."""
        if seconds is None:
            return "Unknown"

        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"

    def __str__(self) -> str:
        """Human-readable progress string."""
        parts = [f"{self.percentage:.1f}%"]

        if self.current_file:
            parts.append(f"({self.current_file})")

        if self.speed_bps is not None:
            parts.append(f"at {self.format_speed()}")

        if self.estimated_remaining is not None:
            parts.append(f"ETA: {self.format_time(self.estimated_remaining)}")

        return " ".join(parts)


class ProgressCallback(Protocol):
    """
    Protocol for progress callback functions.

    Callbacks should accept a ProgressInfo object and handle
    progress reporting as needed.
    """

    def __call__(self, progress: ProgressInfo) -> None:
        """
        Handle progress update.

        Args:
            progress: Structured progress information
        """
        pass


class ProgressTracker:
    """
    Progress tracking helper for operations.

    Manages progress state and callback invocation with
    automatic speed calculation and time estimation.
    """

    def __init__(
        self,
        operation_type: OperationType,
        callback: Optional[ProgressCallback] = None,
        total_bytes: Optional[int] = None,
        total_files: Optional[int] = None,
        update_interval: float = 0.1,  # Minimum seconds between updates
    ):
        """
        Initialize progress tracker.

        Args:
            operation_type: Type of operation being tracked
            callback: Optional callback function for progress updates
            total_bytes: Total bytes to process (if known)
            total_files: Total files to process (if known)
            update_interval: Minimum interval between callback invocations
        """
        self.operation_type = operation_type
        self.callback = callback
        self.total_bytes = total_bytes
        self.total_files = total_files
        self.update_interval = update_interval

        # Progress state
        self.start_time = time.perf_counter()
        self.last_update_time = 0.0
        self.bytes_processed = 0
        self.files_processed = 0
        self.current_file: Optional[str] = None
        self.current_stage = OperationStage.STARTING
        self.metadata: Dict[str, Any] = {}

        # Speed calculation
        self._last_speed_update = self.start_time
        self._last_bytes_for_speed = 0
        self._speed_samples: List[float] = []
        self._max_speed_samples = 10

    def update(
        self,
        bytes_processed: Optional[int] = None,
        files_processed: Optional[int] = None,
        current_file: Optional[str] = None,
        stage: Optional[OperationStage] = None,
        force_callback: bool = False,
        **metadata: Any,
    ) -> None:
        """
        Update progress and potentially invoke callback.

        Args:
            bytes_processed: New bytes processed count
            files_processed: New files processed count
            current_file: Currently processing file
            stage: Current operation stage
            force_callback: Force callback invocation regardless of interval
            **metadata: Additional metadata to include
        """
        current_time = time.perf_counter()

        # Update state
        if bytes_processed is not None:
            self.bytes_processed = bytes_processed
        if files_processed is not None:
            self.files_processed = files_processed
        if current_file is not None:
            self.current_file = current_file
        if stage is not None:
            self.current_stage = stage

        # Update metadata
        self.metadata.update(metadata)

        # Calculate speed
        speed_bps = self._calculate_speed(current_time)

        # Check if we should invoke callback
        time_since_last = current_time - self.last_update_time
        if force_callback or time_since_last >= self.update_interval:
            # Calculate percentage
            if self.total_bytes is not None and self.total_bytes > 0:
                percentage = min(
                    100.0, (self.bytes_processed / self.total_bytes) * 100.0
                )
            elif self.total_files is not None and self.total_files > 0:
                percentage = min(
                    100.0, (self.files_processed / self.total_files) * 100.0
                )
            else:
                # No total known, estimate based on stage
                stage_percentages = {
                    OperationStage.STARTING: 0.0,
                    OperationStage.ANALYZING: 10.0,
                    OperationStage.PROCESSING: 50.0,
                    OperationStage.FINALIZING: 90.0,
                    OperationStage.COMPLETED: 100.0,
                    OperationStage.FAILED: 0.0,
                }
                percentage = stage_percentages.get(self.current_stage, 0.0)

            # Calculate estimated remaining time
            estimated_remaining = None
            if speed_bps and speed_bps > 0:
                remaining_bytes = self.bytes_remaining
                if remaining_bytes is not None and remaining_bytes > 0:
                    estimated_remaining = remaining_bytes / speed_bps

            # Create progress info
            progress = ProgressInfo(
                percentage=percentage,
                bytes_processed=self.bytes_processed,
                total_bytes=self.total_bytes,
                speed_bps=speed_bps,
                elapsed_time=current_time - self.start_time,
                estimated_remaining=estimated_remaining,
                operation_type=self.operation_type,
                operation_stage=self.current_stage,
                current_file=self.current_file,
                files_processed=self.files_processed,
                total_files=self.total_files,
                metadata=self.metadata.copy(),
            )

            # Invoke callback
            if self.callback:
                try:
                    self.callback(progress)
                except Exception as e:
                    logger.warning(f"Progress callback error: {e}")

            self.last_update_time = current_time

    def _calculate_speed(self, current_time: float) -> Optional[float]:
        """Calculate current processing speed in bytes per second."""
        time_diff = current_time - self._last_speed_update

        # Update speed every second
        if time_diff >= 1.0:
            bytes_diff = self.bytes_processed - self._last_bytes_for_speed
            current_speed = bytes_diff / time_diff

            # Add to samples for smoothing
            self._speed_samples.append(current_speed)
            if len(self._speed_samples) > self._max_speed_samples:
                self._speed_samples.pop(0)

            # Update tracking variables
            self._last_speed_update = current_time
            self._last_bytes_for_speed = self.bytes_processed

        # Return average speed from samples
        if self._speed_samples:
            return sum(self._speed_samples) / len(self._speed_samples)

        return None

    @property
    def bytes_remaining(self) -> Optional[int]:
        """Get remaining bytes to process."""
        if self.total_bytes is not None:
            return max(0, self.total_bytes - self.bytes_processed)
        return None

    def set_stage(self, stage: OperationStage) -> None:
        """Set operation stage and force callback update."""
        self.update(stage=stage, force_callback=True)

    def complete(self) -> None:
        """Mark operation as completed."""
        self.set_stage(OperationStage.COMPLETED)
        if self.total_bytes is not None:
            self.update(bytes_processed=self.total_bytes, force_callback=True)

    def fail(self, error_message: Optional[str] = None) -> None:
        """Mark operation as failed."""
        if error_message:
            self.metadata["error_message"] = error_message
        self.set_stage(OperationStage.FAILED)


# Predefined callback functions for common use cases


def console_progress_callback(progress: ProgressInfo) -> None:
    """
    Simple console progress callback.

    Prints progress information to stdout with a simple format.
    """
    print(f"\r{progress.operation_type.value.title()}: {progress}", end="", flush=True)

    if progress.operation_stage in (OperationStage.COMPLETED, OperationStage.FAILED):
        print()  # New line when done


def detailed_console_callback(progress: ProgressInfo) -> None:
    """
    Detailed console progress callback with full information.

    Shows comprehensive progress details including speed, timing, and files.
    """
    lines = [
        f"{progress.operation_type.value.title()} Progress: {progress.percentage:.1f}%",
        f"Stage: {progress.operation_stage.value}",
    ]

    if progress.current_file:
        lines.append(f"File: {progress.current_file}")

    if progress.total_bytes:
        lines.append(f"Bytes: {progress.bytes_processed:,} / {progress.total_bytes:,}")

    if progress.total_files:
        lines.append(f"Files: {progress.files_processed} / {progress.total_files}")

    if progress.speed_bps:
        lines.append(f"Speed: {progress.format_speed()}")

    if progress.estimated_remaining:
        lines.append(f"ETA: {progress.format_time(progress.estimated_remaining)}")

    print("\n".join(lines))
    print("-" * 50)


def json_progress_callback(progress: ProgressInfo) -> None:
    """
    JSON progress callback for structured logging or API integration.

    Outputs progress as JSON for parsing by other tools.
    """
    import json

    data = {
        "percentage": progress.percentage,
        "bytes_processed": progress.bytes_processed,
        "total_bytes": progress.total_bytes,
        "speed_bps": progress.speed_bps,
        "elapsed_time": progress.elapsed_time,
        "estimated_remaining": progress.estimated_remaining,
        "operation_type": progress.operation_type.value,
        "operation_stage": progress.operation_stage.value,
        "current_file": progress.current_file,
        "files_processed": progress.files_processed,
        "total_files": progress.total_files,
        "metadata": progress.metadata,
    }

    print(json.dumps(data, ensure_ascii=False))


# Factory function for creating callbacks
def create_callback(callback_type: str = "console", **options: Any) -> ProgressCallback:
    """
    Factory function for creating progress callbacks.

    Args:
        callback_type: Type of callback ("console", "detailed", "json")
        **options: Additional options for callback configuration

    Returns:
        Configured progress callback function

    Example:
        >>> callback = py7zz.create_callback("detailed")
        >>> py7zz.create_archive("output.7z", ["files/"], progress_callback=callback)
    """
    callbacks = {
        "console": console_progress_callback,
        "detailed": detailed_console_callback,
        "json": json_progress_callback,
    }

    if callback_type not in callbacks:
        available = ", ".join(callbacks.keys())
        raise ValueError(
            f"Unknown callback type '{callback_type}'. Available: {available}"
        )

    return callbacks[callback_type]

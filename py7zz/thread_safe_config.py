# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 py7zz contributors
"""
Thread-safe configuration management for py7zz.

Provides immutable configuration objects and context managers
for safe concurrent access in multi-threaded environments.
"""

import contextlib
import json
import os
import threading
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Union

from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class ImmutableConfig:
    """
    Immutable configuration object for thread-safe operations.

    All fields are read-only to prevent accidental modifications
    in multi-threaded environments.
    """

    # Compression settings
    compression: str = "lzma2"
    level: int = 5
    solid: bool = True

    # Performance settings
    threads: Union[bool, int, None] = (
        None  # Thread control: True=explicit all cores (-mmt=on), False=single thread (-mmt=off), int=specific count (-mmt=N), None=7zz default (equivalent to all cores)
    )
    memory_limit: Optional[str] = None

    # Security settings
    password: Optional[str] = None
    encrypt_filenames: bool = False

    # Advanced options
    dictionary_size: Optional[str] = None
    word_size: Optional[int] = None
    fast_bytes: Optional[int] = None

    # Configuration metadata
    preset_name: str = "balanced"
    created_at: Optional[str] = None

    def replace(self, **changes: Any) -> "ImmutableConfig":
        """
        Create a new config with specified changes.

        Args:
            **changes: Fields to change

        Returns:
            New ImmutableConfig instance with changes applied
        """
        return replace(self, **changes)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        result = {}
        for field_info in self.__dataclass_fields__.values():
            value = getattr(self, field_info.name)
            if value is not None:
                result[field_info.name] = value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ImmutableConfig":
        """Create config from dictionary."""
        # Filter only known fields
        known_fields = set(cls.__dataclass_fields__.keys())
        filtered_data = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered_data)

    def validate(self) -> List[str]:
        """
        Validate configuration and return warnings.

        Returns:
            List of validation warning messages
        """
        warnings = []

        if not 0 <= self.level <= 9:
            warnings.append(f"Compression level {self.level} outside valid range (0-9)")

        if self.memory_limit and not any(
            self.memory_limit.endswith(suffix)
            for suffix in ["k", "m", "g", "K", "M", "G"]
        ):
            warnings.append(
                f"Memory limit '{self.memory_limit}' should end with k/m/g suffix"
            )

        # Check thread configuration
        if (
            isinstance(self.threads, int)
            and not isinstance(self.threads, bool)
            and self.threads < 1
        ):
            raise ValueError(f"Thread count must be positive, got {self.threads}")
        elif self.threads is not None and not isinstance(self.threads, (bool, int)):
            raise TypeError(
                f"threads must be bool, int, or None, got {type(self.threads).__name__}"
            )

        if self.encrypt_filenames and not self.password:
            warnings.append("Filename encryption requires a password")

        return warnings


class ThreadSafeGlobalConfig:
    """
    Thread-safe global configuration manager.

    Uses RWLock pattern to allow concurrent reads while ensuring
    exclusive access for writes. Configurations are immutable
    to prevent accidental modifications.

    Example:
        >>> import py7zz
        >>>
        >>> # Thread-safe configuration access
        >>> config = py7zz.ThreadSafeGlobalConfig.get_config()
        >>>
        >>> # Context manager for temporary config changes
        >>> with py7zz.ThreadSafeGlobalConfig.temporary_config(level=9):
        ...     # Operations use level=9 compression
        ...     py7zz.create_archive("high_compression.7z", ["files/"])
    """

    _lock = threading.RLock()
    _current_config: ImmutableConfig = ImmutableConfig()
    _config_stack: List[ImmutableConfig] = []

    @classmethod
    def get_config(cls) -> ImmutableConfig:
        """
        Get current global configuration (thread-safe).

        Returns:
            Current immutable configuration
        """
        with cls._lock:
            return cls._current_config

    @classmethod
    def set_config(cls, config: ImmutableConfig) -> None:
        """
        Set global configuration (thread-safe).

        Args:
            config: New immutable configuration to set
        """
        with cls._lock:
            # Validate configuration
            warnings = config.validate()
            if warnings:
                for warning in warnings:
                    logger.warning(f"Configuration warning: {warning}")

            cls._current_config = config
            logger.debug(f"Updated global configuration: {config.preset_name}")

    @classmethod
    def update_config(cls, **changes: Any) -> ImmutableConfig:
        """
        Update global configuration with changes (thread-safe).

        Args:
            **changes: Configuration fields to update

        Returns:
            New configuration after updates
        """
        with cls._lock:
            new_config = cls._current_config.replace(**changes)
            cls.set_config(new_config)
            return new_config

    @classmethod
    @contextlib.contextmanager
    def temporary_config(
        cls, config: Optional[ImmutableConfig] = None, **changes: Any
    ) -> Generator[ImmutableConfig, None, None]:
        """
        Context manager for temporary configuration changes.

        Args:
            config: Complete configuration to use temporarily
            **changes: Specific fields to change temporarily

        Yields:
            Active configuration during context

        Example:
            >>> with ThreadSafeGlobalConfig.temporary_config(level=9, solid=False):
            ...     # Operations use specified settings
            ...     create_archive("temp.7z", ["files/"])
            >>> # Original configuration restored
        """
        with cls._lock:
            # Save current config
            original_config = cls._current_config
            cls._config_stack.append(original_config)

            try:
                # Set temporary config
                if config is not None:
                    temp_config = config
                else:
                    temp_config = original_config.replace(**changes)

                cls.set_config(temp_config)
                logger.debug("Applied temporary configuration")

                yield temp_config

            finally:
                # Restore original config
                cls._config_stack.pop()
                cls.set_config(original_config)
                logger.debug("Restored original configuration")

    @classmethod
    def load_from_file(cls, config_path: Union[str, Path]) -> None:
        """
        Load configuration from JSON file (thread-safe).

        Args:
            config_path: Path to configuration file
        """
        config_path = Path(config_path)

        with cls._lock:
            try:
                if config_path.exists():
                    with open(config_path, encoding="utf-8") as f:
                        data = json.load(f)

                    config = ImmutableConfig.from_dict(data)
                    cls.set_config(config)
                    logger.info(f"Loaded configuration from {config_path}")
                else:
                    logger.warning(f"Configuration file not found: {config_path}")

            except Exception as e:
                logger.error(f"Failed to load configuration from {config_path}: {e}")
                raise

    @classmethod
    def save_to_file(cls, config_path: Union[str, Path]) -> None:
        """
        Save current configuration to JSON file (thread-safe).

        Args:
            config_path: Path to save configuration file
        """
        config_path = Path(config_path)

        with cls._lock:
            try:
                config_path.parent.mkdir(parents=True, exist_ok=True)

                config_data = cls._current_config.to_dict()
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)

                logger.info(f"Saved configuration to {config_path}")

            except Exception as e:
                logger.error(f"Failed to save configuration to {config_path}: {e}")
                raise

    @classmethod
    def get_default_config_path(cls) -> Path:
        """Get default user configuration file path."""
        if os.name == "nt":  # Windows
            config_dir = Path(os.environ.get("APPDATA", "~")) / "py7zz"
        else:  # Unix-like
            config_dir = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")) / "py7zz"

        config_dir = config_dir.expanduser()
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.json"

    @classmethod
    def load_user_config(cls) -> None:
        """Load configuration from default user config file."""
        config_path = cls.get_default_config_path()
        if config_path.exists():
            cls.load_from_file(config_path)

    @classmethod
    def save_user_config(cls) -> None:
        """Save current configuration to default user config file."""
        config_path = cls.get_default_config_path()
        cls.save_to_file(config_path)

    @classmethod
    def reset_to_defaults(cls) -> None:
        """Reset configuration to defaults (thread-safe)."""
        with cls._lock:
            cls._current_config = ImmutableConfig()
            cls._config_stack.clear()
            logger.info("Reset configuration to defaults")

    @classmethod
    def get_config_info(cls) -> Dict[str, Any]:
        """
        Get configuration information and statistics.

        Returns:
            Dictionary with configuration details
        """
        with cls._lock:
            return {
                "current_config": cls._current_config.to_dict(),
                "config_stack_depth": len(cls._config_stack),
                "preset_name": cls._current_config.preset_name,
                "warnings": cls._current_config.validate(),
            }


# Preset configurations as immutable objects
PRESET_CONFIGS = {
    "fast": ImmutableConfig(
        preset_name="fast",
        level=1,
        compression="lzma2",
        solid=False,
        threads=True,  # Use all available cores
    ),
    "balanced": ImmutableConfig(
        preset_name="balanced",
        level=5,
        compression="lzma2",
        solid=True,
        threads=None,
    ),
    "ultra": ImmutableConfig(
        preset_name="ultra",
        level=9,
        compression="lzma2",
        solid=True,
        dictionary_size="32m",
        threads=False,  # Single thread for maximum compression
    ),
    "backup": ImmutableConfig(
        preset_name="backup",
        level=6,
        compression="lzma2",
        solid=True,
        dictionary_size="16m",
        threads=None,
    ),
}


def get_preset_config(preset_name: str) -> ImmutableConfig:
    """
    Get immutable preset configuration.

    Args:
        preset_name: Name of the preset

    Returns:
        Immutable configuration for the preset

    Raises:
        ValueError: If preset name is not found
    """
    if preset_name not in PRESET_CONFIGS:
        available = ", ".join(PRESET_CONFIGS.keys())
        raise ValueError(f"Unknown preset '{preset_name}'. Available: {available}")

    return PRESET_CONFIGS[preset_name]


def apply_preset(preset_name: str) -> None:
    """
    Apply a preset configuration globally.

    Args:
        preset_name: Name of the preset to apply
    """
    config = get_preset_config(preset_name)
    ThreadSafeGlobalConfig.set_config(config)


# Context manager for preset-based operations
@contextlib.contextmanager
def with_preset(preset_name: str) -> Generator[ImmutableConfig, None, None]:
    """
    Context manager for operations with a specific preset.

    Args:
        preset_name: Name of the preset to use

    Yields:
        Active preset configuration

    Example:
        >>> with py7zz.with_preset("ultra"):
        ...     py7zz.create_archive("high_compression.7z", ["files/"])
    """
    config = get_preset_config(preset_name)
    with ThreadSafeGlobalConfig.temporary_config(config) as active_config:
        yield active_config

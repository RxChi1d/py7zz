"""
Configuration and Preset System

Provides advanced configuration options and preset configurations
for different use cases.
"""

from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class Config:
    """
    Advanced configuration for 7z operations.

    This class allows fine-grained control over compression parameters.
    """

    # Compression settings
    compression: str = "lzma2"  # lzma2, lzma, ppmd, bzip2, deflate
    level: int = 5  # 0-9, higher = better compression
    solid: bool = True  # Solid archive (better compression)

    # Performance settings
    threads: Optional[int] = None  # Number of threads (None = auto)
    memory_limit: Optional[str] = None  # Memory limit (e.g., "1g", "512m")

    # Security settings
    password: Optional[str] = None  # Archive password
    encrypt_filenames: bool = False  # Encrypt file names

    # Advanced options
    dictionary_size: Optional[str] = None  # Dictionary size (e.g., "32m")
    word_size: Optional[int] = None  # Word size for LZMA
    fast_bytes: Optional[int] = None  # Fast bytes for LZMA

    def to_7z_args(self) -> List[str]:
        """Convert config to 7z command line arguments."""
        args = []

        # Compression level
        args.append(f"-mx{self.level}")

        # Compression method
        args.append(f"-m0={self.compression}")

        # Solid archive
        if not self.solid:
            args.append("-ms=off")

        # Threads
        if self.threads is not None:
            args.append(f"-mmt{self.threads}")

        # Memory limit
        if self.memory_limit:
            args.append(f"-mmemuse={self.memory_limit}")

        # Dictionary size
        if self.dictionary_size:
            args.append(f"-md={self.dictionary_size}")

        # Word size
        if self.word_size:
            args.append(f"-mfb={self.word_size}")

        # Fast bytes
        if self.fast_bytes:
            args.append(f"-mfb={self.fast_bytes}")

        # Password
        if self.password:
            args.append(f"-p{self.password}")

        # Encrypt filenames
        if self.encrypt_filenames and self.password:
            args.append("-mhe")

        return args


class Presets:
    """
    Predefined configurations for common use cases.
    """

    @staticmethod
    def fast() -> Config:
        """
        Fast compression preset.

        Optimized for speed over compression ratio.
        Good for temporary files or when time is critical.
        """
        return Config(
            compression="lzma2",
            level=1,
            solid=False,
            threads=None,  # Use all available threads
        )

    @staticmethod
    def balanced() -> Config:
        """
        Balanced preset (default).

        Good balance between compression ratio and speed.
        Suitable for most general-purpose compression tasks.
        """
        return Config(
            compression="lzma2",
            level=5,
            solid=True,
            threads=None,
        )

    @staticmethod
    def backup() -> Config:
        """
        Backup preset.

        Optimized for maximum compression ratio.
        Good for long-term storage where space matters more than time.
        """
        return Config(
            compression="lzma2",
            level=7,
            solid=True,
            dictionary_size="64m",
            threads=None,
        )

    @staticmethod
    def ultra() -> Config:
        """
        Ultra compression preset.

        Maximum compression ratio at the cost of speed.
        Use when storage space is extremely limited.
        """
        return Config(
            compression="lzma2",
            level=9,
            solid=True,
            dictionary_size="128m",
            word_size=64,
            fast_bytes=64,
            threads=1,  # Single thread for maximum compression
        )

    @staticmethod
    def secure() -> Config:
        """
        Secure preset with encryption.

        Balanced compression with password protection.
        Note: Password must be set separately.
        """
        return Config(
            compression="lzma2",
            level=5,
            solid=True,
            encrypt_filenames=True,
            # password must be set by user
        )

    @staticmethod
    def compatibility() -> Config:
        """
        Compatibility preset.

        Uses widely supported compression methods.
        Good for archives that need to be opened on older systems.
        """
        return Config(
            compression="deflate",
            level=6,
            solid=False,
        )

    @classmethod
    def get_preset(cls, name: str) -> Config:
        """
        Get a preset configuration by name.

        Args:
            name: Preset name ("fast", "balanced", "backup", "ultra", "secure", "compatibility")

        Returns:
            Config object for the specified preset

        Raises:
            ValueError: If preset name is not recognized
        """
        presets = {
            "fast": cls.fast,
            "balanced": cls.balanced,
            "backup": cls.backup,
            "ultra": cls.ultra,
            "secure": cls.secure,
            "compatibility": cls.compatibility,
        }

        if name not in presets:
            available = ", ".join(presets.keys())
            raise ValueError(f"Unknown preset '{name}'. Available presets: {available}")

        return presets[name]()

    @classmethod
    def list_presets(cls) -> List[str]:
        """List all available preset names."""
        return ["fast", "balanced", "backup", "ultra", "secure", "compatibility"]


def create_custom_config(**kwargs: Any) -> Config:
    """
    Create a custom configuration with specified parameters.

    Args:
        **kwargs: Any Config parameters to override

    Returns:
        Config object with specified parameters

    Example:
        >>> config = create_custom_config(level=9, threads=4, password="secret")
        >>> # Use with SevenZipFile or create_archive
    """
    return Config(**kwargs)


def get_recommended_preset(purpose: str) -> Config:
    """
    Get recommended preset based on intended purpose.

    Args:
        purpose: Intended use ("temp", "backup", "distribution", "secure", "fast")

    Returns:
        Recommended Config object
    """
    recommendations = {
        "temp": Presets.fast(),
        "temporary": Presets.fast(),
        "backup": Presets.backup(),
        "archive": Presets.backup(),
        "distribution": Presets.balanced(),
        "share": Presets.balanced(),
        "secure": Presets.secure(),
        "encrypted": Presets.secure(),
        "fast": Presets.fast(),
        "quick": Presets.fast(),
        "max": Presets.ultra(),
        "maximum": Presets.ultra(),
        "ultra": Presets.ultra(),
    }

    return recommendations.get(purpose.lower(), Presets.balanced())

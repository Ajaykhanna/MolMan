"""
Configuration management for MolMan.

This module handles user preferences, application settings, and recent files tracking.
Configuration is stored in JSON format at ~/.molman/config.json.
"""

import json
import copy
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from .logging_config import get_logger
from .exceptions import (
    ConfigurationError,
    InvalidConfigError,
    MissingConfigError,
)

# Initialize logger
logger = get_logger(__name__)

# Default configuration directory
DEFAULT_CONFIG_DIR = Path.home() / ".molman"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"

# Default configuration values
DEFAULT_CONFIG = {
    "version": "1.0",
    "created": None,
    "last_modified": None,
    "preferences": {
        "auto_save": {
            "enabled": True,
            "interval_minutes": 5,
        },
        "recent_files": {
            "max_count": 10,
            "files": [],
        },
        "logging": {
            "level": "INFO",
            "enable_console": True,
            "enable_file": True,
        },
        "rendering": {
            "default_backend": "matplotlib",  # or "plotly"
            "show_bonds": True,
            "show_atom_labels": False,
            "background_color": "white",
        },
        "units": {
            "distance": "angstrom",  # or "nanometer", "bohr"
            "angle": "degrees",  # or "radians"
        },
    },
}


class ConfigManager:
    """
    Manages application configuration and user preferences.

    Handles loading, saving, and updating configuration stored in JSON format.
    Provides thread-safe access to configuration values.
    """

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize the configuration manager.

        Args:
            config_file: Path to configuration file (default: ~/.molman/config.json)
        """
        self.config_file = config_file or DEFAULT_CONFIG_FILE
        self.config: Dict[str, Any] = {}
        self._ensure_config_dir()
        logger.debug(f"ConfigManager initialized with config file: {self.config_file}")

    def _ensure_config_dir(self) -> None:
        """Ensure the configuration directory exists."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Configuration directory ensured: {self.config_file.parent}")

    def load(self) -> Dict[str, Any]:
        """
        Load configuration from file. Creates default if doesn't exist.

        Returns:
            Dictionary containing configuration

        Raises:
            InvalidConfigError: If configuration file is corrupted
        """
        if not self.config_file.exists():
            logger.info("Configuration file not found, creating default")
            self.config = self._create_default_config()
            self.save()
            return self.config

        try:
            with self.config_file.open("r") as f:
                self.config = json.load(f)

            # Merge with defaults to ensure all keys exist
            self.config = self._merge_with_defaults(self.config)

            logger.info(f"Configuration loaded from {self.config_file}")
            return self.config

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse configuration file: {e}")
            raise InvalidConfigError(f"Configuration file is corrupted: {e}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise ConfigurationError(f"Failed to load configuration: {e}")

    def save(self) -> None:
        """
        Save current configuration to file.

        Raises:
            ConfigurationError: If save fails
        """
        try:
            self._ensure_config_dir()

            # Update last modified timestamp
            self.config["last_modified"] = datetime.now().isoformat()

            with self.config_file.open("w") as f:
                json.dump(self.config, f, indent=2)

            logger.info(f"Configuration saved to {self.config_file}")

        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise ConfigurationError(f"Failed to save configuration: {e}")

    def _create_default_config(self) -> Dict[str, Any]:
        """Create a new default configuration."""
        config = copy.deepcopy(DEFAULT_CONFIG)
        config["created"] = datetime.now().isoformat()
        config["last_modified"] = config["created"]
        logger.debug("Created default configuration")
        return config

    def _merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge loaded config with defaults to ensure all keys exist.

        Args:
            config: Loaded configuration

        Returns:
            Merged configuration with all default keys
        """
        def deep_merge(default: Dict, custom: Dict) -> Dict:
            """Recursively merge dictionaries."""
            result = copy.deepcopy(default)
            for key, value in custom.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        return deep_merge(DEFAULT_CONFIG, config)

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated path.

        Args:
            key_path: Dot-separated path (e.g., "preferences.auto_save.enabled")
            default: Default value if key not found

        Returns:
            Configuration value or default

        Example:
            >>> config.get("preferences.auto_save.enabled")
            True
        """
        keys = key_path.split(".")
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                logger.debug(f"Config key not found: {key_path}, using default: {default}")
                return default

        return value

    def set(self, key_path: str, value: Any) -> None:
        """
        Set configuration value by dot-separated path.

        Args:
            key_path: Dot-separated path (e.g., "preferences.auto_save.enabled")
            value: Value to set

        Example:
            >>> config.set("preferences.auto_save.enabled", False)
        """
        keys = key_path.split(".")
        target = self.config

        # Navigate to the parent of the final key
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]

        # Set the final value
        target[keys[-1]] = value
        logger.debug(f"Configuration updated: {key_path} = {value}")

    def add_recent_file(self, file_path: Path) -> None:
        """
        Add a file to the recent files list.

        Args:
            file_path: Path to the file
        """
        max_count = self.get("preferences.recent_files.max_count", 10)
        recent_files = self.get("preferences.recent_files.files", [])

        # Convert Path to string
        file_str = str(file_path.absolute())

        # Remove if already exists
        if file_str in recent_files:
            recent_files.remove(file_str)

        # Add to front
        recent_files.insert(0, file_str)

        # Trim to max count
        recent_files = recent_files[:max_count]

        # Update config
        self.set("preferences.recent_files.files", recent_files)
        self.save()

        logger.info(f"Added to recent files: {file_path}")

    def get_recent_files(self) -> List[Path]:
        """
        Get list of recent files.

        Returns:
            List of Path objects for recent files
        """
        recent_files = self.get("preferences.recent_files.files", [])
        # Convert strings to Path objects and filter out non-existent files
        paths = []
        for file_str in recent_files:
            path = Path(file_str)
            if path.exists():
                paths.append(path)

        # Update list if some files no longer exist
        if len(paths) != len(recent_files):
            self.set("preferences.recent_files.files", [str(p) for p in paths])
            self.save()

        return paths

    def clear_recent_files(self) -> None:
        """Clear the recent files list."""
        self.set("preferences.recent_files.files", [])
        self.save()
        logger.info("Recent files list cleared")

    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        logger.warning("Resetting configuration to defaults")
        self.config = self._create_default_config()
        self.save()

    def export_config(self, export_path: Path) -> None:
        """
        Export configuration to a file.

        Args:
            export_path: Path where to export configuration
        """
        try:
            with export_path.open("w") as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration exported to {export_path}")
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            raise ConfigurationError(f"Failed to export configuration: {e}")

    def import_config(self, import_path: Path) -> None:
        """
        Import configuration from a file.

        Args:
            import_path: Path to configuration file to import

        Raises:
            InvalidConfigError: If imported file is invalid
        """
        try:
            with import_path.open("r") as f:
                imported_config = json.load(f)

            # Merge with defaults
            self.config = self._merge_with_defaults(imported_config)
            self.save()

            logger.info(f"Configuration imported from {import_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse imported configuration: {e}")
            raise InvalidConfigError(f"Imported configuration is corrupted: {e}")
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            raise ConfigurationError(f"Failed to import configuration: {e}")


# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """
    Get the global configuration manager instance (singleton pattern).

    Returns:
        ConfigManager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
        _config_manager.load()
    return _config_manager

"""
Unit tests for molvis_core.config module.

Tests configuration management, user preferences, and recent files tracking.
"""

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from molvis_core.config import DEFAULT_CONFIG, ConfigManager, get_config_manager
from molvis_core.exceptions import ConfigurationError, InvalidConfigError


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory."""
    config_dir = tmp_path / ".molman"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def config_manager(temp_config_dir):
    """Create a ConfigManager with temporary directory."""
    config_file = temp_config_dir / "config.json"
    return ConfigManager(config_file)


class TestConfigManager:
    """Tests for ConfigManager class."""

    @pytest.mark.unit
    def test_create_default_config(self, config_manager):
        """Test creating default configuration."""
        config_manager.load()

        assert config_manager.config["version"] == "1.0"
        assert "preferences" in config_manager.config
        assert "auto_save" in config_manager.config["preferences"]
        assert config_manager.config_file.exists()

    @pytest.mark.unit
    def test_load_existing_config(self, config_manager):
        """Test loading existing configuration."""
        # Create a config file
        config_data = {
            "version": "1.0",
            "preferences": {
                "auto_save": {
                    "enabled": False,
                    "interval_minutes": 10,
                }
            }
        }

        with config_manager.config_file.open("w") as f:
            json.dump(config_data, f)

        # Load it
        config_manager.load()

        assert not config_manager.get("preferences.auto_save.enabled")
        assert config_manager.get("preferences.auto_save.interval_minutes") == 10

    @pytest.mark.unit
    def test_save_config(self, config_manager):
        """Test saving configuration."""
        config_manager.load()
        config_manager.set("preferences.auto_save.enabled", False)
        config_manager.save()

        # Load again and verify
        new_manager = ConfigManager(config_manager.config_file)
        new_manager.load()

        assert not new_manager.get("preferences.auto_save.enabled")

    @pytest.mark.unit
    def test_get_nested_value(self, config_manager):
        """Test getting nested configuration value."""
        config_manager.load()

        value = config_manager.get("preferences.auto_save.interval_minutes")
        assert value == 5  # Default value

    @pytest.mark.unit
    def test_get_with_default(self, config_manager):
        """Test getting non-existent key with default."""
        config_manager.load()

        value = config_manager.get("nonexistent.key", "default_value")
        assert value == "default_value"

    @pytest.mark.unit
    def test_set_nested_value(self, config_manager):
        """Test setting nested configuration value."""
        config_manager.load()
        config_manager.set("preferences.auto_save.enabled", False)

        assert not config_manager.get("preferences.auto_save.enabled")

    @pytest.mark.unit
    def test_set_new_path(self, config_manager):
        """Test setting value on non-existent path."""
        config_manager.load()
        config_manager.set("new.nested.key", "value")

        assert config_manager.get("new.nested.key") == "value"

    @pytest.mark.unit
    def test_add_recent_file(self, config_manager, tmp_path):
        """Test adding file to recent files."""
        config_manager.load()

        # Create a temp file
        test_file = tmp_path / "test.molman"
        test_file.touch()

        config_manager.add_recent_file(test_file)

        recent = config_manager.get_recent_files()
        assert len(recent) == 1
        assert recent[0] == test_file

    @pytest.mark.unit
    def test_recent_files_max_count(self, config_manager, tmp_path):
        """Test that recent files are limited to max count."""
        config_manager.load()
        config_manager.set("preferences.recent_files.max_count", 3)

        # Add 5 files
        for i in range(5):
            test_file = tmp_path / f"test{i}.molman"
            test_file.touch()
            config_manager.add_recent_file(test_file)

        recent = config_manager.get_recent_files()
        assert len(recent) == 3  # Limited to max_count

    @pytest.mark.unit
    def test_recent_files_no_duplicates(self, config_manager, tmp_path):
        """Test that recent files don't have duplicates."""
        config_manager.load()
        config_manager.clear_recent_files()  # Clear any existing files

        test_file = tmp_path / "test.molman"
        test_file.touch()

        # Add same file multiple times
        config_manager.add_recent_file(test_file)
        config_manager.add_recent_file(test_file)
        config_manager.add_recent_file(test_file)

        recent = config_manager.get_recent_files()
        assert len(recent) == 1

    @pytest.mark.unit
    def test_recent_files_filters_nonexistent(self, config_manager, tmp_path):
        """Test that get_recent_files filters out non-existent files."""
        config_manager.load()
        config_manager.clear_recent_files()  # Clear any existing files

        # Add a file that exists
        existing_file = tmp_path / "existing.molman"
        existing_file.touch()
        config_manager.add_recent_file(existing_file)

        # Manually add a non-existent file path
        nonexistent_file = tmp_path / "nonexistent.molman"
        recent_list = config_manager.get("preferences.recent_files.files", [])
        recent_list.append(str(nonexistent_file))
        config_manager.set("preferences.recent_files.files", recent_list)

        # Get recent files - should filter out non-existent
        recent = config_manager.get_recent_files()
        assert len(recent) == 1
        assert recent[0] == existing_file

    @pytest.mark.unit
    def test_clear_recent_files(self, config_manager, tmp_path):
        """Test clearing recent files."""
        config_manager.load()

        # Add files
        for i in range(3):
            test_file = tmp_path / f"test{i}.molman"
            test_file.touch()
            config_manager.add_recent_file(test_file)

        assert len(config_manager.get_recent_files()) == 3

        # Clear
        config_manager.clear_recent_files()
        assert len(config_manager.get_recent_files()) == 0

    @pytest.mark.unit
    def test_reset_to_defaults(self, config_manager):
        """Test resetting configuration to defaults."""
        config_manager.load()

        # Modify config
        config_manager.set("preferences.auto_save.enabled", False)
        config_manager.set("preferences.auto_save.interval_minutes", 999)
        config_manager.save()

        # Verify modifications were saved
        assert not config_manager.get("preferences.auto_save.enabled")

        # Reset
        config_manager.reset_to_defaults()

        # Should be back to defaults
        assert config_manager.get("preferences.auto_save.enabled")
        assert config_manager.get("preferences.auto_save.interval_minutes") == 5

    @pytest.mark.unit
    def test_export_config(self, config_manager, tmp_path):
        """Test exporting configuration."""
        config_manager.load()
        config_manager.set("preferences.auto_save.enabled", False)

        export_path = tmp_path / "exported_config.json"
        config_manager.export_config(export_path)

        assert export_path.exists()

        # Verify content
        with export_path.open("r") as f:
            exported = json.load(f)

        assert not exported["preferences"]["auto_save"]["enabled"]

    @pytest.mark.unit
    def test_import_config(self, config_manager, tmp_path):
        """Test importing configuration."""
        # Create a config to import
        import_data = {
            "version": "1.0",
            "preferences": {
                "auto_save": {
                    "enabled": False,
                    "interval_minutes": 99,
                }
            }
        }

        import_path = tmp_path / "import_config.json"
        with import_path.open("w") as f:
            json.dump(import_data, f)

        # Import
        config_manager.load()
        config_manager.import_config(import_path)

        assert not config_manager.get("preferences.auto_save.enabled")
        assert config_manager.get("preferences.auto_save.interval_minutes") == 99

    @pytest.mark.unit
    def test_import_invalid_config(self, config_manager, tmp_path):
        """Test importing invalid configuration."""
        # Create invalid JSON file
        import_path = tmp_path / "invalid_config.json"
        with import_path.open("w") as f:
            f.write("{ invalid json }")

        config_manager.load()

        with pytest.raises(InvalidConfigError):
            config_manager.import_config(import_path)

    @pytest.mark.unit
    def test_load_corrupted_config(self, config_manager):
        """Test loading corrupted configuration file."""
        # Create corrupted config file
        with config_manager.config_file.open("w") as f:
            f.write("{ corrupted json")

        with pytest.raises(InvalidConfigError):
            config_manager.load()

    @pytest.mark.unit
    def test_merge_with_defaults(self, temp_config_dir):
        """Test that loaded config is merged with defaults."""
        # Create a NEW config manager with a different file
        config_file = temp_config_dir / "merge_test.json"
        test_config_manager = ConfigManager(config_file)

        # Create partial config
        partial_config = {
            "version": "1.0",
            "preferences": {
                "auto_save": {
                    "enabled": False,
                }
            }
        }

        with config_file.open("w") as f:
            json.dump(partial_config, f)

        test_config_manager.load()

        # Should have default interval_minutes even though not in file
        assert test_config_manager.get("preferences.auto_save.interval_minutes") == 5
        # But custom enabled value
        assert test_config_manager.get("preferences.auto_save.enabled") is False

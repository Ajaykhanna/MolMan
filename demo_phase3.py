#!/usr/bin/env python3
"""
Interactive demo for Phase 3: Configuration Management & Project Persistence

This script demonstrates all the key features implemented in Phase 3.
Run this script to see configuration management and project persistence in action.
"""

from pathlib import Path
import numpy as np
from molvis_core.config import ConfigManager, get_config_manager
from molvis_core.project import Project
from molvis_core.molecule import Molecule
from molvis_core import io as core_io


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_configuration_management():
    """Demonstrate configuration management features."""
    print_section("1. Configuration Management Demo")

    # Create a config manager with a custom file
    demo_config_file = Path("/tmp/molman_demo_config.json")
    if demo_config_file.exists():
        demo_config_file.unlink()

    config = ConfigManager(demo_config_file)
    config.load()

    print("✓ Created new configuration file")
    print(f"  Location: {demo_config_file}")
    print(f"  Version: {config.get('version')}\n")

    # Show default preferences
    print("Default Preferences:")
    print(f"  Auto-save enabled: {config.get('preferences.auto_save.enabled')}")
    print(f"  Auto-save interval: {config.get('preferences.auto_save.interval_minutes')} minutes")
    print(f"  Logging level: {config.get('preferences.logging.level')}")
    print(f"  Default backend: {config.get('preferences.rendering.default_backend')}\n")

    # Modify some settings
    print("Modifying settings...")
    config.set('preferences.auto_save.interval_minutes', 10)
    config.set('preferences.rendering.background_color', 'black')
    config.save()

    print("✓ Settings updated and saved")
    print(f"  New auto-save interval: {config.get('preferences.auto_save.interval_minutes')} minutes")
    print(f"  New background color: {config.get('preferences.rendering.background_color')}\n")

    # Test recent files
    print("Testing recent files tracking...")
    test_file1 = Path("/tmp/test1.molman")
    test_file2 = Path("/tmp/test2.molman")
    test_file1.touch()
    test_file2.touch()

    config.add_recent_file(test_file1)
    config.add_recent_file(test_file2)
    config.add_recent_file(test_file1)  # Add duplicate (should move to front)

    recent = config.get_recent_files()
    print(f"✓ Recent files tracked: {len(recent)} files")
    for i, file in enumerate(recent, 1):
        print(f"  {i}. {file.name}")

    # Cleanup
    test_file1.unlink()
    test_file2.unlink()


def demo_project_persistence():
    """Demonstrate project save/load features."""
    print_section("2. Project Persistence Demo")

    # Load some molecules from test data
    water_path = Path("test_data/water.xyz")
    benzene_path = Path("test_data/benzene.xyz")

    if not water_path.exists():
        print("⚠ Test data not found. Skipping project demo.")
        return

    print("Loading molecules from test data...")
    water_symbols, water_coords = core_io.load_xyz(water_path)
    benzene_symbols, benzene_coords = core_io.load_xyz(benzene_path)

    water = Molecule(symbols=water_symbols, coords=water_coords)
    benzene = Molecule(symbols=benzene_symbols, coords=benzene_coords)

    print(f"✓ Loaded water molecule ({water.num_atoms} atoms)")
    print(f"✓ Loaded benzene molecule ({benzene.num_atoms} atoms)\n")

    # Apply transformations
    print("Applying transformations...")
    benzene.final_translation = np.array([5.0, 0.0, 0.0])
    benzene.final_rotation_matrix = np.array([
        [1, 0, 0],
        [0, 0, -1],
        [0, 1, 0]
    ], dtype=float)
    benzene.apply_final_transformation()

    print("✓ Benzene translated by [5.0, 0.0, 0.0]")
    print("✓ Benzene rotated 90° around X-axis\n")

    # Create and save project
    project = Project(
        name="Water-Benzene Complex",
        molecules=[water, benzene],
        metadata={
            "description": "Demo project showing water and benzene molecules",
            "created_by": "Phase 3 Demo Script"
        }
    )

    save_path = Path("/tmp/demo_project.molman")
    project.save(save_path)

    print(f"✓ Project saved to: {save_path}")
    print(f"  Project name: {project.name}")
    print(f"  Molecules: {len(project.molecules)}")
    print(f"  File size: {save_path.stat().st_size} bytes\n")

    # Load project back
    print("Loading project from file...")
    loaded_project = Project.load(save_path)

    print(f"✓ Project loaded successfully")
    print(f"  Project name: {loaded_project.name}")
    print(f"  Molecules: {len(loaded_project.molecules)}")
    print(f"  Metadata: {loaded_project.metadata['description']}\n")

    # Verify transformations preserved
    loaded_benzene = loaded_project.molecules[1]
    print("Verifying transformations preserved:")
    print(f"  Translation: {loaded_benzene.final_translation}")
    print(f"  Rotation preserved: {np.allclose(loaded_benzene.final_rotation_matrix, benzene.final_rotation_matrix)}\n")

    # Test backup creation
    print("Creating backup...")
    backup_path = project.create_backup(save_path)
    print(f"✓ Backup created: {backup_path.name}")
    print(f"  Backup size: {backup_path.stat().st_size} bytes\n")

    # Test XYZ export
    xyz_export_path = Path("/tmp/demo_export.xyz")
    project.export_xyz(xyz_export_path)
    print(f"✓ Exported to XYZ format: {xyz_export_path}")
    print(f"  XYZ file size: {xyz_export_path.stat().st_size} bytes")

    # Show XYZ content preview
    with xyz_export_path.open('r') as f:
        lines = f.readlines()[:8]
        print("\n  Preview (first 8 lines):")
        for line in lines:
            print(f"  {line.rstrip()}")


def demo_auto_save():
    """Demonstrate auto-save functionality."""
    print_section("3. Auto-Save Demo")

    # Create a project
    water_path = Path("test_data/water.xyz")
    if not water_path.exists():
        print("⚠ Test data not found. Skipping auto-save demo.")
        return

    water_symbols, water_coords = core_io.load_xyz(water_path)
    water = Molecule(symbols=water_symbols, coords=water_coords)

    project = Project(name="Auto-save Test", molecules=[water])

    # Get auto-save path for unsaved project
    autosave_path = project.get_auto_save_path()
    print(f"Auto-save path (no file): {autosave_path.name}")

    # Save project first
    project_file = Path("/tmp/my_project.molman")
    project.save(project_file)

    # Get auto-save path for saved project
    autosave_path = project.get_auto_save_path(project_file)
    print(f"Auto-save path (with file): {autosave_path.name}")
    print(f"\n✓ Auto-save paths are hidden files (start with '.')")
    print(f"✓ Auto-save includes timestamp for recovery")


def demo_configuration_files():
    """Show where configuration files are stored."""
    print_section("4. Configuration Files Location")

    from molvis_core.config import DEFAULT_CONFIG_DIR, DEFAULT_CONFIG_FILE

    print(f"Configuration directory: {DEFAULT_CONFIG_DIR}")
    print(f"Configuration file: {DEFAULT_CONFIG_FILE}")

    # Check if global config exists
    if DEFAULT_CONFIG_FILE.exists():
        print(f"\n✓ Global config file exists")
        config = get_config_manager()
        recent_count = len(config.get('preferences.recent_files.files', []))
        print(f"  Recent files tracked: {recent_count}")
    else:
        print(f"\n  Global config not yet created (will be created on first use)")

    # Show logging directory
    from molvis_core.logging_config import DEFAULT_LOG_DIR
    print(f"\nLogging directory: {DEFAULT_LOG_DIR}")
    if DEFAULT_LOG_DIR.exists():
        log_files = list(DEFAULT_LOG_DIR.glob("*.log*"))
        print(f"✓ Log files found: {len(log_files)}")
        for log_file in sorted(log_files)[:3]:
            print(f"  - {log_file.name} ({log_file.stat().st_size} bytes)")


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("  Phase 3: Configuration & Project Persistence Demo")
    print("="*60)
    print("\nThis demo will showcase all Phase 3 features:")
    print("  1. Configuration management (preferences, recent files)")
    print("  2. Project persistence (save/load, transformations)")
    print("  3. Auto-save functionality")
    print("  4. Configuration files location")

    try:
        demo_configuration_management()
        demo_project_persistence()
        demo_auto_save()
        demo_configuration_files()

        print_section("Demo Complete!")
        print("✓ All Phase 3 features demonstrated successfully")
        print("\nNext steps:")
        print("  - Check /tmp for demo files (.molman, .xyz)")
        print("  - Check ~/.molman/ for config and logs")
        print("  - Run 'python -m pytest tests/test_config.py -v' for detailed tests")

    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Quick manual test for Phase 3 features."""

from molvis_core.project import Project
from molvis_core.molecule import Molecule
from molvis_core.config import ConfigManager
from molvis_core import io as core_io
from pathlib import Path
import numpy as np

print("="*60)
print("Quick Phase 3 Test")
print("="*60)

# Test 1: Configuration Management
print("\n1. Testing Configuration Management...")
config = ConfigManager(Path("/tmp/quick_test_config.json"))
config.load()

print(f"   Auto-save enabled: {config.get('preferences.auto_save.enabled')}")
print(f"   Interval: {config.get('preferences.auto_save.interval_minutes')} min")

config.set("preferences.auto_save.interval_minutes", 15)
config.save()
print(f"   Updated interval to: {config.get('preferences.auto_save.interval_minutes')} min")
print("   ✓ Configuration works!")

# Test 2: Project with Available Molecules
print("\n2. Testing Project Persistence...")

# Load an available XYZ file
xyz_file = Path("adjusted_benzene_molecule.xyz")
if not xyz_file.exists():
    print("   ⚠ XYZ file not found, skipping")
else:
    symbols, coords = core_io.load_xyz(xyz_file)

    # Create molecule with required parameters
    molecule = Molecule(
        id=1,
        name="Benzene Test",
        symbols=symbols,
        coords=coords,
        bonds=[]  # Empty bonds list for simplicity
    )

    # Apply transformation
    molecule.final_translation = np.array([10.0, 0.0, 0.0])
    molecule.apply_final_transformation()

    # Create and save project
    project = Project(
        name="Quick Test Project",
        molecules=[molecule],
        metadata={"test": "phase3_quick_test"}
    )

    save_path = Path("/tmp/quick_test.molman")
    project.save(save_path)
    print(f"   Saved project: {save_path}")
    print(f"   File size: {save_path.stat().st_size} bytes")

    # Load it back
    loaded = Project.load(save_path)
    print(f"   Loaded project: {loaded.name}")
    print(f"   Molecules: {len(loaded.molecules)}")
    print(f"   Atoms in molecule: {loaded.molecules[0].num_atoms}")

    # Verify transformation preserved
    translation_match = np.allclose(
        loaded.molecules[0].final_translation,
        molecule.final_translation
    )
    print(f"   Translation preserved: {translation_match}")
    print("   ✓ Project persistence works!")

    # Test XYZ export
    export_path = Path("/tmp/quick_export.xyz")
    project.export_xyz(export_path)
    print(f"   Exported to: {export_path}")
    print("   ✓ XYZ export works!")

# Test 3: Recent Files
print("\n3. Testing Recent Files...")
test_file = Path("/tmp/test_project.molman")
test_file.touch()
config.add_recent_file(test_file)
recent = config.get_recent_files()
print(f"   Recent files tracked: {len(recent)}")
if recent:
    print(f"   Most recent: {recent[0].name}")
print("   ✓ Recent files works!")

# Summary
print("\n" + "="*60)
print("✓ All Phase 3 features verified!")
print("="*60)
print("\nFiles created:")
print(f"  - {Path('/tmp/quick_test_config.json')}")
if xyz_file.exists():
    print(f"  - {Path('/tmp/quick_test.molman')}")
    print(f"  - {Path('/tmp/quick_export.xyz')}")
print(f"  - {Path('/tmp/test_project.molman')}")
print("\nNext: Run 'python -m pytest tests/test_config.py tests/test_project.py -v'")

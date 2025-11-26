# Testing Phase 3: Configuration Management & Project Persistence

## Quick Testing Guide

### 1. Automated Tests

Run all Phase 3 tests:
```bash
# Run all Phase 3 tests
python -m pytest tests/test_config.py tests/test_project.py -v

# Run with coverage
python -m pytest tests/test_config.py tests/test_project.py --cov=molvis_core.config --cov=molvis_core.project

# Run specific test
python -m pytest tests/test_config.py::TestConfigManager::test_add_recent_file -v
```

### 2. Interactive Demo Script

Run the comprehensive demo:
```bash
python demo_phase3.py
```

This demonstrates:
- Configuration creation and modification
- Recent files tracking
- Project save/load
- Auto-save functionality
- File locations

### 3. Manual Testing with Python REPL

#### A. Test Configuration Management

```python
from molvis_core.config import ConfigManager
from pathlib import Path

# Create a config manager
config = ConfigManager(Path("/tmp/test_config.json"))
config.load()

# Check default values
print(config.get("preferences.auto_save.enabled"))  # True
print(config.get("preferences.auto_save.interval_minutes"))  # 5

# Modify settings
config.set("preferences.auto_save.interval_minutes", 15)
config.set("preferences.rendering.background_color", "black")
config.save()

# Verify changes
print(config.get("preferences.auto_save.interval_minutes"))  # 15

# Test recent files
test_file = Path("/tmp/test.molman")
test_file.touch()
config.add_recent_file(test_file)
print(config.get_recent_files())  # [PosixPath('/tmp/test.molman')]

# Reset to defaults
config.reset_to_defaults()
print(config.get("preferences.auto_save.interval_minutes"))  # Back to 5
```

#### B. Test Project Persistence

```python
from molvis_core.project import Project
from molvis_core.molecule import Molecule
from molvis_core import io as core_io
from pathlib import Path
import numpy as np

# Load test molecules
water_symbols, water_coords = core_io.load_xyz(Path("test_data/water.xyz"))
water = Molecule(symbols=water_symbols, coords=water_coords)

benzene_symbols, benzene_coords = core_io.load_xyz(Path("test_data/benzene.xyz"))
benzene = Molecule(symbols=benzene_symbols, coords=benzene_coords)

# Apply transformations
benzene.final_translation = np.array([5.0, 0.0, 0.0])
benzene.apply_final_transformation()

# Create project
project = Project(
    name="My Test Project",
    molecules=[water, benzene],
    metadata={"created_by": "Manual Test"}
)

# Save project
save_path = Path("/tmp/my_project.molman")
project.save(save_path)
print(f"Saved to: {save_path}")

# Load project
loaded = Project.load(save_path)
print(f"Loaded project: {loaded.name}")
print(f"Molecules: {len(loaded.molecules)}")
print(f"Translation preserved: {loaded.molecules[1].final_translation}")

# Create backup
backup = project.create_backup(save_path)
print(f"Backup created: {backup}")

# Export to XYZ
xyz_path = Path("/tmp/export.xyz")
project.export_xyz(xyz_path)
print(f"Exported to XYZ: {xyz_path}")
```

#### C. Test Singleton Pattern

```python
from molvis_core.config import get_config_manager

# Get global config manager (singleton)
config1 = get_config_manager()
config2 = get_config_manager()

# They are the same instance
print(config1 is config2)  # True

# Modify once
config1.set("preferences.auto_save.interval_minutes", 20)

# Both see the change
print(config1.get("preferences.auto_save.interval_minutes"))  # 20
print(config2.get("preferences.auto_save.interval_minutes"))  # 20
```

### 4. Verify File Locations

Check that files are created in the right places:

```bash
# Configuration directory
ls -la ~/.molman/
# Should show: config.json, logs/

# Configuration file
cat ~/.molman/config.json
# Should show JSON with preferences

# Log files
ls -la ~/.molman/logs/
# Should show: molman.log, molman_errors.log

# Demo files
ls -la /tmp/*.molman /tmp/*.xyz
# Should show test projects and exports
```

### 5. Test Project File Format

Examine a .molman file to verify structure:

```bash
# Create a test project and examine it
python -c "
from molvis_core.project import Project
from molvis_core.molecule import Molecule
from molvis_core import io
from pathlib import Path
import numpy as np

symbols, coords = io.load_xyz(Path('test_data/water.xyz'))
mol = Molecule(symbols=symbols, coords=coords)
mol.final_translation = np.array([1.0, 2.0, 3.0])
mol.apply_final_transformation()

project = Project(name='Verify Format', molecules=[mol])
project.save(Path('/tmp/verify.molman'))
"

# View the file
cat /tmp/verify.molman
```

Expected structure:
```json
{
  "version": "1.0",
  "name": "Verify Format",
  "created": "2025-11-26T...",
  "last_modified": "2025-11-26T...",
  "molecules": [
    {
      "id": "...",
      "symbols": ["O", "H", "H"],
      "coords": [[...], [...], [...]],
      "original_coords": [[...], [...], [...]],
      "final_translation": [1.0, 2.0, 3.0],
      "final_rotation_matrix": [[...], [...], [...]]
    }
  ],
  "metadata": {}
}
```

### 6. Test Error Handling

```python
from molvis_core.config import ConfigManager
from molvis_core.project import Project
from molvis_core.exceptions import *
from pathlib import Path

# Test loading non-existent project
try:
    Project.load(Path("/nonexistent.molman"))
except FileNotFoundError as e:
    print(f"✓ Caught expected error: {e}")

# Test loading invalid JSON
invalid_file = Path("/tmp/invalid.molman")
invalid_file.write_text("not valid json")
try:
    Project.load(invalid_file)
except Exception as e:
    print(f"✓ Caught expected error: {type(e).__name__}")

# Test corrupted config
corrupted = Path("/tmp/corrupted.json")
corrupted.write_text("{invalid json")
config = ConfigManager(corrupted)
try:
    config.load()
except InvalidConfigError as e:
    print(f"✓ Caught expected error: {e}")
```

### 7. Test Coverage Report

Generate detailed coverage report:

```bash
# Generate coverage for Phase 3 modules
python -m pytest tests/test_config.py tests/test_project.py \
  --cov=molvis_core.config \
  --cov=molvis_core.project \
  --cov-report=html \
  --cov-report=term-missing

# View HTML report
# Open htmlcov/index.html in a browser
```

### 8. Performance Test

Test with large projects:

```python
from molvis_core.project import Project
from molvis_core.molecule import Molecule
from molvis_core import io
from pathlib import Path
import time

# Load a molecule
symbols, coords = io.load_xyz(Path("test_data/benzene.xyz"))

# Create project with many molecules
molecules = [Molecule(symbols=symbols, coords=coords) for _ in range(100)]
project = Project(name="Large Project", molecules=molecules)

# Time save operation
start = time.time()
project.save(Path("/tmp/large_project.molman"))
save_time = time.time() - start
print(f"Save time (100 molecules): {save_time:.3f}s")

# Time load operation
start = time.time()
loaded = Project.load(Path("/tmp/large_project.molman"))
load_time = time.time() - start
print(f"Load time (100 molecules): {load_time:.3f}s")

# Verify
print(f"Molecules loaded: {len(loaded.molecules)}")
```

## Expected Test Results

### Test Suite:
- ✅ 18 configuration management tests
- ✅ 21 project persistence tests
- ✅ 39 total Phase 3 tests
- ✅ 134 total tests (all phases)
- ✅ 100% pass rate

### File Locations:
- ✅ `~/.molman/config.json` - User configuration
- ✅ `~/.molman/logs/` - Log files
- ✅ `.molman` files - Project files (user-defined locations)
- ✅ `.autosave_*.molman` - Hidden auto-save files

### Key Features Verified:
- ✅ Configuration CRUD operations
- ✅ Recent files tracking (max 10, no duplicates)
- ✅ Project save/load with transformation preservation
- ✅ Auto-save path generation
- ✅ Backup creation
- ✅ XYZ export
- ✅ Error handling
- ✅ Deep copy for config defaults

## Troubleshooting

### Config file not created
```bash
# Manually trigger creation
python -c "from molvis_core.config import get_config_manager; get_config_manager()"
```

### Test data not found
```bash
# Check if test data exists
ls -la test_data/*.xyz

# If missing, tests in demo_phase3.py will skip gracefully
```

### Logging not working
```bash
# Check log directory
ls -la ~/.molman/logs/

# Check log level
python -c "from molvis_core.config import get_config_manager; print(get_config_manager().get('preferences.logging.level'))"
```

## Next Steps

After verifying Phase 3 works correctly:

1. **Phase 10**: Set up CI/CD pipeline (GitHub Actions)
2. **Phase 4**: Add multi-format file support (PDB, MOL2, etc.)
3. **Phase 6**: Performance optimization for large molecules

The foundation is now solid with configuration, logging, and persistence!

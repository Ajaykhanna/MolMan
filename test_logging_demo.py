#!/usr/bin/env python3
"""
Demonstration script for the MolMan logging and error handling system.

This script demonstrates:
1. Logging configuration and levels
2. Custom exception handling
3. File operation logging
4. Graceful error handling
"""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from molvis_core.logging_config import setup_logging, enable_debug_mode, get_logger
from molvis_core import io as core_io
from molvis_core.molecule import Molecule
from molvis_core import geometry, logic
import numpy as np


def main():
    print("=" * 70)
    print("MolMan Logging & Error Handling Demonstration")
    print("=" * 70)
    print()

    # === Test 1: Initialize Logging ===
    print("1. Initializing logging system...")
    setup_logging(level=20, enable_console_logging=True, enable_file_logging=True)
    logger = get_logger("demo")
    logger.info("Logging system initialized successfully")
    print(f"   ✓ Logs will be written to: ~/.molman/logs/")
    print()

    # === Test 2: Successful File Loading ===
    print("2. Testing successful file loading...")
    water_path = Path("tests/fixtures/water.xyz")
    if water_path.exists():
        symbols, coords = core_io.load_xyz(water_path)
        logger.info(f"Loaded {len(symbols)} atoms from {water_path.name}")
        print(f"   ✓ Successfully loaded {len(symbols)} atoms from water.xyz")
    print()

    # === Test 3: Error Handling - File Not Found ===
    print("3. Testing error handling (file not found)...")
    try:
        core_io.load_xyz(Path("nonexistent.xyz"))
    except Exception as e:
        print(f"   ✓ Caught exception: {type(e).__name__}")
        print(f"   ✓ Error message: {e}")
    print()

    # === Test 4: Molecule Creation with Logging ===
    print("4. Testing molecule creation with logging...")
    test_symbols = ['C', 'H', 'H', 'H', 'H']
    test_coords = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [-0.5, 0.866, 0.0],
        [-0.5, -0.866, 0.0],
        [0.0, 0.0, 1.0]
    ])
    mol = Molecule(
        id=1,
        name="Methane",
        symbols=test_symbols,
        coords=test_coords,
        bonds=[]
    )
    print(f"   ✓ Created molecule '{mol.name}' with {mol.num_atoms} atoms")
    print()

    # === Test 5: Bond Determination with Logging ===
    print("5. Testing bond determination...")
    bonds = logic.determine_bonds(test_symbols, test_coords)
    print(f"   ✓ Determined {len(bonds)} bonds")
    print()

    # === Test 6: Geometric Transformations ===
    print("6. Testing geometric transformations...")
    rotation_matrix = geometry.build_rotation_matrix(0, 0, 90)
    translation = np.array([5.0, 0.0, 0.0])
    transformed = geometry.apply_transform(
        test_coords,
        rotation_matrix,
        translation
    )
    print(f"   ✓ Applied rotation and translation to {len(test_coords)} atoms")
    print()

    # === Test 7: Enable Debug Mode ===
    print("7. Enabling debug mode for verbose logging...")
    enable_debug_mode()
    logger.debug("This is a debug message - you'll see detailed info now")

    # Perform an operation in debug mode
    centroid = geometry.calculate_centroid(test_coords)
    print(f"   ✓ Debug mode enabled - check logs for detailed output")
    print()

    # === Test 8: Error Validation ===
    print("8. Testing input validation with custom exceptions...")
    try:
        # Try to create invalid molecule
        Molecule(
            id=2,
            name="Invalid",
            symbols=['C', 'H'],
            coords=np.array([[0.0, 0.0, 0.0]]),  # Mismatch: 2 symbols, 1 coord
            bonds=[]
        )
    except Exception as e:
        print(f"   ✓ Validation caught: {type(e).__name__}")
        print(f"   ✓ Error: {e}")
    print()

    # === Test 9: Format XYZ String ===
    print("9. Testing XYZ string formatting...")
    xyz_string = core_io.format_xyz_string(
        symbols=test_symbols,
        coords=test_coords,
        comment="Test molecule for logging demo"
    )
    print(f"   ✓ Formatted XYZ string ({len(xyz_string)} characters)")
    print()

    # === Summary ===
    print("=" * 70)
    print("Demonstration Complete!")
    print("=" * 70)
    print()
    print("Key Features Demonstrated:")
    print("  ✓ Centralized logging with file rotation")
    print("  ✓ Custom exception hierarchy for precise error handling")
    print("  ✓ Debug mode for verbose diagnostics")
    print("  ✓ Structured logging across all modules")
    print("  ✓ Graceful error messages with context")
    print()
    print("Log files location: ~/.molman/logs/")
    print("  - molman.log: All log messages (INFO and above)")
    print("  - molman_errors.log: Error messages only")
    print()
    print("To view logs:")
    print("  tail -f ~/.molman/logs/molman.log")
    print()


if __name__ == "__main__":
    main()

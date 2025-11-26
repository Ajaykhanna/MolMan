"""
Pytest configuration and shared fixtures for MolMan tests.
"""

# Add project root to path for imports
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from molvis_core import io as core_io
from molvis_core.molecule import Molecule

# === Path Fixtures ===

@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def water_xyz_path(fixtures_dir) -> Path:
    """Return path to water.xyz fixture."""
    return fixtures_dir / "water.xyz"


@pytest.fixture
def benzene_xyz_path(fixtures_dir) -> Path:
    """Return path to benzene.xyz fixture."""
    return fixtures_dir / "benzene.xyz"


@pytest.fixture
def methane_xyz_path(fixtures_dir) -> Path:
    """Return path to methane.xyz fixture."""
    return fixtures_dir / "methane.xyz"


@pytest.fixture
def malformed_xyz_path(fixtures_dir) -> Path:
    """Return path to malformed.xyz fixture."""
    return fixtures_dir / "malformed.xyz"


@pytest.fixture
def empty_xyz_path(fixtures_dir) -> Path:
    """Return path to empty.xyz fixture."""
    return fixtures_dir / "empty.xyz"


@pytest.fixture
def multiblock_xyz_path(fixtures_dir) -> Path:
    """Return path to multiblock.xyz fixture."""
    return fixtures_dir / "multiblock.xyz"


# === Data Fixtures ===

@pytest.fixture
def water_data() -> tuple[list[str], np.ndarray]:
    """Return water molecule symbols and coordinates."""
    symbols = ['O', 'H', 'H']
    coords = np.array([
        [0.000000, 0.000000, 0.119262],
        [0.000000, 0.763239, -0.477047],
        [0.000000, -0.763239, -0.477047]
    ])
    return symbols, coords


@pytest.fixture
def benzene_data() -> tuple[list[str], np.ndarray]:
    """Return benzene molecule symbols and coordinates."""
    symbols = ['C', 'C', 'C', 'C', 'C', 'C', 'H', 'H', 'H', 'H', 'H', 'H']
    coords = np.array([
        [0.000000, 1.396800, 0.000000],
        [1.209700, 0.698400, 0.000000],
        [1.209700, -0.698400, 0.000000],
        [0.000000, -1.396800, 0.000000],
        [-1.209700, -0.698400, 0.000000],
        [-1.209700, 0.698400, 0.000000],
        [0.000000, 2.478800, 0.000000],
        [2.146700, 1.240400, 0.000000],
        [2.146700, -1.240400, 0.000000],
        [0.000000, -2.478800, 0.000000],
        [-2.146700, -1.240400, 0.000000],
        [-2.146700, 1.240400, 0.000000]
    ])
    return symbols, coords


@pytest.fixture
def methane_data() -> tuple[list[str], np.ndarray]:
    """Return methane molecule symbols and coordinates."""
    symbols = ['C', 'H', 'H', 'H', 'H']
    coords = np.array([
        [0.000000, 0.000000, 0.000000],
        [0.629118, 0.629118, 0.629118],
        [-0.629118, -0.629118, 0.629118],
        [-0.629118, 0.629118, -0.629118],
        [0.629118, -0.629118, -0.629118]
    ])
    return symbols, coords


# === Molecule Fixtures ===

@pytest.fixture
def water_molecule(water_data) -> Molecule:
    """Return a Molecule object for water."""
    symbols, coords = water_data
    return Molecule(
        id=0,
        name="Water",
        symbols=symbols,
        coords=coords,
        bonds=[(0, 1), (0, 2)]  # O-H bonds
    )


@pytest.fixture
def benzene_molecule(benzene_data) -> Molecule:
    """Return a Molecule object for benzene."""
    from molvis_core.logic import determine_bonds
    symbols, coords = benzene_data
    bonds = determine_bonds(symbols, coords)
    return Molecule(
        id=0,
        name="Benzene",
        symbols=symbols,
        coords=coords,
        bonds=bonds
    )


@pytest.fixture
def empty_molecule() -> Molecule:
    """Return an empty Molecule object for edge case testing."""
    return Molecule(
        id=0,
        name="Empty",
        symbols=[],
        coords=np.array([]).reshape(0, 3),
        bonds=[]
    )


# === Utility Fixtures ===

@pytest.fixture
def tolerance() -> float:
    """Return default floating point tolerance for comparisons."""
    return 1e-6


@pytest.fixture
def approx_equal():
    """Return a function for approximate equality testing."""
    def _approx_equal(a, b, tol=1e-6):
        return np.allclose(a, b, atol=tol, rtol=tol)
    return _approx_equal

"""
molvis_core/logic.py

Contains core algorithms for molecular analysis, such as bond determination.
"""

import numpy as np
from typing import List, Tuple, Optional

# Import constants and helpers from within the core library
from .constants import AVERAGE_BOND_LENGTHS, BOND_TOLERANCE


def get_bond_distance_range(
    atom1_symbol: str, atom2_symbol: str
) -> Optional[Tuple[float, float]]:
    """
    Retrieves the minimum and maximum distance criteria for a potential bond
    between two atom types.

    Uses the AVERAGE_BOND_LENGTHS dictionary and BOND_TOLERANCE constant.

    Args:
        atom1_symbol: Symbol of the first atom (case-insensitive).
        atom2_symbol: Symbol of the second atom (case-insensitive).

    Returns:
        A tuple (min_distance, max_distance) in Angstroms if the atom pair
        is defined in AVERAGE_BOND_LENGTHS, otherwise None.
    """
    # Use capitalized symbols for consistent dictionary lookup
    key = frozenset([atom1_symbol.capitalize(), atom2_symbol.capitalize()])
    average_length = AVERAGE_BOND_LENGTHS.get(key)

    if average_length is not None:
        # Ensure minimum distance is physically reasonable (e.g., > 0.1)
        min_distance = max(0.1, average_length - BOND_TOLERANCE)
        max_distance = average_length + BOND_TOLERANCE
        return min_distance, max_distance
    else:
        # Bond type not defined in constants
        return None


def determine_bonds(symbols: List[str], coords: np.ndarray) -> List[Tuple[int, int]]:
    """
    Determines bonds between atoms based on element types and distances.

    Iterates through all unique pairs of atoms, calculates the distance,
    and checks if it falls within the range defined by `get_bond_distance_range`.

    Args:
        symbols: List of atom symbols for the molecule.
        coords: NumPy array (N x 3) of corresponding atomic coordinates.

    Returns:
        A list of tuples, where each tuple contains the zero-based indices
        of two bonded atoms within the input lists/arrays. Returns an empty
        list if fewer than 2 atoms are present.
    """
    bonds: List[Tuple[int, int]] = []
    num_atoms = len(symbols)

    # Cannot form bonds with fewer than 2 atoms
    if num_atoms < 2:
        return bonds

    # Check coordinate shape consistency
    if coords.shape != (num_atoms, 3):
        raise ValueError(
            f"Shape mismatch: Found {len(symbols)} symbols but coords shape is {coords.shape}"
        )

    # Iterate through unique pairs of atoms
    for i in range(num_atoms):
        for j in range(i + 1, num_atoms):
            atom1_sym = symbols[i]
            atom2_sym = symbols[j]

            # Get the bonding distance range for this pair of elements
            bond_range = get_bond_distance_range(atom1_sym, atom2_sym)

            if bond_range is not None:
                min_dist, max_dist = bond_range
                min_dist_sq = min_dist**2
                max_dist_sq = max_dist**2

                # Calculate squared distance for efficiency
                delta_vec = coords[i] - coords[j]
                distance_sq = np.dot(delta_vec, delta_vec)  # Faster than np.linalg.norm

                # Check if the distance falls within the allowed range
                if min_dist_sq <= distance_sq <= max_dist_sq:
                    bonds.append((i, j))  # Add bond as a tuple of indices

    return bonds

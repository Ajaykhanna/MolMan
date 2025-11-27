"""
molvis_core/molecule.py

Defines the core data structure for representing a molecule.
Includes methods for managing transformation state relative to original coordinates.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .logging_config import get_logger
from .exceptions import (
    InvalidMoleculeError,
    AtomCountMismatchError,
    InvalidCoordinatesError,
)

# Import necessary geometry functions (using relative import)
from .geometry import calculate_centroid

# Initialize logger for this module
logger = get_logger(__name__)


@dataclass
class Molecule:
    """
    Represents a single molecule unit, typically loaded from one file or
    representing a distinct component in a system.

    Stores original data, identifiers, current transformed coordinates,
    and the final accumulated transformation relative to the original state.

    Attributes:
        id: Unique global integer identifier.
        name: String identifier for display.
        symbols: List of atomic symbols.
        coords: NumPy array of original atomic coordinates (N x 3).
        bonds: List of tuples representing bonds (indices relative to this molecule).
        source_file_index: Optional index of the source file.
        source_file_name: Optional original filename.
        metadata: Dictionary for storing format-specific metadata.
        transformed_coords: NumPy array (N x 3) holding the current coordinates
                            after applying final_translation and final_rotation_matrix.
        final_translation: NumPy array (3,) storing the total translation applied
                           relative to the original centered position.
        final_rotation_matrix: 3x3 NumPy array storing the total rotation applied.
    """

    id: int
    name: str
    symbols: List[str]
    coords: np.ndarray
    bonds: List[Tuple[int, int]]
    source_file_index: Optional[int] = None
    source_file_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # --- State Attributes ---
    # Current coordinates after transformations applied in apply_final_transformation
    transformed_coords: np.ndarray = field(init=False)
    # Stored final transformation state relative to original coordinates
    final_translation: np.ndarray = field(default_factory=lambda: np.zeros(3))
    final_rotation_matrix: np.ndarray = field(default_factory=lambda: np.identity(3))

    def __post_init__(self):
        """
        Basic validation and initial state calculation after initialization.

        Raises:
            InvalidCoordinatesError: If coordinates have invalid shape
            AtomCountMismatchError: If symbols and coordinates counts don't match
        """
        logger.debug(f"Initializing molecule '{self.name}' (ID: {self.id}) with {len(self.symbols)} atoms")

        if (
            not isinstance(self.coords, np.ndarray)
            or self.coords.ndim != 2
            or self.coords.shape[1] != 3
        ):
            if self.coords.size != 0:
                logger.error(f"Invalid coordinates shape for molecule '{self.name}': {self.coords.shape}")
                raise InvalidCoordinatesError(
                    f"Coordinates must be a NumPy array of shape (N, 3), got {self.coords.shape}"
                )

        if len(self.symbols) != self.coords.shape[0]:
            if not (len(self.symbols) == 0 and self.coords.shape[0] == 0):
                logger.error(
                    f"Atom count mismatch in molecule '{self.name}': "
                    f"{len(self.symbols)} symbols vs {self.coords.shape[0]} coordinates"
                )
                raise AtomCountMismatchError(len(self.symbols), self.coords.shape[0])

        # Calculate initial transformed_coords based on default identity/zero transforms
        self.apply_final_transformation()
        logger.info(f"Successfully initialized molecule '{self.name}' with {self.num_atoms} atoms")

    def reset_transformation(self):
        """
        Resets the stored final transformation (translation, rotation) to
        identity/zero and recalculates transformed_coords accordingly.
        """
        logger.debug(f"Resetting transformation for molecule '{self.name}' (ID: {self.id})")
        self.final_translation = np.zeros(3)
        self.final_rotation_matrix = np.identity(3)
        # Recalculate transformed_coords based on reset state
        self.apply_final_transformation()
        logger.info(f"Transformation reset for molecule '{self.name}'")

    @property
    def centroid(self) -> np.ndarray:
        """
        Calculates the geometric centroid based on the *original* coordinates.

        Returns:
            NumPy array representing the (x, y, z) centroid, or [0, 0, 0] if
            no coordinates exist.
        """
        # Use the geometry helper function for consistency
        return calculate_centroid(self.coords)

    def apply_final_transformation(self):
        """
        Applies the stored final_rotation_matrix and final_translation
        to the original coordinates to update self.transformed_coords.
        Rotation occurs around the original centroid.
        """
        logger.debug(
            f"Applying transformation to molecule '{self.name}' "
            f"(translation: {self.final_translation})"
        )

        if self.coords.size == 0:
            self.transformed_coords = np.array([])  # Ensure it's empty if no coords
            logger.warning(f"Molecule '{self.name}' has no coordinates to transform")
            return

        original_centroid = self.centroid  # Use property which uses helper

        # Center original coordinates
        coords_centered = self.coords - original_centroid
        # Apply stored rotation
        coords_rotated = coords_centered @ self.final_rotation_matrix.T
        # Translate back to original centroid position
        coords_recentered = coords_rotated + original_centroid
        # Apply stored translation
        self.transformed_coords = coords_recentered + self.final_translation

        logger.debug(f"Transformation applied to {self.num_atoms} atoms in molecule '{self.name}'")

    def get_atom_coord(self, index: int) -> Optional[np.ndarray]:
        """Safely retrieves the *original* coordinates of an atom by index."""
        if 0 <= index < self.num_atoms:
            return self.coords[index]
        return None

    def get_atom_symbol(self, index: int) -> Optional[str]:
        """Safely retrieves the symbol of an atom by index."""
        if 0 <= index < self.num_atoms:
            return self.symbols[index]
        return None

    @property
    def num_atoms(self) -> int:
        """Returns the number of atoms in the molecule."""
        return len(self.symbols)

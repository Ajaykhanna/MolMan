"""
Unit tests for molvis_core.molecule module.

Tests the Molecule class including initialization, transformations,
centroid calculations, and state management.
"""

import pytest
import numpy as np
from molvis_core.molecule import Molecule
from molvis_core.exceptions import (
    InvalidCoordinatesError,
    AtomCountMismatchError,
)


class TestMoleculeInitialization:
    """Tests for Molecule initialization and validation."""

    @pytest.mark.unit
    def test_molecule_creation_water(self, water_data):
        """Test creating a valid water molecule."""
        symbols, coords = water_data
        mol = Molecule(
            id=0,
            name="Water",
            symbols=symbols,
            coords=coords,
            bonds=[(0, 1), (0, 2)]
        )

        assert mol.id == 0
        assert mol.name == "Water"
        assert len(mol.symbols) == 3
        assert mol.coords.shape == (3, 3)
        assert len(mol.bonds) == 2
        assert mol.num_atoms == 3

    @pytest.mark.unit
    def test_molecule_empty(self, empty_molecule):
        """Test creating an empty molecule."""
        mol = empty_molecule

        assert mol.num_atoms == 0
        assert mol.coords.shape == (0, 3)
        assert len(mol.bonds) == 0
        assert len(mol.symbols) == 0

    @pytest.mark.unit
    def test_molecule_invalid_coords_shape(self):
        """Test that invalid coordinate shape raises error."""
        with pytest.raises(InvalidCoordinatesError):
            Molecule(
                id=0,
                name="Invalid",
                symbols=['C'],
                coords=np.array([1.0, 2.0, 3.0]),  # Wrong shape (should be (1, 3))
                bonds=[]
            )

    @pytest.mark.unit
    def test_molecule_mismatched_symbols_coords(self):
        """Test that mismatched symbols and coords raises error."""
        with pytest.raises(AtomCountMismatchError):
            Molecule(
                id=0,
                name="Mismatched",
                symbols=['C', 'H'],  # 2 symbols
                coords=np.array([[0.0, 0.0, 0.0]]),  # 1 coord
                bonds=[]
            )

    @pytest.mark.unit
    def test_molecule_post_init_transformation(self, water_data):
        """Test that post_init applies initial transformation."""
        symbols, coords = water_data
        mol = Molecule(
            id=0,
            name="Water",
            symbols=symbols,
            coords=coords,
            bonds=[]
        )

        # After initialization, transformed_coords should match original coords
        np.testing.assert_array_almost_equal(
            mol.transformed_coords,
            mol.coords
        )


class TestMoleculeCentroid:
    """Tests for centroid calculation."""

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_centroid_water(self, water_molecule):
        """Test centroid calculation for water molecule."""
        mol = water_molecule
        centroid = mol.centroid

        # Calculate expected centroid manually
        expected = np.mean(mol.coords, axis=0)

        np.testing.assert_array_almost_equal(centroid, expected)

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_centroid_benzene(self, benzene_molecule):
        """Test centroid for benzene (should be at origin)."""
        mol = benzene_molecule
        centroid = mol.centroid

        # Benzene is centered at origin
        np.testing.assert_array_almost_equal(
            centroid,
            np.array([0.0, 0.0, 0.0]),
            decimal=5
        )

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_centroid_empty(self, empty_molecule):
        """Test centroid of empty molecule returns zeros."""
        mol = empty_molecule
        centroid = mol.centroid

        np.testing.assert_array_equal(centroid, np.array([0.0, 0.0, 0.0]))

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_centroid_single_atom(self):
        """Test centroid of single atom molecule."""
        mol = Molecule(
            id=0,
            name="Single",
            symbols=['C'],
            coords=np.array([[1.0, 2.0, 3.0]]),
            bonds=[]
        )

        centroid = mol.centroid
        np.testing.assert_array_equal(centroid, np.array([1.0, 2.0, 3.0]))


class TestMoleculeTransformation:
    """Tests for molecule transformation methods."""

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_apply_final_transformation_identity(self, water_molecule):
        """Test applying identity transformation."""
        mol = water_molecule
        original_coords = mol.coords.copy()

        # Apply identity transformation
        mol.final_translation = np.zeros(3)
        mol.final_rotation_matrix = np.identity(3)
        mol.apply_final_transformation()

        np.testing.assert_array_almost_equal(
            mol.transformed_coords,
            original_coords
        )

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_apply_translation_only(self, water_molecule):
        """Test applying translation only."""
        mol = water_molecule
        translation = np.array([1.0, 2.0, 3.0])

        mol.final_translation = translation
        mol.final_rotation_matrix = np.identity(3)
        mol.apply_final_transformation()

        expected = mol.coords + translation
        np.testing.assert_array_almost_equal(
            mol.transformed_coords,
            expected
        )

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_apply_rotation_only(self, water_molecule):
        """Test applying rotation only (90 degrees around Z-axis)."""
        mol = water_molecule

        # 90 degree rotation around Z-axis
        angle = np.radians(90)
        rotation_z = np.array([
            [np.cos(angle), -np.sin(angle), 0],
            [np.sin(angle), np.cos(angle), 0],
            [0, 0, 1]
        ])

        mol.final_translation = np.zeros(3)
        mol.final_rotation_matrix = rotation_z
        mol.apply_final_transformation()

        # Verify rotation occurred around centroid
        assert mol.transformed_coords.shape == mol.coords.shape
        # After rotation, coordinates should be different
        assert not np.allclose(mol.transformed_coords, mol.coords)

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_reset_transformation(self, water_molecule):
        """Test resetting transformation to identity."""
        mol = water_molecule
        original_coords = mol.coords.copy()

        # Apply some transformation
        mol.final_translation = np.array([5.0, 5.0, 5.0])
        mol.final_rotation_matrix = np.array([
            [0, -1, 0],
            [1, 0, 0],
            [0, 0, 1]
        ])
        mol.apply_final_transformation()

        # Reset
        mol.reset_transformation()

        # Should be back to original
        np.testing.assert_array_equal(mol.final_translation, np.zeros(3))
        np.testing.assert_array_equal(mol.final_rotation_matrix, np.identity(3))
        np.testing.assert_array_almost_equal(
            mol.transformed_coords,
            original_coords
        )

    @pytest.mark.unit
    @pytest.mark.geometry
    def test_transformation_empty_molecule(self, empty_molecule):
        """Test transformation on empty molecule doesn't crash."""
        mol = empty_molecule

        mol.final_translation = np.array([1.0, 2.0, 3.0])
        mol.apply_final_transformation()

        assert mol.transformed_coords.size == 0

        mol.reset_transformation()
        assert mol.transformed_coords.size == 0


class TestMoleculeProperties:
    """Tests for molecule properties and accessors."""

    @pytest.mark.unit
    def test_num_atoms_property(self, water_molecule, benzene_molecule):
        """Test num_atoms property."""
        assert water_molecule.num_atoms == 3
        assert benzene_molecule.num_atoms == 12

    @pytest.mark.unit
    def test_get_atom_coord_valid(self, water_molecule):
        """Test getting valid atom coordinates."""
        mol = water_molecule

        coord = mol.get_atom_coord(0)
        assert coord is not None
        np.testing.assert_array_almost_equal(
            coord,
            mol.coords[0]
        )

    @pytest.mark.unit
    def test_get_atom_coord_invalid(self, water_molecule):
        """Test getting invalid atom index returns None."""
        mol = water_molecule

        assert mol.get_atom_coord(-1) is None
        assert mol.get_atom_coord(100) is None

    @pytest.mark.unit
    def test_get_atom_symbol_valid(self, water_molecule):
        """Test getting valid atom symbol."""
        mol = water_molecule

        assert mol.get_atom_symbol(0) == 'O'
        assert mol.get_atom_symbol(1) == 'H'
        assert mol.get_atom_symbol(2) == 'H'

    @pytest.mark.unit
    def test_get_atom_symbol_invalid(self, water_molecule):
        """Test getting invalid atom symbol returns None."""
        mol = water_molecule

        assert mol.get_atom_symbol(-1) is None
        assert mol.get_atom_symbol(100) is None


class TestMoleculeEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.unit
    def test_large_translation(self, water_molecule):
        """Test very large translation values."""
        mol = water_molecule

        large_translation = np.array([1e10, 1e10, 1e10])
        mol.final_translation = large_translation
        mol.apply_final_transformation()

        # Should not crash, coords should be very large
        assert np.all(mol.transformed_coords > 1e9)

    @pytest.mark.unit
    def test_multiple_transformations(self, water_molecule):
        """Test applying transformations sequentially."""
        mol = water_molecule
        original_coords = mol.coords.copy()

        # First transformation
        mol.final_translation = np.array([1.0, 0.0, 0.0])
        mol.apply_final_transformation()
        coords_after_first = mol.transformed_coords.copy()

        # Second transformation
        mol.final_translation = np.array([0.0, 1.0, 0.0])
        mol.apply_final_transformation()
        coords_after_second = mol.transformed_coords.copy()

        # Transformations should be different
        assert not np.allclose(coords_after_first, coords_after_second)

    @pytest.mark.unit
    def test_molecule_copy_independence(self, water_data):
        """Test that modifying coords doesn't affect original."""
        symbols, coords = water_data
        original_coords = coords.copy()

        mol = Molecule(
            id=0,
            name="Water",
            symbols=symbols,
            coords=coords,
            bonds=[]
        )

        # Modify molecule
        mol.final_translation = np.array([10.0, 10.0, 10.0])
        mol.apply_final_transformation()

        # Original coords passed in should not be modified
        np.testing.assert_array_equal(coords, original_coords)

"""
Unit tests for molvis_core.logic module.

Tests bond determination algorithms and related chemical logic.
"""

import pytest
import numpy as np
from molvis_core import logic
from molvis_core.exceptions import AtomCountMismatchError


class TestGetBondDistanceRange:
    """Tests for get_bond_distance_range function."""

    @pytest.mark.unit
    def test_ch_bond_range(self):
        """Test C-H bond distance range."""
        min_dist, max_dist = logic.get_bond_distance_range('C', 'H')

        # C-H average is 1.09, tolerance is 0.3
        assert min_dist == pytest.approx(1.09 - 0.3, abs=0.01)
        assert max_dist == pytest.approx(1.09 + 0.3, abs=0.01)

    @pytest.mark.unit
    def test_cc_bond_range(self):
        """Test C-C bond distance range."""
        min_dist, max_dist = logic.get_bond_distance_range('C', 'C')

        # C-C average is 1.53, tolerance is 0.3
        assert min_dist == pytest.approx(1.53 - 0.3, abs=0.01)
        assert max_dist == pytest.approx(1.53 + 0.3, abs=0.01)

    @pytest.mark.unit
    def test_oh_bond_range(self):
        """Test O-H bond distance range."""
        min_dist, max_dist = logic.get_bond_distance_range('O', 'H')

        # O-H average is 0.96, tolerance is 0.3
        assert min_dist == pytest.approx(0.96 - 0.3, abs=0.01)
        assert max_dist == pytest.approx(0.96 + 0.3, abs=0.01)

    @pytest.mark.unit
    def test_case_insensitive(self):
        """Test that element symbols are case-insensitive."""
        range1 = logic.get_bond_distance_range('C', 'H')
        range2 = logic.get_bond_distance_range('c', 'h')
        range3 = logic.get_bond_distance_range('C', 'h')

        assert range1 == range2 == range3

    @pytest.mark.unit
    def test_order_independent(self):
        """Test that atom order doesn't matter."""
        range1 = logic.get_bond_distance_range('C', 'H')
        range2 = logic.get_bond_distance_range('H', 'C')

        assert range1 == range2

    @pytest.mark.unit
    def test_undefined_bond_type(self):
        """Test that undefined bond types return None."""
        result = logic.get_bond_distance_range('C', 'Xe')
        assert result is None

        result = logic.get_bond_distance_range('Unknown', 'Element')
        assert result is None

    @pytest.mark.unit
    def test_minimum_distance_threshold(self):
        """Test that minimum distance has a physical lower bound."""
        # Even if average - tolerance is negative, min should be > 0.1
        min_dist, max_dist = logic.get_bond_distance_range('O', 'H')

        assert min_dist >= 0.1


class TestDetermineBonds:
    """Tests for determine_bonds function."""

    @pytest.mark.unit
    def test_determine_bonds_water(self, water_data):
        """Test bond determination for water molecule."""
        symbols, coords = water_data
        bonds = logic.determine_bonds(symbols, coords)

        # Water should have 2 O-H bonds
        assert len(bonds) == 2

        # Check that bonds involve oxygen (index 0) and hydrogens (1, 2)
        bond_set = set(bonds)
        assert (0, 1) in bond_set or (1, 0) in bond_set
        assert (0, 2) in bond_set or (2, 0) in bond_set

    @pytest.mark.unit
    def test_determine_bonds_methane(self, methane_data):
        """Test bond determination for methane molecule."""
        symbols, coords = methane_data
        bonds = logic.determine_bonds(symbols, coords)

        # Methane should have 4 C-H bonds
        assert len(bonds) == 4

        # All bonds should involve carbon (index 0)
        for bond in bonds:
            assert 0 in bond

    @pytest.mark.unit
    def test_determine_bonds_benzene(self, benzene_data):
        """Test bond determination for benzene molecule."""
        symbols, coords = benzene_data
        bonds = logic.determine_bonds(symbols, coords)

        # Benzene should have 12 bonds (6 C-C + 6 C-H)
        assert len(bonds) == 12

        # Count C-C and C-H bonds
        cc_bonds = 0
        ch_bonds = 0

        for i, j in bonds:
            if symbols[i] == 'C' and symbols[j] == 'C':
                cc_bonds += 1
            elif (symbols[i] == 'C' and symbols[j] == 'H') or \
                 (symbols[i] == 'H' and symbols[j] == 'C'):
                ch_bonds += 1

        assert cc_bonds == 6
        assert ch_bonds == 6

    @pytest.mark.unit
    def test_determine_bonds_empty(self):
        """Test bond determination for empty molecule."""
        symbols = []
        coords = np.array([]).reshape(0, 3)

        bonds = logic.determine_bonds(symbols, coords)

        assert len(bonds) == 0

    @pytest.mark.unit
    def test_determine_bonds_single_atom(self):
        """Test bond determination for single atom."""
        symbols = ['C']
        coords = np.array([[0.0, 0.0, 0.0]])

        bonds = logic.determine_bonds(symbols, coords)

        assert len(bonds) == 0

    @pytest.mark.unit
    def test_determine_bonds_no_bonds(self):
        """Test atoms too far apart have no bonds."""
        symbols = ['C', 'C']
        coords = np.array([
            [0.0, 0.0, 0.0],
            [100.0, 0.0, 0.0]  # Very far apart
        ])

        bonds = logic.determine_bonds(symbols, coords)

        assert len(bonds) == 0

    @pytest.mark.unit
    def test_determine_bonds_undefined_element(self):
        """Test that undefined element pairs have no bonds."""
        symbols = ['Xe', 'Xe']
        coords = np.array([
            [0.0, 0.0, 0.0],
            [1.5, 0.0, 0.0]
        ])

        bonds = logic.determine_bonds(symbols, coords)

        # No bond definition for Xe-Xe
        assert len(bonds) == 0

    @pytest.mark.unit
    def test_determine_bonds_no_duplicates(self, water_data):
        """Test that bond list has no duplicate bonds."""
        symbols, coords = water_data
        bonds = logic.determine_bonds(symbols, coords)

        # Check no duplicate bonds (considering order doesn't matter)
        bond_set = set()
        for i, j in bonds:
            # Normalize order
            bond = tuple(sorted([i, j]))
            assert bond not in bond_set
            bond_set.add(bond)

    @pytest.mark.unit
    def test_determine_bonds_shape_mismatch(self):
        """Test that mismatched shapes raise error."""
        symbols = ['C', 'H']
        coords = np.array([[0.0, 0.0, 0.0]])  # Only 1 coord for 2 symbols

        with pytest.raises(AtomCountMismatchError):
            logic.determine_bonds(symbols, coords)

    @pytest.mark.unit
    def test_determine_bonds_boundary_distance(self):
        """Test bonds at exact boundary distances."""
        symbols = ['C', 'H']

        # C-H average is 1.09, range is [0.79, 1.39]
        # Test at exact max distance
        coords = np.array([
            [0.0, 0.0, 0.0],
            [1.39, 0.0, 0.0]
        ])

        bonds = logic.determine_bonds(symbols, coords)
        assert len(bonds) == 1  # Should detect bond at boundary

        # Test just outside max distance
        coords = np.array([
            [0.0, 0.0, 0.0],
            [1.40, 0.0, 0.0]
        ])

        bonds = logic.determine_bonds(symbols, coords)
        assert len(bonds) == 0  # Should not detect bond

    @pytest.mark.unit
    @pytest.mark.slow
    def test_determine_bonds_performance(self):
        """Test bond determination performance on larger system."""
        # Create a grid of carbons (not realistic but tests performance)
        n = 20  # 20x20x20 = 8000 atoms
        symbols = ['C'] * (n * n * n)

        x = np.linspace(0, 10, n)
        y = np.linspace(0, 10, n)
        z = np.linspace(0, 10, n)

        xx, yy, zz = np.meshgrid(x, y, z)
        coords = np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()])

        # Should complete without hanging (might find many bonds)
        bonds = logic.determine_bonds(symbols, coords)

        # Just verify it completes and returns a list
        assert isinstance(bonds, list)


class TestLogicEdgeCases:
    """Tests for edge cases in logic functions."""

    @pytest.mark.unit
    def test_very_close_atoms(self):
        """Test atoms very close together (< min distance)."""
        symbols = ['C', 'H']
        coords = np.array([
            [0.0, 0.0, 0.0],
            [0.05, 0.0, 0.0]  # Very close
        ])

        bonds = logic.determine_bonds(symbols, coords)

        # Should not detect bond if too close
        assert len(bonds) == 0

    @pytest.mark.unit
    def test_collinear_atoms(self):
        """Test collinear atoms."""
        symbols = ['C', 'C', 'C']
        coords = np.array([
            [0.0, 0.0, 0.0],
            [1.5, 0.0, 0.0],  # Good C-C distance
            [3.0, 0.0, 0.0]   # Another good C-C distance
        ])

        bonds = logic.determine_bonds(symbols, coords)

        # Should detect both C-C bonds
        assert len(bonds) == 2

"""
Unit tests for molvis_core.io module.

Tests file I/O operations including XYZ file parsing, formatting,
and multi-block handling.
"""

import pytest
import numpy as np
from pathlib import Path
from molvis_core import io as core_io


class TestLoadXYZ:
    """Tests for load_xyz function."""

    @pytest.mark.unit
    @pytest.mark.io
    def test_load_xyz_water(self, water_xyz_path, water_data):
        """Test loading water.xyz file."""
        symbols, coords = core_io.load_xyz(water_xyz_path)
        expected_symbols, expected_coords = water_data

        assert symbols == expected_symbols
        np.testing.assert_array_almost_equal(coords, expected_coords)

    @pytest.mark.unit
    @pytest.mark.io
    def test_load_xyz_benzene(self, benzene_xyz_path):
        """Test loading benzene.xyz file."""
        symbols, coords = core_io.load_xyz(benzene_xyz_path)

        assert len(symbols) == 12
        assert coords.shape == (12, 3)
        assert symbols[:6] == ['C'] * 6  # First 6 are carbons
        assert symbols[6:] == ['H'] * 6  # Last 6 are hydrogens

    @pytest.mark.unit
    @pytest.mark.io
    def test_load_xyz_methane(self, methane_xyz_path):
        """Test loading methane.xyz file."""
        symbols, coords = core_io.load_xyz(methane_xyz_path)

        assert len(symbols) == 5
        assert coords.shape == (5, 3)
        assert symbols[0] == 'C'
        assert symbols[1:] == ['H'] * 4

    @pytest.mark.unit
    @pytest.mark.io
    def test_load_xyz_nonexistent_file(self):
        """Test loading non-existent file returns None."""
        result = core_io.load_xyz(Path('/nonexistent/file.xyz'))

        assert result == (None, None)

    @pytest.mark.unit
    @pytest.mark.io
    def test_load_xyz_empty_file(self, empty_xyz_path):
        """Test loading empty molecule file."""
        symbols, coords = core_io.load_xyz(empty_xyz_path)

        assert symbols == []
        assert coords.size == 0

    @pytest.mark.unit
    @pytest.mark.io
    def test_load_xyz_malformed(self, malformed_xyz_path):
        """Test loading malformed XYZ file."""
        # Should handle gracefully - might return partial data or None
        symbols, coords = core_io.load_xyz(malformed_xyz_path)

        # Should not crash, but data might be incomplete
        if symbols is not None:
            assert len(symbols) <= 5  # Header says 5 but file is incomplete


class TestLoadXYZFromText:
    """Tests for load_xyz_from_text function."""

    @pytest.mark.unit
    @pytest.mark.io
    def test_load_from_text_water(self):
        """Test loading water molecule from text."""
        xyz_text = """3
Water molecule
O     0.000000     0.000000     0.119262
H     0.000000     0.763239    -0.477047
H     0.000000    -0.763239    -0.477047
"""

        symbols, coords = core_io.load_xyz_from_text(xyz_text)

        assert len(symbols) == 3
        assert symbols == ['O', 'H', 'H']
        assert coords.shape == (3, 3)

    @pytest.mark.unit
    @pytest.mark.io
    def test_load_from_text_empty_string(self):
        """Test loading from empty string."""
        result = core_io.load_xyz_from_text("")

        assert result == (None, None)

    @pytest.mark.unit
    @pytest.mark.io
    def test_load_from_text_no_atoms(self):
        """Test loading text with zero atoms."""
        xyz_text = """0
Empty molecule
"""

        symbols, coords = core_io.load_xyz_from_text(xyz_text)

        assert symbols == []
        assert coords.size == 0

    @pytest.mark.unit
    @pytest.mark.io
    def test_load_from_text_malformed_header(self):
        """Test handling malformed header."""
        xyz_text = """not_a_number
Comment line
C     0.0     0.0     0.0
"""

        result = core_io.load_xyz_from_text(xyz_text)

        assert result == (None, None)

    @pytest.mark.unit
    @pytest.mark.io
    def test_load_from_text_whitespace_handling(self):
        """Test that whitespace is handled correctly."""
        xyz_text = """  3
  Water molecule
  O     0.000000     0.000000     0.119262
  H     0.000000     0.763239    -0.477047
  H     0.000000    -0.763239    -0.477047
"""

        symbols, coords = core_io.load_xyz_from_text(xyz_text)

        assert len(symbols) == 3
        assert symbols == ['O', 'H', 'H']


class TestLoadMultipleXYZFromText:
    """Tests for load_multiple_xyz_from_text function."""

    @pytest.mark.unit
    @pytest.mark.io
    def test_load_multiblock_two_waters(self):
        """Test loading two water molecules from multiblock text."""
        xyz_text = """3
First water
O     0.000000     0.000000     0.119262
H     0.000000     0.763239    -0.477047
H     0.000000    -0.763239    -0.477047
3
Second water
O     5.000000     0.000000     0.119262
H     5.000000     0.763239    -0.477047
H     5.000000    -0.763239    -0.477047
"""

        molecules = core_io.load_multiple_xyz_from_text(xyz_text)

        assert len(molecules) == 2

        # Check first molecule
        symbols1, coords1 = molecules[0]
        assert len(symbols1) == 3
        assert symbols1 == ['O', 'H', 'H']

        # Check second molecule
        symbols2, coords2 = molecules[1]
        assert len(symbols2) == 3
        assert symbols2 == ['O', 'H', 'H']
        assert coords2[0][0] == pytest.approx(5.0)

    @pytest.mark.unit
    @pytest.mark.io
    def test_load_multiblock_single(self):
        """Test that single block is parsed correctly."""
        xyz_text = """3
Single water
O     0.000000     0.000000     0.119262
H     0.000000     0.763239    -0.477047
H     0.000000    -0.763239    -0.477047
"""

        molecules = core_io.load_multiple_xyz_from_text(xyz_text)

        assert len(molecules) == 1
        symbols, coords = molecules[0]
        assert len(symbols) == 3

    @pytest.mark.unit
    @pytest.mark.io
    def test_load_multiblock_empty(self):
        """Test loading empty multiblock text."""
        molecules = core_io.load_multiple_xyz_from_text("")

        assert len(molecules) == 0

    @pytest.mark.unit
    @pytest.mark.io
    def test_load_multiblock_with_blank_lines(self):
        """Test handling blank lines between blocks."""
        xyz_text = """3
First water
O     0.000000     0.000000     0.119262
H     0.000000     0.763239    -0.477047
H     0.000000    -0.763239    -0.477047


3
Second water
O     5.000000     0.000000     0.119262
H     5.000000     0.763239    -0.477047
H     5.000000    -0.763239    -0.477047
"""

        molecules = core_io.load_multiple_xyz_from_text(xyz_text)

        assert len(molecules) == 2

    @pytest.mark.unit
    @pytest.mark.io
    def test_load_multiblock_malformed_block(self):
        """Test handling malformed block in multiblock text."""
        xyz_text = """3
Good water
O     0.000000     0.000000     0.119262
H     0.000000     0.763239    -0.477047
H     0.000000    -0.763239    -0.477047
5
Bad block - not enough atoms
C     0.0     0.0     0.0
H     1.0     0.0     0.0
"""

        molecules = core_io.load_multiple_xyz_from_text(xyz_text)

        # Should get at least the good water, malformed block should be skipped
        assert len(molecules) >= 1
        symbols, coords = molecules[0]
        assert len(symbols) == 3


class TestFormatXYZString:
    """Tests for format_xyz_string function."""

    @pytest.mark.unit
    @pytest.mark.io
    def test_format_xyz_simple(self):
        """Test formatting simple molecule to XYZ string."""
        symbols = ['O', 'H', 'H']
        coords = np.array([
            [0.0, 0.0, 0.1],
            [0.0, 0.7, -0.4],
            [0.0, -0.7, -0.4]
        ])
        comment = "Water molecule"

        result = core_io.format_xyz_string(symbols, coords, comment)

        # Check format
        lines = result.strip().split('\n')
        assert lines[0] == '3'
        assert lines[1] == comment
        assert len(lines) == 5  # Header + comment + 3 atoms

        # Check first atom line
        assert lines[2].startswith('O')

    @pytest.mark.unit
    @pytest.mark.io
    def test_format_xyz_no_comment(self):
        """Test formatting without comment."""
        symbols = ['C']
        coords = np.array([[0.0, 0.0, 0.0]])

        result = core_io.format_xyz_string(symbols, coords)

        lines = result.strip().split('\n')
        assert lines[0] == '1'
        assert lines[1] == ''  # Empty comment
        assert lines[2].startswith('C')

    @pytest.mark.unit
    @pytest.mark.io
    def test_format_xyz_empty(self):
        """Test formatting empty molecule."""
        symbols = []
        coords = np.array([]).reshape(0, 3)

        result = core_io.format_xyz_string(symbols, coords)

        lines = result.strip().split('\n')
        assert lines[0] == '0'

    @pytest.mark.unit
    @pytest.mark.io
    def test_format_xyz_large_coords(self):
        """Test formatting with large coordinate values."""
        symbols = ['C']
        coords = np.array([[1234.567890, -9876.543210, 0.000001]])

        result = core_io.format_xyz_string(symbols, coords)

        lines = result.strip().split('\n')
        # Check that coordinates are formatted with proper precision
        assert '1234.567890' in lines[2]
        assert '-9876.543210' in lines[2]

    @pytest.mark.unit
    @pytest.mark.io
    def test_format_xyz_shape_mismatch(self):
        """Test that shape mismatch raises error."""
        symbols = ['C', 'H']
        coords = np.array([[0.0, 0.0, 0.0]])  # Only 1 coord for 2 symbols

        with pytest.raises(ValueError, match="does not match"):
            core_io.format_xyz_string(symbols, coords)

    @pytest.mark.unit
    @pytest.mark.io
    def test_format_xyz_invalid_coords_shape(self):
        """Test that invalid coordinate shape raises error."""
        symbols = ['C']
        coords = np.array([0.0, 0.0, 0.0])  # 1D instead of 2D

        with pytest.raises(ValueError, match="shape \\(N, 3\\)"):
            core_io.format_xyz_string(symbols, coords)


class TestCreateTwoBenzenes:
    """Tests for create_two_benzenes function."""

    @pytest.mark.unit
    @pytest.mark.io
    def test_create_default_distance(self):
        """Test creating two benzenes with default distance."""
        symbols, coords, boundaries = core_io.create_two_benzenes()

        # Should have 24 atoms total (12 per benzene)
        assert len(symbols) == 24
        assert coords.shape == (24, 3)

        # Should have 2 molecule boundaries
        assert len(boundaries) == 2
        assert boundaries[0] == (0, 12)
        assert boundaries[1] == (12, 24)

        # First 12 should be benzene symbols
        assert symbols[:6] == ['C'] * 6
        assert symbols[6:12] == ['H'] * 6

    @pytest.mark.unit
    @pytest.mark.io
    def test_create_custom_distance(self):
        """Test creating two benzenes with custom distance."""
        distance = 10.0
        symbols, coords, boundaries = core_io.create_two_benzenes(distance=distance)

        # Get centroids of both benzenes
        coords1 = coords[boundaries[0][0]:boundaries[0][1]]
        coords2 = coords[boundaries[1][0]:boundaries[1][1]]

        centroid1 = np.mean(coords1, axis=0)
        centroid2 = np.mean(coords2, axis=0)

        # Distance between centroids should be along X-axis
        separation = np.linalg.norm(centroid2 - centroid1)
        assert separation == pytest.approx(distance, abs=0.01)

        # Separation should be primarily along X-axis
        assert abs(centroid2[0] - centroid1[0]) == pytest.approx(distance, abs=0.01)

    @pytest.mark.unit
    @pytest.mark.io
    def test_create_zero_distance(self):
        """Test creating two benzenes with zero separation."""
        symbols, coords, boundaries = core_io.create_two_benzenes(distance=0.0)

        # Should still create two molecules
        assert len(boundaries) == 2

        # But they'll overlap at same position
        coords1 = coords[boundaries[0][0]:boundaries[0][1]]
        coords2 = coords[boundaries[1][0]:boundaries[1][1]]

        centroid1 = np.mean(coords1, axis=0)
        centroid2 = np.mean(coords2, axis=0)

        # Centroids should be very close (within numerical precision)
        np.testing.assert_array_almost_equal(centroid1, centroid2, decimal=10)


class TestIOEdgeCases:
    """Tests for edge cases in I/O functions."""

    @pytest.mark.unit
    @pytest.mark.io
    def test_load_xyz_permissions(self, tmp_path):
        """Test handling of permission errors."""
        # Create a file
        test_file = tmp_path / "test.xyz"
        test_file.write_text("3\nTest\nC 0 0 0\nH 1 0 0\nH 0 1 0\n")

        # Make it readable
        test_file.chmod(0o444)

        # Should be able to read
        symbols, coords = core_io.load_xyz(test_file)
        assert symbols is not None

    @pytest.mark.unit
    @pytest.mark.io
    def test_format_then_parse_roundtrip(self, water_data):
        """Test that formatting then parsing gives back original data."""
        symbols_orig, coords_orig = water_data

        # Format to string
        xyz_string = core_io.format_xyz_string(symbols_orig, coords_orig, "Test")

        # Parse back
        symbols_parsed, coords_parsed = core_io.load_xyz_from_text(xyz_string)

        # Should get back same data
        assert symbols_parsed == symbols_orig
        np.testing.assert_array_almost_equal(coords_parsed, coords_orig, decimal=5)

    @pytest.mark.unit
    @pytest.mark.io
    def test_unicode_in_comment(self):
        """Test handling unicode characters in comment line."""
        symbols = ['C']
        coords = np.array([[0.0, 0.0, 0.0]])
        comment = "Test with unicode: α, β, γ, 中文"

        result = core_io.format_xyz_string(symbols, coords, comment)

        # Should not crash
        assert comment in result

    @pytest.mark.unit
    @pytest.mark.io
    def test_very_long_comment(self):
        """Test handling very long comment line."""
        symbols = ['C']
        coords = np.array([[0.0, 0.0, 0.0]])
        comment = "X" * 10000  # Very long comment

        result = core_io.format_xyz_string(symbols, coords, comment)

        # Should not crash
        assert len(result) > 10000

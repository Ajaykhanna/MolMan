"""
Tests for the XYZ format parser.
"""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from molvis_core.exceptions import EmptyFileError, FileNotFoundError, FileParseError
from molvis_core.formats.xyz import XYZParser
from molvis_core.molecule import Molecule


class TestXYZParser:
    """Tests for the XYZ format parser."""

    @pytest.fixture
    def parser(self):
        """Create an XYZ parser instance."""
        return XYZParser()

    @pytest.fixture
    def water_xyz_file(self, tmp_path):
        """Create a temporary water molecule XYZ file."""
        content = "3\nWater molecule\nO  0.000  0.000  0.000\nH  0.757  0.586  0.000\nH -0.757  0.586  0.000\n"
        xyz_file = tmp_path / "water.xyz"
        xyz_file.write_text(content)
        return xyz_file

    @pytest.fixture
    def benzene_xyz_file(self, tmp_path):
        """Create a temporary benzene molecule XYZ file."""
        content = """12
Benzene ring
C    0.000    1.400    0.000
C    1.212    0.700    0.000
C    1.212   -0.700    0.000
C    0.000   -1.400    0.000
C   -1.212   -0.700    0.000
C   -1.212    0.700    0.000
H    0.000    2.490    0.000
H    2.156    1.245    0.000
H    2.156   -1.245    0.000
H    0.000   -2.490    0.000
H   -2.156   -1.245    0.000
H   -2.156    1.245    0.000
"""
        xyz_file = tmp_path / "benzene.xyz"
        xyz_file.write_text(content)
        return xyz_file

    @pytest.fixture
    def multi_molecule_xyz_file(self, tmp_path):
        """Create a file with multiple molecules."""
        content = """2
H2 molecule
H  0.0  0.0  0.0
H  0.74 0.0  0.0
3
Water molecule
O  0.000  0.000  0.000
H  0.757  0.586  0.000
H -0.757  0.586  0.000
"""
        xyz_file = tmp_path / "multi.xyz"
        xyz_file.write_text(content)
        return xyz_file

    def test_parser_attributes(self, parser):
        """Test parser class attributes."""
        assert parser.format_name == "XYZ"
        assert ".xyz" in parser.extensions
        assert parser.supports_multiple is True

    def test_parse_water_molecule(self, parser, water_xyz_file):
        """Test parsing a water molecule."""
        molecules = parser.parse(water_xyz_file)

        assert len(molecules) == 1
        mol = molecules[0]

        assert len(mol.symbols) == 3
        assert mol.symbols == ['O', 'H', 'H']
        assert mol.coords.shape == (3, 3)

        # Check coordinates
        np.testing.assert_array_almost_equal(mol.coords[0], [0.0, 0.0, 0.0])
        np.testing.assert_array_almost_equal(mol.coords[1], [0.757, 0.586, 0.0])
        np.testing.assert_array_almost_equal(mol.coords[2], [-0.757, 0.586, 0.0])

        # Check metadata
        assert 'comment' in mol.metadata
        assert mol.metadata['comment'] == "Water molecule"

    def test_parse_benzene_molecule(self, parser, benzene_xyz_file):
        """Test parsing a benzene molecule."""
        molecules = parser.parse(benzene_xyz_file)

        assert len(molecules) == 1
        mol = molecules[0]

        assert len(mol.symbols) == 12
        assert mol.symbols.count('C') == 6
        assert mol.symbols.count('H') == 6
        assert mol.coords.shape == (12, 3)

    def test_parse_multiple_molecules(self, parser, multi_molecule_xyz_file):
        """Test parsing file with multiple molecules."""
        molecules = parser.parse(multi_molecule_xyz_file)

        assert len(molecules) == 2

        # First molecule (H2)
        h2 = molecules[0]
        assert len(h2.symbols) == 2
        assert h2.symbols == ['H', 'H']
        assert h2.metadata['comment'] == "H2 molecule"

        # Second molecule (Water)
        water = molecules[1]
        assert len(water.symbols) == 3
        assert water.symbols == ['O', 'H', 'H']
        assert water.metadata['comment'] == "Water molecule"

    def test_parse_file_not_found(self, parser):
        """Test parsing non-existent file."""
        with pytest.raises(FileNotFoundError) as exc_info:
            parser.parse(Path("nonexistent.xyz"))

        assert "nonexistent.xyz" in str(exc_info.value)

    def test_parse_empty_file(self, parser, tmp_path):
        """Test parsing empty file."""
        empty_file = tmp_path / "empty.xyz"
        empty_file.write_text("")

        with pytest.raises(EmptyFileError) as exc_info:
            parser.parse(empty_file)

        assert "empty.xyz" in str(exc_info.value)

    def test_parse_invalid_atom_count(self, parser, tmp_path):
        """Test parsing file with invalid atom count."""
        invalid_file = tmp_path / "invalid.xyz"
        invalid_file.write_text("not_a_number\nComment\nH 0 0 0\n")

        with pytest.raises(FileParseError) as exc_info:
            parser.parse(invalid_file)

        assert "Expected atom count" in str(exc_info.value)

    def test_parse_negative_atom_count(self, parser, tmp_path):
        """Test parsing file with negative atom count."""
        invalid_file = tmp_path / "invalid.xyz"
        invalid_file.write_text("-5\nComment\nH 0 0 0\n")

        with pytest.raises(FileParseError) as exc_info:
            parser.parse(invalid_file)

        assert "Invalid atom count" in str(exc_info.value)

    def test_parse_incomplete_file(self, parser, tmp_path):
        """Test parsing file that ends prematurely."""
        incomplete_file = tmp_path / "incomplete.xyz"
        incomplete_file.write_text("3\nWater\nO 0 0 0\nH 1 0 0\n")  # Missing 1 atom

        with pytest.raises(FileParseError) as exc_info:
            parser.parse(incomplete_file)

        assert "file ended prematurely" in str(exc_info.value)

    def test_parse_invalid_atom_line(self, parser, tmp_path):
        """Test parsing file with invalid atom line."""
        invalid_file = tmp_path / "invalid.xyz"
        invalid_file.write_text("2\nTest\nO 0 0 0\nH invalid_coord 0 0\n")

        with pytest.raises(FileParseError) as exc_info:
            parser.parse(invalid_file)

        assert "Invalid atom line" in str(exc_info.value)

    def test_parse_missing_coordinates(self, parser, tmp_path):
        """Test parsing file with missing coordinates."""
        invalid_file = tmp_path / "invalid.xyz"
        invalid_file.write_text("2\nTest\nO 0 0\nH 1 0 0\n")  # Missing Z coordinate

        with pytest.raises(FileParseError) as exc_info:
            parser.parse(invalid_file)

        assert "Expected 'Element X Y Z'" in str(exc_info.value)

    def test_write_single_molecule(self, parser, water_xyz_file, tmp_path):
        """Test writing a single molecule to XYZ file."""
        # Parse original
        molecules = parser.parse(water_xyz_file)

        # Write to new file
        output_file = tmp_path / "output.xyz"
        parser.write(molecules, output_file)

        # Parse again and compare
        reloaded = parser.parse(output_file)
        assert len(reloaded) == 1

        original = molecules[0]
        reloaded_mol = reloaded[0]

        assert original.symbols == reloaded_mol.symbols
        np.testing.assert_array_almost_equal(original.coords, reloaded_mol.coords)

    def test_write_multiple_molecules(self, parser, multi_molecule_xyz_file, tmp_path):
        """Test writing multiple molecules to XYZ file."""
        # Parse original
        molecules = parser.parse(multi_molecule_xyz_file)

        # Write to new file
        output_file = tmp_path / "output.xyz"
        parser.write(molecules, output_file)

        # Parse again and compare
        reloaded = parser.parse(output_file)
        assert len(reloaded) == len(molecules)

        for orig, reload in zip(molecules, reloaded):
            assert orig.symbols == reload.symbols
            np.testing.assert_array_almost_equal(orig.coords, reload.coords)

    def test_write_with_custom_comments(self, parser, tmp_path):
        """Test writing with custom comments."""
        # Create a simple molecule
        from molvis_core.molecule import Molecule

        mol = Molecule(
            id=1,
            name="H2",
            symbols=['H', 'H'],
            coords=np.array([[0.0, 0.0, 0.0], [0.74, 0.0, 0.0]]),
            bonds=[]
        )

        output_file = tmp_path / "output.xyz"
        parser.write([mol], output_file, comments=["Custom comment for H2"])

        # Read back and check comment
        reloaded = parser.parse(output_file)
        assert reloaded[0].metadata['comment'] == "Custom comment for H2"

    def test_write_with_custom_precision(self, parser, tmp_path):
        """Test writing with custom coordinate precision."""
        from molvis_core.molecule import Molecule

        mol = Molecule(
            id=1,
            name="Test",
            symbols=['H'],
            coords=np.array([[1.23456789, 2.3456789, 3.456789]]),
            bonds=[]
        )

        output_file = tmp_path / "output.xyz"
        parser.write([mol], output_file, precision=3)

        # Read back and check precision
        content = output_file.read_text()
        assert "1.235" in content  # Should be rounded to 3 decimals

    def test_validate_valid_file(self, parser, water_xyz_file):
        """Test validation of valid XYZ file."""
        assert parser.validate(water_xyz_file) is True

    def test_validate_invalid_file(self, parser, tmp_path):
        """Test validation of invalid file."""
        invalid_file = tmp_path / "invalid.xyz"
        invalid_file.write_text("This is not an XYZ file\n")

        assert parser.validate(invalid_file) is False

    def test_validate_nonexistent_file(self, parser):
        """Test validation of non-existent file."""
        assert parser.validate(Path("nonexistent.xyz")) is False

    def test_can_handle(self, parser):
        """Test the can_handle method."""
        assert parser.can_handle(Path("test.xyz")) is True
        assert parser.can_handle(Path("test.pdb")) is False

    def test_get_metadata_schema(self, parser):
        """Test getting metadata schema."""
        schema = parser.get_metadata_schema()
        assert 'comment' in schema
        assert schema['comment'] is str

    def test_roundtrip_preserves_data(self, parser, benzene_xyz_file, tmp_path):
        """Test that write->read roundtrip preserves all data."""
        # Parse original
        original_molecules = parser.parse(benzene_xyz_file)

        # Write and re-read
        output_file = tmp_path / "roundtrip.xyz"
        parser.write(original_molecules, output_file)
        reloaded_molecules = parser.parse(output_file)

        # Compare
        assert len(original_molecules) == len(reloaded_molecules)

        for orig, reload in zip(original_molecules, reloaded_molecules):
            assert orig.symbols == reload.symbols
            np.testing.assert_array_almost_equal(orig.coords, reload.coords, decimal=5)
            assert orig.metadata.get('comment') == reload.metadata.get('comment')


@pytest.mark.integration
class TestXYZIntegration:
    """Integration tests for XYZ parser."""

    def test_load_and_write_workflow(self, tmp_path):
        """Test complete load->modify->write workflow."""
        from molvis_core.formats import load_structure, write_structure

        # Create initial file
        input_file = tmp_path / "input.xyz"
        input_file.write_text("2\nH2\nH 0.0 0.0 0.0\nH 0.74 0.0 0.0\n")

        # Load
        molecules = load_structure(input_file)
        assert len(molecules) == 1

        # Modify coordinates
        molecules[0].coords += 1.0

        # Write
        output_file = tmp_path / "output.xyz"
        write_structure(molecules, output_file)

        # Verify
        reloaded = load_structure(output_file)
        np.testing.assert_array_almost_equal(
            reloaded[0].coords[0],
            [1.0, 1.0, 1.0]
        )

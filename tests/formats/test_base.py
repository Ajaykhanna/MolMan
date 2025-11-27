"""
Tests for the base format infrastructure.

Tests FormatDetector, FormatRegistry, and base functionality.
"""

import tempfile
from pathlib import Path

import pytest

from molvis_core.exceptions import UnsupportedFormatError
from molvis_core.formats import FormatDetector, FormatRegistry
from molvis_core.formats.base import FileFormatBase
from molvis_core.formats.xyz import XYZParser


class TestFormatDetector:
    """Tests for the FormatDetector class."""

    def test_detect_from_extension_xyz(self):
        """Test detecting XYZ format from file extension."""
        file_path = Path("test.xyz")
        format_name = FormatDetector.detect_from_extension(file_path)
        assert format_name == "xyz"

    def test_detect_from_extension_pdb(self):
        """Test detecting PDB format from file extension."""
        file_path = Path("protein.pdb")
        format_name = FormatDetector.detect_from_extension(file_path)
        assert format_name == "pdb"

    def test_detect_from_extension_mol2(self):
        """Test detecting MOL2 format from file extension."""
        file_path = Path("ligand.mol2")
        format_name = FormatDetector.detect_from_extension(file_path)
        assert format_name == "mol2"

    def test_detect_from_extension_sdf(self):
        """Test detecting SDF format from file extension."""
        file_path = Path("compounds.sdf")
        format_name = FormatDetector.detect_from_extension(file_path)
        assert format_name == "sdf"

    def test_detect_from_extension_cif(self):
        """Test detecting CIF format from file extension."""
        file_path = Path("crystal.cif")
        format_name = FormatDetector.detect_from_extension(file_path)
        assert format_name == "cif"

    def test_detect_from_extension_unknown(self):
        """Test detecting unknown format returns None."""
        file_path = Path("data.txt")
        format_name = FormatDetector.detect_from_extension(file_path)
        assert format_name is None

    def test_detect_from_content_xyz(self, tmp_path):
        """Test detecting XYZ format from file content."""
        xyz_file = tmp_path / "test.dat"
        xyz_file.write_text("3\nWater\nO 0.0 0.0 0.0\nH 0.757 0.586 0.0\nH -0.757 0.586 0.0\n")

        format_name = FormatDetector.detect_from_content(xyz_file)
        assert format_name == "xyz"

    def test_detect_from_content_pdb(self, tmp_path):
        """Test detecting PDB format from file content."""
        pdb_file = tmp_path / "test.dat"
        pdb_file.write_text("HEADER    TEST PROTEIN\nATOM      1  CA  ALA A   1       0.000   0.000   0.000\n")

        format_name = FormatDetector.detect_from_content(pdb_file)
        assert format_name == "pdb"

    def test_detect_from_content_mol2(self, tmp_path):
        """Test detecting MOL2 format from file content."""
        mol2_file = tmp_path / "test.dat"
        mol2_file.write_text("@<TRIPOS>MOLECULE\nbenzene\n")

        format_name = FormatDetector.detect_from_content(mol2_file)
        assert format_name == "mol2"

    def test_detect_from_content_sdf(self, tmp_path):
        """Test detecting SDF format from file content."""
        sdf_file = tmp_path / "test.dat"
        sdf_file.write_text("\n  test\n\n  0  0  0  0  0\nM  END\n")

        format_name = FormatDetector.detect_from_content(sdf_file)
        assert format_name == "sdf"

    def test_detect_from_content_cif(self, tmp_path):
        """Test detecting CIF format from file content."""
        cif_file = tmp_path / "test.dat"
        cif_file.write_text("data_test\nloop_\n_atom_site_label\n")

        format_name = FormatDetector.detect_from_content(cif_file)
        assert format_name == "cif"

    def test_detect_from_content_unknown(self, tmp_path):
        """Test detecting unknown format from content returns None."""
        unknown_file = tmp_path / "test.dat"
        unknown_file.write_text("This is some random text\n")

        format_name = FormatDetector.detect_from_content(unknown_file)
        assert format_name is None

    def test_detect_extension_only(self):
        """Test detect() with extension only and unsupported extension."""
        # File with unsupported extension should raise error
        file_path = Path("test.unknown")
        with pytest.raises(UnsupportedFormatError):
            FormatDetector.detect(file_path, use_content=False)

    def test_detect_unsupported_format(self):
        """Test detect() raises error for unsupported format."""
        file_path = Path("data.txt")
        with pytest.raises(UnsupportedFormatError) as exc_info:
            FormatDetector.detect(file_path, use_content=False)

        assert "Could not determine format" in str(exc_info.value)


class TestFormatRegistry:
    """Tests for the FormatRegistry class."""

    def test_xyz_parser_registered(self):
        """Test that XYZ parser is automatically registered."""
        assert FormatRegistry.is_supported('xyz')

    def test_get_parser_xyz(self):
        """Test getting XYZ parser from registry."""
        parser = FormatRegistry.get_parser('xyz')
        assert isinstance(parser, XYZParser)
        assert parser.format_name == "XYZ"

    def test_get_parser_case_insensitive(self):
        """Test that format names are case-insensitive."""
        parser1 = FormatRegistry.get_parser('xyz')
        parser2 = FormatRegistry.get_parser('XYZ')
        assert type(parser1) is type(parser2)

    def test_get_parser_unsupported(self):
        """Test getting unsupported parser raises error."""
        with pytest.raises(UnsupportedFormatError) as exc_info:
            FormatRegistry.get_parser('unsupported')

        assert "format:unsupported" in str(exc_info.value)
        assert "Available formats" in str(exc_info.value)

    def test_list_formats(self):
        """Test listing registered formats."""
        formats = FormatRegistry.list_formats()
        assert 'xyz' in formats
        assert isinstance(formats, list)

    def test_is_supported(self):
        """Test checking if format is supported."""
        assert FormatRegistry.is_supported('xyz') is True
        assert FormatRegistry.is_supported('unsupported') is False

    def test_register_custom_parser(self):
        """Test registering a custom parser."""

        class CustomParser(FileFormatBase):
            format_name = "CUSTOM"
            extensions = [".cst"]

            def parse(self, file_path):
                return []

            def write(self, molecules, file_path, **kwargs):
                pass

            def validate(self, file_path):
                return True

        # Register
        FormatRegistry.register('custom', CustomParser)
        assert FormatRegistry.is_supported('custom')

        # Get parser
        parser = FormatRegistry.get_parser('custom')
        assert isinstance(parser, CustomParser)

        # Clean up
        FormatRegistry.unregister('custom')
        assert not FormatRegistry.is_supported('custom')

    def test_unregister_parser(self):
        """Test unregistering a parser."""

        class TempParser(FileFormatBase):
            format_name = "TEMP"
            extensions = [".tmp"]

            def parse(self, file_path):
                return []

            def write(self, molecules, file_path, **kwargs):
                pass

            def validate(self, file_path):
                return True

        # Register and verify
        FormatRegistry.register('temp', TempParser)
        assert FormatRegistry.is_supported('temp')

        # Unregister and verify
        FormatRegistry.unregister('temp')
        assert not FormatRegistry.is_supported('temp')

    def test_get_parser_for_file_with_format(self, tmp_path):
        """Test getting parser for file with explicit format."""
        test_file = tmp_path / "test.xyz"
        test_file.write_text("3\nTest\nO 0 0 0\nH 1 0 0\nH 0 1 0\n")

        parser = FormatRegistry.get_parser_for_file(test_file, format_name='xyz')
        assert isinstance(parser, XYZParser)

    def test_get_parser_for_file_auto_detect(self, tmp_path):
        """Test getting parser for file with auto-detection."""
        test_file = tmp_path / "test.xyz"
        test_file.write_text("3\nTest\nO 0 0 0\nH 1 0 0\nH 0 1 0\n")

        parser = FormatRegistry.get_parser_for_file(test_file)
        assert isinstance(parser, XYZParser)


class TestFileFormatBase:
    """Tests for the FileFormatBase abstract class."""

    def test_can_handle(self):
        """Test the can_handle method."""
        parser = XYZParser()

        assert parser.can_handle(Path("test.xyz")) is True
        assert parser.can_handle(Path("test.pdb")) is False
        assert parser.can_handle(Path("test.txt")) is False

    def test_get_metadata_schema(self):
        """Test getting metadata schema."""
        parser = XYZParser()
        schema = parser.get_metadata_schema()

        assert isinstance(schema, dict)
        assert 'comment' in schema
        assert schema['comment'] is str


@pytest.mark.integration
class TestFormatIntegration:
    """Integration tests for the format infrastructure."""

    def test_full_workflow_xyz(self, tmp_path):
        """Test complete workflow: detect -> get parser -> parse."""
        # Create test file
        xyz_file = tmp_path / "test.xyz"
        xyz_file.write_text("2\nH2 molecule\nH 0.0 0.0 0.0\nH 0.74 0.0 0.0\n")

        # Detect format
        format_name = FormatDetector.detect(xyz_file)
        assert format_name == 'xyz'

        # Get parser
        parser = FormatRegistry.get_parser(format_name)
        assert isinstance(parser, XYZParser)

        # Parse file
        molecules = parser.parse(xyz_file)
        assert len(molecules) == 1
        assert len(molecules[0].symbols) == 2

"""
Tests for the PDB format parser.
"""

from pathlib import Path

import numpy as np
import pytest

from molvis_core.exceptions import FileNotFoundError
from molvis_core.formats.pdb import PDBParser


class TestPDBParser:
    """Tests for the PDB format parser."""

    @pytest.fixture
    def parser(self):
        """Create a PDB parser instance."""
        return PDBParser()

    @pytest.fixture
    def simple_pdb_file(self, tmp_path):
        """Create a simple PDB file with a few atoms."""
        content = """HEADER    TEST PROTEIN                            01-JAN-00   1ABC
TITLE     SIMPLE TEST STRUCTURE
ATOM      1  CA  ALA A   1       1.000   2.000   3.000  1.00 20.00           C
ATOM      2  CB  ALA A   1       2.000   3.000   4.000  1.00 25.00           C
ATOM      3  CA  GLY A   2       3.000   4.000   5.000  1.00 30.00           C
END
"""
        pdb_file = tmp_path / "simple.pdb"
        pdb_file.write_text(content)
        return pdb_file

    @pytest.fixture
    def multi_model_pdb_file(self, tmp_path):
        """Create a PDB file with multiple models."""
        content = """HEADER    MULTI-MODEL STRUCTURE
MODEL        1
ATOM      1  CA  ALA A   1       1.000   2.000   3.000  1.00 20.00           C
ATOM      2  CB  ALA A   1       2.000   3.000   4.000  1.00 25.00           C
ENDMDL
MODEL        2
ATOM      1  CA  ALA A   1       1.500   2.500   3.500  1.00 20.00           C
ATOM      2  CB  ALA A   1       2.500   3.500   4.500  1.00 25.00           C
ENDMDL
END
"""
        pdb_file = tmp_path / "multi.pdb"
        pdb_file.write_text(content)
        return pdb_file

    @pytest.fixture
    def hetatm_pdb_file(self, tmp_path):
        """Create a PDB file with HETATM records."""
        content = """HEADER    PROTEIN WITH LIGAND
ATOM      1  CA  ALA A   1       1.000   2.000   3.000  1.00 20.00           C
HETATM    2  O   HOH A 101       5.000   6.000   7.000  1.00 30.00           O
HETATM    3  C1  LIG B 201       8.000   9.000  10.000  1.00 40.00           C
END
"""
        pdb_file = tmp_path / "hetatm.pdb"
        pdb_file.write_text(content)
        return pdb_file

    @pytest.fixture
    def multi_chain_pdb_file(self, tmp_path):
        """Create a PDB file with multiple chains."""
        content = """HEADER    MULTI-CHAIN PROTEIN
ATOM      1  CA  ALA A   1       1.000   2.000   3.000  1.00 20.00           C
ATOM      2  CA  GLY A   2       2.000   3.000   4.000  1.00 25.00           C
ATOM      3  CA  VAL B   1       5.000   6.000   7.000  1.00 30.00           C
ATOM      4  CA  LEU B   2       6.000   7.000   8.000  1.00 35.00           C
END
"""
        pdb_file = tmp_path / "multi_chain.pdb"
        pdb_file.write_text(content)
        return pdb_file

    @pytest.fixture
    def conect_pdb_file(self, tmp_path):
        """Create a PDB file with CONECT records."""
        content = """HEADER    LIGAND WITH BONDS
HETATM    1  C1  LIG A   1       0.000   0.000   0.000  1.00 20.00           C
HETATM    2  C2  LIG A   1       1.500   0.000   0.000  1.00 20.00           C
HETATM    3  C3  LIG A   1       2.250   1.299   0.000  1.00 20.00           C
CONECT    1    2
CONECT    2    1    3
CONECT    3    2
END
"""
        pdb_file = tmp_path / "conect.pdb"
        pdb_file.write_text(content)
        return pdb_file

    def test_parser_attributes(self, parser):
        """Test parser class attributes."""
        assert parser.format_name == "PDB"
        assert ".pdb" in parser.extensions
        assert ".ent" in parser.extensions
        assert parser.supports_multiple is True

    def test_parse_simple_pdb(self, parser, simple_pdb_file):
        """Test parsing a simple PDB file."""
        molecules = parser.parse(simple_pdb_file)

        assert len(molecules) == 1
        mol = molecules[0]

        # Check atoms
        assert len(mol.symbols) == 3
        assert mol.symbols == ['C', 'C', 'C']

        # Check coordinates
        np.testing.assert_array_almost_equal(
            mol.coords[0], [1.0, 2.0, 3.0]
        )
        np.testing.assert_array_almost_equal(
            mol.coords[1], [2.0, 3.0, 4.0]
        )
        np.testing.assert_array_almost_equal(
            mol.coords[2], [3.0, 4.0, 5.0]
        )

        # Check metadata
        assert 'pdb_id' in mol.metadata
        assert mol.metadata['pdb_id'] == '1ABC'
        assert 'title' in mol.metadata
        assert 'SIMPLE TEST STRUCTURE' in mol.metadata['title']

    def test_parse_metadata(self, parser, simple_pdb_file):
        """Test parsing PDB metadata."""
        molecules = parser.parse(simple_pdb_file)
        metadata = molecules[0].metadata

        assert metadata['pdb_id'] == '1ABC'
        assert 'SIMPLE TEST STRUCTURE' in metadata['title']
        assert metadata['deposition_date'] == '01-JAN-00'
        assert metadata['classification'] == 'TEST PROTEIN'

    def test_parse_multi_model(self, parser, multi_model_pdb_file):
        """Test parsing PDB file with multiple models."""
        molecules = parser.parse(multi_model_pdb_file)

        # Should have 2 models
        assert len(molecules) == 2

        # First model
        mol1 = molecules[0]
        assert len(mol1.symbols) == 2
        np.testing.assert_array_almost_equal(
            mol1.coords[0], [1.0, 2.0, 3.0]
        )
        assert mol1.metadata['model_number'] == 1

        # Second model
        mol2 = molecules[1]
        assert len(mol2.symbols) == 2
        np.testing.assert_array_almost_equal(
            mol2.coords[0], [1.5, 2.5, 3.5]
        )
        assert mol2.metadata['model_number'] == 2

    def test_parse_specific_model(self, parser, multi_model_pdb_file):
        """Test parsing a specific model from multi-model PDB."""
        molecules = parser.parse(multi_model_pdb_file, model=2)

        # Should only get model 2
        assert len(molecules) == 1
        mol = molecules[0]
        assert mol.metadata['model_number'] == 2
        np.testing.assert_array_almost_equal(
            mol.coords[0], [1.5, 2.5, 3.5]
        )

    def test_parse_with_hetatm(self, parser, hetatm_pdb_file):
        """Test parsing PDB with HETATM records included."""
        molecules = parser.parse(hetatm_pdb_file, include_hetatm=True)

        mol = molecules[0]
        # Should have 1 ATOM + 2 HETATM = 3 total
        assert len(mol.symbols) == 3
        assert mol.symbols == ['C', 'O', 'C']

    def test_parse_without_hetatm(self, parser, hetatm_pdb_file):
        """Test parsing PDB with HETATM records excluded."""
        molecules = parser.parse(hetatm_pdb_file, include_hetatm=False)

        mol = molecules[0]
        # Should only have 1 ATOM
        assert len(mol.symbols) == 1
        assert mol.symbols == ['C']

    def test_parse_multi_chain(self, parser, multi_chain_pdb_file):
        """Test parsing PDB with multiple chains."""
        molecules = parser.parse(multi_chain_pdb_file)

        mol = molecules[0]
        # Should have all 4 atoms
        assert len(mol.symbols) == 4

        # Check atom details preserve chain information
        assert 'atoms' in mol.metadata
        atoms = mol.metadata['atoms']
        assert atoms[0]['chain_id'] == 'A'
        assert atoms[1]['chain_id'] == 'A'
        assert atoms[2]['chain_id'] == 'B'
        assert atoms[3]['chain_id'] == 'B'

    def test_parse_specific_chain(self, parser, multi_chain_pdb_file):
        """Test parsing specific chain from PDB."""
        molecules = parser.parse(multi_chain_pdb_file, chains=['A'])

        mol = molecules[0]
        # Should only have 2 atoms from chain A
        assert len(mol.symbols) == 2

        atoms = mol.metadata['atoms']
        assert all(atom['chain_id'] == 'A' for atom in atoms)

    def test_parse_multiple_chains(self, parser, multi_chain_pdb_file):
        """Test parsing multiple specific chains."""
        molecules = parser.parse(multi_chain_pdb_file, chains=['A', 'B'])

        mol = molecules[0]
        # Should have all 4 atoms (both chains requested)
        assert len(mol.symbols) == 4

    def test_parse_conect_records(self, parser, conect_pdb_file):
        """Test parsing CONECT records for bond information."""
        molecules = parser.parse(conect_pdb_file)

        mol = molecules[0]
        # Should have 3 atoms
        assert len(mol.symbols) == 3

        # Should have 2 bonds: 1-2 and 2-3
        assert len(mol.bonds) == 2
        bonds_set = {tuple(sorted(bond)) for bond in mol.bonds}
        assert (0, 1) in bonds_set  # Atoms 1-2 (0-indexed)
        assert (1, 2) in bonds_set  # Atoms 2-3 (0-indexed)

    def test_parse_atom_details(self, parser, simple_pdb_file):
        """Test that atom details are preserved in metadata."""
        molecules = parser.parse(simple_pdb_file)

        mol = molecules[0]
        assert 'atoms' in mol.metadata

        atoms = mol.metadata['atoms']
        assert len(atoms) == 3

        # Check first atom
        atom1 = atoms[0]
        assert atom1['name'] == 'CA'
        assert atom1['res_name'] == 'ALA'
        assert atom1['chain_id'] == 'A'
        assert atom1['res_seq'] == 1
        assert atom1['occupancy'] == 1.0
        assert atom1['temp_factor'] == 20.0

    def test_parse_file_not_found(self, parser):
        """Test parsing non-existent file."""
        with pytest.raises(FileNotFoundError):
            parser.parse(Path("nonexistent.pdb"))

    def test_parse_empty_pdb(self, parser, tmp_path):
        """Test parsing PDB file with no atoms."""
        empty_file = tmp_path / "empty.pdb"
        empty_file.write_text("HEADER    EMPTY\nEND\n")

        molecules = parser.parse(empty_file)
        # Should return one empty molecule with metadata
        assert len(molecules) == 1
        assert len(molecules[0].symbols) == 0

    def test_write_simple_pdb(self, parser, simple_pdb_file, tmp_path):
        """Test writing a simple PDB file."""
        # Parse original
        molecules = parser.parse(simple_pdb_file)

        # Write to new file
        output_file = tmp_path / "output.pdb"
        parser.write(molecules, output_file)

        # Read back and compare
        reloaded = parser.parse(output_file)
        assert len(reloaded) == 1

        original = molecules[0]
        reloaded_mol = reloaded[0]

        assert original.symbols == reloaded_mol.symbols
        np.testing.assert_array_almost_equal(
            original.coords, reloaded_mol.coords, decimal=3
        )

    def test_write_multi_model(self, parser, multi_model_pdb_file, tmp_path):
        """Test writing multi-model PDB file."""
        # Parse original
        molecules = parser.parse(multi_model_pdb_file)

        # Write to new file
        output_file = tmp_path / "output.pdb"
        parser.write(molecules, output_file)

        # Read back
        reloaded = parser.parse(output_file)
        assert len(reloaded) == len(molecules)

        for orig, reload in zip(molecules, reloaded):
            assert orig.symbols == reload.symbols
            np.testing.assert_array_almost_equal(
                orig.coords, reload.coords, decimal=3
            )

    def test_write_with_conect(self, parser, conect_pdb_file, tmp_path):
        """Test writing PDB with CONECT records."""
        # Parse original
        molecules = parser.parse(conect_pdb_file)

        # Write to new file with CONECT
        output_file = tmp_path / "output.pdb"
        parser.write(molecules, output_file, write_conect=True)

        # Read back and check bonds preserved
        reloaded = parser.parse(output_file)
        assert len(reloaded[0].bonds) == len(molecules[0].bonds)

    def test_write_without_conect(self, parser, conect_pdb_file, tmp_path):
        """Test writing PDB without CONECT records."""
        # Parse original
        molecules = parser.parse(conect_pdb_file)

        # Write without CONECT
        output_file = tmp_path / "output.pdb"
        parser.write(molecules, output_file, write_conect=False)

        # Verify CONECT is not in output
        content = output_file.read_text()
        assert "CONECT" not in content

    def test_write_without_header(self, parser, simple_pdb_file, tmp_path):
        """Test writing PDB without header records."""
        molecules = parser.parse(simple_pdb_file)

        output_file = tmp_path / "output.pdb"
        parser.write(molecules, output_file, write_header=False)

        # Verify no HEADER/TITLE in output
        content = output_file.read_text()
        assert not content.startswith("HEADER")
        assert "TITLE" not in content

    def test_validate_valid_pdb(self, parser, simple_pdb_file):
        """Test validation of valid PDB file."""
        assert parser.validate(simple_pdb_file) is True

    def test_validate_invalid_pdb(self, parser, tmp_path):
        """Test validation of invalid file."""
        invalid_file = tmp_path / "invalid.pdb"
        invalid_file.write_text("This is not a PDB file\n")

        assert parser.validate(invalid_file) is False

    def test_validate_nonexistent_file(self, parser):
        """Test validation of non-existent file."""
        assert parser.validate(Path("nonexistent.pdb")) is False

    def test_can_handle(self, parser):
        """Test the can_handle method."""
        assert parser.can_handle(Path("test.pdb")) is True
        assert parser.can_handle(Path("test.ent")) is True
        assert parser.can_handle(Path("test.xyz")) is False

    def test_get_metadata_schema(self, parser):
        """Test getting metadata schema."""
        schema = parser.get_metadata_schema()
        assert 'format' in schema
        assert 'pdb_id' in schema
        assert 'title' in schema
        assert 'atoms' in schema

    def test_roundtrip_preserves_data(self, parser, multi_chain_pdb_file, tmp_path):
        """Test that write->read roundtrip preserves all important data."""
        # Parse original
        original_molecules = parser.parse(multi_chain_pdb_file)

        # Write and re-read
        output_file = tmp_path / "roundtrip.pdb"
        parser.write(original_molecules, output_file)
        reloaded_molecules = parser.parse(output_file)

        # Compare
        assert len(original_molecules) == len(reloaded_molecules)

        for orig, reload in zip(original_molecules, reloaded_molecules):
            assert orig.symbols == reload.symbols
            np.testing.assert_array_almost_equal(
                orig.coords, reload.coords, decimal=3
            )

            # Check atom details preserved
            orig_atoms = orig.metadata.get('atoms', [])
            reload_atoms = reload.metadata.get('atoms', [])
            assert len(orig_atoms) == len(reload_atoms)

            for orig_atom, reload_atom in zip(orig_atoms, reload_atoms):
                assert orig_atom['chain_id'] == reload_atom['chain_id']
                assert orig_atom['res_name'] == reload_atom['res_name']
                assert orig_atom['res_seq'] == reload_atom['res_seq']


@pytest.mark.integration
class TestPDBIntegration:
    """Integration tests for PDB parser."""

    def test_load_and_write_workflow(self, tmp_path):
        """Test complete load->modify->write workflow."""
        from molvis_core.formats import load_structure, write_structure

        # Create initial file
        input_file = tmp_path / "input.pdb"
        input_file.write_text("""HEADER    TEST
ATOM      1  CA  ALA A   1       0.000   0.000   0.000  1.00 20.00           C
ATOM      2  CB  ALA A   1       1.000   0.000   0.000  1.00 25.00           C
END
""")

        # Load
        molecules = load_structure(input_file)
        assert len(molecules) == 1

        # Modify coordinates
        molecules[0].coords += 5.0

        # Write
        output_file = tmp_path / "output.pdb"
        write_structure(molecules, output_file)

        # Verify
        reloaded = load_structure(output_file)
        np.testing.assert_array_almost_equal(
            reloaded[0].coords[0],
            [5.0, 5.0, 5.0],
            decimal=3
        )

    def test_format_auto_detection(self, tmp_path):
        """Test that PDB format is auto-detected."""
        from molvis_core.formats import FormatDetector

        pdb_file = tmp_path / "test.pdb"
        pdb_file.write_text("ATOM      1  CA  ALA A   1       0.000   0.000   0.000\n")

        # Test extension detection
        format_ext = FormatDetector.detect_from_extension(pdb_file)
        assert format_ext == 'pdb'

        # Test content detection
        format_content = FormatDetector.detect_from_content(pdb_file)
        assert format_content == 'pdb'

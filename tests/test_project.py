"""
Unit tests for molvis_core.project module.

Tests project serialization, saving, loading, and management.
"""

import json
from pathlib import Path

import numpy as np
import pytest

from molvis_core.exceptions import FileFormatError, FileParseError
from molvis_core.molecule import Molecule
from molvis_core.project import Project, create_backup, get_auto_save_path


@pytest.fixture
def water_molecule():
    """Create a water molecule for testing."""
    symbols = ['O', 'H', 'H']
    coords = np.array([
        [0.0, 0.0, 0.119262],
        [0.0, 0.763239, -0.477047],
        [0.0, -0.763239, -0.477047]
    ])
    return Molecule(
        id=1,
        name="Water",
        symbols=symbols,
        coords=coords,
        bonds=[(0, 1), (0, 2)]
    )


@pytest.fixture
def benzene_molecule():
    """Create a benzene molecule for testing."""
    symbols = ['C'] * 6 + ['H'] * 6
    coords = np.array([
        [0.0, 1.3968, 0.0],
        [1.2097, 0.6984, 0.0],
        [1.2097, -0.6984, 0.0],
        [0.0, -1.3968, 0.0],
        [-1.2097, -0.6984, 0.0],
        [-1.2097, 0.6984, 0.0],
        [0.0, 2.4788, 0.0],
        [2.1467, 1.2404, 0.0],
        [2.1467, -1.2404, 0.0],
        [0.0, -2.4788, 0.0],
        [-2.1467, -1.2404, 0.0],
        [-2.1467, 1.2404, 0.0],
    ])
    bonds = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0)]  # Ring bonds
    return Molecule(
        id=2,
        name="Benzene",
        symbols=symbols,
        coords=coords,
        bonds=bonds
    )


class TestProject:
    """Tests for Project class."""

    @pytest.mark.unit
    def test_create_empty_project(self):
        """Test creating an empty project."""
        project = Project(name="Test Project")

        assert project.name == "Test Project"
        assert len(project.molecules) == 0
        assert project.file_path is None
        assert project.version == "1.0"

    @pytest.mark.unit
    def test_create_project_with_molecules(self, water_molecule, benzene_molecule):
        """Test creating project with molecules."""
        project = Project(
            name="Multi-Molecule Project",
            molecules=[water_molecule, benzene_molecule]
        )

        assert len(project.molecules) == 2
        assert project.molecules[0].name == "Water"
        assert project.molecules[1].name == "Benzene"

    @pytest.mark.unit
    def test_add_molecule(self, water_molecule):
        """Test adding molecule to project."""
        project = Project(name="Test")
        project.add_molecule(water_molecule)

        assert len(project.molecules) == 1
        assert project.molecules[0].name == "Water"

    @pytest.mark.unit
    def test_remove_molecule(self, water_molecule, benzene_molecule):
        """Test removing molecule from project."""
        project = Project(name="Test", molecules=[water_molecule, benzene_molecule])

        # Remove water
        removed = project.remove_molecule(1)

        assert removed is True
        assert len(project.molecules) == 1
        assert project.molecules[0].name == "Benzene"

    @pytest.mark.unit
    def test_remove_nonexistent_molecule(self, water_molecule):
        """Test removing non-existent molecule."""
        project = Project(name="Test", molecules=[water_molecule])

        removed = project.remove_molecule(999)

        assert removed is False
        assert len(project.molecules) == 1

    @pytest.mark.unit
    def test_get_molecule(self, water_molecule, benzene_molecule):
        """Test getting molecule by ID."""
        project = Project(name="Test", molecules=[water_molecule, benzene_molecule])

        mol = project.get_molecule(1)
        assert mol is not None
        assert mol.name == "Water"

        mol = project.get_molecule(2)
        assert mol is not None
        assert mol.name == "Benzene"

        mol = project.get_molecule(999)
        assert mol is None

    @pytest.mark.unit
    def test_serialize_deserialize(self, water_molecule):
        """Test serialization and deserialization."""
        project = Project(name="Serialization Test", molecules=[water_molecule])

        # Serialize
        data = project.to_dict()

        assert data["name"] == "Serialization Test"
        assert len(data["molecules"]) == 1
        assert data["molecules"][0]["name"] == "Water"

        # Deserialize
        restored_project = Project.from_dict(data)

        assert restored_project.name == "Serialization Test"
        assert len(restored_project.molecules) == 1
        assert restored_project.molecules[0].name == "Water"

        # Check coordinates are preserved
        np.testing.assert_array_almost_equal(
            restored_project.molecules[0].coords,
            water_molecule.coords
        )

    @pytest.mark.unit
    def test_serialize_with_transformations(self, water_molecule):
        """Test serialization preserves transformations."""
        # Apply transformation
        water_molecule.final_translation = np.array([1.0, 2.0, 3.0])
        water_molecule.apply_final_transformation()

        project = Project(name="Transform Test", molecules=[water_molecule])

        # Serialize and deserialize
        data = project.to_dict()
        restored_project = Project.from_dict(data)

        # Check transformation is preserved
        restored_mol = restored_project.molecules[0]
        np.testing.assert_array_almost_equal(
            restored_mol.final_translation,
            np.array([1.0, 2.0, 3.0])
        )

    @pytest.mark.unit
    def test_save_project(self, water_molecule, tmp_path):
        """Test saving project to file."""
        project = Project(name="Save Test", molecules=[water_molecule])
        save_path = tmp_path / "test_project.molman"

        project.save(save_path)

        assert save_path.exists()

        # Verify JSON structure
        with save_path.open("r") as f:
            data = json.load(f)

        assert data["name"] == "Save Test"
        assert len(data["molecules"]) == 1

    @pytest.mark.unit
    def test_load_project(self, water_molecule, tmp_path):
        """Test loading project from file."""
        # Create and save project
        original_project = Project(name="Load Test", molecules=[water_molecule])
        save_path = tmp_path / "test_project.molman"
        original_project.save(save_path)

        # Load it back
        loaded_project = Project.load(save_path)

        assert loaded_project.name == "Load Test"
        assert len(loaded_project.molecules) == 1
        assert loaded_project.molecules[0].name == "Water"
        assert loaded_project.file_path == save_path

    @pytest.mark.unit
    def test_save_load_roundtrip(self, water_molecule, benzene_molecule, tmp_path):
        """Test complete save/load roundtrip."""
        # Create project with multiple molecules and transformations
        water_molecule.final_translation = np.array([5.0, 0.0, 0.0])
        water_molecule.apply_final_transformation()

        original = Project(
            name="Roundtrip Test",
            molecules=[water_molecule, benzene_molecule],
            metadata={"description": "Test project"}
        )

        save_path = tmp_path / "roundtrip.molman"
        original.save(save_path)

        # Load and verify
        loaded = Project.load(save_path)

        assert loaded.name == original.name
        assert len(loaded.molecules) == len(original.molecules)
        assert loaded.metadata["description"] == "Test project"

        # Verify transformations
        np.testing.assert_array_almost_equal(
            loaded.molecules[0].final_translation,
            water_molecule.final_translation
        )

    @pytest.mark.unit
    def test_load_nonexistent_file(self, tmp_path):
        """Test loading non-existent file raises error."""
        nonexistent_path = tmp_path / "nonexistent.molman"

        with pytest.raises(FileNotFoundError):
            Project.load(nonexistent_path)

    @pytest.mark.unit
    def test_load_invalid_json(self, tmp_path):
        """Test loading invalid JSON raises error."""
        invalid_path = tmp_path / "invalid.molman"
        with invalid_path.open("w") as f:
            f.write("{ invalid json")

        with pytest.raises(FileFormatError):
            Project.load(invalid_path)

    @pytest.mark.unit
    def test_export_xyz(self, water_molecule, benzene_molecule, tmp_path):
        """Test exporting project to XYZ format."""
        project = Project(name="Export Test", molecules=[water_molecule, benzene_molecule])
        export_path = tmp_path / "exported.xyz"

        project.export_xyz(export_path)

        assert export_path.exists()

        # Verify content
        content = export_path.read_text()
        assert "Water" in content
        assert "Benzene" in content
        # Check atom counts are present
        assert "3\n" in content  # Water has 3 atoms
        assert "12\n" in content  # Benzene has 12 atoms

    @pytest.mark.unit
    def test_project_repr(self, water_molecule):
        """Test project string representation."""
        project = Project(name="Repr Test", molecules=[water_molecule])
        project.file_path = Path("/path/to/test.molman")

        repr_str = repr(project)

        assert "Repr Test" in repr_str
        assert "molecules=1" in repr_str
        assert "test.molman" in repr_str

    @pytest.mark.unit
    def test_create_backup(self, water_molecule, tmp_path):
        """Test creating project backup."""
        project = Project(name="Backup Test", molecules=[water_molecule])
        project_path = tmp_path / "test.molman"
        project.save(project_path)

        # Create backup
        backup_path = create_backup(project_path)

        assert backup_path.exists()
        assert "_autosave" not in backup_path.name or backup_path.parent.name == ".molman_backups"

    @pytest.mark.unit
    def test_get_auto_save_path_with_file(self, water_molecule, tmp_path):
        """Test getting auto-save path for saved project."""
        project = Project(name="AutoSave Test", molecules=[water_molecule])
        project.file_path = tmp_path / "test.molman"

        autosave_path = get_auto_save_path(project)

        assert autosave_path.parent == tmp_path
        assert "_autosave" in autosave_path.name

    @pytest.mark.unit
    def test_get_auto_save_path_without_file(self):
        """Test getting auto-save path for unsaved project."""
        project = Project(name="Unsaved Project")

        autosave_path = get_auto_save_path(project)

        assert autosave_path.parent.name == "autosaves"
        assert "_autosave" in autosave_path.name


class TestProjectEdgeCases:
    """Edge case tests for Project class."""

    @pytest.mark.unit
    def test_empty_project_serialization(self):
        """Test serializing empty project."""
        project = Project(name="Empty")
        data = project.to_dict()

        assert data["name"] == "Empty"
        assert len(data["molecules"]) == 0

        # Should be able to deserialize
        restored = Project.from_dict(data)
        assert restored.name == "Empty"
        assert len(restored.molecules) == 0

    @pytest.mark.unit
    def test_project_with_metadata(self):
        """Test project with custom metadata."""
        metadata = {
            "author": "Test User",
            "description": "Test Description",
            "tags": ["test", "example"],
        }

        project = Project(name="Metadata Test", metadata=metadata)
        data = project.to_dict()

        assert data["metadata"]["author"] == "Test User"
        assert "tags" in data["metadata"]

        # Verify after deserialization
        restored = Project.from_dict(data)
        assert restored.metadata["author"] == "Test User"

    @pytest.mark.unit
    def test_multiple_save_locations(self, water_molecule, tmp_path):
        """Test saving to different locations."""
        project = Project(name="Multi-Save", molecules=[water_molecule])

        # Save to first location
        path1 = tmp_path / "location1" / "project.molman"
        path1.parent.mkdir()
        project.save(path1)
        assert path1.exists()

        # Save to second location
        path2 = tmp_path / "location2" / "project.molman"
        path2.parent.mkdir()
        project.save(path2)
        assert path2.exists()

        # Both should have same content
        with path1.open() as f1, path2.open() as f2:
            data1 = json.load(f1)
            data2 = json.load(f2)

        assert data1["name"] == data2["name"]

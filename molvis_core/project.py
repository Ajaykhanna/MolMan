"""
Project management for MolMan.

This module handles project serialization, saving, and loading of complete
workspaces including molecules, transformations, and project settings.

Project files use the .molman extension and are stored as JSON.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np

from .logging_config import get_logger
from .molecule import Molecule
from .config import get_config_manager
from .exceptions import (
    FileFormatError,
    FileParseError,
    InvalidConfigError,
)

# Initialize logger
logger = get_logger(__name__)

# Project file version
PROJECT_VERSION = "1.0"


class Project:
    """
    Represents a MolMan project containing molecules and settings.

    A project can be saved to a .molman file and loaded later, preserving
    all molecules, transformations, and project-specific settings.
    """

    def __init__(
        self,
        name: str = "Untitled Project",
        molecules: Optional[List[Molecule]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a new project.

        Args:
            name: Project name
            molecules: List of Molecule objects
            metadata: Additional project metadata
        """
        self.name = name
        self.molecules = molecules or []
        self.metadata = metadata or {}
        self.file_path: Optional[Path] = None

        # Project metadata
        self.created = self.metadata.get("created", datetime.now().isoformat())
        self.last_modified = datetime.now().isoformat()
        self.version = PROJECT_VERSION

        logger.info(f"Created new project: {self.name}")

    def add_molecule(self, molecule: Molecule) -> None:
        """
        Add a molecule to the project.

        Args:
            molecule: Molecule instance to add
        """
        self.molecules.append(molecule)
        self.last_modified = datetime.now().isoformat()
        logger.info(f"Added molecule '{molecule.name}' to project '{self.name}'")

    def remove_molecule(self, molecule_id: int) -> bool:
        """
        Remove a molecule from the project by ID.

        Args:
            molecule_id: ID of molecule to remove

        Returns:
            True if removed, False if not found
        """
        for i, mol in enumerate(self.molecules):
            if mol.id == molecule_id:
                removed_name = mol.name
                self.molecules.pop(i)
                self.last_modified = datetime.now().isoformat()
                logger.info(f"Removed molecule '{removed_name}' from project '{self.name}'")
                return True
        logger.warning(f"Molecule with ID {molecule_id} not found in project")
        return False

    def get_molecule(self, molecule_id: int) -> Optional[Molecule]:
        """
        Get a molecule by ID.

        Args:
            molecule_id: ID of molecule to retrieve

        Returns:
            Molecule instance or None if not found
        """
        for mol in self.molecules:
            if mol.id == molecule_id:
                return mol
        return None

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize project to dictionary for JSON storage.

        Returns:
            Dictionary representation of project
        """
        logger.debug(f"Serializing project '{self.name}' with {len(self.molecules)} molecules")

        return {
            "version": self.version,
            "name": self.name,
            "created": self.created,
            "last_modified": self.last_modified,
            "metadata": self.metadata,
            "molecules": [self._serialize_molecule(mol) for mol in self.molecules],
        }

    @staticmethod
    def _serialize_molecule(molecule: Molecule) -> Dict[str, Any]:
        """
        Serialize a molecule to dictionary.

        Args:
            molecule: Molecule to serialize

        Returns:
            Dictionary representation of molecule
        """
        return {
            "id": molecule.id,
            "name": molecule.name,
            "symbols": molecule.symbols,
            "coords": molecule.coords.tolist(),  # Convert numpy to list
            "bonds": molecule.bonds,
            "source_file_index": molecule.source_file_index,
            "source_file_name": molecule.source_file_name,
            "final_translation": molecule.final_translation.tolist(),
            "final_rotation_matrix": molecule.final_rotation_matrix.tolist(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Project":
        """
        Deserialize project from dictionary.

        Args:
            data: Dictionary containing project data

        Returns:
            Project instance

        Raises:
            FileFormatError: If data format is invalid
        """
        try:
            logger.debug(f"Deserializing project: {data.get('name', 'Unknown')}")

            # Extract basic project info
            name = data.get("name", "Untitled Project")
            metadata = data.get("metadata", {})
            metadata["created"] = data.get("created")

            # Deserialize molecules
            molecules = []
            for mol_data in data.get("molecules", []):
                mol = cls._deserialize_molecule(mol_data)
                molecules.append(mol)

            # Create project
            project = cls(name=name, molecules=molecules, metadata=metadata)
            project.version = data.get("version", PROJECT_VERSION)
            project.last_modified = data.get("last_modified", datetime.now().isoformat())

            logger.info(f"Deserialized project '{name}' with {len(molecules)} molecules")
            return project

        except Exception as e:
            logger.error(f"Failed to deserialize project: {e}")
            raise FileFormatError("project data", f"Invalid project format: {e}")

    @staticmethod
    def _deserialize_molecule(data: Dict[str, Any]) -> Molecule:
        """
        Deserialize a molecule from dictionary.

        Args:
            data: Dictionary containing molecule data

        Returns:
            Molecule instance
        """
        # Convert lists back to numpy arrays
        coords = np.array(data["coords"])
        final_translation = np.array(data["final_translation"])
        final_rotation_matrix = np.array(data["final_rotation_matrix"])

        # Create molecule
        mol = Molecule(
            id=data["id"],
            name=data["name"],
            symbols=data["symbols"],
            coords=coords,
            bonds=data["bonds"],
            source_file_index=data.get("source_file_index"),
            source_file_name=data.get("source_file_name"),
        )

        # Restore transformation state
        mol.final_translation = final_translation
        mol.final_rotation_matrix = final_rotation_matrix
        mol.apply_final_transformation()

        return mol

    def save(self, file_path: Optional[Path] = None) -> None:
        """
        Save project to a .molman file.

        Args:
            file_path: Path to save file (uses self.file_path if None)

        Raises:
            ValueError: If no file path specified
            FileParseError: If save fails
        """
        if file_path is None:
            if self.file_path is None:
                raise ValueError("No file path specified for save")
            file_path = self.file_path
        else:
            self.file_path = file_path

        logger.info(f"Saving project '{self.name}' to {file_path}")

        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Update modification time
            self.last_modified = datetime.now().isoformat()

            # Serialize and save
            with file_path.open("w") as f:
                json.dump(self.to_dict(), f, indent=2)

            # Add to recent files
            config = get_config_manager()
            config.add_recent_file(file_path)

            logger.info(f"Project saved successfully to {file_path}")

        except Exception as e:
            logger.error(f"Failed to save project: {e}")
            raise FileParseError(str(file_path), 0, f"Failed to save project: {e}")

    @classmethod
    def load(cls, file_path: Path) -> "Project":
        """
        Load a project from a .molman file.

        Args:
            file_path: Path to .molman file

        Returns:
            Project instance

        Raises:
            FileNotFoundError: If file doesn't exist
            FileFormatError: If file format is invalid
            FileParseError: If parsing fails
        """
        logger.info(f"Loading project from {file_path}")

        if not file_path.exists():
            logger.error(f"Project file not found: {file_path}")
            raise FileNotFoundError(f"Project file not found: {file_path}")

        try:
            with file_path.open("r") as f:
                data = json.load(f)

            # Deserialize project
            project = cls.from_dict(data)
            project.file_path = file_path

            # Add to recent files
            config = get_config_manager()
            config.add_recent_file(file_path)

            logger.info(f"Project loaded successfully from {file_path}")
            return project

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse project file: {e}")
            raise FileFormatError(str(file_path), f"Invalid JSON format: {e}")
        except Exception as e:
            logger.error(f"Failed to load project: {e}")
            raise FileParseError(str(file_path), 0, f"Failed to load project: {e}")

    def export_xyz(self, output_path: Path) -> None:
        """
        Export all molecules to a multi-block XYZ file.

        Args:
            output_path: Path for output XYZ file
        """
        from .io import format_xyz_string

        logger.info(f"Exporting project to XYZ: {output_path}")

        try:
            with output_path.open("w") as f:
                for mol in self.molecules:
                    # Use transformed coordinates
                    xyz_str = format_xyz_string(
                        symbols=mol.symbols,
                        coords=mol.transformed_coords,
                        comment=f"{mol.name} (from project: {self.name})",
                    )
                    f.write(xyz_str)
                    f.write("\n")  # Extra line between molecules

            logger.info(f"Exported {len(self.molecules)} molecules to {output_path}")

        except Exception as e:
            logger.error(f"Failed to export to XYZ: {e}")
            raise FileParseError(str(output_path), 0, f"Failed to export: {e}")

    def __repr__(self) -> str:
        """String representation of project."""
        return f"Project(name='{self.name}', molecules={len(self.molecules)}, file={self.file_path})"


def create_backup(project_path: Path) -> Path:
    """
    Create a backup of a project file.

    Args:
        project_path: Path to project file

    Returns:
        Path to backup file

    Raises:
        FileParseError: If backup fails
    """
    logger.info(f"Creating backup of {project_path}")

    try:
        backup_dir = project_path.parent / ".molman_backups"
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{project_path.stem}_{timestamp}.molman"
        backup_path = backup_dir / backup_name

        # Copy file
        import shutil
        shutil.copy2(project_path, backup_path)

        logger.info(f"Backup created: {backup_path}")
        return backup_path

    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        raise FileParseError(str(project_path), 0, f"Failed to create backup: {e}")


def get_auto_save_path(project: Project) -> Path:
    """
    Get the auto-save path for a project.

    Args:
        project: Project instance

    Returns:
        Path for auto-save file
    """
    if project.file_path:
        return project.file_path.parent / f".{project.file_path.stem}_autosave.molman"
    else:
        # Use temp directory if project not saved yet
        from pathlib import Path
        temp_dir = Path.home() / ".molman" / "autosaves"
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir / f"{project.name}_autosave.molman"

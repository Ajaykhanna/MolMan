"""
XYZ file format parser.

The XYZ format is a simple text-based format for molecular structures:

Format:
    Line 1: Number of atoms
    Line 2: Comment line (optional)
    Lines 3+: Element X Y Z (one atom per line)

Example:
    3
    Water molecule
    O  0.000  0.000  0.000
    H  0.757  0.586  0.000
    H -0.757  0.586  0.000
"""

from pathlib import Path
from typing import Any, List

import numpy as np

from molvis_core.exceptions import (
    EmptyFileError,
    FileNotFoundError,
    FileParseError,
)
from molvis_core.formats.base import FileFormatBase
from molvis_core.logging_config import get_logger
from molvis_core.molecule import Molecule

logger = get_logger(__name__)


class XYZParser(FileFormatBase):
    """Parser for XYZ format files.

    The XYZ format is one of the simplest molecular file formats, containing
    only atomic symbols and Cartesian coordinates.
    """

    format_name = "XYZ"
    extensions = [".xyz"]
    supports_multiple = True  # Can contain multiple structures

    def parse(self, file_path: Path) -> List[Molecule]:
        """Parse an XYZ file and return Molecule objects.

        Args:
            file_path: Path to the XYZ file

        Returns:
            List of Molecule objects (one per structure in file)

        Raises:
            FileNotFoundError: If the file doesn't exist
            EmptyFileError: If the file is empty
            FileParseError: If parsing fails
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(str(file_path))

        logger.debug(f"Parsing XYZ file: {file_path}")

        try:
            with open(file_path, 'r') as f:
                lines = [line.strip() for line in f if line.strip()]

            if not lines:
                raise EmptyFileError(str(file_path))

            molecules = []
            line_idx = 0

            while line_idx < len(lines):
                # Parse one molecule
                molecule, lines_consumed = self._parse_single_molecule(
                    lines[line_idx:], line_idx, str(file_path)
                )
                molecules.append(molecule)
                line_idx += lines_consumed

            if not molecules:
                raise EmptyFileError(str(file_path))

            logger.info(
                f"Successfully parsed {len(molecules)} molecule(s) from {file_path}"
            )
            return molecules

        except (EmptyFileError, FileParseError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error parsing XYZ file: {e}")
            raise FileParseError(str(file_path), 0, str(e))

    def _parse_single_molecule(
        self, lines: List[str], offset: int, filepath: str
    ) -> tuple:
        """Parse a single molecule from XYZ lines.

        Args:
            lines: List of lines to parse (starting with atom count)
            offset: Line number offset for error reporting
            filepath: File path for error messages

        Returns:
            Tuple of (Molecule object, number of lines consumed)

        Raises:
            FileParseError: If parsing fails
        """
        if not lines:
            raise FileParseError(filepath, offset + 1, "Unexpected end of file")

        # Line 1: Number of atoms
        try:
            num_atoms = int(lines[0])
        except ValueError:
            raise FileParseError(
                filepath,
                offset + 1,
                f"Expected atom count, got: '{lines[0]}'"
            )

        if num_atoms <= 0:
            raise FileParseError(
                filepath,
                offset + 1,
                f"Invalid atom count: {num_atoms}"
            )

        # Line 2: Comment (optional)
        comment = lines[1] if len(lines) > 1 else ""

        # Lines 3+: Atoms
        if len(lines) < num_atoms + 2:
            raise FileParseError(
                filepath,
                offset + 1,
                f"Expected {num_atoms} atoms, but file ended prematurely"
            )

        symbols = []
        coords = []

        for i in range(num_atoms):
            line_num = offset + i + 3  # +1 for 1-indexing, +2 for count+comment
            atom_line = lines[i + 2]

            try:
                parts = atom_line.split()
                if len(parts) < 4:
                    raise FileParseError(
                        filepath,
                        line_num,
                        f"Expected 'Element X Y Z', got: '{atom_line}'"
                    )

                symbol = parts[0]
                x, y, z = float(parts[1]), float(parts[2]), float(parts[3])

                symbols.append(symbol)
                coords.append([x, y, z])

            except (ValueError, IndexError) as e:
                raise FileParseError(
                    filepath,
                    line_num,
                    f"Invalid atom line '{atom_line}': {e}"
                )

        # Create Molecule
        # Generate a simple ID based on line position
        mol_id = offset // 100 + 1

        # Extract name from comment if available, otherwise use default
        mol_name = comment if comment else f"Molecule_{mol_id}"

        molecule = Molecule(
            id=mol_id,
            name=mol_name,
            symbols=symbols,
            coords=np.array(coords, dtype=float),
            bonds=[]  # Bonds are not stored in XYZ format
        )

        # Store comment as metadata
        if comment:
            molecule.metadata = {'comment': comment}

        lines_consumed = num_atoms + 2
        return molecule, lines_consumed

    def write(self, molecules: List[Molecule], file_path: Path, **kwargs) -> None:
        """Write molecule(s) to an XYZ file.

        Args:
            molecules: List of Molecule objects to write
            file_path: Path where the file should be written
            **kwargs: Optional arguments:
                - comments: List of comment strings (one per molecule)
                - precision: Number of decimal places (default: 6)

        Raises:
            FileIOError: If writing fails
        """
        file_path = Path(file_path)
        comments = kwargs.get('comments', [])
        precision = kwargs.get('precision', 6)

        logger.debug(f"Writing {len(molecules)} molecule(s) to {file_path}")

        try:
            with open(file_path, 'w') as f:
                for idx, molecule in enumerate(molecules):
                    # Get comment from metadata or provided list
                    if idx < len(comments):
                        comment = comments[idx]
                    elif hasattr(molecule, 'metadata') and 'comment' in molecule.metadata:
                        comment = molecule.metadata['comment']
                    else:
                        comment = f"Molecule {idx + 1}"

                    # Write molecule
                    f.write(f"{len(molecule.symbols)}\n")
                    f.write(f"{comment}\n")

                    for symbol, coord in zip(molecule.symbols, molecule.coords):
                        x, y, z = coord
                        f.write(
                            f"{symbol:2s} {x:{precision+5}.{precision}f} "
                            f"{y:{precision+5}.{precision}f} "
                            f"{z:{precision+5}.{precision}f}\n"
                        )

            logger.info(f"Successfully wrote XYZ file: {file_path}")

        except Exception as e:
            from molvis_core.exceptions import FileIOError
            logger.error(f"Error writing XYZ file: {e}")
            raise FileIOError(f"Failed to write XYZ file: {e}")

    def validate(self, file_path: Path) -> bool:
        """Validate that a file is a valid XYZ file.

        Args:
            file_path: Path to the file to validate

        Returns:
            True if the file is valid XYZ format
        """
        try:
            # Try to parse it
            self.parse(file_path)
            return True
        except Exception:
            return False

    def get_metadata_schema(self) -> dict:
        """Return the metadata schema for XYZ format.

        Returns:
            Dictionary of metadata fields
        """
        return {
            'comment': str,
        }

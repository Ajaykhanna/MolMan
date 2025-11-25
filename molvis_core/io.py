"""
molvis_core/io.py

Handles file input/output operations, specifically for XYZ format,
and provides functions for generating example structures.
"""

import numpy as np
from pathlib import Path
import sys
from typing import List, Tuple, Optional

from .logging_config import get_logger
from .exceptions import (
    FileNotFoundError as MolManFileNotFoundError,
    FileFormatError,
    FileParseError,
    EmptyFileError,
    AtomCountMismatchError,
    InvalidCoordinatesError,
)

# Use relative import within the package
try:
    from .constants import DEFAULT_BENZENE_DISTANCE
except ImportError:
    # Fallback for running as script? Or assume it's used as module.
    print("Warning: Could not perform relative import in io.py", file=sys.stderr)
    DEFAULT_BENZENE_DISTANCE = 3.0

# Initialize logger for this module
logger = get_logger(__name__)


# --- Benzene Definition --- (Content same as before)
BENZENE_SYMBOLS = ["C", "C", "C", "C", "C", "C", "H", "H", "H", "H", "H", "H"]
BENZENE_COORDS = np.array(
    [
        [0.0000, 1.3968, 0.0000],
        [1.2097, 0.6984, 0.0000],
        [1.2097, -0.6984, 0.0000],
        [0.0000, -1.3968, 0.0000],
        [-1.2097, -0.6984, 0.0000],
        [-1.2097, 0.6984, 0.0000],
        [0.0000, 2.4788, 0.0000],
        [2.1467, 1.2404, 0.0000],
        [2.1467, -1.2404, 0.0000],
        [0.0000, -2.4788, 0.0000],
        [-2.1467, -1.2404, 0.0000],
        [-2.1467, 1.2404, 0.0000],
    ]
)


def create_two_benzenes(
    distance: float = DEFAULT_BENZENE_DISTANCE,
) -> Tuple[List[str], np.ndarray, List[Tuple[int, int]]]:
    """
    Generates symbols, coordinates, and molecule boundary indices for two
    benzene molecules separated along the X-axis.

    Args:
        distance: The separation distance between the centroids of the two
                  benzene rings along the X-axis (in Angstroms). Defaults to
                  DEFAULT_BENZENE_DISTANCE from constants.

    Returns:
        A tuple containing:
        - all_symbols (List[str]): Combined list (24 atoms).
        - all_coords (np.ndarray): Combined (24, 3) array of coordinates.
        - molecule_boundaries (List[Tuple[int, int]]): List indicating start and
          end indices (exclusive) for each molecule, e.g., [(0, 12), (12, 24)].
    """
    symbols1 = BENZENE_SYMBOLS[:]
    coords1 = BENZENE_COORDS.copy()
    symbols2 = BENZENE_SYMBOLS[:]
    coords2 = BENZENE_COORDS.copy()
    shift_vector = np.array([distance, 0.0, 0.0])
    coords2 += shift_vector
    all_symbols = symbols1 + symbols2
    all_coords = np.vstack((coords1, coords2))
    num_atoms_per = len(BENZENE_SYMBOLS)
    molecule_boundaries = [(0, num_atoms_per), (num_atoms_per, 2 * num_atoms_per)]
    logger.info(f"Generated two benzenes separated by {distance} Å")
    return all_symbols, all_coords, molecule_boundaries


def load_xyz(file_path: Path) -> Tuple[Optional[List[str]], Optional[np.ndarray]]:
    """
    Loads atom symbols and coordinates from a standard XYZ file path.

    Args:
        file_path: Path to the XYZ file

    Returns:
        Tuple of (symbols list, coordinates array) or (None, None) on error

    Raises:
        MolManFileNotFoundError: If file doesn't exist
        EmptyFileError: If file is empty
        FileFormatError: If file format is invalid
        FileParseError: If parsing fails
    """
    logger.debug(f"Loading XYZ file: {file_path}")

    if not file_path.is_file():
        logger.error(f"File not found: {file_path}")
        raise MolManFileNotFoundError(str(file_path))

    try:
        with file_path.open("r") as file:
            lines = file.readlines()
            if not lines:
                logger.error(f"File is empty: {file_path}")
                raise EmptyFileError(str(file_path))

            try:
                atom_count = int(lines[0].strip())
                logger.debug(f"Expected atom count from header: {atom_count}")
            except ValueError as e:
                logger.error(
                    f"Invalid atom count in {file_path}: '{lines[0].strip()}'"
                )
                raise FileFormatError(
                    str(file_path),
                    f"First line must be an integer (atom count), found: '{lines[0].strip()}'",
                )
            if len(lines) < 2:
                logger.error(
                    f"File {file_path} must have at least 2 lines (count and comment/coords)"
                )
                raise FileFormatError(
                    str(file_path),
                    "File must have at least 2 lines (count and comment/coords)",
                )

            coord_lines = lines[2:]
            symbols: List[str] = []
            coords_list: List[List[float]] = []
            actual_atom_count = 0

            for i, line in enumerate(coord_lines):
                if actual_atom_count >= atom_count:
                    if i < len(coord_lines) and line.strip():
                        logger.warning(
                            f"Stopped reading {file_path.name} at line {i+3} "
                            f"(header count {atom_count} reached)"
                        )
                    break

                parts = line.strip().split()
                if not parts:
                    continue

                if len(parts) < 4:
                    logger.warning(
                        f"Line {i+3} in {file_path.name} malformed "
                        f"(expected Symbol X Y Z): '{line.strip()}'. Skipping"
                    )
                    continue

                try:
                    symbols.append(parts[0])
                    coords_list.append(list(map(float, parts[1:4])))
                    actual_atom_count += 1
                except ValueError as e:
                    logger.warning(
                        f"Error parsing coordinates at line {i+3} "
                        f"in {file_path.name}: {e}. Skipping"
                    )
                    continue

            if actual_atom_count == 0 and atom_count > 0:
                logger.error(f"No valid coordinate lines found in {file_path.name}")
                raise EmptyFileError(str(file_path))

            if actual_atom_count != atom_count:
                logger.warning(
                    f"Found {actual_atom_count} atoms in {file_path.name}, "
                    f"but header specified {atom_count}"
                )

            logger.info(
                f"Successfully loaded {actual_atom_count} atoms from {file_path.name}"
            )
            return symbols, np.array(coords_list)

    except (MolManFileNotFoundError, EmptyFileError, FileFormatError, FileParseError):
        # Re-raise our custom exceptions
        raise
    except ValueError as e:
        logger.error(f"Error reading {file_path.name}: {e}")
        raise FileFormatError(str(file_path), str(e))
    except Exception as e:
        logger.error(f"Unexpected error reading {file_path.name}: {e}")
        raise FileParseError(str(file_path), 0, str(e))


def load_xyz_from_text(
    xyz_text: str, source_name: str = "Input Text"
) -> Tuple[Optional[List[str]], Optional[np.ndarray]]:
    """
    Loads atom symbols and coordinates from XYZ file content provided as text
    (assumes text contains *only one* molecule definition).

    Args:
        xyz_text: String containing the XYZ file content for one molecule.
        source_name: Identifier for the source (e.g., "Pasted Text", filename).

    Returns:
        A tuple containing (list of symbols, NumPy array of coordinates N x 3)
        if successful, otherwise (None, None). Errors/warnings are printed to stderr.

    Raises:
        EmptyFileError: If the text is empty
        FileFormatError: If the text format is invalid
        FileParseError: If parsing fails
    """
    logger.debug(f"Parsing XYZ text from source: {source_name}")

    symbols: List[str] = []
    coords_list: List[List[float]] = []
    lines = xyz_text.strip().splitlines()

    if not lines:
        logger.error(f"Input source '{source_name}' is empty")
        raise EmptyFileError(source_name)

    try:
        atom_count_str = lines[0].strip()
        atom_count = int(atom_count_str)
        logger.debug(f"Expected atom count from {source_name}: {atom_count}")
    except (ValueError, IndexError) as e:
        logger.error(
            f"First line of '{source_name}' must be number of atoms, got: {lines[0] if lines else 'empty'}"
        )
        raise FileFormatError(
            source_name, "First line must be number of atoms"
        )

    if len(lines) < 2:
        logger.error(f"'{source_name}' must have at least 2 lines")
        raise FileFormatError(
            source_name, "Must have at least 2 lines"
        )
    coord_lines = lines[2:]
    actual_atom_count = 0

    for i, line in enumerate(coord_lines):
        if actual_atom_count >= atom_count:
            if i < len(coord_lines) and line.strip():
                logger.warning(
                    f"'{source_name}': Stopped reading at line {i+3} "
                    f"(header count {atom_count} reached)"
                )
            break

        parts = line.strip().split()
        if not parts:
            continue

        if len(parts) < 4:
            logger.warning(
                f"'{source_name}' Line {i+3} malformed: '{line.strip()}'. Skipping"
            )
            continue

        try:
            symbols.append(parts[0])
            coords_list.append(list(map(float, parts[1:4])))
            actual_atom_count += 1
        except ValueError as e:
            logger.warning(
                f"'{source_name}' Error parsing coords line {i+3}: {e}. Skipping"
            )
            continue

    if actual_atom_count == 0 and atom_count > 0:
        logger.error(f"'{source_name}': No valid coordinate lines found")
        raise EmptyFileError(source_name)

    if actual_atom_count != atom_count:
        logger.warning(
            f"'{source_name}': Found {actual_atom_count} atoms, header said {atom_count}"
        )

    logger.info(f"Successfully parsed {actual_atom_count} atoms from {source_name}")
    return symbols, np.array(coords_list)


# --- NEW Function ---
def load_multiple_xyz_from_text(
    xyz_multiblock_text: str, source_name: str = "Pasted Text"
) -> List[Tuple[List[str], np.ndarray]]:
    """
    Loads multiple concatenated XYZ blocks from a single string.

    Parses the text sequentially, identifying blocks by the integer atom count
    on the first line of each block. Skips malformed blocks.

    Args:
        xyz_multiblock_text: String containing one or more concatenated XYZ blocks.
        source_name: Base identifier for naming parsed molecules if needed later
                     (e.g., "Pasted").

    Returns:
        A list of tuples, where each tuple is (symbols, coords_array) for one
        successfully parsed molecule block. Returns an empty list if no valid
        blocks are found or the input is empty.
    """
    logger.debug(f"Parsing multiple XYZ blocks from {source_name}")

    parsed_molecules: List[Tuple[List[str], np.ndarray]] = []
    lines = xyz_multiblock_text.strip().splitlines()
    total_lines = len(lines)
    current_line_index = 0
    block_num = 0

    while current_line_index < total_lines:
        # Skip blank lines between blocks
        while (
            current_line_index < total_lines and not lines[current_line_index].strip()
        ):
            current_line_index += 1
        if current_line_index >= total_lines:
            break  # End of text

        block_num += 1
        start_line_num = current_line_index + 1  # For user messages (1-based)

        # --- Read Atom Count ---
        try:
            atom_count_str = lines[current_line_index].strip()
            atom_count = int(atom_count_str)
            if atom_count <= 0:
                logger.warning(
                    f"Invalid atom count ({atom_count}) for block {block_num} "
                    f"at line {start_line_num} in {source_name}. Skipping block"
                )
                current_line_index += 1  # Move past the bad count line
                continue
        except (ValueError, IndexError):
            logger.warning(
                f"Expected integer atom count for block {block_num} at line {start_line_num} "
                f"in {source_name}, found '{lines[current_line_index].strip()}'. Skipping block"
            )
            current_line_index += 1  # Move past the non-integer line
            continue

        # --- Check if enough lines remain for comment + coords ---
        comment_line_index = current_line_index + 1
        first_coord_line_index = current_line_index + 2
        last_coord_line_index_excl = first_coord_line_index + atom_count

        if comment_line_index >= total_lines:
            logger.warning(
                f"Missing comment line after atom count for block {block_num} "
                f"at line {start_line_num} in {source_name}. Skipping block"
            )
            current_line_index += 1  # Move past count line
            continue
        if last_coord_line_index_excl > total_lines:
            logger.warning(
                f"Not enough coordinate lines for block {block_num} (expected {atom_count}) "
                f"starting at line {start_line_num} in {source_name}. Skipping block"
            )
            current_line_index += 1  # Move past count line
            continue

        # --- Parse Coordinates for this block ---
        coord_lines = lines[first_coord_line_index:last_coord_line_index_excl]
        block_symbols: List[str] = []
        block_coords_list: List[List[float]] = []
        block_parse_success = True

        for i, line in enumerate(coord_lines):
            line_num_abs = first_coord_line_index + i + 1  # For user messages
            parts = line.strip().split()
            if (
                not parts
            ):  # Should not happen if atom count is correct, but check anyway
                logger.warning(
                    f"Blank line {line_num_abs} found within coordinate block {block_num} "
                    f"of {source_name}. Skipping line"
                )
                continue  # Or should this invalidate the block? Let's skip line for now.
            if len(parts) < 4:
                logger.warning(
                    f"Line {line_num_abs} in block {block_num} of {source_name} malformed. Skipping block"
                )
                block_parse_success = False
                break
            try:
                block_symbols.append(parts[0])
                block_coords_list.append(list(map(float, parts[1:4])))
            except ValueError as e:
                logger.warning(
                    f"Error parsing coords line {line_num_abs} in block {block_num} "
                    f"of {source_name}: {e}. Skipping block"
                )
                block_parse_success = False
                break

        # --- Store if block parsed successfully ---
        if block_parse_success and len(block_symbols) == atom_count:
            coords_array = np.array(block_coords_list)
            parsed_molecules.append((block_symbols, coords_array))
            logger.debug(
                f"Successfully parsed block {block_num} ({atom_count} atoms) from {source_name}"
            )
        elif block_parse_success and len(block_symbols) != atom_count:
            logger.warning(
                f"Found {len(block_symbols)} atoms in block {block_num} of {source_name}, "
                f"but header specified {atom_count}. Skipping block"
            )
        # else: error message already logged

        # Move to the start of the next potential block
        current_line_index = last_coord_line_index_excl

    logger.info(f"Successfully parsed {len(parsed_molecules)} molecule blocks from {source_name}")
    return parsed_molecules


def format_xyz_string(symbols: List[str], coords: np.ndarray, comment: str = "") -> str:
    """
    Formats symbols and coordinates into an XYZ file string.

    Args:
        symbols: List of atom symbols
        coords: NumPy array of coordinates (N, 3)
        comment: Optional comment line

    Returns:
        Formatted XYZ string

    Raises:
        InvalidCoordinatesError: If coordinates array has invalid shape
        AtomCountMismatchError: If symbols and coordinates counts don't match
    """
    logger.debug(f"Formatting XYZ string for {len(symbols)} atoms")

    num_atoms = len(symbols)

    if coords.ndim != 2 or coords.shape[1] != 3:
        logger.error(f"Invalid coordinates shape: {coords.shape}, expected (N, 3)")
        raise InvalidCoordinatesError(
            f"Coordinates array must have shape (N, 3), but got {coords.shape}"
        )

    if num_atoms != coords.shape[0]:
        logger.error(
            f"Atom count mismatch: {num_atoms} symbols vs {coords.shape[0]} coordinates"
        )
        raise AtomCountMismatchError(num_atoms, coords.shape[0])

    lines = [f"{num_atoms}", comment]
    for symbol, coord in zip(symbols, coords):
        lines.append(
            f"{symbol:<4} {coord[0]:>12.6f} {coord[1]:>12.6f} {coord[2]:>12.6f}"
        )

    logger.debug(f"Successfully formatted XYZ string with {num_atoms} atoms")
    return "\n".join(lines) + "\n"

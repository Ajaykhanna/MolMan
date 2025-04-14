"""
molvis_core/io.py

Handles file input/output operations, specifically for XYZ format,
and provides functions for generating example structures.
"""

import numpy as np
from pathlib import Path
import sys
from typing import List, Tuple, Optional

# Use relative import within the package
try:
    from .constants import DEFAULT_BENZENE_DISTANCE
except ImportError:
    # Fallback for running as script? Or assume it's used as module.
    print("Warning: Could not perform relative import in io.py", file=sys.stderr)
    DEFAULT_BENZENE_DISTANCE = 3.0


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
    print(f"Generated two benzenes separated by {distance} Å.")
    return all_symbols, all_coords, molecule_boundaries


def load_xyz(file_path: Path) -> Tuple[Optional[List[str]], Optional[np.ndarray]]:
    """Loads atom symbols and coordinates from a standard XYZ file path."""
    # ... (Implementation remains the same as previous version) ...
    if not file_path.is_file():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return None, None
    try:
        with file_path.open("r") as file:
            lines = file.readlines()
            if not lines:
                raise ValueError(f"File is empty: {file_path}")
            try:
                atom_count = int(lines[0].strip())
            except ValueError:
                raise ValueError(
                    f"First line must be an integer (atom count), found: '{lines[0].strip()}'"
                )
            if len(lines) < 2:
                raise ValueError(
                    "File must have at least 2 lines (count and comment/coords)."
                )
            coord_lines = lines[2:]
            symbols: List[str] = []
            coords_list: List[List[float]] = []
            actual_atom_count = 0
            for i, line in enumerate(coord_lines):
                if actual_atom_count >= atom_count:
                    if i < len(coord_lines) and line.strip():
                        print(
                            f"Warning: Stopped reading coordinates at line {i+3} in {file_path.name} as atom count ({atom_count}) from header was reached.",
                            file=sys.stderr,
                        )
                    break
                parts = line.strip().split()
                if not parts:
                    continue
                if len(parts) < 4:
                    print(
                        f"Warning: Line {i+3} in {file_path.name} malformed (expected Symbol X Y Z): '{line.strip()}'. Skipping.",
                        file=sys.stderr,
                    )
                    continue
                try:
                    symbols.append(parts[0])
                    coords_list.append(list(map(float, parts[1:4])))
                    actual_atom_count += 1
                except ValueError as e:
                    print(
                        f"Warning: Error parsing coordinates on line {i+3} in {file_path.name}: {e}. Skipping.",
                        file=sys.stderr,
                    )
                    continue
            if actual_atom_count == 0 and atom_count > 0:
                raise ValueError(f"No valid coordinate lines found in {file_path.name}")
            if actual_atom_count != atom_count:
                print(
                    f"Warning: Found {actual_atom_count} atoms in {file_path.name}, but header specified {atom_count}.",
                    file=sys.stderr,
                )
            return symbols, np.array(coords_list)
    except ValueError as e:
        print(f"Error reading {file_path.name}: {e}", file=sys.stderr)
        return None, None
    except Exception as e:
        print(f"Unexpected error reading {file_path.name}: {e}", file=sys.stderr)
        return None, None


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
        ValueError: If the text format is invalid.
    """
    # ... (Implementation same as previous version) ...
    symbols: List[str] = []
    coords_list: List[List[float]] = []
    lines = xyz_text.strip().splitlines()
    if not lines:
        print(f"Error: Input source '{source_name}' is empty.", file=sys.stderr)
        return None, None
    try:
        atom_count_str = lines[0].strip()
        atom_count = int(atom_count_str)
    except (ValueError, IndexError):
        print(
            f"Error: First line of '{source_name}' must be number of atoms.",
            file=sys.stderr,
        )
        return None, None
    if len(lines) < 2:
        print(f"Error: '{source_name}' must have at least 2 lines.", file=sys.stderr)
        return None, None
    coord_lines = lines[2:]
    actual_atom_count = 0
    for i, line in enumerate(coord_lines):
        if actual_atom_count >= atom_count:
            if i < len(coord_lines) and line.strip():
                print(
                    f"Warning: '{source_name}': Stopped reading at line {i+3} (header count {atom_count} reached).",
                    file=sys.stderr,
                )
            break
        parts = line.strip().split()
        if not parts:
            continue
        if len(parts) < 4:
            print(
                f"Warning: '{source_name}' Line {i+3} malformed: '{line.strip()}'. Skipping.",
                file=sys.stderr,
            )
            continue
        try:
            symbols.append(parts[0])
            coords_list.append(list(map(float, parts[1:4])))
            actual_atom_count += 1
        except ValueError as e:
            print(
                f"Warning: '{source_name}' Error parsing coords line {i+3}: {e}. Skipping.",
                file=sys.stderr,
            )
            continue
    if actual_atom_count == 0 and atom_count > 0:
        print(
            f"Error: '{source_name}': No valid coordinate lines found.", file=sys.stderr
        )
        return None, None
    if actual_atom_count != atom_count:
        print(
            f"Warning: '{source_name}': Found {actual_atom_count} atoms, header said {atom_count}.",
            file=sys.stderr,
        )
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
                print(
                    f"Warning: Invalid atom count ({atom_count}) found for block {block_num} starting at line {start_line_num} in {source_name}. Skipping block.",
                    file=sys.stderr,
                )
                current_line_index += 1  # Move past the bad count line
                continue
        except (ValueError, IndexError):
            print(
                f"Warning: Expected integer atom count for block {block_num} at line {start_line_num} in {source_name}, found '{lines[current_line_index].strip()}'. Skipping block.",
                file=sys.stderr,
            )
            current_line_index += 1  # Move past the non-integer line
            continue

        # --- Check if enough lines remain for comment + coords ---
        comment_line_index = current_line_index + 1
        first_coord_line_index = current_line_index + 2
        last_coord_line_index_excl = first_coord_line_index + atom_count

        if comment_line_index >= total_lines:
            print(
                f"Warning: Missing comment line after atom count for block {block_num} at line {start_line_num} in {source_name}. Skipping block.",
                file=sys.stderr,
            )
            current_line_index += 1  # Move past count line
            continue
        if last_coord_line_index_excl > total_lines:
            print(
                f"Warning: Not enough coordinate lines found for block {block_num} (expected {atom_count}) starting at line {start_line_num} in {source_name}. Skipping block.",
                file=sys.stderr,
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
                print(
                    f"Warning: Blank line {line_num_abs} found within coordinate block {block_num} of {source_name}. Skipping line.",
                    file=sys.stderr,
                )
                continue  # Or should this invalidate the block? Let's skip line for now.
            if len(parts) < 4:
                print(
                    f"Warning: Line {line_num_abs} in block {block_num} of {source_name} malformed. Skipping block.",
                    file=sys.stderr,
                )
                block_parse_success = False
                break
            try:
                block_symbols.append(parts[0])
                block_coords_list.append(list(map(float, parts[1:4])))
            except ValueError as e:
                print(
                    f"Warning: Error parsing coords line {line_num_abs} in block {block_num} of {source_name}: {e}. Skipping block.",
                    file=sys.stderr,
                )
                block_parse_success = False
                break

        # --- Store if block parsed successfully ---
        if block_parse_success and len(block_symbols) == atom_count:
            coords_array = np.array(block_coords_list)
            parsed_molecules.append((block_symbols, coords_array))
            print(
                f"  Successfully parsed block {block_num} ({atom_count} atoms) from {source_name}."
            )
        elif block_parse_success and len(block_symbols) != atom_count:
            print(
                f"Warning: Found {len(block_symbols)} atoms in block {block_num} of {source_name}, but header specified {atom_count}. Skipping block.",
                file=sys.stderr,
            )
        # else: error message already printed

        # Move to the start of the next potential block
        current_line_index = last_coord_line_index_excl

    return parsed_molecules


def format_xyz_string(symbols: List[str], coords: np.ndarray, comment: str = "") -> str:
    """Formats symbols and coordinates into an XYZ file string."""
    # ... (Implementation remains the same as previous version) ...
    num_atoms = len(symbols)
    if coords.ndim != 2 or coords.shape[1] != 3:
        raise ValueError(
            f"Coordinates array must have shape (N, 3), but got {coords.shape}"
        )
    if num_atoms != coords.shape[0]:
        raise ValueError(
            f"Number of symbols ({num_atoms}) does not match number of coordinates ({coords.shape[0]})"
        )
    lines = [f"{num_atoms}", comment]
    for symbol, coord in zip(symbols, coords):
        lines.append(
            f"{symbol:<4} {coord[0]:>12.6f} {coord[1]:>12.6f} {coord[2]:>12.6f}"
        )
    return "\n".join(lines) + "\n"

"""
PDB (Protein Data Bank) file format parser.

The PDB format is widely used for macromolecular structures. It contains
detailed information about atoms, residues, chains, and experimental metadata.

Format specification: https://www.wwpdb.org/documentation/file-format

Key record types:
    HEADER: Classification and deposition date
    TITLE: Description of the experiment
    ATOM: Atomic coordinates for standard residues
    HETATM: Atomic coordinates for heteroatoms (ligands, ions, water)
    CONECT: Connectivity information (bonds)
    MODEL/ENDMDL: Multiple models (e.g., NMR structures)
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

from molvis_core.exceptions import (
    FileNotFoundError,
    FileParseError,
    FormatValidationError,
)
from molvis_core.formats.base import FileFormatBase
from molvis_core.logging_config import get_logger
from molvis_core.molecule import Molecule

logger = get_logger(__name__)


class PDBParser(FileFormatBase):
    """Parser for PDB format files.

    The PDB format is one of the most common formats for protein structures.
    It contains detailed atomic coordinates, chain information, and metadata.

    Attributes:
        format_name: "PDB"
        extensions: [".pdb", ".ent"]
        supports_multiple: True (can contain multiple models)
    """

    format_name = "PDB"
    extensions = [".pdb", ".ent"]
    supports_multiple = True

    def parse(
        self,
        file_path: Path,
        chains: Optional[List[str]] = None,
        include_hetatm: bool = True,
        model: Optional[int] = None
    ) -> List[Molecule]:
        """Parse a PDB file and return Molecule objects.

        Args:
            file_path: Path to the PDB file
            chains: List of chain IDs to parse (None = all chains)
            include_hetatm: Whether to include HETATM records
            model: Specific model number to parse (None = all models)

        Returns:
            List of Molecule objects (one per model)

        Raises:
            FileNotFoundError: If the file doesn't exist
            FileParseError: If parsing fails
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(str(file_path))

        logger.debug(f"Parsing PDB file: {file_path}")

        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()

            # Parse metadata
            metadata = self._parse_metadata(lines)

            # Parse models
            models = self._parse_models(
                lines,
                chains=chains,
                include_hetatm=include_hetatm,
                target_model=model
            )

            if not models:
                logger.warning(f"No atom records found in {file_path}")
                # Return empty molecule with metadata
                empty_mol = Molecule(
                    id=1,
                    name=metadata.get('title', 'Empty PDB'),
                    symbols=[],
                    coords=np.array([]).reshape(0, 3),
                    bonds=[],
                    metadata=metadata
                )
                return [empty_mol]

            # Add metadata to all models
            for mol in models:
                mol.metadata.update(metadata)

            logger.info(
                f"Successfully parsed {len(models)} model(s) from {file_path}"
            )
            return models

        except (FileNotFoundError, FileParseError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error parsing PDB file: {e}")
            raise FileParseError(str(file_path), 0, str(e))

    def _parse_metadata(self, lines: List[str]) -> Dict[str, Any]:
        """Extract metadata from PDB header records.

        Args:
            lines: All lines from the PDB file

        Returns:
            Dictionary of metadata fields
        """
        metadata = {}

        for line in lines:
            record_type = line[0:6].strip()

            if record_type == "HEADER":
                # HEADER record: columns 11-50 classification, 51-59 date, 63-66 ID code
                if len(line) >= 50:
                    metadata['classification'] = line[10:50].strip()
                if len(line) >= 59:
                    metadata['deposition_date'] = line[50:59].strip()
                if len(line) >= 66:
                    metadata['pdb_id'] = line[62:66].strip()

            elif record_type == "TITLE":
                # TITLE can span multiple lines
                title_text = line[10:].strip() if len(line) > 10 else ""
                if 'title' in metadata:
                    metadata['title'] += " " + title_text
                else:
                    metadata['title'] = title_text

            elif record_type == "EXPDTA":
                # Experimental technique
                if len(line) > 10:
                    metadata['experimental_method'] = line[10:].strip()

            elif record_type == "REMARK":
                # REMARK 2 contains resolution for X-ray structures
                if len(line) > 11 and line[7:10].strip() == "2":
                    if "RESOLUTION" in line.upper():
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == "RESOLUTION." and i + 1 < len(parts):
                                try:
                                    metadata['resolution'] = float(parts[i + 1])
                                except ValueError:
                                    pass

        return metadata

    def _parse_models(
        self,
        lines: List[str],
        chains: Optional[List[str]],
        include_hetatm: bool,
        target_model: Optional[int]
    ) -> List[Molecule]:
        """Parse all models from PDB file.

        Args:
            lines: All lines from the PDB file
            chains: Chain IDs to include (None = all)
            include_hetatm: Include HETATM records
            target_model: Specific model to parse (None = all)

        Returns:
            List of Molecule objects
        """
        models = []
        current_model_atoms = []
        current_model_num = 1
        in_model = False
        has_model_records = False
        skip_current_model = False

        # Track connectivity
        connections: Dict[int, Set[int]] = {}

        for line_num, line in enumerate(lines, 1):
            record_type = line[0:6].strip()

            if record_type == "MODEL":
                has_model_records = True
                in_model = True
                try:
                    current_model_num = int(line[10:14])
                except (ValueError, IndexError):
                    current_model_num = len(models) + 1

                # Check if we should skip this model
                if target_model is not None and current_model_num != target_model:
                    skip_current_model = True
                else:
                    skip_current_model = False

            elif record_type == "ENDMDL":
                in_model = False
                if current_model_atoms and not skip_current_model:
                    # Create molecule for this model
                    mol = self._create_molecule_from_atoms(
                        current_model_atoms,
                        current_model_num,
                        connections
                    )
                    models.append(mol)
                    current_model_atoms = []

                # If we got the target model, stop parsing
                if target_model is not None and current_model_num == target_model:
                    break

                skip_current_model = False

            elif record_type in ("ATOM", "HETATM"):
                # Skip if we're skipping this model
                if skip_current_model:
                    continue

                # Skip HETATM if not requested
                if record_type == "HETATM" and not include_hetatm:
                    continue

                # Only parse if we're in the right model (or no MODEL records exist)
                if has_model_records and not in_model:
                    continue

                # Parse atom record
                try:
                    atom_data = self._parse_atom_record(line)

                    # Filter by chain if specified
                    if chains is not None and atom_data['chain_id'] not in chains:
                        continue

                    current_model_atoms.append(atom_data)

                except Exception as e:
                    logger.warning(f"Failed to parse ATOM/HETATM at line {line_num}: {e}")

            elif record_type == "CONECT":
                # Parse connectivity
                try:
                    conect_data = self._parse_conect_record(line)
                    atom_serial = conect_data[0]
                    if atom_serial not in connections:
                        connections[atom_serial] = set()
                    connections[atom_serial].update(conect_data[1:])
                except Exception as e:
                    logger.debug(f"Failed to parse CONECT at line {line_num}: {e}")

        # Handle files without MODEL/ENDMDL records
        if not has_model_records and current_model_atoms:
            mol = self._create_molecule_from_atoms(
                current_model_atoms,
                1,
                connections
            )
            models.append(mol)

        return models

    def _parse_atom_record(self, line: str) -> Dict[str, Any]:
        """Parse a single ATOM or HETATM record.

        PDB ATOM format (fixed columns):
            1-6:   Record type (ATOM/HETATM)
            7-11:  Atom serial number
            13-16: Atom name
            17:    Alternate location indicator
            18-20: Residue name
            22:    Chain identifier
            23-26: Residue sequence number
            27:    Insertion code
            31-38: X coordinate (Å)
            39-46: Y coordinate (Å)
            47-54: Z coordinate (Å)
            55-60: Occupancy
            61-66: Temperature factor
            77-78: Element symbol
            79-80: Charge

        Args:
            line: ATOM/HETATM record line

        Returns:
            Dictionary with atom data

        Raises:
            ValueError: If required fields cannot be parsed
        """
        # Ensure line is long enough
        line = line.ljust(80)

        atom_data = {
            'record_type': line[0:6].strip(),
            'serial': int(line[6:11]),
            'atom_name': line[12:16].strip(),
            'alt_loc': line[16:17].strip(),
            'res_name': line[17:20].strip(),
            'chain_id': line[21:22].strip(),
            'res_seq': int(line[22:26]),
            'icode': line[26:27].strip(),
            'x': float(line[30:38]),
            'y': float(line[38:46]),
            'z': float(line[46:54]),
            'occupancy': float(line[54:60]) if line[54:60].strip() else 1.0,
            'temp_factor': float(line[60:66]) if line[60:66].strip() else 0.0,
            'element': line[76:78].strip() if len(line) > 76 else '',
            'charge': line[78:80].strip() if len(line) > 78 else '',
        }

        # If element is not specified, derive from atom name
        if not atom_data['element']:
            # Remove digits and take first 1-2 characters
            atom_name = atom_data['atom_name']
            element = ''.join([c for c in atom_name if c.isalpha()])
            atom_data['element'] = element[:2] if len(element) > 1 else element

        return atom_data

    def _parse_conect_record(self, line: str) -> List[int]:
        """Parse a CONECT record.

        Format: CONECT atom1 atom2 atom3 atom4 ...

        Args:
            line: CONECT record line

        Returns:
            List of connected atom serial numbers
        """
        # Split into 5-character fields after "CONECT"
        parts = [line[i:i+5].strip() for i in range(6, len(line), 5)]
        return [int(p) for p in parts if p.isdigit()]

    def _create_molecule_from_atoms(
        self,
        atoms: List[Dict[str, Any]],
        model_num: int,
        connections: Dict[int, Set[int]]
    ) -> Molecule:
        """Create a Molecule object from parsed atom data.

        Args:
            atoms: List of atom dictionaries
            model_num: Model number
            connections: CONECT data mapping serial numbers to bonded atoms

        Returns:
            Molecule object
        """
        # Extract symbols and coordinates
        symbols = [atom['element'] for atom in atoms]
        coords = np.array([[atom['x'], atom['y'], atom['z']] for atom in atoms])

        # Map serial numbers to array indices
        serial_to_index = {atom['serial']: i for i, atom in enumerate(atoms)}

        # Build bonds from CONECT records
        bonds = []
        processed_pairs = set()

        for atom_serial, bonded_serials in connections.items():
            if atom_serial in serial_to_index:
                idx1 = serial_to_index[atom_serial]
                for bonded_serial in bonded_serials:
                    if bonded_serial in serial_to_index:
                        idx2 = serial_to_index[bonded_serial]
                        # Avoid duplicate bonds (A-B and B-A)
                        pair = tuple(sorted([idx1, idx2]))
                        if pair not in processed_pairs:
                            bonds.append(pair)
                            processed_pairs.add(pair)

        # Create molecule name from first residue or use default
        if atoms:
            first_atom = atoms[0]
            mol_name = f"{first_atom['res_name']}_{first_atom['chain_id']}_Model{model_num}"
        else:
            mol_name = f"Model_{model_num}"

        # Store detailed atom information in metadata
        atom_details = []
        for atom in atoms:
            atom_details.append({
                'serial': atom['serial'],
                'name': atom['atom_name'],
                'res_name': atom['res_name'],
                'chain_id': atom['chain_id'],
                'res_seq': atom['res_seq'],
                'occupancy': atom['occupancy'],
                'temp_factor': atom['temp_factor'],
            })

        molecule = Molecule(
            id=model_num,
            name=mol_name,
            symbols=symbols,
            coords=coords,
            bonds=bonds,
            metadata={
                'format': 'PDB',
                'model_number': model_num,
                'atoms': atom_details,
            }
        )

        return molecule

    def write(
        self,
        molecules: List[Molecule],
        file_path: Path,
        **kwargs
    ) -> None:
        """Write molecule(s) to a PDB file.

        Args:
            molecules: List of Molecule objects to write
            file_path: Path where the file should be written
            **kwargs: Optional arguments:
                - write_conect: Write CONECT records (default: True)
                - write_header: Write HEADER/TITLE records (default: True)

        Raises:
            FileIOError: If writing fails
        """
        file_path = Path(file_path)
        write_conect = kwargs.get('write_conect', True)
        write_header = kwargs.get('write_header', True)

        logger.debug(f"Writing {len(molecules)} molecule(s) to {file_path}")

        try:
            with open(file_path, 'w') as f:
                # Write header if requested
                if write_header and molecules:
                    metadata = molecules[0].metadata
                    if 'pdb_id' in metadata:
                        f.write(f"HEADER    {metadata.get('classification', ''):40s}"
                                f"{metadata.get('deposition_date', ''):9s}   "
                                f"{metadata['pdb_id']:4s}\n")
                    if 'title' in metadata:
                        title = metadata['title']
                        # Split title into 60-character chunks
                        for i in range(0, len(title), 60):
                            f.write(f"TITLE     {title[i:i+60]}\n")

                # Write models
                multi_model = len(molecules) > 1

                for model_idx, molecule in enumerate(molecules, 1):
                    if multi_model:
                        f.write(f"MODEL     {model_idx:4d}\n")

                    # Write atoms
                    atom_serial = 1
                    for i, (symbol, coord) in enumerate(zip(molecule.symbols, molecule.coords)):
                        # Get atom details from metadata if available
                        atom_info = None
                        if 'atoms' in molecule.metadata and i < len(molecule.metadata['atoms']):
                            atom_info = molecule.metadata['atoms'][i]

                        # Determine record type
                        record_type = "ATOM  "
                        atom_name = atom_info['name'] if atom_info else symbol
                        res_name = atom_info['res_name'] if atom_info else "UNK"
                        chain_id = atom_info['chain_id'] if atom_info else "A"
                        res_seq = atom_info['res_seq'] if atom_info else 1
                        occupancy = atom_info['occupancy'] if atom_info else 1.0
                        temp_factor = atom_info['temp_factor'] if atom_info else 0.0

                        # Format ATOM record
                        f.write(
                            f"{record_type:6s}"
                            f"{atom_serial:5d} "
                            f"{atom_name:4s} "
                            f"{res_name:3s} "
                            f"{chain_id:1s}"
                            f"{res_seq:4d}    "
                            f"{coord[0]:8.3f}"
                            f"{coord[1]:8.3f}"
                            f"{coord[2]:8.3f}"
                            f"{occupancy:6.2f}"
                            f"{temp_factor:6.2f}          "
                            f"{symbol:>2s}\n"
                        )
                        atom_serial += 1

                    # Write CONECT records if requested
                    if write_conect and molecule.bonds:
                        conect_dict: Dict[int, List[int]] = {}
                        for bond in molecule.bonds:
                            idx1, idx2 = bond
                            # Use 1-based indexing for PDB
                            serial1 = idx1 + 1
                            serial2 = idx2 + 1

                            if serial1 not in conect_dict:
                                conect_dict[serial1] = []
                            if serial2 not in conect_dict:
                                conect_dict[serial2] = []

                            conect_dict[serial1].append(serial2)
                            conect_dict[serial2].append(serial1)

                        # Write CONECT records
                        for serial in sorted(conect_dict.keys()):
                            bonded = sorted(conect_dict[serial])
                            # CONECT can have up to 4 bonds per line
                            for i in range(0, len(bonded), 4):
                                chunk = bonded[i:i+4]
                                conect_line = f"CONECT{serial:5d}"
                                for bonded_serial in chunk:
                                    conect_line += f"{bonded_serial:5d}"
                                f.write(conect_line + "\n")

                    if multi_model:
                        f.write("ENDMDL\n")

                f.write("END\n")

            logger.info(f"Successfully wrote PDB file: {file_path}")

        except Exception as e:
            from molvis_core.exceptions import FileIOError
            logger.error(f"Error writing PDB file: {e}")
            raise FileIOError(f"Failed to write PDB file: {e}")

    def validate(self, file_path: Path) -> bool:
        """Validate that a file is a valid PDB file.

        Args:
            file_path: Path to the file to validate

        Returns:
            True if the file is valid PDB format
        """
        try:
            if not file_path.exists():
                return False

            with open(file_path, 'r') as f:
                lines = f.readlines()

            # Check for at least one ATOM or HETATM record
            has_atoms = any(
                line.startswith('ATOM  ') or line.startswith('HETATM')
                for line in lines
            )

            return has_atoms

        except Exception:
            return False

    def get_metadata_schema(self) -> Dict[str, type]:
        """Return the metadata schema for PDB format.

        Returns:
            Dictionary of metadata fields
        """
        return {
            'format': str,
            'pdb_id': str,
            'title': str,
            'classification': str,
            'deposition_date': str,
            'experimental_method': str,
            'resolution': float,
            'model_number': int,
            'atoms': list,  # List of atom detail dicts
        }

"""
Multi-format molecular file support for MolMan.

This package provides parsers and writers for various molecular file formats:
- XYZ: Simple Cartesian coordinates
- PDB: Protein Data Bank format
- MOL2: Tripos molecular format
- SDF: Structure Data File
- CIF: Crystallographic Information File

Example usage:
    >>> from molvis_core.formats import load_structure, write_structure
    >>> molecules = load_structure('protein.pdb')
    >>> write_structure(molecules, 'output.xyz')

    >>> from molvis_core.formats import FormatRegistry
    >>> parser = FormatRegistry.get_parser('pdb')
    >>> molecules = parser.parse(Path('protein.pdb'))
"""

from molvis_core.formats.base import (
    FileFormatBase,
    FormatDetector,
    FormatRegistry,
    load_structure,
    write_structure,
)
from molvis_core.formats.pdb import PDBParser
from molvis_core.formats.xyz import XYZParser

# Register parsers
FormatRegistry.register('xyz', XYZParser)
FormatRegistry.register('pdb', PDBParser)

__all__ = [
    'FileFormatBase',
    'FormatDetector',
    'FormatRegistry',
    'load_structure',
    'write_structure',
    'PDBParser',
    'XYZParser',
]

# Version info
__version__ = '1.0.0'

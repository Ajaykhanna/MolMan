# Phase 4: Multi-Format File Support - Design Document

## Overview

This document outlines the design for adding support for multiple molecular file formats to MolMan.

## Supported Formats

### 1. PDB (Protein Data Bank)
**File Extension:** `.pdb`
**Primary Use:** Protein and nucleic acid structures
**Format:** Text-based, fixed-width columns

**Key Features:**
- Atom coordinates (ATOM, HETATM records)
- Chain information
- Residue names and numbers
- B-factors and occupancy
- Secondary structure (HELIX, SHEET)
- Connectivity (CONECT records)
- Metadata (HEADER, TITLE, REMARK)

**Example:**
```
HEADER    HYDROLASE                               01-JUN-95   1ABC
ATOM      1  N   MET A   1      27.340  24.430   2.614  1.00  0.00           N
ATOM      2  CA  MET A   1      26.266  25.413   2.842  1.00  0.00           C
```

### 2. MOL2 (Tripos)
**File Extension:** `.mol2`
**Primary Use:** Small molecules, drug design
**Format:** Text-based, sectioned

**Key Features:**
- Atom types (Sybyl atom types)
- Bond information with bond types
- Partial charges
- Substructure information
- Molecule name and type

**Example:**
```
@<TRIPOS>MOLECULE
benzene
 12 12 0 0 0
SMALL
GASTEIGER

@<TRIPOS>ATOM
      1 C1          0.0000    1.4000    0.0000 C.ar    1  BEN1        0.0000
```

### 3. SDF (Structure Data File)
**File Extension:** `.sdf`
**Primary Use:** Chemical databases, multiple structures
**Format:** Text-based, MOL-based with data fields

**Key Features:**
- Multiple structures in one file
- 3D coordinates
- Bond information
- Properties and data fields
- Molecular formula

**Example:**
```

  Mrv0541 02151109593D

  6  6  0  0  0  0            999 V2000
    0.0000    1.4000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
M  END
> <PUBCHEM_COMPOUND_CID>
241

$$$$
```

### 4. CIF (Crystallographic Information File)
**File Extension:** `.cif`
**Primary Use:** Crystallographic structures
**Format:** Text-based, dictionary-based

**Key Features:**
- Unit cell parameters
- Space group information
- Atomic coordinates
- Symmetry operations
- Metadata (authors, journal, DOI)

**Example:**
```
data_global
_chemical_name_common 'benzene'
loop_
_atom_site_label
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
C1 0.0000 0.0000 0.0000
```

## Architecture Design

### Base Class Hierarchy

```
FileFormatBase (ABC)
├── PDBParser
├── MOL2Parser
├── SDFParser
└── CIFParser
```

### Core Components

#### 1. Format Detection
```python
class FormatDetector:
    @staticmethod
    def detect(file_path: Path) -> str:
        """Auto-detect file format from extension and content."""
        pass
```

#### 2. Base Parser Interface
```python
class FileFormatBase(ABC):
    @abstractmethod
    def parse(self, file_path: Path) -> List[Molecule]:
        """Parse file and return molecule(s)."""
        pass

    @abstractmethod
    def write(self, molecules: List[Molecule], file_path: Path) -> None:
        """Write molecule(s) to file."""
        pass

    @abstractmethod
    def validate(self, file_path: Path) -> bool:
        """Validate file format."""
        pass
```

#### 3. Format Registry
```python
class FormatRegistry:
    """Central registry for all file format parsers."""

    _parsers = {
        'pdb': PDBParser,
        'mol2': MOL2Parser,
        'sdf': SDFParser,
        'cif': CIFParser,
        'xyz': XYZParser,  # Existing
    }
```

#### 4. Universal Loader
```python
def load_structure(file_path: Path, format: Optional[str] = None) -> List[Molecule]:
    """Universal structure loader with auto-detection."""
    if format is None:
        format = FormatDetector.detect(file_path)

    parser = FormatRegistry.get_parser(format)
    return parser.parse(file_path)
```

### Metadata Preservation

Enhanced Molecule class to store format-specific metadata:

```python
@dataclass
class Molecule:
    # ... existing fields ...

    # New metadata fields
    metadata: Dict[str, Any] = field(default_factory=dict)
    residues: Optional[List[Residue]] = None  # For PDB
    chains: Optional[List[Chain]] = None  # For PDB
    properties: Optional[Dict[str, Any]] = None  # For SDF
    crystal_info: Optional[CrystalInfo] = None  # For CIF
```

## Implementation Plan

### Phase 4.1: Infrastructure (Days 1-2)
- [ ] Create `molvis_core/formats/` package
- [ ] Implement `FileFormatBase` abstract class
- [ ] Implement `FormatDetector`
- [ ] Implement `FormatRegistry`
- [ ] Create universal `load_structure()` function

### Phase 4.2: PDB Parser (Days 2-3)
- [ ] Implement PDB reader (ATOM, HETATM)
- [ ] Parse chain information
- [ ] Parse residue information
- [ ] Parse CONECT records
- [ ] Parse metadata (HEADER, REMARK)
- [ ] Support chain selection
- [ ] Write tests with real PDB files

### Phase 4.3: MOL2 Parser (Days 3-4)
- [ ] Implement MOL2 reader
- [ ] Parse atom section with Sybyl types
- [ ] Parse bond section
- [ ] Parse partial charges
- [ ] Preserve substructure info
- [ ] Write tests

### Phase 4.4: SDF Parser (Days 4-5)
- [ ] Implement SDF reader
- [ ] Support multiple structures
- [ ] Parse property fields
- [ ] Handle V2000 and V3000 formats
- [ ] Write tests

### Phase 4.5: CIF Parser (Days 5-6)
- [ ] Implement CIF reader
- [ ] Parse crystallographic data
- [ ] Handle symmetry operations
- [ ] Extract atomic coordinates
- [ ] Write tests

### Phase 4.6: Format Conversion (Days 6-7)
- [ ] Implement conversion utilities
- [ ] PDB ↔ XYZ
- [ ] MOL2 ↔ XYZ
- [ ] SDF ↔ XYZ
- [ ] Lossy conversion warnings
- [ ] Write tests

### Phase 4.7: Testing & Documentation (Days 7-10)
- [ ] Create comprehensive test suite
- [ ] Test with real-world files
- [ ] Performance testing (large PDB files)
- [ ] Update documentation
- [ ] Create usage examples
- [ ] Update README

## File Structure

```
molvis_core/
├── formats/
│   ├── __init__.py
│   ├── base.py           # FileFormatBase, FormatDetector, FormatRegistry
│   ├── pdb.py            # PDB parser
│   ├── mol2.py           # MOL2 parser
│   ├── sdf.py            # SDF parser
│   ├── cif.py            # CIF parser
│   └── converters.py     # Format conversion utilities
├── molecule.py           # Enhanced with metadata fields
└── io.py                 # Universal load_structure() function

tests/
├── formats/
│   ├── __init__.py
│   ├── test_pdb.py
│   ├── test_mol2.py
│   ├── test_sdf.py
│   ├── test_cif.py
│   ├── test_detection.py
│   └── test_conversion.py
└── test_data/
    ├── sample.pdb
    ├── sample.mol2
    ├── sample.sdf
    └── sample.cif
```

## Error Handling

New exceptions for format-specific errors:

```python
# molvis_core/exceptions.py

class FileFormatError(MolManError):
    """Base class for file format errors."""
    pass

class UnsupportedFormatError(FileFormatError):
    """Raised when file format is not supported."""
    pass

class FormatValidationError(FileFormatError):
    """Raised when file fails format validation."""
    pass

class FormatConversionError(FileFormatError):
    """Raised when format conversion fails."""
    pass
```

## Testing Strategy

### Unit Tests
- Parse valid files
- Handle malformed files
- Validate metadata preservation
- Test format detection
- Test conversions

### Integration Tests
- Load → Modify → Save roundtrip
- Cross-format conversion
- Large file handling (>10,000 atoms)

### Test Data
- Real PDB files from RCSB PDB
- Sample MOL2 from drug databases
- SDF from PubChem
- CIF from crystallographic databases

## Success Criteria

- [ ] All 4 formats (PDB, MOL2, SDF, CIF) can be read
- [ ] Format auto-detection works correctly
- [ ] Metadata is preserved during load/save
- [ ] Chain selection works for PDB
- [ ] Format conversion utilities functional
- [ ] 100+ tests covering all formats
- [ ] Performance: Load 10,000 atom structure < 1 second
- [ ] Documentation complete with examples

## Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| Complex PDB format variations | Start with common records, expand incrementally |
| Large file memory usage | Stream parsing for large structures |
| Format ambiguities | Clear validation and error messages |
| Lossy conversions | Document limitations, warn users |

## Dependencies

**Required:**
- Phase 1 (Testing)
- Phase 2 (Logging, Exceptions)

**Optional:**
- External libraries: None (pure Python implementation)
- Future: Consider `BioPython` for validation

## Timeline

- **Days 1-2**: Infrastructure and base classes
- **Days 3-4**: PDB parser (most complex)
- **Days 5-6**: MOL2 and SDF parsers
- **Days 7-8**: CIF parser and conversions
- **Days 9-10**: Testing and documentation

**Total: 10 days**

---

*Document Version: 1.0*
*Last Updated: 2025-11-26*

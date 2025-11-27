"""
Base classes and infrastructure for multi-format file support.

This module provides the foundation for reading and writing molecular structures
in various file formats (PDB, MOL2, SDF, CIF, XYZ).
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from molvis_core.exceptions import UnsupportedFormatError
from molvis_core.logging_config import get_logger

logger = get_logger(__name__)


class FileFormatBase(ABC):
    """Abstract base class for all file format parsers.

    All format-specific parsers (PDB, MOL2, SDF, CIF, XYZ) must inherit from
    this class and implement the required methods.

    Attributes:
        format_name: Human-readable name of the format (e.g., "PDB", "MOL2")
        extensions: List of file extensions supported (e.g., [".pdb", ".ent"])
        supports_multiple: Whether format can contain multiple structures
    """

    format_name: str = "Unknown"
    extensions: List[str] = []
    supports_multiple: bool = False

    @abstractmethod
    def parse(self, file_path: Path) -> List[Any]:
        """Parse a file and return a list of Molecule objects.

        Args:
            file_path: Path to the file to parse

        Returns:
            List of Molecule objects. Even single-molecule formats return a list.

        Raises:
            FileNotFoundError: If the file doesn't exist
            FileFormatError: If the file format is invalid
            FileParseError: If parsing fails
        """
        pass

    @abstractmethod
    def write(self, molecules: List[Any], file_path: Path, **kwargs) -> None:
        """Write molecule(s) to a file.

        Args:
            molecules: List of Molecule objects to write
            file_path: Path where the file should be written
            **kwargs: Format-specific options

        Raises:
            FileIOError: If writing fails
            InvalidMoleculeError: If molecule data is invalid
        """
        pass

    @abstractmethod
    def validate(self, file_path: Path) -> bool:
        """Validate that a file conforms to this format.

        Args:
            file_path: Path to the file to validate

        Returns:
            True if the file is valid for this format, False otherwise
        """
        pass

    def can_handle(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file.

        This is a quick check based on file extension. For more thorough
        validation, use validate().

        Args:
            file_path: Path to check

        Returns:
            True if the file extension matches this format
        """
        suffix = file_path.suffix.lower()
        return suffix in self.extensions

    def get_metadata_schema(self) -> Dict[str, type]:
        """Return the metadata schema for this format.

        Returns:
            Dictionary mapping metadata field names to their types.
            Empty dict by default; override for format-specific metadata.
        """
        return {}


class FormatDetector:
    """Automatically detect file format from extension and content.

    This class provides methods to identify molecular file formats both
    from filename extensions and by analyzing file content.
    """

    # Mapping of file extensions to format names
    EXTENSION_MAP = {
        '.xyz': 'xyz',
        '.pdb': 'pdb',
        '.ent': 'pdb',  # Alternative PDB extension
        '.mol2': 'mol2',
        '.sdf': 'sdf',
        '.sd': 'sdf',  # Alternative SDF extension
        '.cif': 'cif',
        '.mmcif': 'cif',  # Macromolecular CIF
    }

    # Format signatures for content-based detection
    FORMAT_SIGNATURES = {
        'pdb': [b'HEADER', b'ATOM  ', b'HETATM'],
        'mol2': [b'@<TRIPOS>MOLECULE', b'@<TRIPOS>ATOM'],
        'sdf': [b'M  END', b'$$$$'],
        'cif': [b'data_', b'loop_', b'_atom_site'],
    }

    @staticmethod
    def detect_from_extension(file_path: Path) -> Optional[str]:
        """Detect format from file extension.

        Args:
            file_path: Path to the file

        Returns:
            Format name (e.g., 'pdb', 'mol2') or None if unknown
        """
        suffix = file_path.suffix.lower()
        format_name = FormatDetector.EXTENSION_MAP.get(suffix)

        if format_name:
            logger.debug(f"Detected format '{format_name}' from extension '{suffix}'")
        else:
            logger.debug(f"Unknown extension '{suffix}'")

        return format_name

    @staticmethod
    def detect_from_content(file_path: Path, max_bytes: int = 1024) -> Optional[str]:
        """Detect format by analyzing file content.

        Args:
            file_path: Path to the file
            max_bytes: Maximum number of bytes to read for detection

        Returns:
            Format name (e.g., 'pdb', 'mol2') or None if unknown
        """
        try:
            with open(file_path, 'rb') as f:
                content = f.read(max_bytes)

            # Check each format's signatures
            for format_name, signatures in FormatDetector.FORMAT_SIGNATURES.items():
                if any(sig in content for sig in signatures):
                    logger.debug(
                        f"Detected format '{format_name}' from content analysis"
                    )
                    return format_name

            # XYZ format detection (first line should be atom count)
            try:
                first_line = content.split(b'\n')[0].decode('utf-8').strip()
                if first_line.isdigit():
                    logger.debug("Detected format 'xyz' from content analysis")
                    return 'xyz'
            except (UnicodeDecodeError, IndexError):
                pass

            logger.debug("Could not detect format from content")
            return None

        except Exception as e:
            logger.error(f"Error reading file for format detection: {e}")
            return None

    @staticmethod
    def detect(file_path: Path, use_content: bool = True) -> str:
        """Detect file format using multiple methods.

        Tries extension-based detection first, then content-based if enabled.

        Args:
            file_path: Path to the file
            use_content: Whether to use content analysis if extension fails

        Returns:
            Format name (e.g., 'pdb', 'mol2')

        Raises:
            UnsupportedFormatError: If format cannot be detected
        """
        # Try extension first
        format_name = FormatDetector.detect_from_extension(file_path)

        # Fall back to content analysis if enabled
        if format_name is None and use_content:
            format_name = FormatDetector.detect_from_content(file_path)

        # Raise error if still unknown
        if format_name is None:
            raise UnsupportedFormatError(
                str(file_path),
                format_hint="Could not determine format from extension or content"
            )

        return format_name


class FormatRegistry:
    """Central registry for all file format parsers.

    This class manages the mapping between format names and their parser classes.
    It provides a single point of access for loading any supported file format.

    Example:
        >>> from molvis_core.formats import FormatRegistry
        >>> parser = FormatRegistry.get_parser('pdb')
        >>> molecules = parser.parse(Path('protein.pdb'))
    """

    _parsers: Dict[str, Type[FileFormatBase]] = {}

    @classmethod
    def register(cls, format_name: str, parser_class: Type[FileFormatBase]) -> None:
        """Register a parser for a specific format.

        Args:
            format_name: Name of the format (e.g., 'pdb', 'mol2')
            parser_class: Parser class that inherits from FileFormatBase
        """
        cls._parsers[format_name.lower()] = parser_class
        logger.debug(f"Registered parser for format '{format_name}'")

    @classmethod
    def unregister(cls, format_name: str) -> None:
        """Unregister a parser.

        Args:
            format_name: Name of the format to unregister
        """
        format_name = format_name.lower()
        if format_name in cls._parsers:
            del cls._parsers[format_name]
            logger.debug(f"Unregistered parser for format '{format_name}'")

    @classmethod
    def get_parser(cls, format_name: str) -> FileFormatBase:
        """Get a parser instance for the specified format.

        Args:
            format_name: Name of the format (e.g., 'pdb', 'mol2')

        Returns:
            Instance of the appropriate parser class

        Raises:
            UnsupportedFormatError: If no parser is registered for this format
        """
        format_name = format_name.lower()
        parser_class = cls._parsers.get(format_name)

        if parser_class is None:
            raise UnsupportedFormatError(
                f"format:{format_name}",
                format_hint=f"Available formats: {', '.join(cls.list_formats())}"
            )

        return parser_class()

    @classmethod
    def list_formats(cls) -> List[str]:
        """List all registered formats.

        Returns:
            List of format names
        """
        return sorted(cls._parsers.keys())

    @classmethod
    def is_supported(cls, format_name: str) -> bool:
        """Check if a format is supported.

        Args:
            format_name: Name of the format to check

        Returns:
            True if the format has a registered parser
        """
        return format_name.lower() in cls._parsers

    @classmethod
    def get_parser_for_file(cls, file_path: Path, format_name: Optional[str] = None) -> FileFormatBase:
        """Get the appropriate parser for a file.

        If format_name is not provided, it will be auto-detected.

        Args:
            file_path: Path to the file
            format_name: Optional explicit format name

        Returns:
            Instance of the appropriate parser

        Raises:
            UnsupportedFormatError: If format is not supported
        """
        if format_name is None:
            format_name = FormatDetector.detect(file_path)

        return cls.get_parser(format_name)


def load_structure(file_path: Path, format_name: Optional[str] = None) -> List[Any]:
    """Universal structure loader with automatic format detection.

    This is the main entry point for loading molecular structures from any
    supported file format.

    Args:
        file_path: Path to the structure file
        format_name: Optional format name. If not provided, will be auto-detected.

    Returns:
        List of Molecule objects

    Raises:
        FileNotFoundError: If the file doesn't exist
        UnsupportedFormatError: If the format is not supported
        FileFormatError: If the file format is invalid
        FileParseError: If parsing fails

    Example:
        >>> from molvis_core.formats import load_structure
        >>> molecules = load_structure(Path('protein.pdb'))
        >>> molecules = load_structure(Path('ligand.mol2'), format_name='mol2')
    """
    file_path = Path(file_path)

    if not file_path.exists():
        from molvis_core.exceptions import FileNotFoundError
        raise FileNotFoundError(str(file_path))

    # Get appropriate parser
    parser = FormatRegistry.get_parser_for_file(file_path, format_name)

    # Log the operation
    logger.info(f"Loading structure from {file_path} using {parser.format_name} parser")

    # Parse and return
    molecules = parser.parse(file_path)
    logger.info(f"Successfully loaded {len(molecules)} molecule(s)")

    return molecules


def write_structure(
    molecules: List[Any],
    file_path: Path,
    format_name: Optional[str] = None,
    **kwargs
) -> None:
    """Universal structure writer.

    Args:
        molecules: List of Molecule objects to write
        file_path: Path where the file should be written
        format_name: Optional format name. If not provided, determined from extension.
        **kwargs: Format-specific options

    Raises:
        UnsupportedFormatError: If the format is not supported
        FileIOError: If writing fails

    Example:
        >>> from molvis_core.formats import write_structure
        >>> write_structure([molecule], Path('output.pdb'))
    """
    file_path = Path(file_path)

    # Determine format
    if format_name is None:
        format_name = FormatDetector.detect_from_extension(file_path)
        if format_name is None:
            raise UnsupportedFormatError(
                str(file_path),
                format_hint="Could not determine format from extension"
            )

    # Get appropriate parser
    parser = FormatRegistry.get_parser(format_name)

    # Log the operation
    logger.info(
        f"Writing {len(molecules)} molecule(s) to {file_path} "
        f"using {parser.format_name} format"
    )

    # Write
    parser.write(molecules, file_path, **kwargs)
    logger.info(f"Successfully wrote structure to {file_path}")

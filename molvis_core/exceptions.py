"""
Custom exception classes for MolMan.

This module defines specific exception types for different error conditions,
making error handling more precise and informative.
"""


class MolManError(Exception):
    """Base exception class for all MolMan errors."""

    pass


# === File I/O Exceptions ===


class FileIOError(MolManError):
    """Base class for file I/O related errors."""

    pass


class FileNotFoundError(FileIOError):
    """Raised when a requested file cannot be found."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        super().__init__(f"File not found: {filepath}")


class FileFormatError(FileIOError):
    """Raised when a file has an invalid or unsupported format."""

    def __init__(self, filepath: str, reason: str):
        self.filepath = filepath
        self.reason = reason
        super().__init__(f"Invalid file format in '{filepath}': {reason}")


class FileParseError(FileIOError):
    """Raised when parsing a file fails."""

    def __init__(self, filepath: str, line_number: int, reason: str):
        self.filepath = filepath
        self.line_number = line_number
        self.reason = reason
        super().__init__(
            f"Failed to parse '{filepath}' at line {line_number}: {reason}"
        )


class EmptyFileError(FileIOError):
    """Raised when a file is empty or contains no valid molecules."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        super().__init__(f"File is empty or contains no valid molecules: {filepath}")


# === Molecule Validation Exceptions ===


class MoleculeError(MolManError):
    """Base class for molecule-related errors."""

    pass


class InvalidMoleculeError(MoleculeError):
    """Raised when molecule data is invalid."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Invalid molecule: {reason}")


class AtomCountMismatchError(MoleculeError):
    """Raised when the number of atoms doesn't match coordinate array."""

    def __init__(self, expected: int, actual: int):
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"Atom count mismatch: expected {expected} atoms, got {actual}"
        )


class InvalidAtomSymbolError(MoleculeError):
    """Raised when an atom symbol is not recognized."""

    def __init__(self, symbol: str):
        self.symbol = symbol
        super().__init__(f"Invalid or unrecognized atom symbol: '{symbol}'")


class InvalidCoordinatesError(MoleculeError):
    """Raised when atomic coordinates are invalid."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Invalid atomic coordinates: {reason}")


# === Geometry and Transformation Exceptions ===


class GeometryError(MolManError):
    """Base class for geometry calculation errors."""

    pass


class InvalidRotationError(GeometryError):
    """Raised when rotation parameters are invalid."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Invalid rotation: {reason}")


class InvalidTransformationError(GeometryError):
    """Raised when transformation parameters are invalid."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Invalid transformation: {reason}")


class DimensionMismatchError(GeometryError):
    """Raised when array dimensions don't match expected values."""

    def __init__(self, expected: str, actual: str):
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"Dimension mismatch: expected {expected}, got {actual}"
        )


# === Bond Calculation Exceptions ===


class BondError(MolManError):
    """Base class for bond-related errors."""

    pass


class InvalidBondError(BondError):
    """Raised when bond indices are invalid."""

    def __init__(self, atom1: int, atom2: int, reason: str):
        self.atom1 = atom1
        self.atom2 = atom2
        self.reason = reason
        super().__init__(
            f"Invalid bond between atoms {atom1} and {atom2}: {reason}"
        )


class MissingBondDataError(BondError):
    """Raised when bond distance data is missing for an atom pair."""

    def __init__(self, symbol1: str, symbol2: str):
        self.symbol1 = symbol1
        self.symbol2 = symbol2
        super().__init__(
            f"No bond distance data available for atom pair: {symbol1}-{symbol2}"
        )


# === Configuration Exceptions ===


class ConfigurationError(MolManError):
    """Base class for configuration-related errors."""

    pass


class InvalidConfigError(ConfigurationError):
    """Raised when configuration is invalid."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Invalid configuration: {reason}")


class MissingConfigError(ConfigurationError):
    """Raised when required configuration is missing."""

    def __init__(self, key: str):
        self.key = key
        super().__init__(f"Missing required configuration: {key}")


# === Data Validation Exceptions ===


class ValidationError(MolManError):
    """Base class for validation errors."""

    pass


class InvalidParameterError(ValidationError):
    """Raised when a function parameter is invalid."""

    def __init__(self, param_name: str, value, reason: str):
        self.param_name = param_name
        self.value = value
        self.reason = reason
        super().__init__(
            f"Invalid parameter '{param_name}' = {value}: {reason}"
        )


class ValueOutOfRangeError(ValidationError):
    """Raised when a value is outside the acceptable range."""

    def __init__(self, param_name: str, value, min_val, max_val):
        self.param_name = param_name
        self.value = value
        self.min_val = min_val
        self.max_val = max_val
        super().__init__(
            f"Value {value} for '{param_name}' is out of range [{min_val}, {max_val}]"
        )


# === File Format Exceptions (Phase 4) ===


class UnsupportedFormatError(FileFormatError):
    """Raised when a file format is not supported."""

    def __init__(self, filepath: str, format_hint: str = ""):
        self.filepath = filepath
        self.format_hint = format_hint
        msg = f"Unsupported file format: {filepath}"
        if format_hint:
            msg += f" (detected as: {format_hint})"
        super(FileIOError, self).__init__(msg)


class FormatValidationError(FileFormatError):
    """Raised when file format validation fails."""

    def __init__(self, filepath: str, format_type: str, reason: str):
        self.filepath = filepath
        self.format_type = format_type
        self.reason = reason
        super(FileIOError, self).__init__(
            f"{format_type} validation failed for '{filepath}': {reason}"
        )


class FormatConversionError(MolManError):
    """Raised when format conversion fails."""

    def __init__(self, from_format: str, to_format: str, reason: str):
        self.from_format = from_format
        self.to_format = to_format
        self.reason = reason
        super().__init__(
            f"Failed to convert from {from_format} to {to_format}: {reason}"
        )


class MissingMetadataError(MolManError):
    """Raised when required metadata is missing from a file."""

    def __init__(self, filepath: str, metadata_key: str):
        self.filepath = filepath
        self.metadata_key = metadata_key
        super().__init__(
            f"Missing required metadata '{metadata_key}' in file: {filepath}"
        )

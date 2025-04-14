"""
molvis_core/helpers.py

Provides utility functions used by other parts of the core library or applications.
"""

from typing import List, Dict, Any


def get_element_property(
    symbols: List[str], property_dict: Dict[str, Any], default_value: Any
) -> List[Any]:
    """
    Looks up a property (e.g., color, radius) for a list of element symbols.

    Performs case-insensitive lookup by capitalizing the input symbols.

    Args:
        symbols: A list of element symbol strings.
        property_dict: A dictionary mapping capitalized element symbols
                       to property values.
        default_value: The value to return if a symbol is not found in the
                       dictionary.

    Returns:
        A list of property values corresponding to the input symbols.
    """
    # Capitalize symbol from input file/text for robust lookup
    return [property_dict.get(s.capitalize(), default_value) for s in symbols]

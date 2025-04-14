"""
molvis_core/constants.py

Defines core constants used for molecular visualization and calculations.

Includes:
- Representation style names
- CPK color definitions
- Covalent and Van der Waals radii
- Plotting scale factors and line widths (defaults, can be overridden by plotters)
- Bond calculation parameters (average lengths, tolerance)
- Default settings
- GUI Interaction Constants (Slider ranges, resolutions)
"""

from typing import Dict, FrozenSet, Tuple, List  # Added List import

# == Representation Styles ==
STYLE_LINES = "Lines"
STYLE_BALL_STICK = "Ball and Stick"
STYLE_SPACE_FILLING = "Space Filling"
REPRESENTATION_STYLES: List[str] = [STYLE_LINES, STYLE_BALL_STICK, STYLE_SPACE_FILLING]
DEFAULT_REPRESENTATION: str = STYLE_BALL_STICK

# == Colors (CPK - Corey-Pauling-Koltun) ==
CPK_COLORS: Dict[str, str] = {
    # Based on common conventions, hex codes for precision
    "H": "#FFFFFF",
    "C": "#222222",
    "N": "#0000FF",
    "O": "#FF0000",
    "F": "#00FF00",
    "Cl": "#00FF00",
    "Br": "#A52A2A",
    "I": "#800080",  # Brown for Br, Purple for I
    "He": "#ADD8E6",
    "Ne": "#ADD8E6",
    "Ar": "#ADD8E6",
    "Xe": "#ADD8E6",
    "Kr": "#ADD8E6",  # Light Blue for Noble Gases
    "P": "#FFA500",
    "S": "#FFFF00",
    "B": "#FFC0CB",  # Orange for P, Yellow for S, Pink for B
    "Li": "#EE82EE",
    "Na": "#EE82EE",
    "K": "#EE82EE",
    "Rb": "#EE82EE",
    "Cs": "#EE82EE",
    "Fr": "#EE82EE",  # Violet for Alkali
    "Be": "#008000",
    "Mg": "#008000",
    "Ca": "#008000",
    "Sr": "#008000",
    "Ba": "#008000",
    "Ra": "#008000",  # Dark Green for Alkaline Earth
    "Ti": "#808080",
    "Fe": "#FF8C00",  # Gray for Ti, Dark Orange for Fe
    # Add more elements as needed
    # Consider case-insensitivity during lookup using .capitalize()
}
DEFAULT_ATOM_COLOR: str = "#FF69B4"  # Default Pink for unknown elements
DEFAULT_BOND_COLOR: str = "#555555"  # Default Dark Grey for bonds
ATOM_EDGE_COLOR: str = "#000000"  # Black edge for atoms for better visibility

# == Radii (in Angstroms) ==
# Approximate covalent radii (adjust based on source/need)
COVALENT_RADII: Dict[str, float] = {
    "H": 0.37,
    "C": 0.77,
    "N": 0.75,
    "O": 0.73,
    "F": 0.71,
    "Cl": 0.99,
    "Br": 1.14,
    "I": 1.33,
    "P": 1.10,
    "S": 1.05,
    "B": 0.85,
    "Li": 1.67,
    "Na": 1.90,
    "K": 2.43,
    "Mg": 1.45,
    "Ca": 1.94,
    "Fe": 1.56,
    "Ti": 1.60,
    # Add more common elements
}
# Approximate Van der Waals radii (adjust based on source/need)
VDW_RADII: Dict[str, float] = {
    "H": 1.20,
    "C": 1.70,
    "N": 1.55,
    "O": 1.52,
    "F": 1.47,
    "Cl": 1.75,
    "Br": 1.85,
    "I": 1.98,
    "P": 1.80,
    "S": 1.80,
    "B": 1.92,  # Estimate for B
    "Li": 1.82,
    "Na": 2.27,
    "K": 2.75,
    "Mg": 1.73,
    "Ca": 2.31,  # Estimate for Ca vdW
    "Fe": 2.00,
    "Ti": 2.00,  # Estimates for transition metals vdW
    # Add more common elements
}
DEFAULT_COVALENT_RADIUS: float = 0.6
DEFAULT_VDW_RADIUS: float = 1.5

# == Plotting Scale Factors & Line Widths (Base values, plotter modules might override/use differently) ==
# These need tuning based on figure size and desired appearance in specific plotting libraries
# Scatter 's' is area in Matplotlib, Plotly 'size' is diameter-like. These are indicative.
BASE_RADIUS_TO_PLOT_SCALE_BALL_STICK: float = (
    25.0  # Factor to multiply radius by for B&S size
)
BASE_RADIUS_TO_PLOT_SCALE_SPACE_FILLING: float = (
    35.0  # Factor to multiply radius by for SF size
)
BASE_LINE_WIDTH_LINES: float = 1.0
BASE_LINE_WIDTH_BALL_STICK: float = 4.0

# == Bond Calculation ==
# Average bond lengths in Angstroms (add more as needed)
AVERAGE_BOND_LENGTHS: Dict[FrozenSet[str], float] = {
    frozenset(["C", "C"]): 1.53,
    frozenset(["C", "N"]): 1.47,
    frozenset(["C", "O"]): 1.42,
    frozenset(["C", "H"]): 1.09,
    frozenset(["N", "H"]): 1.00,
    frozenset(["O", "H"]): 0.96,
    # Example double/triple bonds (can be added if specific detection needed)
    # frozenset(["C", "C", "double"]): 1.34,
    # frozenset(["C", "O", "double"]): 1.21,
}
# Tolerance in Angstroms for bond determination
BOND_TOLERANCE: float = 0.3

# == GUI Interaction Constants ==
# Added based on previous implementation needs for UI sliders
SLIDER_TRANSLATION_RANGE: Tuple[float, float] = (-10.0, 10.0)
SLIDER_ROTATION_RANGE: Tuple[float, float] = (-180.0, 180.0)
SLIDER_RESOLUTION_TRANS: float = 0.1
SLIDER_RESOLUTION_ROT: float = 1.0

# == Default Settings / Misc ==
DEFAULT_OUTPUT_FILENAME: str = "adjusted_molecule.xyz"
DEFAULT_BENZENE_DISTANCE: float = 3.0  # Angstroms

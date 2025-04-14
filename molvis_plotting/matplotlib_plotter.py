"""
molvis_plotting/matplotlib_plotter.py

Provides functions for plotting molecular structures using Matplotlib.
"""

import sys
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Optional, Tuple, Any

# --- Matplotlib Specific Constants ---
MPL_RADIUS_TO_SCATTER_SCALE_BALL_STICK: float = 350.0
MPL_RADIUS_TO_SCATTER_SCALE_SPACE_FILLING: float = 500.0
MPL_LINE_WIDTH_LINES: float = 1.0
MPL_LINE_WIDTH_BALL_STICK: float = 4.0
MPL_PLOT_ELEVATION: float = 20.0
MPL_PLOT_AZIMUTH: float = 30.0

# Type alias for transformation state dictionary managed by UI layer
TransformState = Dict[
    str, np.ndarray
]  # Expects {'translation': vec (3,), 'rotation': mat (3x3)}

# --- Import Core Library Components ---
# Use absolute imports assuming molvis_core is accessible from project root
from molvis_core.molecule import Molecule
from molvis_core.constants import (
    STYLE_LINES,
    STYLE_BALL_STICK,
    STYLE_SPACE_FILLING,
    CPK_COLORS,
    COVALENT_RADII,
    VDW_RADII,
    DEFAULT_ATOM_COLOR,
    DEFAULT_BOND_COLOR,
    ATOM_EDGE_COLOR,
    DEFAULT_COVALENT_RADIUS,
    DEFAULT_VDW_RADIUS,
    # get_element_property is no longer imported from here
)

# Import helper function from its own module
from molvis_core.helpers import get_element_property
from molvis_core.geometry import apply_transform


def plot_molecules_matplotlib(
    ax: plt.Axes,
    molecules: List[Molecule],
    molecule_transforms: Dict[int, TransformState],
    style: str,
    global_offset: np.ndarray,
):
    """
    Plots molecules onto the provided 3D Matplotlib axes using specified styles.

    Applies individual transformations stored in `molecule_transforms` and the
    `global_offset` to the original coordinates of each molecule before plotting.

    Args:
        ax: The Matplotlib Axes3D object to plot onto. It will be cleared first.
        molecules: A list of core Molecule objects containing intrinsic data.
        molecule_transforms: A dictionary mapping molecule ID (int) to its current
                             transformation state {'translation': vec, 'rotation': mat}.
        style: The representation style string (e.g., STYLE_BALL_STICK).
        global_offset: A NumPy array (3,) representing the global system offset
                       to be added to all coordinates after individual transforms.
    """
    # ... (Function implementation remains the same as previous version) ...
    ax.clear()
    all_final_coords_list = []
    mol_colors_mpl = plt.cm.tab20

    if not molecules:
        ax.set_title("No molecules loaded.")
        ax.set_xlabel("X (Å)")
        ax.set_ylabel("Y (Å)")
        ax.set_zlabel("Z (Å)")
        return

    for idx, molecule in enumerate(molecules):
        if molecule.num_atoms == 0:
            continue
        transform_state = molecule_transforms.get(
            molecule.id, {"translation": np.zeros(3), "rotation": np.identity(3)}
        )
        current_rotation = transform_state["rotation"]
        current_translation = transform_state["translation"]
        # Use imported geometry function
        transformed_coords_relative = apply_transform(
            coords=molecule.coords,
            rotation_matrix=current_rotation,
            translation_vector=current_translation,
            center_of_rotation=molecule.centroid,
        )
        final_coords = transformed_coords_relative + global_offset
        all_final_coords_list.append(final_coords)
        symbols = molecule.symbols
        x, y, z = final_coords.T
        # Use imported helper function
        atom_colors = get_element_property(symbols, CPK_COLORS, DEFAULT_ATOM_COLOR)
        show_label = molecule.name if idx < 15 else None

        try:
            if style == STYLE_LINES:
                ax.scatter(
                    x,
                    y,
                    z,
                    c=atom_colors,
                    s=10,
                    edgecolors=ATOM_EDGE_COLOR,
                    linewidths=0.5,
                    depthshade=True,
                    label=show_label,
                )
                for i, j in molecule.bonds:
                    if 0 <= i < len(final_coords) and 0 <= j < len(final_coords):
                        bond_coords = final_coords[[i, j]]
                        ax.plot(
                            bond_coords[:, 0],
                            bond_coords[:, 1],
                            bond_coords[:, 2],
                            color=DEFAULT_BOND_COLOR,
                            linewidth=MPL_LINE_WIDTH_LINES,
                        )
            elif style == STYLE_BALL_STICK:
                radii = get_element_property(
                    symbols, COVALENT_RADII, DEFAULT_COVALENT_RADIUS
                )
                sizes = [(r**2) * MPL_RADIUS_TO_SCATTER_SCALE_BALL_STICK for r in radii]
                ax.scatter(
                    x,
                    y,
                    z,
                    c=atom_colors,
                    s=sizes,
                    edgecolors=ATOM_EDGE_COLOR,
                    linewidths=0.5,
                    depthshade=True,
                    label=show_label,
                )
                for i, j in molecule.bonds:
                    if 0 <= i < len(final_coords) and 0 <= j < len(final_coords):
                        bond_coords = final_coords[[i, j]]
                        ax.plot(
                            bond_coords[:, 0],
                            bond_coords[:, 1],
                            bond_coords[:, 2],
                            color=DEFAULT_BOND_COLOR,
                            linewidth=MPL_LINE_WIDTH_BALL_STICK,
                            solid_capstyle="round",
                        )
            elif style == STYLE_SPACE_FILLING:
                radii = get_element_property(symbols, VDW_RADII, DEFAULT_VDW_RADIUS)
                sizes = [
                    (r**2) * MPL_RADIUS_TO_SCATTER_SCALE_SPACE_FILLING for r in radii
                ]
                ax.scatter(
                    x,
                    y,
                    z,
                    c=atom_colors,
                    s=sizes,
                    edgecolors=None,
                    linewidths=0,
                    depthshade=True,
                    label=show_label,
                )
            else:
                ax.scatter(x, y, z, label=f"{molecule.name} (Unknown Style)")
        except Exception as e:
            print(
                f"Error plotting molecule {molecule.name} (ID: {molecule.id}): {e}",
                file=sys.stderr,
            )

    ax.set_xlabel("X (Å)")
    ax.set_ylabel("Y (Å)")
    ax.set_zlabel("Z (Å)")
    ax.set_title(f"Molecule Visualization ({style})")
    if not all_final_coords_list:
        ax.set_title(f"No molecules plotted ({style})")
        return
    try:
        all_final_coords_array = np.vstack(all_final_coords_list)
        if all_final_coords_array.size == 0:
            ax.set_title(f"No coordinates plotted ({style})")
            return
        min_coords = np.min(all_final_coords_array, axis=0)
        max_coords = np.max(all_final_coords_array, axis=0)
        center = (max_coords + min_coords) / 2.0
        ranges = max_coords - min_coords
        buffer = max(1.0, np.max(ranges) * 0.1)
        max_range_dim = (np.max(ranges) / 2.0) + buffer
        if max_range_dim <= buffer:
            max_range_dim = buffer * 2
        ax.set_xlim(center[0] - max_range_dim, center[0] + max_range_dim)
        ax.set_ylim(center[1] - max_range_dim, center[1] + max_range_dim)
        ax.set_zlim(center[2] - max_range_dim, center[2] + max_range_dim)
    except ValueError as e:
        print(f"Error calculating axis limits: {e}", file=sys.stderr)
        ax.set_title(f"Molecule Visualization ({style}) - Axis Limit Error")
    ax.view_init(elev=MPL_PLOT_ELEVATION, azim=MPL_PLOT_AZIMUTH)
    num_mols_plotted = len(all_final_coords_list)
    if num_mols_plotted > 1 and num_mols_plotted <= 15:
        ax.legend(
            title="Molecules",
            fontsize="small",
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
        )

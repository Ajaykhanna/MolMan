"""
molvis_plotting/plotly_plotter.py

Provides functions for plotting molecular structures using Plotly,
generating interactive figures.
"""

import sys
import plotly.graph_objects as go
import numpy as np
from typing import List, Dict, Optional, Tuple, Any

# --- Plotly Specific Constants ---
PLOTLY_RADIUS_TO_SIZE_BALL_STICK: float = 18.0
PLOTLY_RADIUS_TO_SIZE_SPACE_FILLING: float = 25.0
PLOTLY_LINE_WIDTH_LINES: float = 2.0
PLOTLY_LINE_WIDTH_BALL_STICK: float = 6.0

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


def plot_molecules_plotly(
    molecules: List[Molecule],
    molecule_transforms: Dict[int, TransformState],
    style: str,
    global_offset: np.ndarray,
) -> go.Figure:
    """
    Creates an interactive Plotly 3D figure of the molecules.

    Applies individual transformations stored in `molecule_transforms` and the
    `global_offset` to the original coordinates of each molecule before plotting.

    Args:
        molecules: A list of core Molecule objects containing intrinsic data.
        molecule_transforms: A dictionary mapping molecule ID (int) to its current
                             transformation state {'translation': vec, 'rotation': mat}.
        style: The representation style string (e.g., STYLE_BALL_STICK).
        global_offset: A NumPy array (3,) representing the global system offset.

    Returns:
        A plotly.graph_objects.Figure object containing the visualization.
    """
    # ... (Function implementation remains the same as previous version) ...
    fig = go.Figure()
    bond_x, bond_y, bond_z = [], [], []
    if not molecules:
        fig.update_layout(title="No molecules loaded.")
        return fig

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
        if final_coords.size == 0:
            continue
        symbols = molecule.symbols
        x, y, z = final_coords.T
        # Use imported helper function
        atom_colors = get_element_property(symbols, CPK_COLORS, DEFAULT_ATOM_COLOR)
        hover_texts = [
            f"{molecule.name}<br>Atom {i}: {s}<br>Pos: ({px:.3f}, {py:.3f}, {pz:.3f})"
            for i, (s, px, py, pz) in enumerate(zip(symbols, x, y, z))
        ]
        marker_props = dict(
            color=atom_colors,
            symbol="circle",
            line=dict(color=ATOM_EDGE_COLOR, width=0.5),
        )
        atom_visible = True
        trace_name = molecule.name
        if style == STYLE_LINES:
            marker_props["size"] = 3
        elif style == STYLE_BALL_STICK:
            radii = get_element_property(
                symbols, COVALENT_RADII, DEFAULT_COVALENT_RADIUS
            )
            marker_props["size"] = [r * PLOTLY_RADIUS_TO_SIZE_BALL_STICK for r in radii]
        elif style == STYLE_SPACE_FILLING:
            radii = get_element_property(symbols, VDW_RADII, DEFAULT_VDW_RADIUS)
            marker_props["size"] = [
                r * PLOTLY_RADIUS_TO_SIZE_SPACE_FILLING for r in radii
            ]
            marker_props["line"]["width"] = 0
        else:
            marker_props["size"] = 5
            atom_visible = False
        if atom_visible:
            try:
                fig.add_trace(
                    go.Scatter3d(
                        x=x,
                        y=y,
                        z=z,
                        mode="markers",
                        marker=marker_props,
                        name=trace_name,
                        legendgroup=trace_name,
                        hoverinfo="text",
                        text=hover_texts,
                    )
                )
            except Exception as e:
                print(
                    f"Error adding atom trace for molecule {molecule.name} (ID: {molecule.id}): {e}",
                    file=sys.stderr,
                )
        show_bonds = style == STYLE_LINES or style == STYLE_BALL_STICK
        if show_bonds:
            for i, j in molecule.bonds:
                if 0 <= i < len(final_coords) and 0 <= j < len(final_coords):
                    bond_x.extend([final_coords[i, 0], final_coords[j, 0], None])
                    bond_y.extend([final_coords[i, 1], final_coords[j, 1], None])
                    bond_z.extend([final_coords[i, 2], final_coords[j, 2], None])
    if bond_x:
        bond_line_width = (
            PLOTLY_LINE_WIDTH_LINES
            if style == STYLE_LINES
            else PLOTLY_LINE_WIDTH_BALL_STICK
        )
        try:
            fig.add_trace(
                go.Scatter3d(
                    x=bond_x,
                    y=bond_y,
                    z=bond_z,
                    mode="lines",
                    line=dict(color=DEFAULT_BOND_COLOR, width=bond_line_width),
                    hoverinfo="none",
                    showlegend=False,
                    name="Bonds",
                )
            )
        except Exception as e:
            print(f"Error adding bond trace: {e}", file=sys.stderr)
    axis_settings = dict(
        showbackground=True,
        backgroundcolor="#FFFFFF",
        showticklabels=True,
        tickcolor="rgb(127,127,127)",
        ticklen=5,
        showgrid=True,
        gridcolor="rgb(220, 220, 220)",
        zeroline=False,
        zerolinecolor="rgb(255, 255, 255)",
        titlefont=dict(color="black"),
        tickfont=dict(color="black"),
    )
    scene_dict = dict(
        xaxis=dict(**axis_settings, title="X (Å)"),
        yaxis=dict(**axis_settings, title="Y (Å)"),
        zaxis=dict(**axis_settings, title="Z (Å)"),
        aspectmode="data",
    )
    fig.update_layout(
        title=f"Molecule Visualization ({style})",
        scene=scene_dict,
        showlegend=True,
        legend=dict(
            title="Molecules",
            itemsizing="constant",
            x=0.01,
            y=0.99,
            bgcolor="rgba(255,255,255,0.6)",
        ),
        margin=dict(l=0, r=0, b=0, t=40),
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    return fig

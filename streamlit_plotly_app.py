# --- Streamlit App for Molecule Visualization ---
# Developed by: Ajay Khanna, ChatGPT-4o, and Google Gemini 2.5 Pro Experimental
# Date: April.09.2025

import streamlit as st
import plotly.graph_objects as go
import numpy as np
from typing import List, Tuple, Dict, Optional, FrozenSet, Any
from dataclasses import dataclass, field
import io
import copy

# --- Constants ---
# == Representation Styles ==
STYLE_LINES = "Lines"
STYLE_BALL_STICK = "Ball and Stick"
STYLE_SPACE_FILLING = "Space Filling"
REPRESENTATION_STYLES = [STYLE_LINES, STYLE_BALL_STICK, STYLE_SPACE_FILLING]
DEFAULT_REPRESENTATION = STYLE_BALL_STICK
# == Colors (CPK) ==
CPK_COLORS: Dict[str, str] = {
    "H": "white",
    "C": "#222222",
    "N": "blue",
    "O": "red",
    "F": "green",
    "Cl": "green",
    "Br": "darkred",
    "I": "purple",
    "He": "cyan",
    "Ne": "cyan",
    "Ar": "cyan",
    "Xe": "cyan",
    "Kr": "cyan",
    "P": "orange",
    "S": "yellow",
    "B": "pink",
    "Li": "violet",
    "Na": "violet",
    "K": "violet",
    "Rb": "violet",
    "Cs": "violet",
    "Fr": "violet",
    "Be": "darkgreen",
    "Mg": "darkgreen",
    "Ca": "darkgreen",
    "Sr": "darkgreen",
    "Ba": "darkgreen",
    "Ra": "darkgreen",
    "Ti": "gray",
    "Fe": "darkorange",
}
DEFAULT_ATOM_COLOR = "pink"
DEFAULT_BOND_COLOR = "#555555"
ATOM_EDGE_COLOR = "black"
# == Radii (in Angstroms) ==
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
}
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
    "B": 1.92,
    "Li": 1.82,
    "Na": 2.27,
    "K": 2.75,
    "Mg": 1.73,
    "Ca": 2.31,
    "Fe": 2.00,
    "Ti": 2.00,
}
DEFAULT_COVALENT_RADIUS = 0.6
DEFAULT_VDW_RADIUS = 1.5
# == Plotly Scale Factors & Line Widths ==
RADIUS_TO_PLOTLY_SIZE_BALL_STICK = 18
RADIUS_TO_PLOTLY_SIZE_SPACE_FILLING = 25
LINE_WIDTH_LINES_PLOTLY = 2
LINE_WIDTH_BALL_STICK_PLOTLY = 6
# == Bond Calculation ==
AVERAGE_BOND_LENGTHS: Dict[FrozenSet[str], float] = {
    frozenset(["C", "C"]): 1.53,
    frozenset(["C", "N"]): 1.47,
    frozenset(["C", "O"]): 1.42,
    frozenset(["C", "H"]): 1.09,
    frozenset(["N", "H"]): 1.00,
    frozenset(["O", "H"]): 0.96,
}
BOND_TOLERANCE: float = 0.3
# == GUI Constants ==
SLIDER_TRANSLATION_RANGE: Tuple[float, float] = (-10.0, 10.0)
SLIDER_ROTATION_RANGE: Tuple[float, float] = (-180.0, 180.0)
SLIDER_RESOLUTION_TRANS: float = 0.1
SLIDER_RESOLUTION_ROT: float = 1.0
DEFAULT_OUTPUT_FILENAME: str = "combined_adjusted_molecule.xyz"
# Format strings for slider value labels (Not directly used in Streamlit UI like Tkinter)
# FORMAT_TRANS = "{:.1f}"; FORMAT_ROT = "{:.0f}"


# --- Data Structures ---
@dataclass
class Molecule:
    """
    Represents a molecule with atomic symbols, coordinates, bonds, and transformations.

    Attributes:
        symbols: List of atomic symbols.
        coords: Original atomic coordinates.
        bonds: List of bonds as tuples of atom indices.
        id: Unique identifier for the molecule.
        name: Name of the molecule.
        source_file_index: Index of the source file.
        source_file_name: Name of the source file.
        transformed_coords: Transformed atomic coordinates.
        final_translation: Final translation vector applied to the molecule.
        final_rotation_matrix: Final rotation matrix applied to the molecule.
    """

    symbols: List[str]
    coords: np.ndarray
    bonds: List[Tuple[int, int]]
    id: int
    name: str
    source_file_index: int
    source_file_name: str
    transformed_coords: np.ndarray = field(init=False)
    final_translation: np.ndarray = field(default_factory=lambda: np.zeros(3))
    final_rotation_matrix: np.ndarray = field(default_factory=lambda: np.identity(3))

    def __post_init__(self):
        """Initializes transformed coordinates based on the final transformation."""
        self.apply_final_transformation()

    def reset_transformation(self):
        """Resets translation and rotation to their default states."""
        self.final_translation = np.zeros(3)
        self.final_rotation_matrix = np.identity(3)
        self.apply_final_transformation()

    @property
    def centroid(self) -> np.ndarray:
        """Calculates the geometric centroid of the molecule."""
        return np.mean(self.coords, axis=0) if self.coords.size > 0 else np.zeros(3)

    def apply_final_transformation(self):
        """
        Applies the final rotation and translation to the original coordinates
        to compute the transformed coordinates.
        """
        if self.coords.size == 0:
            self.transformed_coords = np.array([])
            return
        original_centroid = self.centroid
        coords_centered = self.coords - original_centroid
        coords_rotated = coords_centered @ self.final_rotation_matrix.T
        coords_recentered = coords_rotated + original_centroid
        self.transformed_coords = coords_recentered + self.final_translation


# --- Helper Functions ---
def get_element_property(
    symbols: List[str], property_dict: Dict[str, Any], default_value: Any
) -> List[Any]:
    """
    Retrieves a property (e.g., color, radius) for a list of atomic symbols.

    Args:
        symbols: List of atomic symbols.
        property_dict: Dictionary mapping symbols to properties.
        default_value: Default value if a symbol is not found.

    Returns:
        List of properties corresponding to the symbols.
    """
    return [property_dict.get(s.capitalize(), default_value) for s in symbols]


def build_rotation_matrix(
    angle_x_deg: float, angle_y_deg: float, angle_z_deg: float
) -> np.ndarray:
    """
    Constructs a 3D rotation matrix using ZYX Tait-Bryan angles.

    Args:
        angle_x_deg: Rotation angle around the X-axis in degrees.
        angle_y_deg: Rotation angle around the Y-axis in degrees.
        angle_z_deg: Rotation angle around the Z-axis in degrees.

    Returns:
        A 3x3 rotation matrix.
    """
    theta_x, theta_y, theta_z = (
        np.radians(angle_x_deg),
        np.radians(angle_y_deg),
        np.radians(angle_z_deg),
    )
    cos_x, sin_x = np.cos(theta_x), np.sin(theta_x)
    cos_y, sin_y = np.cos(theta_y), np.sin(theta_y)
    cos_z, sin_z = np.cos(theta_z), np.sin(theta_z)
    R_x = np.array([[1, 0, 0], [0, cos_x, -sin_x], [0, sin_x, cos_x]])
    R_y = np.array([[cos_y, 0, sin_y], [0, 1, 0], [-sin_y, 0, cos_y]])
    R_z = np.array([[cos_z, -sin_z, 0], [sin_z, cos_z, 0], [0, 0, 1]])
    return R_z @ R_y @ R_x


# --- Core Logic Functions ---
def get_bond_distance_range(atom1: str, atom2: str) -> Optional[Tuple[float, float]]:
    """
    Determines the minimum and maximum bond distance for two atom types.

    Args:
        atom1: Symbol of the first atom.
        atom2: Symbol of the second atom.

    Returns:
        A tuple of minimum and maximum bond distances, or None if not defined.
    """
    key = frozenset([atom1.capitalize(), atom2.capitalize()])
    average_length = AVERAGE_BOND_LENGTHS.get(key)
    if average_length is not None:
        min_distance = max(0.1, average_length - BOND_TOLERANCE)
        max_distance = average_length + BOND_TOLERANCE
        return min_distance, max_distance
    else:
        return None


def determine_bonds(symbols: List[str], coords: np.ndarray) -> List[Tuple[int, int]]:
    """
    Identifies bonds between atoms based on their types and distances.

    Args:
        symbols: List of atomic symbols.
        coords: Atomic coordinates.

    Returns:
        List of bonds as tuples of atom indices.
    """
    bonds: List[Tuple[int, int]] = []
    num_atoms = len(symbols)
    if num_atoms < 2:
        return bonds
    for i in range(num_atoms):
        for j in range(i + 1, num_atoms):
            atom1 = symbols[i]
            atom2 = symbols[j]
            bond_range = get_bond_distance_range(atom1, atom2)
            if bond_range is not None:
                min_dist_sq = bond_range[0] ** 2
                max_dist_sq = bond_range[1] ** 2
                delta = coords[i] - coords[j]
                distance_sq = np.dot(delta, delta)
                if min_dist_sq <= distance_sq <= max_dist_sq:
                    bonds.append((i, j))
    return bonds


def load_xyz_from_text(
    xyz_text: str, source_name: str = "Pasted Text"
) -> Tuple[Optional[List[str]], Optional[np.ndarray]]:
    """
    Parses atomic symbols and coordinates from an XYZ file format string.

    Args:
        xyz_text: Content of the XYZ file as a string.
        source_name: Name of the source (for error reporting).

    Returns:
        A tuple containing a list of symbols and a NumPy array of coordinates.
    """
    symbols: List[str] = []
    coords_list: List[List[float]] = []
    lines = xyz_text.strip().splitlines()
    if not lines:
        st.error(f"Input source '{source_name}' is empty.")
        return None, None
    try:
        atom_count_str = lines[0].strip()
        atom_count = int(lines[0].strip())
    except (ValueError, IndexError):
        st.error(f"First line of '{source_name}' must be number of atoms.")
        return None, None
    if len(lines) < 2:
        st.error(f"'{source_name}' must have at least 2 lines.")
        return None, None
    coord_lines = lines[2:]
    actual_atom_count = 0
    for i, line in enumerate(coord_lines):
        if actual_atom_count >= atom_count:
            if i < len(coord_lines):
                st.warning(
                    f"'{source_name}': Stopped reading at line {i+3} (header count {atom_count} reached)."
                )
            break
        parts = line.strip().split()
        if not parts:
            continue
        if len(parts) < 4:
            st.warning(
                f"'{source_name}' Line {i+3} malformed: '{line.strip()}'. Skipping."
            )
            continue
        try:
            symbols.append(parts[0])
            coords_list.append(list(map(float, parts[1:4])))
            actual_atom_count += 1
        except ValueError as e:
            st.warning(
                f"'{source_name}' Error parsing coords line {i+3}: {e}. Skipping."
            )
            continue
    if actual_atom_count == 0 and atom_count > 0:
        st.error(f"'{source_name}': No valid coordinate lines found.")
        return None, None
    if actual_atom_count != atom_count:
        st.warning(
            f"'{source_name}': Found {actual_atom_count} atoms, header said {atom_count}."
        )
    return symbols, np.array(coords_list)


# --- Transformation Helper ---
# --- Plotting Function (Using Plotly) ---
def plot_molecules_plotly(
    molecules: List[Molecule], style: str, global_offset: np.ndarray
) -> go.Figure:
    """
    Creates a 3D Plotly visualization of molecules.

    Args:
        molecules: List of Molecule objects to visualize.
        style: Visualization style (e.g., "Lines", "Ball and Stick").
        global_offset: Global offset to apply to all molecules.

    Returns:
        A Plotly Figure object.
    """
    fig = go.Figure()
    all_coords_list = []  # To determine axis ranges later
    bond_x, bond_y, bond_z = [], [], []

    for idx, molecule in enumerate(molecules):
        # Use transformed_coords which already reflect individual final transforms
        coords_relative = molecule.transformed_coords
        if coords_relative.size == 0:
            continue

        # Apply global offset for final plotting position
        final_coords = coords_relative + global_offset
        all_coords_list.append(final_coords)  # Use these for limits

        symbols = molecule.symbols
        x, y, z = final_coords.T  # Plot final positions

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
            marker_props["size"] = [r * RADIUS_TO_PLOTLY_SIZE_BALL_STICK for r in radii]
        elif style == STYLE_SPACE_FILLING:
            radii = get_element_property(symbols, VDW_RADII, DEFAULT_VDW_RADIUS)
            marker_props["size"] = [
                r * RADIUS_TO_PLOTLY_SIZE_SPACE_FILLING for r in radii
            ]
            marker_props["line"]["width"] = 0
        else:
            marker_props["size"] = 5
            atom_visible = False

        if atom_visible:
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

        show_bonds = style == STYLE_LINES or style == STYLE_BALL_STICK
        if show_bonds:
            for i, j in molecule.bonds:
                if 0 <= i < len(final_coords) and 0 <= j < len(final_coords):
                    bond_x.extend([final_coords[i, 0], final_coords[j, 0], None])
                    bond_y.extend([final_coords[i, 1], final_coords[j, 1], None])
                    bond_z.extend([final_coords[i, 2], final_coords[j, 2], None])

    if bond_x:
        bond_line_width = (
            LINE_WIDTH_LINES_PLOTLY
            if style == STYLE_LINES
            else LINE_WIDTH_BALL_STICK_PLOTLY
        )
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

    # --- Layout ---
    axis_settings = dict(
        showbackground=False,
        showticklabels=True,
        showgrid=True,
        zeroline=False,
        titlefont=dict(color="black"),
        gridcolor="lightgrey",
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
        legend=dict(title="Molecules", itemsizing="constant", x=0.01, y=0.99),
        margin=dict(l=0, r=0, b=0, t=40),
    )

    return fig


# --- Centroid Helper ---
def calculate_overall_centroid(
    molecules: List[Molecule], global_offset: np.ndarray
) -> Optional[np.ndarray]:
    """
    Computes the overall centroid of all visible molecules.

    Args:
        molecules: List of Molecule objects.
        global_offset: Global offset applied to the system.

    Returns:
        The centroid as a NumPy array, or None if no coordinates are available.
    """
    if not molecules:
        return None
    all_coords = []
    for mol in molecules:
        final_coords = mol.transformed_coords + global_offset
        if final_coords.size > 0:
            all_coords.append(final_coords)
    if not all_coords:
        return None
    try:
        combined_coords = np.vstack(all_coords)
    except ValueError:
        return None
    return np.mean(combined_coords, axis=0)


# --- Main Streamlit App ---
def main():
    """
    Main function for the Streamlit app. Handles UI, input processing,
    molecule visualization, and transformations.
    """
    st.set_page_config(layout="wide", page_title="Molecule Visualizer")
    st.title("🧪 Interactive Molecule Visualizer (Streamlit + Plotly)")

    # --- Initialize Session State ---
    st.session_state.setdefault("molecule_data", None)  # List[Molecule] or None
    st.session_state.setdefault("input_processed", False)
    st.session_state.setdefault(
        "input_source_key", None
    )  # Key representing current input(s)
    st.session_state.setdefault(
        "selected_mol_names", []
    )  # Stores names from multiselect
    st.session_state.setdefault(
        "prev_selected_mol_names", []
    )  # Stores previous selection for comparison
    st.session_state.setdefault("download_content", None)
    st.session_state.setdefault("show_download", False)
    st.session_state.setdefault("current_style", DEFAULT_REPRESENTATION)
    st.session_state.setdefault("global_offset", np.zeros(3))  # Global system offset
    # Slider state variables
    st.session_state.setdefault("slider_trans_x", 0.0)
    st.session_state.setdefault("slider_trans_y", 0.0)
    st.session_state.setdefault("slider_trans_z", 0.0)
    st.session_state.setdefault("slider_rot_x", 0.0)
    st.session_state.setdefault("slider_rot_y", 0.0)
    st.session_state.setdefault("slider_rot_z", 0.0)
    # Target centroid state
    st.session_state.setdefault("target_centroid_x", 0.0)
    st.session_state.setdefault("target_centroid_y", 0.0)
    st.session_state.setdefault("target_centroid_z", 0.0)

    # --- Input Handling ---
    st.sidebar.header("1. Load Molecule Data")
    input_option = st.sidebar.radio(
        "Input method:", ("Upload XYZ File(s)", "Paste XYZ Content"), key="input_option"
    )
    current_input_key = None
    files_to_process: List[Tuple[str, str]] = []
    input_changed = False
    if input_option == "Upload XYZ File(s)":
        uploaded_files = st.sidebar.file_uploader(
            "Upload .xyz file(s)",
            type=["xyz"],
            accept_multiple_files=True,
            key="file_uploader",
        )
        if uploaded_files:
            current_input_key = tuple(
                sorted([(f.name, f.size) for f in uploaded_files])
            )
            if st.session_state.input_source_key != current_input_key:
                st.session_state.input_source_key = current_input_key
                st.session_state.input_processed = False
                input_changed = True
                for uploaded_file in uploaded_files:
                    try:
                        files_to_process.append(
                            (
                                uploaded_file.name,
                                uploaded_file.getvalue().decode("utf-8"),
                            )
                        )
                    except Exception as e:
                        st.sidebar.error(f"Error reading {uploaded_file.name}: {e}")
                        files_to_process = []
                        st.session_state.input_source_key = None
                        break
        else:
            if st.session_state.input_source_key and isinstance(
                st.session_state.input_source_key, tuple
            ):
                st.session_state.input_source_key = None
                st.session_state.input_processed = False
                st.session_state.molecule_data = None
                input_changed = True
    else:  # Paste
        pasted_text = st.sidebar.text_area(
            "Paste single XYZ content here", height=150, key="paste_area"
        )
        if pasted_text:
            current_input_key = hash(pasted_text)
            if st.session_state.input_source_key != current_input_key:
                st.session_state.input_source_key = current_input_key
                st.session_state.input_processed = False
                input_changed = True
                files_to_process.append(("Pasted Text", pasted_text))
        else:
            if st.session_state.input_source_key and isinstance(
                st.session_state.input_source_key, int
            ):
                st.session_state.input_source_key = None
                st.session_state.input_processed = False
                st.session_state.molecule_data = None
                input_changed = True

    # --- Data Processing Step ---
    if input_changed and files_to_process:
        st.session_state.molecule_data = None
        all_molecules = []
        global_mol_index = 0
        valid_data_found = False
        with st.spinner(f"Processing {len(files_to_process)} source(s)..."):
            for file_idx, (file_name, file_content) in enumerate(files_to_process):
                symbols, coords = load_xyz_from_text(
                    file_content, source_name=file_name
                )
                if symbols is not None and coords is not None and len(symbols) > 0:
                    bonds = determine_bonds(symbols, coords)
                    base_name = file_name if len(files_to_process) > 1 else "Molecule"
                    if base_name == "Pasted Text" and len(files_to_process) == 1:
                        base_name = "Molecule"
                    mol_name = f"{base_name}"  # Simplified name
                    molecule = Molecule(
                        symbols=symbols,
                        coords=coords,
                        bonds=bonds,
                        id=global_mol_index,
                        name=mol_name,
                        source_file_index=file_idx,
                        source_file_name=file_name,
                    )
                    all_molecules.append(molecule)
                    global_mol_index += 1
                    valid_data_found = True
                else:
                    st.warning(
                        f"Skipping '{file_name}' due to loading errors or no atoms found."
                    )
        if valid_data_found:
            st.session_state.molecule_data = all_molecules
            st.session_state.input_processed = True
            # Reset state related to previous data
            st.session_state.selected_mol_names = [m.name for m in all_molecules][:1]
            st.session_state.prev_selected_mol_names = copy.deepcopy(
                st.session_state.selected_mol_names
            )  # Initialize prev selection
            st.session_state.global_offset = np.zeros(3)
            st.session_state.slider_trans_x = 0.0
            st.session_state.slider_trans_y = 0.0
            st.session_state.slider_trans_z = 0.0
            st.session_state.slider_rot_x = 0.0
            st.session_state.slider_rot_y = 0.0
            st.session_state.slider_rot_z = 0.0
            st.sidebar.success(f"{len(all_molecules)} molecule(s) loaded.")
            st.rerun()  # Rerun to update UI
        else:
            st.error("Failed to load valid molecules.")
            st.session_state.molecule_data = None
            st.session_state.input_processed = False

    # --- Display Area ---
    if not st.session_state.get("molecule_data"):
        st.info("⬅️ Please upload XYZ file(s) or paste content in the sidebar.")
        st.subheader("XYZ Format:")
        st.code(
            """[Number of Atoms]\n[Comment Line]\n[Element] [X] [Y] [Z]\n...""",
            language="text",
        )
        return

    # Data is ready
    molecules: List[Molecule] = st.session_state.molecule_data
    molecule_names = [m.name for m in molecules]
    mol_name_to_id_map = {m.name: m.id for m in molecules}

    # --- Sidebar Controls ---
    st.sidebar.header("2. Visualization")
    current_style = st.sidebar.selectbox(
        "Representation Style",
        REPRESENTATION_STYLES,
        index=REPRESENTATION_STYLES.index(st.session_state.current_style),
        key="style_select",
    )
    st.session_state.current_style = current_style

    st.sidebar.header("3. Transformations")
    # Molecule Selection
    selected_mol_names = st.sidebar.multiselect(
        "Modify Molecules:",
        molecule_names,
        default=st.session_state.selected_mol_names,
        key="mol_select",
    )

    # --- Slider Sync Logic ---
    # Check if selection changed since last run
    if set(selected_mol_names) != set(st.session_state.prev_selected_mol_names):
        print(f"Selection changed: {selected_mol_names}")
        if len(selected_mol_names) == 1:
            selected_id = mol_name_to_id_map.get(selected_mol_names[0])
            selected_mol = next((m for m in molecules if m.id == selected_id), None)
            if selected_mol:
                print(f"  Syncing sliders to '{selected_mol.name}'")
                # Update session state vars that control slider values for the *next* rerun
                st.session_state.slider_trans_x = selected_mol.final_translation[0]
                st.session_state.slider_trans_y = selected_mol.final_translation[1]
                st.session_state.slider_trans_z = selected_mol.final_translation[2]
                st.session_state.slider_rot_x = 0.0  # Reset rotation
                st.session_state.slider_rot_y = 0.0
                st.session_state.slider_rot_z = 0.0
            else:  # Should not happen if name map is correct
                print(
                    "  Warning: Selected molecule not found for sync. Resetting sliders."
                )
                st.session_state.slider_trans_x = 0.0
                st.session_state.slider_trans_y = 0.0
                st.session_state.slider_trans_z = 0.0
                st.session_state.slider_rot_x = 0.0
                st.session_state.slider_rot_y = 0.0
                st.session_state.slider_rot_z = 0.0
        else:  # 0 or >1 selected
            print(f"  Selection count is {len(selected_mol_names)}. Resetting sliders.")
            st.session_state.slider_trans_x = 0.0
            st.session_state.slider_trans_y = 0.0
            st.session_state.slider_trans_z = 0.0
            st.session_state.slider_rot_x = 0.0
            st.session_state.slider_rot_y = 0.0
            st.session_state.slider_rot_z = 0.0
        # Update previous selection and trigger rerun to show synced/reset sliders
        st.session_state.prev_selected_mol_names = copy.deepcopy(selected_mol_names)
        st.rerun()

    # Draw Sliders using session state for value
    trans_x = st.sidebar.slider(
        "Translate X (Å)",
        SLIDER_TRANSLATION_RANGE[0],
        SLIDER_TRANSLATION_RANGE[1],
        st.session_state.slider_trans_x,
        SLIDER_RESOLUTION_TRANS,
        key="tx",
        format="%.1f",
    )
    trans_y = st.sidebar.slider(
        "Translate Y (Å)",
        SLIDER_TRANSLATION_RANGE[0],
        SLIDER_TRANSLATION_RANGE[1],
        st.session_state.slider_trans_y,
        SLIDER_RESOLUTION_TRANS,
        key="ty",
        format="%.1f",
    )
    trans_z = st.sidebar.slider(
        "Translate Z (Å)",
        SLIDER_TRANSLATION_RANGE[0],
        SLIDER_TRANSLATION_RANGE[1],
        st.session_state.slider_trans_z,
        SLIDER_RESOLUTION_TRANS,
        key="tz",
        format="%.1f",
    )
    rot_x = st.sidebar.slider(
        "Rotate X (°)",
        SLIDER_ROTATION_RANGE[0],
        SLIDER_ROTATION_RANGE[1],
        st.session_state.slider_rot_x,
        SLIDER_RESOLUTION_ROT,
        key="rx",
        format="%d",
    )
    rot_y = st.sidebar.slider(
        "Rotate Y (°)",
        SLIDER_ROTATION_RANGE[0],
        SLIDER_ROTATION_RANGE[1],
        st.session_state.slider_rot_y,
        SLIDER_RESOLUTION_ROT,
        key="ry",
        format="%d",
    )
    rot_z = st.sidebar.slider(
        "Rotate Z (°)",
        SLIDER_ROTATION_RANGE[0],
        SLIDER_ROTATION_RANGE[1],
        st.session_state.slider_rot_z,
        SLIDER_RESOLUTION_ROT,
        key="rz",
        format="%d",
    )

    # Store current slider values back into session state for next run's default
    st.session_state.slider_trans_x = trans_x
    st.session_state.slider_trans_y = trans_y
    st.session_state.slider_trans_z = trans_z
    st.session_state.slider_rot_x = rot_x
    st.session_state.slider_rot_y = rot_y
    st.session_state.slider_rot_z = rot_z

    # --- Centroid and Reset Buttons ---
    st.sidebar.header("4. Centering & Reset")
    col1, col2 = st.sidebar.columns(2)
    center_selected_pressed = col1.button("Center Selected", key="center_sel")
    reset_pressed = col2.button("Reset View", key="reset_view")

    st.sidebar.subheader("System Centroid")
    center_origin_pressed = st.sidebar.button(
        "Center System at Origin", key="center_sys_o", use_container_width=True
    )

    st.sidebar.markdown("Move System Centroid to Target:")
    t_col1, t_col2, t_col3 = st.sidebar.columns(3)
    target_x = t_col1.number_input(
        "Target X",
        key="target_x",
        value=st.session_state.target_centroid_x,
        format="%.2f",
    )
    target_y = t_col2.number_input(
        "Target Y",
        key="target_y",
        value=st.session_state.target_centroid_y,
        format="%.2f",
    )
    target_z = t_col3.number_input(
        "Target Z",
        key="target_z",
        value=st.session_state.target_centroid_z,
        format="%.2f",
    )
    # Update state from number inputs
    st.session_state.target_centroid_x = target_x
    st.session_state.target_centroid_y = target_y
    st.session_state.target_centroid_z = target_z
    center_target_pressed = st.sidebar.button(
        "Move to Target", key="center_sys_t", use_container_width=True
    )

    # --- Apply Button Actions (State Modifications) ---
    # These modify state, the rerun will handle applying/redrawing
    if reset_pressed:
        print("Reset View button pressed")
        st.session_state.global_offset = np.zeros(3)
        for mol in molecules:
            mol.reset_transformation()
        # Reset slider state variables
        st.session_state.slider_trans_x = 0.0
        st.session_state.slider_trans_y = 0.0
        st.session_state.slider_trans_z = 0.0
        st.session_state.slider_rot_x = 0.0
        st.session_state.slider_rot_y = 0.0
        st.session_state.slider_rot_z = 0.0
        # Reset target inputs
        st.session_state.target_centroid_x = 0.0
        st.session_state.target_centroid_y = 0.0
        st.session_state.target_centroid_z = 0.0
        st.rerun()

    if center_selected_pressed:
        print("Center Selected button pressed")
        selected_indices_cs = [
            mol_name_to_id_map[name]
            for name in selected_mol_names
            if name in mol_name_to_id_map
        ]
        if not selected_indices_cs:
            st.warning("No molecules selected to center.")
        else:
            molecules_to_center = [m for m in molecules if m.id in selected_indices_cs]
            for molecule in molecules_to_center:
                if molecule.transformed_coords.size > 0:
                    mol_centroid = np.mean(molecule.transformed_coords, axis=0)
                    offset = -mol_centroid
                    molecule.final_translation += offset  # Modify stored state
                    molecule.apply_final_transformation()  # Update transformed_coords
            st.rerun()  # Rerun to show changes

    if center_origin_pressed:
        print("Center System Origin button pressed")
        current_centroid = calculate_overall_centroid(
            molecules, st.session_state.global_offset
        )
        if current_centroid is not None:
            offset_needed = -current_centroid
            st.session_state.global_offset += offset_needed  # Modify stored state
            st.rerun()  # Rerun to show changes
        else:
            st.warning("Cannot calculate system centroid.")

    if center_target_pressed:
        print("Center System Target button pressed")
        target_centroid = np.array(
            [target_x, target_y, target_z]
        )  # Read from number inputs
        current_centroid = calculate_overall_centroid(
            molecules, st.session_state.global_offset
        )
        if current_centroid is not None:
            offset_needed = target_centroid - current_centroid
            st.session_state.global_offset += offset_needed  # Modify stored state
            st.rerun()  # Rerun to show changes
        else:
            st.warning("Cannot calculate system centroid.")

    # --- Apply Transformations based on current slider values ---
    selected_indices_tf = [
        mol_name_to_id_map[name]
        for name in selected_mol_names
        if name in mol_name_to_id_map
    ]
    current_trans_vector = np.array(
        [trans_x, trans_y, trans_z]
    )  # Use values read from sliders this run
    current_rot_matrix = build_rotation_matrix(
        rot_x, rot_y, rot_z
    )  # Use values read from sliders this run

    # Update the final state for selected molecules based on current sliders
    # This allows the sliders to directly control the selected molecules' state
    if selected_indices_tf:
        # print(f"Applying slider transform to molecules: {selected_indices_tf}")
        for molecule in molecules:
            if molecule.id in selected_indices_tf:
                molecule.final_translation = current_trans_vector
                molecule.final_rotation_matrix = current_rot_matrix
                molecule.apply_final_transformation()  # Recalculate transformed_coords

    # --- Plotting ---
    st.header("Molecule View (Interactive)")
    st.caption("Click and drag to rotate, scroll to zoom, right-click drag to pan.")
    try:
        # Pass the current global offset from session state
        plotly_fig = plot_molecules_plotly(
            molecules, current_style, st.session_state.global_offset
        )
        st.plotly_chart(plotly_fig, use_container_width=True)
    except Exception as e:
        st.error(f"An error occurred during plotting: {e}")
        # import traceback; st.code(traceback.format_exc())

    # --- Save Functionality ---
    st.sidebar.header("5. Export")
    if st.sidebar.button("Prepare Combined Adjusted XYZ"):
        st.session_state.download_content = None
        st.session_state.show_download = False
        symbols_combined = []
        coords_to_save_list = []
        for molecule in st.session_state.molecule_data:  # Use data from session state
            symbols_combined.extend(molecule.symbols)
            # Save final displayed coordinates
            coords_to_save = (
                molecule.transformed_coords + st.session_state.global_offset
            )
            coords_to_save_list.append(coords_to_save)
        if not coords_to_save_list:
            st.sidebar.warning("No molecule data to save.")
        else:
            coords_combined_np = np.vstack(coords_to_save_list)
            total_atoms = len(symbols_combined)
            xyz_content = f"{total_atoms}\nCombined adjusted structure (Global Offset: {st.session_state.global_offset})\n"
            for symbol, coord in zip(symbols_combined, coords_combined_np):
                xyz_content += f"{symbol:<4} {coord[0]:>12.6f} {coord[1]:>12.6f} {coord[2]:>12.6f}\n"
            st.session_state.download_content = xyz_content
            st.session_state.show_download = True
            st.rerun()
    if st.session_state.get("show_download", False) and st.session_state.get(
        "download_content"
    ):
        st.sidebar.download_button(
            label="Download Combined XYZ",
            data=st.session_state.download_content,
            file_name="combined_adjusted_molecule.xyz",
            mime="text/plain",
            on_click=lambda: st.session_state.update(show_download=False),
        )


if __name__ == "__main__":
    main()

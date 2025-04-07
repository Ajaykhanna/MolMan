# Refactored Streamlit App with Plotly for Interactive Visualization
import streamlit as st

# Remove matplotlib import for plotting
# import matplotlib.pyplot as plt
import plotly.graph_objects as go  # Import Plotly
import numpy as np
from typing import List, Tuple, Dict, Optional, FrozenSet, Any
from dataclasses import dataclass, field
import io

# --- Constants ---
# == Representation Styles == (Keep these)
STYLE_LINES = "Lines"
STYLE_BALL_STICK = "Ball and Stick"
STYLE_SPACE_FILLING = "Space Filling"
REPRESENTATION_STYLES = [STYLE_LINES, STYLE_BALL_STICK, STYLE_SPACE_FILLING]
DEFAULT_REPRESENTATION = STYLE_BALL_STICK
# == Colors (CPK) == (Keep these)
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
# == Radii (in Angstroms) == (Keep these)
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

# == Plotly Scale Factors & Line Widths (ADJUSTED FOR PLOTLY) ==
# Plotly marker size is roughly diameter in pixels. Requires tuning.
RADIUS_TO_PLOTLY_SIZE_BALL_STICK = 18  # Adjust this factor
RADIUS_TO_PLOTLY_SIZE_SPACE_FILLING = 25  # Adjust this factor
LINE_WIDTH_LINES_PLOTLY = 2
LINE_WIDTH_BALL_STICK_PLOTLY = 6

# == Bond Calculation == (Keep these)
AVERAGE_BOND_LENGTHS: Dict[FrozenSet[str], float] = {
    frozenset(["C", "C"]): 1.53,
    frozenset(["C", "N"]): 1.47,
    frozenset(["C", "O"]): 1.42,
    frozenset(["C", "H"]): 1.09,
    frozenset(["N", "H"]): 1.00,
    frozenset(["O", "H"]): 0.96,
    frozenset(["S", "H"]): 1.02,
    frozenset(["N", "N"]): 1.35,
    frozenset(["C", "Br"]): 1.89,
}
BOND_TOLERANCE: float = 0.3


# --- Data Structures --- (Molecule class essentially the same)
@dataclass
class Molecule:
    symbols: List[str]
    coords: np.ndarray
    bonds: List[Tuple[int, int]]
    id: int
    name: str
    source_file_index: int
    source_file_name: str
    transformed_coords: np.ndarray = field(init=False)

    def __post_init__(self):
        self.reset_transformation()

    def reset_transformation(self):
        self.transformed_coords = self.coords.copy()

    @property
    def centroid(self) -> np.ndarray:
        return np.mean(self.coords, axis=0) if self.coords.size > 0 else np.zeros(3)

    def apply_transformation(self, translation: np.ndarray, rot_matrix: np.ndarray):
        if self.coords.size == 0:
            return
        original_centroid = self.centroid
        coords_centered = self.coords - original_centroid
        coords_rotated = coords_centered @ rot_matrix.T
        coords_recentered = coords_rotated + original_centroid
        self.transformed_coords = coords_recentered + translation


# --- Helper Functions --- (get_element_property, build_rotation_matrix - same)
def get_element_property(
    symbols: List[str], property_dict: Dict[str, Any], default_value: Any
) -> List[Any]:
    return [property_dict.get(s.capitalize(), default_value) for s in symbols]


def build_rotation_matrix(
    angle_x_deg: float, angle_y_deg: float, angle_z_deg: float
) -> np.ndarray:
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


# --- Core Logic Functions --- (get_bond_distance_range, determine_bonds, load_xyz_from_text - same)
def get_bond_distance_range(atom1: str, atom2: str) -> Optional[Tuple[float, float]]:
    key = frozenset([atom1.capitalize(), atom2.capitalize()])
    average_length = AVERAGE_BOND_LENGTHS.get(key)
    if average_length is not None:
        min_distance = max(0.1, average_length - BOND_TOLERANCE)
        max_distance = average_length + BOND_TOLERANCE
        return min_distance, max_distance
    else:
        return None


def determine_bonds(symbols: List[str], coords: np.ndarray) -> List[Tuple[int, int]]:
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
    symbols: List[str] = []
    coords_list: List[List[float]] = []
    lines = xyz_text.strip().splitlines()
    if not lines:
        st.error(f"Input source '{source_name}' is empty.")
        return None, None
    try:
        atom_count_str = lines[0].strip()
        atom_count = int(atom_count_str)
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


# --- Transformation Helper --- (apply_transformations - same)
def apply_transformations(
    molecules: List[Molecule],
    selected_indices: List[int],
    translation: np.ndarray,
    rotation_matrix: np.ndarray,
):
    for idx, molecule in enumerate(molecules):
        if idx in selected_indices:
            molecule.apply_transformation(translation, rotation_matrix)
        else:
            molecule.reset_transformation()


# --- Plotting Function (Using Plotly) ---
# --- Plotting Function (Using Plotly) ---
def plot_molecules_plotly(molecules: List[Molecule], style: str) -> go.Figure:
    """Creates an interactive Plotly 3D figure of the molecules."""
    fig = go.Figure()
    all_coords_list = []

    # --- Consolidated Bond Trace Data ---
    bond_x, bond_y, bond_z = [], [], []

    for idx, molecule in enumerate(molecules):
        coords = molecule.transformed_coords
        symbols = molecule.symbols
        if coords.size == 0:
            continue

        all_coords_list.append(coords)
        x, y, z = coords.T
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
        trace_name = molecule.name  # Use the unique molecule name

        # Determine marker size based on style
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
            marker_props["line"]["width"] = 0  # No edges for space filling
        else:
            marker_props["size"] = 5
            atom_visible = False

        # Add atom trace if visible for the style
        if atom_visible:
            fig.add_trace(
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=z,
                    mode="markers",
                    marker=marker_props,
                    name=trace_name,  # Name shown in legend
                    legendgroup=trace_name,  # **** Explicitly group by molecule name ****
                    hoverinfo="text",
                    text=hover_texts,
                )
            )

        # Prepare Bond Coordinates (Only for styles that show bonds)
        show_bonds = style == STYLE_LINES or style == STYLE_BALL_STICK
        if show_bonds:
            for i, j in molecule.bonds:
                if 0 <= i < len(coords) and 0 <= j < len(coords):
                    bond_x.extend([coords[i, 0], coords[j, 0], None])
                    bond_y.extend([coords[i, 1], coords[j, 1], None])
                    bond_z.extend([coords[i, 2], coords[j, 2], None])

    # --- Add Single Trace for All Bonds (if any exist) ---
    if bond_x:  # Only add if bonds were prepared
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
                showlegend=False,  # **** Make sure bonds trace is NOT in legend ****
                name="Bonds",  # Internal name
            )
        )

    # --- Layout and Axis Configuration --- (Same as before)
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
    # ... (Optional manual range setting logic) ...
    fig.update_layout(
        title=f"Molecule Visualization ({style})",
        scene=scene_dict,
        showlegend=True,
        legend=dict(title="Molecules", itemsizing="constant", x=0.01, y=0.99),
        margin=dict(l=0, r=0, b=0, t=40),
    )

    return fig


# --- Main Streamlit App ---
def main():
    st.set_page_config(layout="wide", page_title="Molecule Visualizer")
    st.title("🧪 Interactive Molecule Visualizer (Streamlit + Plotly)")

    # Initialize Session State
    st.session_state.setdefault("molecule_data", None)
    st.session_state.setdefault("input_processed", False)
    st.session_state.setdefault("input_source_key", None)
    st.session_state.setdefault("selected_mol_names", [])
    st.session_state.setdefault("download_content", None)
    st.session_state.setdefault("show_download", False)
    st.session_state.setdefault("current_style", DEFAULT_REPRESENTATION)

    # Input Handling
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

    # Data Processing
    if input_changed and files_to_process:
        # ... inside the `if input_changed and files_to_process:` block ...
        st.session_state.molecule_data = None  # Clear previous data
        all_molecules = []
        global_mol_index = 0
        valid_data_found = False
        # REMOVED: processing_spinner = st.empty()

        # CORRECTED: Use st.spinner directly as a context manager
        with st.spinner(f"Processing {len(files_to_process)} source(s)..."):
            for file_idx, (file_name, file_content) in enumerate(files_to_process):
                symbols, coords = load_xyz_from_text(
                    file_content, source_name=file_name
                )
                if symbols is not None and coords is not None and len(symbols) > 0:
                    bonds = determine_bonds(symbols, coords)
                    # Create simpler name: Use file name directly if multiple, or generic if single/pasted
                    base_name = file_name if len(files_to_process) > 1 else "Molecule"
                    if base_name == "Pasted Text" and len(files_to_process) == 1:
                        base_name = "Molecule"
                    mol_name = f"{base_name}"  # Simplifed name for legend/selection

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
                    # Error message handled by load_xyz_from_text or warning added
                    st.warning(
                        f"Skipping '{file_name}' due to loading errors or no atoms found."
                    )
        # REMOVED: processing_spinner.empty() # Not needed with 'with' statement

        # --- After processing ---
        if valid_data_found:
            st.session_state.molecule_data = all_molecules
            st.session_state.input_processed = True  # Mark as processed
            st.session_state.selected_mol_names = [m.name for m in all_molecules][
                :1
            ]  # Select first loaded mol
            st.sidebar.success(
                f"{len(all_molecules)} molecule(s) loaded from {len(files_to_process)} source(s)."
            )
            # Rerun needed to update UI, especially the multiselect default
            # st.experimental_rerun()
            st.rerun()
        else:
            st.error("Failed to load any valid molecules from the provided input(s).")
            st.session_state.molecule_data = None  # Ensure data is cleared
            st.session_state.input_processed = False  # Ensure it stays unprocessed

    # Display Area
    if not st.session_state.get("molecule_data"):
        st.info("⬅️ Please upload XYZ file(s) or paste content in the sidebar.")
        # ... (Example XYZ text) ...
        return

    # Data is ready
    molecules = st.session_state.molecule_data
    molecule_names = [m.name for m in molecules]
    mol_name_to_index_map = {
        m.name: m.id for m in molecules
    }  # Use ID which is the global index

    # Sidebar Controls
    st.sidebar.header("2. Visualization")
    current_style = st.sidebar.selectbox(
        "Representation Style",
        REPRESENTATION_STYLES,
        index=REPRESENTATION_STYLES.index(st.session_state.current_style),
        key="style_select",
    )
    st.session_state.current_style = current_style

    st.sidebar.header("3. Transformations")
    valid_default_selection = [
        name for name in st.session_state.selected_mol_names if name in molecule_names
    ]
    if not valid_default_selection and molecule_names:
        valid_default_selection = [molecule_names[0]]
    selected_mol_names = st.sidebar.multiselect(
        "Modify Molecules:",
        molecule_names,
        default=valid_default_selection,
        key="mol_select",
    )
    st.session_state.selected_mol_names = selected_mol_names
    selected_indices = [
        mol_name_to_index_map[name]
        for name in selected_mol_names
        if name in mol_name_to_index_map
    ]

    trans_x = st.sidebar.slider("Translate X (Å)", -10.0, 10.0, 0.0, 0.1, key="tx")
    trans_y = st.sidebar.slider("Translate Y (Å)", -10.0, 10.0, 0.0, 0.1, key="ty")
    trans_z = st.sidebar.slider("Translate Z (Å)", -10.0, 10.0, 0.0, 0.1, key="tz")
    rot_x = st.sidebar.slider("Rotate X (°)", -180, 180, 0, 1, key="rx")
    rot_y = st.sidebar.slider("Rotate Y (°)", -180, 180, 0, 1, key="ry")
    rot_z = st.sidebar.slider("Rotate Z (°)", -180, 180, 0, 1, key="rz")

    # Apply Transformations
    trans_vector = np.array([trans_x, trans_y, trans_z])
    rot_matrix = build_rotation_matrix(rot_x, rot_y, rot_z)
    apply_transformations(molecules, selected_indices, trans_vector, rot_matrix)

    # Plotting using Plotly
    st.header("Molecule View (Interactive)")
    # Add a note about interaction
    st.caption("Click and drag to rotate, scroll to zoom, right-click drag to pan.")
    try:
        plotly_fig = plot_molecules_plotly(molecules, current_style)
        # Use container width makes the plot responsive
        st.plotly_chart(plotly_fig, use_container_width=True)
    except Exception as e:
        st.error(f"An error occurred during plotting: {e}")
        # import traceback; st.code(traceback.format_exc()) # For debugging

    # Save Functionality
    st.sidebar.header("4. Export")
    if st.sidebar.button("Prepare Combined Adjusted XYZ"):
        st.session_state.download_content = None
        st.session_state.show_download = False
        symbols_combined = []
        coords_combined = []
        for molecule in st.session_state.molecule_data:
            symbols_combined.extend(molecule.symbols)
            coords_combined.append(molecule.transformed_coords)
        if not coords_combined:
            st.sidebar.warning("No molecule data to save.")
        else:
            coords_combined_np = np.vstack(coords_combined)
            xyz_content = f"{len(symbols_combined)}\nCombined adjusted structure from Streamlit Visualizer\n"
            for symbol, coord in zip(symbols_combined, coords_combined_np):
                xyz_content += f"{symbol:<4} {coord[0]:>12.6f} {coord[1]:>12.6f} {coord[2]:>12.6f}\n"
            st.session_state.download_content = xyz_content
            st.session_state.show_download = True
            # st.experimental_rerun()
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

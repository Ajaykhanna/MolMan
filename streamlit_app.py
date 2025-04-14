# Refactored Streamlit App (Matplotlib version) with User-Resizable Plot

import streamlit as st

# Keep Matplotlib imports
import matplotlib.pyplot as plt

# Need Axes3D for subplot creation if not done implicitly
# from mpl_toolkits.mplot3d import Axes3D # Might not be strictly necessary depending on matplotlib version
import numpy as np
from typing import List, Tuple, Dict, Optional, FrozenSet, Any
from dataclasses import dataclass, field
import io

# --- Constants --- (Same as Matplotlib version)
STYLE_LINES = "Lines"
STYLE_BALL_STICK = "Ball and Stick"
STYLE_SPACE_FILLING = "Space Filling"
REPRESENTATION_STYLES = [STYLE_LINES, STYLE_BALL_STICK, STYLE_SPACE_FILLING]
DEFAULT_REPRESENTATION = STYLE_BALL_STICK
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
# Matplotlib scale factors
RADIUS_TO_SCATTER_SCALE_BALL_STICK = 350
RADIUS_TO_SCATTER_SCALE_SPACE_FILLING = 500
LINE_WIDTH_LINES = 1.0
LINE_WIDTH_BALL_STICK = 4.0
AVERAGE_BOND_LENGTHS: Dict[FrozenSet[str], float] = {
    frozenset(["C", "C"]): 1.53,
    frozenset(["C", "N"]): 1.47,
    frozenset(["C", "O"]): 1.42,
    frozenset(["C", "H"]): 1.09,
    frozenset(["N", "H"]): 1.00,
    frozenset(["O", "H"]): 0.96,
}
BOND_TOLERANCE: float = 0.3
# Default Plot Size (inches)
DEFAULT_PLOT_WIDTH = 8
DEFAULT_PLOT_HEIGHT = 7


# --- Data Structures --- (Molecule class same as before)
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


# --- Plotting Function (Using Matplotlib) ---
# This is the Matplotlib plot_molecules function from before the Plotly switch
def plot_molecules_matplotlib(ax: plt.Axes, molecules: List[Molecule], style: str):
    """Plots molecules onto the provided 3D Matplotlib axes based on the selected style."""
    ax.clear()
    all_coords_list = []
    mol_colors = plt.cm.tab20  # Use a colormap with more distinct colors

    for idx, molecule in enumerate(molecules):  # idx is the global index
        coords = molecule.transformed_coords
        symbols = molecule.symbols
        if coords.size == 0:
            continue
        all_coords_list.append(coords)
        x, y, z = coords.T
        atom_colors = get_element_property(symbols, CPK_COLORS, DEFAULT_ATOM_COLOR)
        # Color molecules by their global index for distinction
        molecule_color = mol_colors(idx % mol_colors.N)  # Cycle through colors

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
            )
            for i, j in molecule.bonds:
                if 0 <= i < len(coords) and 0 <= j < len(coords):
                    bond_coords = coords[[i, j]]
                    ax.plot(
                        bond_coords[:, 0],
                        bond_coords[:, 1],
                        bond_coords[:, 2],
                        color=DEFAULT_BOND_COLOR,
                        linewidth=LINE_WIDTH_LINES,
                        label=molecule.name if i == 0 and j == 1 and idx < 15 else None,
                    )  # Label first bond?
        elif style == STYLE_BALL_STICK:
            radii = get_element_property(
                symbols, COVALENT_RADII, DEFAULT_COVALENT_RADIUS
            )
            sizes = [(r**2) * RADIUS_TO_SCATTER_SCALE_BALL_STICK for r in radii]
            ax.scatter(
                x,
                y,
                z,
                c=atom_colors,
                s=sizes,
                edgecolors=ATOM_EDGE_COLOR,
                linewidths=0.5,
                depthshade=True,
                label=molecule.name if idx < 15 else None,
            )
            for i, j in molecule.bonds:
                if 0 <= i < len(coords) and 0 <= j < len(coords):
                    bond_coords = coords[[i, j]]
                    ax.plot(
                        bond_coords[:, 0],
                        bond_coords[:, 1],
                        bond_coords[:, 2],
                        color=DEFAULT_BOND_COLOR,
                        linewidth=LINE_WIDTH_BALL_STICK,
                        solid_capstyle="round",
                    )
        elif style == STYLE_SPACE_FILLING:
            radii = get_element_property(symbols, VDW_RADII, DEFAULT_VDW_RADIUS)
            sizes = [(r**2) * RADIUS_TO_SCATTER_SCALE_SPACE_FILLING for r in radii]
            ax.scatter(
                x,
                y,
                z,
                c=atom_colors,
                s=sizes,
                edgecolors=None,
                linewidths=0,
                depthshade=True,
                label=molecule.name if idx < 15 else None,
            )
        else:
            ax.scatter(x, y, z, label=f"{molecule.name} (Unknown Style)")

    if not all_coords_list:
        ax.set_title("No molecules to plot")
        return
    all_coords_array = np.vstack(all_coords_list)
    if all_coords_array.size == 0:
        ax.set_title("No coordinates to plot")
        return

    min_coords = np.min(all_coords_array, axis=0)
    max_coords = np.max(all_coords_array, axis=0)
    center = (max_coords + min_coords) / 2.0
    ranges = max_coords - min_coords
    buffer = max(1.0, np.max(ranges) * 0.1)
    max_range_dim = np.max(ranges) / 2.0 + buffer
    if max_range_dim <= buffer:
        max_range_dim = buffer * 2
    ax.set_xlim(center[0] - max_range_dim, center[0] + max_range_dim)
    ax.set_ylim(center[1] - max_range_dim, center[1] + max_range_dim)
    ax.set_zlim(center[2] - max_range_dim, center[2] + max_range_dim)
    ax.set_xlabel("X (Å)")
    ax.set_ylabel("Y (Å)")
    ax.set_zlabel("Z (Å)")
    ax.set_title(f"Molecule Visualization ({style})")
    ax.view_init(elev=20, azim=30)
    # Add legend only if few enough molecules to be readable
    num_mols = len(molecules)
    if num_mols > 1 and num_mols <= 15:
        ax.legend(
            title="Molecules",
            fontsize="small",
            loc="center left",
            bbox_to_anchor=(1.0, 0.5),
        )


# --- Main Streamlit App ---
def main():
    st.set_page_config(layout="wide", page_title="Molecule Visualizer")
    st.title("🧪 Molecule Visualizer (Streamlit + Matplotlib)")

    # Initialize Session State
    st.session_state.setdefault("molecule_data", None)
    st.session_state.setdefault("input_processed", False)
    st.session_state.setdefault("input_source_key", None)
    st.session_state.setdefault("selected_mol_names", [])
    st.session_state.setdefault("download_content", None)
    st.session_state.setdefault("show_download", False)
    st.session_state.setdefault("current_style", DEFAULT_REPRESENTATION)
    # Add state for plot size
    st.session_state.setdefault("plot_width", DEFAULT_PLOT_WIDTH)
    st.session_state.setdefault("plot_height", DEFAULT_PLOT_HEIGHT)

    # --- Input Handling --- (Same as previous Matplotlib version)
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

    # --- Data Processing Step --- (Same as previous Matplotlib version)
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
                    mol_name = f"{base_name}"
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
            st.session_state.selected_mol_names = [m.name for m in all_molecules][:1]
            st.sidebar.success(f"{len(all_molecules)} molecule(s) loaded.")
            st.rerun()
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

    molecules = st.session_state.molecule_data
    molecule_names = [m.name for m in molecules]
    mol_name_to_index_map = {m.name: m.id for m in molecules}

    # --- Sidebar Controls (Visualization & Transformation) ---
    st.sidebar.header("2. Visualization")
    current_style = st.sidebar.selectbox(
        "Representation Style",
        REPRESENTATION_STYLES,
        index=REPRESENTATION_STYLES.index(st.session_state.current_style),
        key="style_select",
    )
    st.session_state.current_style = current_style

    # *** ADD PLOT SIZE CONTROLS ***
    st.sidebar.subheader("Plot Size")
    plot_width = st.sidebar.slider(
        "Plot Width (inches)",
        min_value=4,
        max_value=16,
        value=st.session_state.plot_width,
        key="plot_w",
    )
    plot_height = st.sidebar.slider(
        "Plot Height (inches)",
        min_value=3,
        max_value=14,
        value=st.session_state.plot_height,
        key="plot_h",
    )
    # Store updated size in session state
    st.session_state.plot_width = plot_width
    st.session_state.plot_height = plot_height
    # *** END PLOT SIZE CONTROLS ***

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

    # --- Plotting ---
    st.header("Molecule View")
    # *** USE SLIDER VALUES FOR FIGSIZE ***
    fig = plt.figure(figsize=(plot_width, plot_height))
    ax = fig.add_subplot(111, projection="3d")
    try:
        # Use the Matplotlib plotting function
        plot_molecules_matplotlib(ax, molecules, current_style)
        # Adjust layout to prevent cutoff, especially legend
        fig.tight_layout(
            rect=[0, 0, 0.9, 1]
        )  # Adjust right margin for legend if needed
    except Exception as e:
        st.error(f"An error occurred during plotting: {e}")
    # Display using st.pyplot
    st.pyplot(fig)

    # --- Save Functionality --- (Same as before)
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
            st.rerun()  # Use stable rerun
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

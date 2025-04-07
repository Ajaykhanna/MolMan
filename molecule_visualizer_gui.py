# Refactored Tkinter App with Multi-File, Representations, Enhanced Plotting

import tkinter as tk
from tkinter import ttk  # For Combobox
from tkinter import filedialog  # Keep for potential future use or saving
import matplotlib.pyplot as plt

# Need Axes3D for subplot creation if not done implicitly
# from mpl_toolkits.mplot3d import Axes3D # Might not be strictly necessary
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import argparse
import os  # Keep for basic path checks maybe? Though pathlib preferred if used
from pathlib import Path  # Use pathlib
import sys
from typing import List, Tuple, Dict, Optional, FrozenSet, Any
from dataclasses import dataclass, field

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
# == Matplotlib Plotting Scale Factors & Line Widths ==
RADIUS_TO_SCATTER_SCALE_BALL_STICK = 350
RADIUS_TO_SCATTER_SCALE_SPACE_FILLING = 500  # Needs tuning
LINE_WIDTH_LINES = 1.0
LINE_WIDTH_BALL_STICK = 4.0
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
SLIDER_TRANSLATION_RANGE: Tuple[float, float] = (-10.0, 10.0)  # Adjusted range
SLIDER_ROTATION_RANGE: Tuple[float, float] = (-180.0, 180.0)
SLIDER_RESOLUTION_TRANS: float = 0.1
SLIDER_RESOLUTION_ROT: float = 1.0
DEFAULT_OUTPUT_FILENAME: str = "combined_adjusted_molecule.xyz"  # Updated default name
DEFAULT_WINDOW_SIZE: str = "1100x700"
PLOT_ELEVATION: float = 20.0
PLOT_AZIMUTH: float = 30.0


# --- Data Structures ---
@dataclass
class Molecule:
    """Represents a single molecule with atoms, coordinates, bonds, and origin info."""

    symbols: List[str]
    coords: np.ndarray
    bonds: List[Tuple[int, int]]
    id: int  # Global index in the combined list
    name: str  # Unique identifier like "File1-Mol1" or filename
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


# --- Helper Functions ---
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


# --- Core Logic Functions ---
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


def load_xyz(file_path: Path) -> Tuple[Optional[List[str]], Optional[np.ndarray]]:
    """Load atom symbols and coordinates from an XYZ file."""
    # Keep error handling similar to previous Tkinter version, maybe print warnings/errors
    if not file_path.is_file():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return None, None
    try:
        with file_path.open("r") as file:
            lines = file.readlines()
            if not lines:
                raise ValueError(f"File is empty: {file_path}")
            atom_count_str = lines[0].strip()
            if not atom_count_str:
                raise ValueError("First line (atom count) is empty.")
            atom_count = int(atom_count_str)
            if len(lines) < 2:
                raise ValueError("File must have at least 2 lines.")
            coord_lines = lines[2:]
            symbols: List[str] = []
            coords_list: List[List[float]] = []
            actual_atom_count = 0
            for i, line in enumerate(coord_lines):
                if actual_atom_count >= atom_count:
                    break
                parts = line.strip().split()
                if not parts:
                    continue
                if len(parts) < 4:
                    print(
                        f"Warning: Line {i+3} in {file_path.name} malformed. Skipping.",
                        file=sys.stderr,
                    )
                    continue
                try:
                    symbols.append(parts[0])
                    coords_list.append(list(map(float, parts[1:4])))
                    actual_atom_count += 1
                except ValueError as e:
                    print(
                        f"Warning: Error parsing coords line {i+3} in {file_path.name}: {e}. Skipping.",
                        file=sys.stderr,
                    )
                    continue
            if actual_atom_count == 0 and atom_count > 0:
                raise ValueError(f"No valid coordinates found in {file_path.name}")
            if actual_atom_count != atom_count:
                print(
                    f"Warning: Found {actual_atom_count} atoms in {file_path.name}, header said {atom_count}.",
                    file=sys.stderr,
                )
            return symbols, np.array(coords_list)
    except ValueError as e:
        print(f"Error reading {file_path.name}: {e}", file=sys.stderr)
        return None, None
    except Exception as e:
        print(f"Unexpected error reading {file_path.name}: {e}", file=sys.stderr)
        return None, None


# --- Main Application Class ---
class MoleculeVisualizer:
    """GUI application for visualizing and manipulating molecules from XYZ files."""

    def __init__(self, master: tk.Tk, xyz_files: List[Path]):
        """Initialize the MoleculeVisualizer."""
        self.master = master
        self.xyz_files = xyz_files
        self.molecules: List[Molecule] = []  # Will hold Molecule objects
        self.selected_molecule_indices: List[int] = []  # Global indices
        self.mol_name_to_id_map: Dict[str, int] = {}  # Map display name to global index

        self._configure_window()
        self._load_and_process_data()  # Load data from multiple files

        # GUI Elements & State
        self.fig: Optional[plt.Figure] = None
        self.ax: Optional[plt.Axes] = None
        self.canvas: Optional[FigureCanvasTkAgg] = None
        self.control_frame: Optional[tk.Frame] = None
        self.selection_vars: Dict[str, tk.IntVar] = {}  # Map name to IntVa
        self.select_all_var: Optional[tk.IntVar] = None
        self.representation_style = tk.StringVar(value=DEFAULT_REPRESENTATION)
        self.trans_x: Optional[tk.DoubleVar] = None
        self.trans_y: Optional[tk.DoubleVar] = None
        self.trans_z: Optional[tk.DoubleVar] = None
        self.rot_x: Optional[tk.DoubleVar] = None
        self.rot_y: Optional[tk.DoubleVar] = None
        self.rot_z: Optional[tk.DoubleVar] = None

        if not self.molecules:
            # Handle case where no molecules were loaded successfully
            print(
                "Error: No valid molecules loaded from input files. Exiting.",
                file=sys.stderr,
            )
            # Optionally show a Tkinter error message box
            messagebox.showerror(
                "Loading Error", "No valid molecules loaded from input files."
            )
            self.master.quit()
            # sys.exit(1) # Exit here might be too abrupt if Tk window is already up
            return  # Stop initialization

        # Default selection: Select the first loaded molecule if available
        if self.molecules:
            first_mol_name = self.molecules[0].name
            self.selected_molecule_indices = [self.mol_name_to_id_map[first_mol_name]]

        self._setup_gui()
        self._update_view()  # Initial plot

    def _configure_window(self):
        """Set up main window properties."""
        num_files = len(self.xyz_files)
        file_text = (
            f"{num_files} file{'s' if num_files != 1 else ''}"
            if num_files > 0
            else "No files"
        )
        self.master.title(f"Molecule Visualizer - {file_text}")
        self.master.geometry(DEFAULT_WINDOW_SIZE)
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)

    def _load_and_process_data(self):
        """Load data from multiple XYZ files and process into Molecule objects."""
        print(f"Processing {len(self.xyz_files)} input file(s)...")
        global_mol_index = 0
        all_molecules = []
        mol_name_to_id = {}

        for file_idx, file_path in enumerate(self.xyz_files):
            print(f"  Loading: {file_path.name}")
            symbols, coords = load_xyz(file_path)

            if symbols is not None and coords is not None and len(symbols) > 0:
                print(f"    Found {len(symbols)} atoms. Calculating bonds...")
                bonds = determine_bonds(symbols, coords)
                print(f"    Found {len(bonds)} bonds.")

                # Determine molecule name
                base_name = file_path.stem  # Use filename without extension
                mol_name = base_name if len(self.xyz_files) > 1 else "Molecule 1"

                molecule = Molecule(
                    symbols=symbols,
                    coords=coords,
                    bonds=bonds,
                    id=global_mol_index,
                    name=mol_name,
                    source_file_index=file_idx,
                    source_file_name=file_path.name,
                )
                all_molecules.append(molecule)
                mol_name_to_id[mol_name] = global_mol_index
                global_mol_index += 1
            else:
                print(
                    f"    Skipping {file_path.name} due to loading errors or no atoms."
                )

        self.molecules = all_molecules
        self.mol_name_to_id_map = mol_name_to_id
        print(f"Successfully loaded {len(self.molecules)} molecule(s) in total.")

    def _setup_gui(self):
        """Create and arrange all GUI elements."""
        main_frame = tk.Frame(self.master)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=1)

        plot_frame = tk.Frame(main_frame)
        plot_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        plot_frame.rowconfigure(0, weight=1)
        plot_frame.columnconfigure(0, weight=1)

        self.fig = plt.figure(figsize=(7, 7))  # Use figsize from constants?
        try:
            self.ax = self.fig.add_subplot(111, projection="3d")
        except Exception as e:
            print(f"Plotting Error: {e}", file=sys.stderr)
            self.master.quit()
            return

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.control_frame = tk.Frame(main_frame, bd=2, relief=tk.SUNKEN)
        self.control_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.control_frame.rowconfigure(0, weight=1)
        self.control_frame.columnconfigure(0, weight=1)

        control_canvas = tk.Canvas(self.control_frame)
        scrollbar = tk.Scrollbar(
            self.control_frame, orient="vertical", command=control_canvas.yview
        )
        scrollable_frame = tk.Frame(control_canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: control_canvas.configure(scrollregion=control_canvas.bbox("all")),
        )
        control_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        control_canvas.configure(yscrollcommand=scrollbar.set)
        control_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._add_controls_to_frame(scrollable_frame)

    def _add_controls_to_frame(self, parent_frame: tk.Frame):
        """Adds control widgets, including representation style, to the frame."""

        # --- Representation Style ---
        style_frame = tk.LabelFrame(
            parent_frame, text="Representation Style", padx=5, pady=5
        )
        style_frame.pack(pady=10, padx=5, fill="x", expand=False)
        style_combo = ttk.Combobox(
            style_frame,
            textvariable=self.representation_style,
            values=REPRESENTATION_STYLES,
            state="readonly",
        )
        style_combo.pack(fill="x", expand=True)
        # Trigger redraw on style change (no transformation needed)
        style_combo.bind("<<ComboboxSelected>>", self._draw_plot)  # Directly call draw

        # --- Molecule Selection ---
        select_frame = tk.LabelFrame(
            parent_frame, text="Select Molecules to Modify", padx=5, pady=5
        )
        select_frame.pack(pady=10, padx=5, fill="x", expand=False)

        self.select_all_var = tk.IntVar(
            value=0
        )  # Default to none selected unless only 1 mol
        chk_all = tk.Checkbutton(
            select_frame,
            text="All Molecules",
            variable=self.select_all_var,
            command=self._toggle_all_selection,
        )
        chk_all.pack(anchor="w")

        self.selection_vars = {}  # Dictionary: name -> IntVar
        sorted_mol_names = sorted(self.mol_name_to_id_map.keys())  # Consistent order

        for mol_name in sorted_mol_names:
            mol_id = self.mol_name_to_id_map[mol_name]
            # Check if this molecule is selected by default
            is_selected = mol_id in self.selected_molecule_indices
            var = tk.IntVar(value=1 if is_selected else 0)
            chk = tk.Checkbutton(
                select_frame,
                text=mol_name,
                variable=var,
                command=self._update_selection_from_individual,
            )
            chk.pack(anchor="w")
            self.selection_vars[mol_name] = var

        # Update select_all state based on initial selection
        if (
            len(self.selected_molecule_indices) == len(self.molecules)
            and len(self.molecules) > 0
        ):
            self.select_all_var.set(1)

        # --- Transformation Sliders ---
        self.trans_x = tk.DoubleVar(value=0.0)
        self.trans_y = tk.DoubleVar(value=0.0)
        self.trans_z = tk.DoubleVar(value=0.0)
        self.rot_x = tk.DoubleVar(value=0.0)
        self.rot_y = tk.DoubleVar(value=0.0)
        self.rot_z = tk.DoubleVar(value=0.0)
        trans_frame = tk.LabelFrame(
            parent_frame, text="Translation (Å)", padx=5, pady=5
        )
        trans_frame.pack(pady=10, padx=5, fill="x", expand=False)
        self._create_slider(
            trans_frame,
            "X:",
            self.trans_x,
            SLIDER_TRANSLATION_RANGE[0],
            SLIDER_TRANSLATION_RANGE[1],
            SLIDER_RESOLUTION_TRANS,
        )
        self._create_slider(
            trans_frame,
            "Y:",
            self.trans_y,
            SLIDER_TRANSLATION_RANGE[0],
            SLIDER_TRANSLATION_RANGE[1],
            SLIDER_RESOLUTION_TRANS,
        )
        self._create_slider(
            trans_frame,
            "Z:",
            self.trans_z,
            SLIDER_TRANSLATION_RANGE[0],
            SLIDER_TRANSLATION_RANGE[1],
            SLIDER_RESOLUTION_TRANS,
        )
        rot_frame = tk.LabelFrame(parent_frame, text="Rotation (°)", padx=5, pady=5)
        rot_frame.pack(pady=10, padx=5, fill="x", expand=False)
        self._create_slider(
            rot_frame,
            "X-axis:",
            self.rot_x,
            SLIDER_ROTATION_RANGE[0],
            SLIDER_ROTATION_RANGE[1],
            SLIDER_RESOLUTION_ROT,
        )
        self._create_slider(
            rot_frame,
            "Y-axis:",
            self.rot_y,
            SLIDER_ROTATION_RANGE[0],
            SLIDER_ROTATION_RANGE[1],
            SLIDER_RESOLUTION_ROT,
        )
        self._create_slider(
            rot_frame,
            "Z-axis:",
            self.rot_z,
            SLIDER_ROTATION_RANGE[0],
            SLIDER_ROTATION_RANGE[1],
            SLIDER_RESOLUTION_ROT,
        )

        # --- Action Buttons ---
        action_frame = tk.Frame(parent_frame, padx=5, pady=5)
        action_frame.pack(pady=10, padx=5, fill="x", expand=False)
        save_btn = tk.Button(
            action_frame, text="Save Combined Structure", command=self.save_structure
        )
        save_btn.pack(side=tk.LEFT, padx=5, expand=True, fill="x")
        reset_btn = tk.Button(action_frame, text="Reset View", command=self.reset_view)
        reset_btn.pack(side=tk.RIGHT, padx=5, expand=True, fill="x")

    def _create_slider(
        self,
        parent: tk.Frame,
        label_text: str,
        variable: tk.DoubleVar,
        from_: float,
        to: float,
        resolution: float,
    ):
        frame = tk.Frame(parent)
        frame.pack(fill="x", pady=2)
        label = tk.Label(frame, text=label_text, width=6, anchor="w")
        label.pack(side=tk.LEFT)
        # Link slider command to _update_view which handles transforms and redraw
        scale = tk.Scale(
            frame,
            variable=variable,
            orient=tk.HORIZONTAL,
            length=200,
            from_=from_,
            to=to,
            resolution=resolution,
            command=self._update_view,
        )
        scale.pack(side=tk.RIGHT, fill="x", expand=True)

    # --- Event Handlers & Update Logic ---
    def _toggle_all_selection(self):
        """Handle clicks on the 'All Molecules' checkbox."""
        select_all = self.select_all_var.get() == 1
        new_selected_indices = []
        for mol_name, var in self.selection_vars.items():
            var.set(1 if select_all else 0)
            if select_all:
                new_selected_indices.append(self.mol_name_to_id_map[mol_name])

        self.selected_molecule_indices = new_selected_indices
        self._update_view()  # Update plot after changing selection

    def _update_selection_from_individual(self):
        """Handle clicks on individual molecule checkboxes."""
        current_selection = []
        for mol_name, var in self.selection_vars.items():
            if var.get() == 1:
                current_selection.append(self.mol_name_to_id_map[mol_name])
        self.selected_molecule_indices = current_selection

        # Update 'All Molecules' checkbox state
        if (
            len(self.selected_molecule_indices) == len(self.molecules)
            and len(self.molecules) > 0
        ):
            self.select_all_var.set(1)
        else:
            self.select_all_var.set(0)

        self._update_view()  # Update plot after changing selection

    def _update_view(self, event: Optional[Any] = None):
        """Update transformations based on sliders and redraw the plot."""
        if not self.molecules or self.ax is None or self.canvas is None:
            return
        if not all(
            [
                self.trans_x,
                self.trans_y,
                self.trans_z,
                self.rot_x,
                self.rot_y,
                self.rot_z,
            ]
        ):
            return

        # 1. Get current transformation parameters
        trans_vector = np.array(
            [self.trans_x.get(), self.trans_y.get(), self.trans_z.get()]
        )
        rot_matrix = build_rotation_matrix(
            self.rot_x.get(), self.rot_y.get(), self.rot_z.get()
        )

        # 2. Apply transformations (modifies molecule.transformed_coords)
        for idx, molecule in enumerate(self.molecules):
            if (
                molecule.id in self.selected_molecule_indices
            ):  # Check against molecule's actual ID
                molecule.apply_transformation(trans_vector, rot_matrix)
            else:
                molecule.reset_transformation()  # Reset others

        # 3. Redraw the plot with current style
        self._draw_plot()

    # --- Plotting --- (Adapted from Streamlit Matplotlib version)
    def _draw_plot(self, event: Optional[Any] = None):
        """Clear axes and redraw molecules based on current style and transformations."""
        if self.ax is None or self.canvas is None or self.fig is None:
            return

        self.ax.clear()
        style = self.representation_style.get()
        all_coords_list = []
        mol_colors = plt.cm.tab20  # Use a colormap with more distinct colors

        # Plotting logic similar to plot_molecules_matplotlib
        for idx, molecule in enumerate(self.molecules):
            coords = molecule.transformed_coords
            symbols = molecule.symbols
            if coords.size == 0:
                continue
            all_coords_list.append(coords)
            x, y, z = coords.T
            atom_colors = get_element_property(symbols, CPK_COLORS, DEFAULT_ATOM_COLOR)
            molecule_color = mol_colors(idx % mol_colors.N)  # Cycle through colors

            # Limit labels in legend to avoid clutter
            show_label = molecule.name if idx < 15 else None

            if style == STYLE_LINES:
                self.ax.scatter(
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
                    if 0 <= i < len(coords) and 0 <= j < len(coords):
                        bond_coords = coords[[i, j]]
                        self.ax.plot(
                            bond_coords[:, 0],
                            bond_coords[:, 1],
                            bond_coords[:, 2],
                            color=DEFAULT_BOND_COLOR,
                            linewidth=LINE_WIDTH_LINES,
                        )
            elif style == STYLE_BALL_STICK:
                radii = get_element_property(
                    symbols, COVALENT_RADII, DEFAULT_COVALENT_RADIUS
                )
                sizes = [(r**2) * RADIUS_TO_SCATTER_SCALE_BALL_STICK for r in radii]
                self.ax.scatter(
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
                    if 0 <= i < len(coords) and 0 <= j < len(coords):
                        bond_coords = coords[[i, j]]
                        self.ax.plot(
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
                self.ax.scatter(
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
                self.ax.scatter(x, y, z, label=f"{molecule.name} (Unknown Style)")

        # Post-Plotting Adjustments
        if not all_coords_list:
            self.ax.set_title("No molecules to plot")
            self.canvas.draw()
            return
        all_coords_array = np.vstack(all_coords_list)
        if all_coords_array.size == 0:
            self.ax.set_title("No coordinates to plot")
            self.canvas.draw()
            return

        min_coords = np.min(all_coords_array, axis=0)
        max_coords = np.max(all_coords_array, axis=0)
        center = (max_coords + min_coords) / 2.0
        ranges = max_coords - min_coords
        buffer = max(1.0, np.max(ranges) * 0.1)
        max_range_dim = np.max(ranges) / 2.0 + buffer
        if max_range_dim <= buffer:
            max_range_dim = buffer * 2
        self.ax.set_xlim(center[0] - max_range_dim, center[0] + max_range_dim)
        self.ax.set_ylim(center[1] - max_range_dim, center[1] + max_range_dim)
        self.ax.set_zlim(center[2] - max_range_dim, center[2] + max_range_dim)
        self.ax.set_xlabel("X (Å)")
        self.ax.set_ylabel("Y (Å)")
        self.ax.set_zlabel("Z (Å)")
        self.ax.set_title(f"Molecule Visualization ({style})")
        self.ax.view_init(elev=PLOT_ELEVATION, azim=PLOT_AZIMUTH)
        num_mols = len(self.molecules)
        if num_mols > 1 and num_mols <= 15:
            self.ax.legend(
                title="Molecules",
                fontsize="small",
                loc="center left",
                bbox_to_anchor=(1.02, 0.5),
            )

        self.fig.tight_layout(rect=[0, 0, 0.85, 1])  # Adjust layout for legend
        self.canvas.draw()

    # --- File Operations & Reset ---
    def save_structure(self):
        """Save the current state of all molecules to a combined XYZ file."""
        if not self.molecules:
            messagebox.showwarning("Save Structure", "No molecules loaded.")
            return

        # Use filedialog to ask for save location
        save_path_str = filedialog.asksaveasfilename(
            initialdir=".",  # Start in current directory
            initialfile=DEFAULT_OUTPUT_FILENAME,
            defaultextension=".xyz",
            filetypes=[("XYZ files", "*.xyz"), ("All files", "*.*")],
        )
        if not save_path_str:
            return  # User cancelled
        save_path = Path(save_path_str)

        symbols_combined = []
        coords_combined = []
        for molecule in self.molecules:
            symbols_combined.extend(molecule.symbols)
            coords_combined.append(molecule.transformed_coords)
        if not coords_combined:
            messagebox.showerror("Save Error", "No coordinate data.")
            return

        coords_combined_np = np.vstack(coords_combined)
        total_atoms = len(symbols_combined)
        try:
            with save_path.open("w") as file:
                file.write(f"{total_atoms}\n")
                file.write(f"Combined adjusted structure from Tkinter Visualizer\n")
                for symbol, coord in zip(symbols_combined, coords_combined_np):
                    file.write(
                        f"{symbol:<4} {coord[0]:>12.6f} {coord[1]:>12.6f} {coord[2]:>12.6f}\n"
                    )
            messagebox.showinfo("Save Successful", f"Structure saved to:\n{save_path}")
            print(f"Combined adjusted structure saved to '{save_path}'")
        except IOError as e:
            messagebox.showerror("Save Error", f"Could not write file:\n{e}")
            print(f"Error saving file: {e}", file=sys.stderr)
        except Exception as e:
            messagebox.showerror(
                "Save Error", f"An unexpected error occurred during saving:\n{e}"
            )
            print(f"Unexpected error saving file: {e}", file=sys.stderr)

    def reset_view(self):
        """Reset sliders to zero and update the plot."""
        if not all(
            [
                self.trans_x,
                self.trans_y,
                self.trans_z,
                self.rot_x,
                self.rot_y,
                self.rot_z,
            ]
        ):
            return
        self.trans_x.set(0.0)
        self.trans_y.set(0.0)
        self.trans_z.set(0.0)
        self.rot_x.set(0.0)
        self.rot_y.set(0.0)
        self.rot_z.set(0.0)
        # Update view resets transformations and redraws
        self._update_view()
        print("View reset to default.")


# --- Main Execution ---
def main():
    """Parse arguments and run the Tkinter Molecule Visualizer application."""
    parser = argparse.ArgumentParser(
        description="Visualize and manipulate molecules from one or more XYZ files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "xyz_files",
        type=Path,
        nargs="+",  # Accept one or more file paths
        help="Path(s) to the input XYZ file(s).",
    )
    # REMOVED: --nMolecules and --nAtoms arguments

    args = parser.parse_args()

    # Basic file existence check
    valid_files = []
    for file_path in args.xyz_files:
        if not file_path.is_file():
            print(f"Error: Input file not found: '{file_path}'", file=sys.stderr)
        elif not file_path.name.lower().endswith(".xyz"):
            print(
                f"Warning: Input file '{file_path.name}' does not have .xyz extension.",
                file=sys.stderr,
            )
            valid_files.append(file_path)  # Still try to process it
        else:
            valid_files.append(file_path)

    if not valid_files:
        print("Error: No valid input files found. Exiting.", file=sys.stderr)
        sys.exit(1)

    # Start the GUI application
    try:
        root = tk.Tk()
        # Pass the list of valid file paths
        app = MoleculeVisualizer(root, valid_files)
        # Only run mainloop if app initialization didn't quit
        if root.winfo_exists():
            root.mainloop()
    except Exception as e:
        print(
            f"\n--- An unexpected error occurred launching the application ---",
            file=sys.stderr,
        )
        print(f"Error Type: {type(e).__name__}", file=sys.stderr)
        print(f"Error Details: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        print("-----------------------------------", file=sys.stderr)
        sys.exit("Application terminated due to an unexpected error.")


if __name__ == "__main__":
    # Need to handle potential Tkinter import errors if DISPLAY is not available
    try:
        # Check if DISPLAY environment variable exists for Linux/macOS, needed for Tkinter
        # This check is basic and might not cover all headless scenarios
        if sys.platform != "win32" and "DISPLAY" not in os.environ:
            print(
                "Error: Cannot run Tkinter GUI. DISPLAY environment variable not set.",
                file=sys.stderr,
            )
            print(
                "If running headless or via SSH, ensure X11 forwarding is enabled or use a virtual framebuffer (e.g., Xvfb).",
                file=sys.stderr,
            )
            sys.exit(1)
        main()
    except tk.TclError as e:
        print(
            f"Error: Failed to initialize Tkinter GUI. Is a display available?",
            file=sys.stderr,
        )
        print(f"({e})", file=sys.stderr)
        sys.exit(1)

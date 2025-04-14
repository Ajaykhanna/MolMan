# Developed by: Ajay Khanna, ChatGPT-4o, and Google Gemini 2.5 Pro Experimental
# Date: April.09.2025
"""
Molecule Visualizer GUI Application

A comprehensive Tkinter-based application for visualizing molecular structures from XYZ files.
Supports multi-file loading, interactive transformations, and multiple representation styles.

Key Features:
- Load multiple molecular structures simultaneously
- Interactive translation and rotation controls
- Representation styles: Lines, Ball and Stick, Space Filling
- Centroid manipulation and global offset tracking
- Save combined molecular structures

Dependencies:
- tkinter
- matplotlib
- numpy

Usage:
    python molecule_visualizer_gui.py molecule1.xyz molecule2.xyz ...
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import argparse
import os  # For DISPLAY check
from pathlib import Path
import sys
from typing import List, Tuple, Dict, Optional, FrozenSet, Any
from dataclasses import dataclass, field

# Import Rotation from scipy if available for potential future rotation sync
# try:
#     from scipy.spatial.transform import Rotation as R
#     SCIPY_AVAILABLE = True
# except ImportError:
#     SCIPY_AVAILABLE = False
#     print("Warning: Scipy not found. Rotation slider sync disabled.", file=sys.stderr)
SCIPY_AVAILABLE = False  # Keep rotation sync disabled for now for simplicity

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
RADIUS_TO_SCATTER_SCALE_SPACE_FILLING = 500
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
SLIDER_TRANSLATION_RANGE: Tuple[float, float] = (-10.0, 10.0)
SLIDER_ROTATION_RANGE: Tuple[float, float] = (-180.0, 180.0)
SLIDER_RESOLUTION_TRANS: float = 0.1
SLIDER_RESOLUTION_ROT: float = 1.0
DEFAULT_OUTPUT_FILENAME: str = "manipulated_structures.xyz"
DEFAULT_WINDOW_SIZE: str = "1200x750"
PLOT_ELEVATION: float = 20.0
PLOT_AZIMUTH: float = 30.0
# == Styling Constants ==
BG_COLOR_FRAME = "#F0F0F0"
BG_COLOR_LBLFRAME = "#ECECEC"
BG_COLOR_BTN = "#D5D5D5"
BG_COLOR_BTN_ACTIVE = "#C0C0C0"
FG_COLOR_LABEL = "#333333"
FONT_DEFAULT = ("Arial", 9)
FONT_BOLD = ("Arial", 10, "bold")
FORMAT_TRANS = "{:.1f}"
FORMAT_ROT = "{:.0f}"


# --- Data Structures ---
@dataclass
class Molecule:
    """
    Represents a single molecule unit, storing original and transformed state.

    Attributes:
        symbols (List[str]): List of atomic symbols.
        coords (np.ndarray): Original coordinates of the molecule.
        bonds (List[Tuple[int, int]]): List of bonds between atoms.
        id (int): Unique identifier for the molecule.
        name (str): Name of the molecule.
        source_file_index (int): Index of the source file.
        source_file_name (str): Name of the source file.
        transformed_coords (np.ndarray): Transformed coordinates of the molecule.
        final_translation (np.ndarray): Final translation vector.
        final_rotation_matrix (np.ndarray): Final rotation matrix.
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
        """
        Initializes transformed state after the main __init__.
        """
        self.apply_final_transformation()

    def reset_transformation(self):
        """
        Resets transformed_coords, final_translation, and final_rotation_matrix.
        """
        self.final_translation = np.zeros(3)
        self.final_rotation_matrix = np.identity(3)
        self.apply_final_transformation()

    @property
    def centroid(self) -> np.ndarray:
        """
        Calculates the geometric centroid based on the original coordinates.

        Returns:
            np.ndarray: The centroid of the molecule.
        """
        return np.mean(self.coords, axis=0) if self.coords.size > 0 else np.zeros(3)

    def apply_final_transformation(self):
        """
        Applies the stored final_rotation_matrix and final_translation
        to the original coordinates to update transformed_coords.
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
    """Looks up a property (e.g., color, radius) for a list of element symbols."""
    return [property_dict.get(s.capitalize(), default_value) for s in symbols]


def build_rotation_matrix(
    angle_x_deg: float, angle_y_deg: float, angle_z_deg: float
) -> np.ndarray:
    """Builds a combined 3D rotation matrix using ZYX Tait-Bryan convention."""
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
    """Retrieves the minimum and maximum distance criteria for a potential bond."""
    key = frozenset([atom1.capitalize(), atom2.capitalize()])
    average_length = AVERAGE_BOND_LENGTHS.get(key)
    if average_length is not None:
        min_distance = max(0.1, average_length - BOND_TOLERANCE)
        max_distance = average_length + BOND_TOLERANCE
        return min_distance, max_distance
    else:
        return None


def determine_bonds(symbols: List[str], coords: np.ndarray) -> List[Tuple[int, int]]:
    """Determines bonds between atoms based on element types and distances."""
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
    """Loads atom symbols and coordinates from a standard XYZ file."""
    if not file_path.is_file():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return None, None
    try:
        with file_path.open("r") as file:
            lines = file.readlines()
            if not lines:
                raise ValueError(f"File is empty: {file_path}")
            atom_count = int(lines[0].strip())
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
    """Main application class for the Tkinter Molecule Visualizer."""

    def __init__(self, master: tk.Tk, xyz_files: List[Path]):
        """Initializes the MoleculeVisualizer application."""
        self.master = master
        self.xyz_files = xyz_files
        self.molecules: List[Molecule] = []
        self.selected_molecule_indices: List[int] = []
        self.mol_name_to_id_map: Dict[str, int] = {}
        self.global_offset = np.zeros(3)
        self._block_slider_command = (
            False  # Flag to prevent slider command during programmatic set
        )

        self._configure_window()
        self._load_and_process_data()

        # GUI Elements & State
        self.fig = None
        self.ax = None
        self.canvas = None
        self.control_frame = None
        self.scrollable_frame = None
        self.selection_vars = {}
        self.select_all_var = tk.IntVar(value=0)  # Initialize here
        self.representation_style = tk.StringVar(value=DEFAULT_REPRESENTATION)
        self.trans_x = tk.DoubleVar(value=0.0)
        self.trans_y = tk.DoubleVar(value=0.0)
        self.trans_z = tk.DoubleVar(value=0.0)
        self.rot_x = tk.DoubleVar(value=0.0)
        self.rot_y = tk.DoubleVar(value=0.0)
        self.rot_z = tk.DoubleVar(value=0.0)
        self.trans_x_str = tk.StringVar()
        self.trans_y_str = tk.StringVar()
        self.trans_z_str = tk.StringVar()
        self.rot_x_str = tk.StringVar()
        self.rot_y_str = tk.StringVar()
        self.rot_z_str = tk.StringVar()
        self.target_x_var = tk.DoubleVar(value=0.0)
        self.target_y_var = tk.DoubleVar(value=0.0)
        self.target_z_var = tk.DoubleVar(value=0.0)
        self.target_x_entry = None
        self.target_y_entry = None
        self.target_z_entry = None

        if not self.molecules:
            messagebox.showerror(
                "Loading Error", "No valid molecules loaded from input files."
            )
            self.master.quit()
            return

        if self.molecules:
            self.selected_molecule_indices = [self.molecules[0].id]

        self._setup_var_traces()
        self._setup_gui()
        # Apply initial transform state (usually identity/zero)
        for mol in self.molecules:
            mol.apply_final_transformation()
        # Sync sliders to initial selection (will reset them to 0 if needed)
        self._sync_sliders_to_selection()
        self._draw_plot()  # Initial plot

    def _configure_window(self):  # (Same as before)
        """Sets up main window properties like title, size, and resizing."""
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
        self.master.config(bg=BG_COLOR_FRAME)

    def _load_and_process_data(self):  # (Same as before)
        """Loads data from multiple XYZ files specified at startup."""
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
                base_name = file_path.stem
                mol_name = base_name if len(self.xyz_files) > 1 else "Molecule 1"
                unique_mol_name = mol_name
                count = 1
                while unique_mol_name in mol_name_to_id:
                    count += 1
                    unique_mol_name = f"{mol_name}_{count}"
                molecule = Molecule(
                    symbols=symbols,
                    coords=coords,
                    bonds=bonds,
                    id=global_mol_index,
                    name=unique_mol_name,
                    source_file_index=file_idx,
                    source_file_name=file_path.name,
                )
                all_molecules.append(molecule)
                mol_name_to_id[unique_mol_name] = global_mol_index
                global_mol_index += 1
            else:
                print(
                    f"    Skipping {file_path.name} due to loading errors or no atoms."
                )
        self.molecules = all_molecules
        self.mol_name_to_id_map = mol_name_to_id
        print(f"Successfully loaded {len(self.molecules)} molecule(s) in total.")

    def _setup_var_traces(self):  # (Same as before)
        """Sets up traces to update slider value labels automatically."""
        self._update_slider_label(self.trans_x, self.trans_x_str, FORMAT_TRANS)
        self._update_slider_label(self.trans_y, self.trans_y_str, FORMAT_TRANS)
        self._update_slider_label(self.trans_z, self.trans_z_str, FORMAT_TRANS)
        self._update_slider_label(self.rot_x, self.rot_x_str, FORMAT_ROT)
        self._update_slider_label(self.rot_y, self.rot_y_str, FORMAT_ROT)
        self._update_slider_label(self.rot_z, self.rot_z_str, FORMAT_ROT)
        self.trans_x.trace_add(
            "write",
            lambda *args: self._update_slider_label(
                self.trans_x, self.trans_x_str, FORMAT_TRANS
            ),
        )
        self.trans_y.trace_add(
            "write",
            lambda *args: self._update_slider_label(
                self.trans_y, self.trans_y_str, FORMAT_TRANS
            ),
        )
        self.trans_z.trace_add(
            "write",
            lambda *args: self._update_slider_label(
                self.trans_z, self.trans_z_str, FORMAT_TRANS
            ),
        )
        self.rot_x.trace_add(
            "write",
            lambda *args: self._update_slider_label(
                self.rot_x, self.rot_x_str, FORMAT_ROT
            ),
        )
        self.rot_y.trace_add(
            "write",
            lambda *args: self._update_slider_label(
                self.rot_y, self.rot_y_str, FORMAT_ROT
            ),
        )
        self.rot_z.trace_add(
            "write",
            lambda *args: self._update_slider_label(
                self.rot_z, self.rot_z_str, FORMAT_ROT
            ),
        )

    def _update_slider_label(
        self, double_var: tk.DoubleVar, string_var: tk.StringVar, fmt_spec: str
    ):  # (Same as before)
        """Updates the StringVar label from the DoubleVar slider value."""
        try:
            string_var.set(fmt_spec.format(double_var.get()))
        except tk.TclError:
            pass
        except Exception as e:
            print(f"Error updating slider label: {e}", file=sys.stderr)

    def _setup_gui(self):  # (Same as before)
        """Creates and arranges main GUI elements, sets up styling and resizing."""
        style = ttk.Style(self.master)
        style.theme_use("clam")
        style.configure(
            "TButton",
            padding=5,
            relief="flat",
            background=BG_COLOR_BTN,
            foreground="black",
            font=FONT_DEFAULT,
            borderwidth=1,
        )
        style.map(
            "TButton",
            background=[
                ("active", BG_COLOR_BTN_ACTIVE),
                ("pressed", BG_COLOR_BTN_ACTIVE),
            ],
        )
        style.configure(
            "TLabelframe",
            padding=6,
            background=BG_COLOR_LBLFRAME,
            relief="groove",
            borderwidth=1,
        )
        style.configure(
            "TLabelframe.Label",
            background=BG_COLOR_LBLFRAME,
            foreground=FG_COLOR_LABEL,
            font=FONT_BOLD,
        )
        style.configure(
            "TCheckbutton",
            background=BG_COLOR_LBLFRAME,
            foreground=FG_COLOR_LABEL,
            font=FONT_DEFAULT,
            padding=(5, 2),
        )
        style.map("TCheckbutton", background=[("active", BG_COLOR_LBLFRAME)])
        style.configure(
            "TCombobox", padding=3, fieldbackground="white", background=BG_COLOR_BTN
        )
        style.configure(
            "TLabel",
            background=BG_COLOR_LBLFRAME,
            foreground=FG_COLOR_LABEL,
            font=FONT_DEFAULT,
        )
        style.configure("Bold.TLabel", font=FONT_BOLD, background=BG_COLOR_LBLFRAME)
        style.configure("TEntry", padding=3, fieldbackground="white")
        style.configure(
            "Value.TLabel",
            background=BG_COLOR_LBLFRAME,
            foreground=FG_COLOR_LABEL,
            font=FONT_DEFAULT,
            anchor="e",
        )
        style.configure(
            "Limit.TLabel",
            background=BG_COLOR_LBLFRAME,
            foreground="#666666",
            font=("Arial", 8),
        )
        main_frame = tk.Frame(self.master, bg=BG_COLOR_FRAME)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=1)
        plot_frame = tk.Frame(main_frame, bg="white")
        plot_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.fig = plt.figure(figsize=(7, 7), facecolor="white")
        try:
            self.ax = self.fig.add_subplot(111, projection="3d", facecolor="white")
        except Exception as e:
            print(f"Plotting Error: {e}", file=sys.stderr)
            self.master.quit()
            return
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.control_frame = tk.Frame(main_frame, bg=BG_COLOR_FRAME, padx=5, pady=5)
        self.control_frame.grid(row=0, column=1, sticky="nsew")
        self.control_frame.rowconfigure(0, weight=1)
        self.control_frame.columnconfigure(0, weight=1)
        control_canvas = tk.Canvas(
            self.control_frame, borderwidth=0, background=BG_COLOR_FRAME
        )
        scrollbar = ttk.Scrollbar(
            self.control_frame, orient="vertical", command=control_canvas.yview
        )
        self.scrollable_frame = tk.Frame(control_canvas, background=BG_COLOR_FRAME)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: control_canvas.configure(scrollregion=control_canvas.bbox("all")),
        )
        canvas_window = control_canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw"
        )
        control_canvas.configure(yscrollcommand=scrollbar.set)
        control_canvas.bind(
            "<Configure>",
            lambda e: control_canvas.itemconfig(canvas_window, width=e.width),
        )
        control_canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self._add_controls_to_frame(self.scrollable_frame)

    def _add_controls_to_frame(self, parent_frame: tk.Frame):  # (Same as before)
        """Creates and packs/grids all control widgets."""
        style_frame = ttk.LabelFrame(
            parent_frame, text="Representation Style", padding=(10, 5)
        )
        style_frame.pack(pady=5, padx=5, fill="x", expand=False)
        style_combo = ttk.Combobox(
            style_frame,
            textvariable=self.representation_style,
            values=REPRESENTATION_STYLES,
            state="readonly",
            font=FONT_DEFAULT,
        )
        style_combo.pack(fill="x", expand=True, padx=5, pady=(0, 5))
        style_combo.bind("<<ComboboxSelected>>", self._draw_plot)
        select_frame = ttk.LabelFrame(
            parent_frame, text="Select Molecules to Modify", padding=(10, 5)
        )
        select_frame.pack(pady=5, padx=5, fill="x", expand=False)
        self.select_all_var = tk.IntVar(value=0)
        chk_all = ttk.Checkbutton(
            select_frame,
            text="All Molecules",
            variable=self.select_all_var,
            command=self._toggle_all_selection,
            style="TCheckbutton",
        )
        chk_all.pack(anchor="w", padx=5)
        self.selection_vars = {}
        sorted_mol_names = sorted(self.mol_name_to_id_map.keys())
        for mol_name in sorted_mol_names:
            mol_id = self.mol_name_to_id_map[mol_name]
            is_selected = mol_id in self.selected_molecule_indices
            var = tk.IntVar(value=1 if is_selected else 0)
            chk = ttk.Checkbutton(
                select_frame,
                text=mol_name,
                variable=var,
                command=self._update_selection_from_individual,
                style="TCheckbutton",
            )
            chk.pack(anchor="w", padx=5)
            self.selection_vars[mol_name] = var
        if (
            len(self.selected_molecule_indices) == len(self.molecules)
            and len(self.molecules) > 0
        ):
            self.select_all_var.set(1)
        center_selected_btn = ttk.Button(
            select_frame,
            text="Center Selected at Origin",
            command=self._center_selected_at_origin,
            style="TButton",
        )
        center_selected_btn.pack(fill="x", padx=5, pady=(5, 2))
        trans_frame = ttk.LabelFrame(
            parent_frame, text="Relative Transformation", padding=(10, 5)
        )
        trans_frame.pack(pady=5, padx=5, fill="x", expand=False)
        self._create_slider(
            trans_frame,
            "Translate X:",
            self.trans_x,
            self.trans_x_str,
            FORMAT_TRANS,
            SLIDER_TRANSLATION_RANGE[0],
            SLIDER_TRANSLATION_RANGE[1],
            SLIDER_RESOLUTION_TRANS,
        )
        self._create_slider(
            trans_frame,
            "Translate Y:",
            self.trans_y,
            self.trans_y_str,
            FORMAT_TRANS,
            SLIDER_TRANSLATION_RANGE[0],
            SLIDER_TRANSLATION_RANGE[1],
            SLIDER_RESOLUTION_TRANS,
        )
        self._create_slider(
            trans_frame,
            "Translate Z:",
            self.trans_z,
            self.trans_z_str,
            FORMAT_TRANS,
            SLIDER_TRANSLATION_RANGE[0],
            SLIDER_TRANSLATION_RANGE[1],
            SLIDER_RESOLUTION_TRANS,
        )
        self._create_slider(
            trans_frame,
            "Rotate X (°):",
            self.rot_x,
            self.rot_x_str,
            FORMAT_ROT,
            SLIDER_ROTATION_RANGE[0],
            SLIDER_ROTATION_RANGE[1],
            SLIDER_RESOLUTION_ROT,
        )
        self._create_slider(
            trans_frame,
            "Rotate Y (°):",
            self.rot_y,
            self.rot_y_str,
            FORMAT_ROT,
            SLIDER_ROTATION_RANGE[0],
            SLIDER_ROTATION_RANGE[1],
            SLIDER_RESOLUTION_ROT,
        )
        self._create_slider(
            trans_frame,
            "Rotate Z (°):",
            self.rot_z,
            self.rot_z_str,
            FORMAT_ROT,
            SLIDER_ROTATION_RANGE[0],
            SLIDER_ROTATION_RANGE[1],
            SLIDER_RESOLUTION_ROT,
        )
        centroid_frame = ttk.LabelFrame(
            parent_frame, text="System Centroid Control", padding=(10, 5)
        )
        centroid_frame.pack(pady=5, padx=5, fill="x", expand=False)
        center_origin_btn = ttk.Button(
            centroid_frame,
            text="Center System at Origin",
            command=self._center_at_origin,
            style="TButton",
        )
        center_origin_btn.pack(fill="x", padx=5, pady=2)
        target_frame = ttk.Frame(centroid_frame, style="TLabelframe")
        target_frame.pack(fill="x", padx=5, pady=(5, 2))
        ttk.Label(target_frame, text="Target:", style="Bold.TLabel").grid(
            row=0, column=0, columnspan=6, sticky="w", pady=(0, 3)
        )
        ttk.Label(target_frame, text="X:", style="TLabel").grid(
            row=1, column=0, sticky="w", padx=(0, 2)
        )
        self.target_x_entry = ttk.Entry(
            target_frame,
            textvariable=self.target_x_var,
            width=7,
            font=FONT_DEFAULT,
            justify="right",
        )
        self.target_x_entry.grid(row=1, column=1, padx=(0, 5))
        ttk.Label(target_frame, text="Y:", style="TLabel").grid(
            row=1, column=2, sticky="w", padx=(0, 2)
        )
        self.target_y_entry = ttk.Entry(
            target_frame,
            textvariable=self.target_y_var,
            width=7,
            font=FONT_DEFAULT,
            justify="right",
        )
        self.target_y_entry.grid(row=1, column=3, padx=(0, 5))
        ttk.Label(target_frame, text="Z:", style="TLabel").grid(
            row=1, column=4, sticky="w", padx=(0, 2)
        )
        self.target_z_entry = ttk.Entry(
            target_frame,
            textvariable=self.target_z_var,
            width=7,
            font=FONT_DEFAULT,
            justify="right",
        )
        self.target_z_entry.grid(row=1, column=5)
        center_target_btn = ttk.Button(
            centroid_frame,
            text="Move System Centroid to Target",
            command=self._center_at_target,
            style="TButton",
        )
        center_target_btn.pack(fill="x", padx=5, pady=(3, 5))
        action_frame = ttk.LabelFrame(parent_frame, text="Actions", padding=(10, 5))
        action_frame.pack(pady=5, padx=5, fill="x", expand=False)
        save_btn = ttk.Button(
            action_frame,
            text="Save Combined Structure",
            command=self.save_structure,
            style="TButton",
        )
        save_btn.pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill="x")
        reset_btn = ttk.Button(
            action_frame, text="Reset View", command=self.reset_view, style="TButton"
        )
        reset_btn.pack(side=tk.RIGHT, padx=5, pady=5, expand=True, fill="x")

    def _create_slider(
        self,
        parent: tk.Frame,
        label_text: str,
        double_var: tk.DoubleVar,
        string_var: tk.StringVar,
        format_spec: str,
        from_: float,
        to: float,
        resolution: float,
    ):
        """Helper creates slider row with labels and links command via handler."""
        row_frame = ttk.Frame(parent, style="TLabelframe")
        row_frame.pack(fill="x", pady=2, padx=5)
        row_frame.columnconfigure(2, weight=1)
        main_label = ttk.Label(
            row_frame, text=label_text, width=12, anchor="w", style="TLabel"
        )
        main_label.grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 2))
        min_label = ttk.Label(row_frame, text=f"{from_:.1f}", style="Limit.TLabel")
        min_label.grid(row=1, column=1, sticky="e", padx=(0, 3))
        # *** Use _handle_slider_change for command ***
        scale = tk.Scale(
            row_frame,
            variable=double_var,
            orient=tk.HORIZONTAL,
            length=150,
            from_=from_,
            to=to,
            resolution=resolution,
            command=self._handle_slider_change,
            showvalue=False,
            troughcolor="black",
            activebackground="#555555",
            background=BG_COLOR_LBLFRAME,
            highlightthickness=0,
            bd=0,
            sliderrelief="flat",
        )
        scale.grid(row=1, column=2, sticky="ew")
        max_label = ttk.Label(row_frame, text=f"{to:+.1f}", style="Limit.TLabel")
        max_label.grid(row=1, column=3, sticky="w", padx=(3, 5))
        value_label = ttk.Label(
            row_frame, textvariable=string_var, width=5, style="Value.TLabel"
        )
        value_label.grid(row=1, column=4, sticky="e")

    # --- Centroid Callbacks ---
    def _calculate_current_centroid(self) -> Optional[np.ndarray]:
        """Calculates the overall centroid of the currently VISIBLE coordinates."""
        if not self.molecules:
            print("Warning: Cannot calculate centroid, no molecules loaded.")
            return None
        all_coords = []
        for mol in self.molecules:
            final_coords = mol.transformed_coords + self.global_offset
            if final_coords.size > 0:
                all_coords.append(final_coords)
        if not all_coords:
            print("Warning: Cannot calculate centroid, no valid coordinates found.")
            return None
        try:
            combined_coords = np.vstack(all_coords)
        except ValueError:
            print("Error: Could not stack coordinate arrays.", file=sys.stderr)
            return None
        return np.mean(combined_coords, axis=0)

    def _center_at_origin(self):
        """Callback to move the entire system centroid to (0,0,0)."""
        print("Centering system at origin...")
        current_centroid = self._calculate_current_centroid()
        if current_centroid is not None:
            offset_needed = -current_centroid
            self.global_offset += offset_needed
            print(
                f"  Applying offset: {offset_needed}, New global offset: {self.global_offset}"
            )
            self._draw_plot()
        else:
            messagebox.showwarning(
                "Centering Error", "Cannot calculate current centroid."
            )

    def _center_at_target(self):
        """Callback to move the entire system centroid to user-defined target."""
        print("Centering system at target...")
        try:
            tx = self.target_x_var.get()
            ty = self.target_y_var.get()
            tz = self.target_z_var.get()
            target_centroid = np.array([tx, ty, tz])
        except tk.TclError:
            messagebox.showerror("Input Error", "Invalid target coordinates.")
            return
        except Exception as e:
            messagebox.showerror(
                "Input Error", f"Could not read target coordinates: {e}"
            )
            return
        current_centroid = self._calculate_current_centroid()
        if current_centroid is not None:
            offset_needed = target_centroid - current_centroid
            self.global_offset += offset_needed
            print(
                f"  Applying offset: {offset_needed}, New global offset: {self.global_offset}"
            )
            self._draw_plot()
        else:
            messagebox.showwarning(
                "Centering Error", "Cannot calculate current centroid."
            )

    def _center_selected_at_origin(self):  # (MODIFIED - Updates final_translation)
        """Callback moves each selected molecule's centroid to the origin."""
        if not self.selected_molecule_indices:
            messagebox.showwarning(
                "No Selection", "Please select molecule(s) to center."
            )
            return
        print(
            f"Centering {len(self.selected_molecule_indices)} selected molecule(s) at origin..."
        )
        molecules_to_center = [
            m for m in self.molecules if m.id in self.selected_molecule_indices
        ]
        if not molecules_to_center:
            messagebox.showerror("Internal Error", "Selected molecule IDs not found.")
            return

        for molecule in molecules_to_center:
            if (
                molecule.transformed_coords.size > 0
            ):  # Use current transformed coords for centroid calc
                try:
                    mol_centroid = np.mean(molecule.transformed_coords, axis=0)
                    offset = -mol_centroid
                    # Apply offset to the stored final_translation
                    molecule.final_translation += offset
                    # Recalculate transformed_coords based on the new final state
                    molecule.apply_final_transformation()
                    print(
                        f"  Centered '{molecule.name}' (new final_translation: {molecule.final_translation})"
                    )
                except Exception as e:
                    print(f"  Error centering '{molecule.name}': {e}", file=sys.stderr)
                    messagebox.showerror(
                        "Centering Error", f"Could not center '{molecule.name}':\n{e}"
                    )
            else:
                print(f"  Skipping '{molecule.name}' as it has no coordinates.")

        self._draw_plot()  # Redraw the plot with updated coordinates

    # --- Event Handlers & Update Logic ---

    def _reset_sliders_to_zero(self):
        """Helper function to reset all transformation sliders to zero."""
        # Note: This will trigger the _handle_slider_change -> _update_view
        # if the flag isn't set, which is prevented during selection changes.
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
        print("  Resetting sliders to zero")
        self.trans_x.set(0.0)
        self.trans_y.set(0.0)
        self.trans_z.set(0.0)
        self.rot_x.set(0.0)
        self.rot_y.set(0.0)
        self.rot_z.set(0.0)

    def _sync_sliders_to_selection(self):
        """Updates sliders based on the current selection."""
        if len(self.selected_molecule_indices) == 1:
            selected_id = self.selected_molecule_indices[0]
            # Find the molecule object (safer than assuming list index matches ID)
            selected_mol = next(
                (m for m in self.molecules if m.id == selected_id), None
            )
            if selected_mol:
                print(f"  Syncing sliders to '{selected_mol.name}'")
                # Sync translation sliders
                self.trans_x.set(selected_mol.final_translation[0])
                self.trans_y.set(selected_mol.final_translation[1])
                self.trans_z.set(selected_mol.final_translation[2])
                # Reset rotation sliders (as planned, avoiding Euler complexity)
                self.rot_x.set(0.0)
                self.rot_y.set(0.0)
                self.rot_z.set(0.0)
                # TODO: Implement Euler angle extraction here if Scipy is available
                # and rotation syncing is desired.
                # if SCIPY_AVAILABLE:
                #     try:
                #         r = R.from_matrix(selected_mol.final_rotation_matrix)
                #         # Use a suitable Euler sequence like 'zyx'
                #         angles_deg = r.as_euler('zyx', degrees=True)
                #         # Be careful with angle order ZYX -> set rot_z, rot_y, rot_x
                #         self.rot_z.set(angles_deg[0])
                #         self.rot_y.set(angles_deg[1])
                #         self.rot_x.set(angles_deg[2])
                #     except Exception as e:
                #         print(f"Error converting rotation matrix to Euler angles: {e}", file=sys.stderr)
                #         # Fallback: Reset rotation sliders if conversion fails
                #         self.rot_x.set(0.0); self.rot_y.set(0.0); self.rot_z.set(0.0)
            else:
                print("  Warning: Selected molecule ID not found for slider sync.")
                self._reset_sliders_to_zero()
        else:
            # 0 or >1 molecules selected, reset all sliders
            print(
                f"  Selection count is {len(self.selected_molecule_indices)}. Resetting sliders."
            )
            self._reset_sliders_to_zero()

    def _toggle_all_selection(self):
        """Handles 'All Molecules' checkbox click. Syncs sliders."""
        select_all = self.select_all_var.get() == 1
        new_selected_indices = []
        for mol_name, var in self.selection_vars.items():
            var.set(1 if select_all else 0)
        if select_all:
            new_selected_indices.extend(self.mol_name_to_id_map.values())

        if set(self.selected_molecule_indices) != set(new_selected_indices):
            self.selected_molecule_indices = new_selected_indices
            print(f"Selection changed (Toggle All): {self.selected_molecule_indices}")
            self._block_slider_command = (
                True  # Prevent update_view trigger from slider.set()
            )
            self._sync_sliders_to_selection()
            self._block_slider_command = False
            self._draw_plot()  # Only redraw needed after syncing/resetting sliders

    def _update_selection_from_individual(self):
        """Handles individual checkbox clicks. Syncs sliders if selection changes."""
        new_selection = [
            self.mol_name_to_id_map[name]
            for name, var in self.selection_vars.items()
            if var.get() == 1
        ]
        all_selected = (
            len(new_selection) == len(self.molecules) and len(self.molecules) > 0
        )
        self.select_all_var.set(1 if all_selected else 0)

        if set(self.selected_molecule_indices) != set(new_selection):
            self.selected_molecule_indices = new_selection
            print(f"Selection changed (Individual): {self.selected_molecule_indices}")
            self._block_slider_command = (
                True  # Prevent update_view trigger from slider.set()
            )
            self._sync_sliders_to_selection()
            self._block_slider_command = False
            self._draw_plot()  # Only redraw needed after syncing/resetting sliders

    def _handle_slider_change(self, event: Optional[Any] = None):
        """Intermediate handler for slider command to respect the block flag."""
        if self._block_slider_command:
            # print("Slider command blocked") # Optional debug print
            return  # Do nothing if change was programmatic
        # print("Slider command executing _update_view") # Optional debug print
        self._update_view()

    def _update_view(self, event: Optional[Any] = None):
        """
        Callback for MANUAL slider changes. Updates the stored transform state
        for selected molecules and redraws the plot.
        """
        if self._block_slider_command:  # Double check flag
            print("Warning: _update_view called while command should be blocked.")
            return
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

        # Get current transform defined by sliders
        current_trans_vector = np.array(
            [self.trans_x.get(), self.trans_y.get(), self.trans_z.get()]
        )
        current_rot_matrix = build_rotation_matrix(
            self.rot_x.get(), self.rot_y.get(), self.rot_z.get()
        )

        # Update the final state for selected molecules ONLY
        if not self.selected_molecule_indices:
            # If nothing is selected, sliders shouldn't really do anything
            # print("Slider moved but nothing selected.") # Optional info
            pass  # Or maybe redraw? Let's just redraw in case global offset changed?
        else:
            print(
                f"Applying slider transform to molecules: {self.selected_molecule_indices}"
            )
            for molecule in self.molecules:
                if molecule.id in self.selected_molecule_indices:
                    molecule.final_translation = current_trans_vector
                    molecule.final_rotation_matrix = current_rot_matrix
                    molecule.apply_final_transformation()  # Recalculate transformed_coords

        # Redraw the plot using updated transformed_coords + global_offset
        self._draw_plot()

    # --- Plotting ---
    def _draw_plot(self, event: Optional[Any] = None):
        """Clears axes and redraws molecules based on current style and transformations."""
        if self.ax is None or self.canvas is None or self.fig is None:
            return
        self.ax.clear()
        style = self.representation_style.get()
        mol_colors = plt.cm.tab20
        all_final_coords_list = []
        # print(f"Drawing plot with style: {style}") # Debug print
        for idx, molecule in enumerate(self.molecules):
            # molecule.apply_final_transformation() # Ensure coords are up-to-date? Should be handled by update_view/reset
            coords_relative = molecule.transformed_coords
            # These reflect final_translation/rotation
            if coords_relative.size == 0:
                continue
            final_coords = coords_relative + self.global_offset
            all_final_coords_list.append(final_coords)
            symbols = molecule.symbols
            x, y, z = final_coords.T
            atom_colors = get_element_property(symbols, CPK_COLORS, DEFAULT_ATOM_COLOR)
            show_label = molecule.name if idx < 15 else None
            # --- Plotting logic based on style ---
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
                    if 0 <= i < len(final_coords) and 0 <= j < len(final_coords):
                        bond_coords = final_coords[[i, j]]
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
                    if 0 <= i < len(final_coords) and 0 <= j < len(final_coords):
                        bond_coords = final_coords[[i, j]]
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
        # --- Post-Plotting Adjustments ---
        if not all_final_coords_list:
            self.ax.set_title("No molecules to plot")
            self.canvas.draw()
            return
        all_final_coords_array = np.vstack(all_final_coords_list)
        if all_final_coords_array.size == 0:
            self.ax.set_title("No coordinates to plot")
            self.canvas.draw()
            return
        min_coords = np.min(all_final_coords_array, axis=0)
        max_coords = np.max(all_final_coords_array, axis=0)
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
        self.fig.tight_layout(rect=[0, 0, 0.85, 1])
        self.canvas.draw()

    # --- File Operations & Reset ---
    def save_structure(self):
        """Saves the current state of all molecules to a combined XYZ file."""
        if not self.molecules:
            messagebox.showwarning("Save Structure", "No molecules loaded.")
            return
        save_path_str = filedialog.asksaveasfilename(
            initialdir=".",
            initialfile=DEFAULT_OUTPUT_FILENAME,
            defaultextension=".xyz",
            filetypes=[("XYZ files", "*.xyz"), ("All files", "*.*")],
        )
        if not save_path_str:
            return
        save_path = Path(save_path_str)
        symbols_combined = []
        coords_to_save_list = []
        for molecule in self.molecules:
            symbols_combined.extend(molecule.symbols)
            coords_to_save = molecule.transformed_coords + self.global_offset
            coords_to_save_list.append(coords_to_save)
        if not coords_to_save_list:
            messagebox.showerror("Save Error", "No coordinate data.")
            return
        coords_combined_np = np.vstack(coords_to_save_list)
        total_atoms = len(symbols_combined)
        try:
            with save_path.open("w") as file:
                file.write(
                    f"{total_atoms}\nCombined adjusted structure (Global Offset: {self.global_offset})\n"
                )
                for symbol, coord in zip(symbols_combined, coords_combined_np):
                    file.write(
                        f"{symbol:<4} {coord[0]:>12.6f} {coord[1]:>12.6f} {coord[2]:>12.6f}\n"
                    )
            messagebox.showinfo("Save Successful", f"Structure saved to:\n{save_path}")
        except IOError as e:
            messagebox.showerror("Save Error", f"Could not write file:\n{e}")
            print(f"Error saving file: {e}", file=sys.stderr)
        except Exception as e:
            messagebox.showerror("Save Error", f"An unexpected error occurred: {e}")
            print(f"Unexpected error saving file: {e}", file=sys.stderr)

    def reset_view(self):
        """Resets sliders, global offset, AND individual molecule transforms."""
        print("Resetting view...")
        self._block_slider_command = True  # Block command during programmatic reset
        self._reset_sliders_to_zero()
        self._block_slider_command = False
        self.global_offset = np.zeros(3)
        print(f"  Global offset reset to: {self.global_offset}")
        self.target_x_var.set(0.0)
        self.target_y_var.set(0.0)
        self.target_z_var.set(0.0)
        # Reset individual molecule transformations
        for molecule in self.molecules:
            molecule.reset_transformation()  # Resets internal state and transformed_coords
        # Redraw the plot with everything reset
        self._draw_plot()
        print("View reset complete.")


# --- Main Execution ---
def main():
    parser = argparse.ArgumentParser(
        description="Visualize molecules from XYZ files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "xyz_files", type=Path, nargs="+", help="Path(s) to the input XYZ file(s)."
    )
    args = parser.parse_args()
    valid_files = []
    for file_path in args.xyz_files:
        if not file_path.is_file():
            print(f"Error: Input file not found: '{file_path}'", file=sys.stderr)
        elif not file_path.name.lower().endswith(".xyz"):
            print(
                f"Warning: Input file '{file_path.name}' no .xyz extension.",
                file=sys.stderr,
            )
            valid_files.append(file_path)
        else:
            valid_files.append(file_path)
    if not valid_files:
        print("Error: No valid input files found. Exiting.", file=sys.stderr)
        sys.exit(1)
    try:
        root = tk.Tk()
        app = MoleculeVisualizer(root, valid_files)
        if root.winfo_exists():
            root.mainloop()
    except Exception as e:
        print(f"\n--- Error launching application ---", file=sys.stderr)
        print(f"Error Type: {type(e).__name__}", file=sys.stderr)
        print(f"Error Details: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        print("-----------------------------------", file=sys.stderr)
        sys.exit("Application terminated due to an unexpected error.")


if __name__ == "__main__":
    try:
        if sys.platform != "win32" and "DISPLAY" not in os.environ:
            print(
                "Error: Cannot run Tkinter GUI. DISPLAY environment variable not set.",
                file=sys.stderr,
            )
            print(
                "Ensure X11 forwarding or a virtual framebuffer (e.g., Xvfb) is active.",
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

"""
molvis_tkinter/app_tkinter.py

Main application script for the Tkinter-based Molecule Visualizer.
Uses molvis_core for data/logic and molvis_plotting.matplotlib_plotter for display.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import argparse
import os
from pathlib import Path
import sys
from typing import List, Tuple, Dict, Optional, Any

# --- Add project root to sys.path ---
try:
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent  # Go up two levels
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        print(f"DEBUG: Added project root to sys.path: {project_root}")
except NameError:
    print(
        "Warning: Could not automatically determine project root via __file__.",
        file=sys.stderr,
    )

# --- Import Core Library Components ---
# Use absolute imports assuming project root is in path
from molvis_core.molecule import Molecule
from molvis_core.constants import (
    REPRESENTATION_STYLES,
    DEFAULT_REPRESENTATION,
    SLIDER_TRANSLATION_RANGE,
    SLIDER_ROTATION_RANGE,
    SLIDER_RESOLUTION_TRANS,
    SLIDER_RESOLUTION_ROT,
    DEFAULT_OUTPUT_FILENAME,
    # Styling and Formatting constants are NOT imported from core
)
from molvis_core import geometry
from molvis_core import logic
from molvis_core import io as core_io  # Alias io


# --- Import Plotting Adapter ---
from molvis_plotting.matplotlib_plotter import plot_molecules_matplotlib


# --- Import Styling ---
try:
    # Import setup function AND specific constants used directly in this file
    from styles import (
        setup_styles,
        BG_COLOR_FRAME,
        BG_COLOR_LBLFRAME,
        FONT_DEFAULT,
        FONT_BOLD,
        BG_COLOR_BTN,
    )
except ImportError as e:
    print(f"FATAL Error importing styles: {e}", file=sys.stderr)
    print("Please ensure tkinter_styles.py is accessible.", file=sys.stderr)
    # Define fallback style function if import fails
    BG_COLOR_FRAME = "#F0F0F0"
    BG_COLOR_LBLFRAME = "#ECECEC"
    FONT_DEFAULT = ("Arial", 9)
    FONT_BOLD = ("Arial", 10, "bold")
    BG_COLOR_BTN = "#D5D5D5"

    def setup_styles(root):
        print("Warning: Using fallback empty style setup.")


# --- Define UI Specific Constants ---
DEFAULT_WINDOW_SIZE = "1200x750"
# Define formatting strings locally
FORMAT_TRANS = "{:.1f}"
FORMAT_ROT = "{:.0f}"

# Type alias for transformation state dictionary managed by UI layer
TransformState = Dict[
    str, np.ndarray
]  # Expects {'translation': vec (3,), 'rotation': mat (3x3)}


# --- Main Application Class ---
class MoleculeVisualizer:
    """
    Main application class for the Tkinter Molecule Visualizer.
    Manages the GUI, state, plotting, and interactions. Uses core library
    for data/logic and matplotlib_plotter for visualization.
    """

    # --- __init__ and other methods ---
    # (Implementation remains the same as the previous version,
    #  references to constants like BG_COLOR_FRAME etc. now use
    #  constants imported from tkinter_styles or defined locally)
    def __init__(self, master: tk.Tk, molecule_source: Any):
        """Initializes the MoleculeVisualizer application."""
        self.master = master
        self.molecules: List[Molecule] = []
        self.molecule_transforms: Dict[int, TransformState] = {}
        self.selected_molecule_ids: List[int] = []
        self.mol_name_to_id_map: Dict[str, int] = {}
        self.global_offset = np.zeros(3)
        self._block_slider_command = False

        self._configure_window(molecule_source)
        self._load_and_process_data(molecule_source)

        self.fig = None
        self.ax = None
        self.canvas = None
        self.control_frame = None
        self.scrollable_frame = None
        self.selection_vars = {}
        self.select_all_var = tk.IntVar(value=0)
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
                "Initialization Error",
                "Molecule loading failed. Cannot start application.",
            )
            self.master.quit()
            return

        if self.molecules:
            self.selected_molecule_ids = [self.molecules[0].id]

        self._setup_var_traces()
        self._setup_gui()
        self._sync_sliders_to_selection()
        self._draw_plot()

    def _configure_window(self, molecule_source: Any):
        """Sets up main window properties like title, size, and resizing."""
        title = "Molecule Visualizer"
        if isinstance(molecule_source, list) and all(
            isinstance(p, Path) for p in molecule_source
        ):
            num_files = len(molecule_source)
            if num_files == 1:
                title += f" - {molecule_source[0].name}"
            elif num_files > 1:
                title += f" - {num_files} files"
        elif isinstance(molecule_source, tuple):
            title += " - Default System"
        self.master.title(title)
        self.master.geometry(DEFAULT_WINDOW_SIZE)  # Use locally defined constant
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)
        self.master.config(bg=BG_COLOR_FRAME)  # Use imported constant

    def _load_and_process_data(self, source: Any):  # (Same as before)
        """Loads molecule data, populates state, initializes transforms."""
        print("Processing input source...")
        all_molecules = []
        mol_name_to_id = {}
        global_mol_index = 0
        if isinstance(source, list) and all(isinstance(p, Path) for p in source):
            print(f"Loading from {len(source)} file path(s)...")
            for file_idx, file_path in enumerate(source):
                print(f"  Loading: {file_path.name}")
                symbols, coords = core_io.load_xyz(file_path)
                if symbols is not None and coords is not None and len(symbols) > 0:
                    print(f"    Found {len(symbols)} atoms. Calculating bonds...")
                    bonds = logic.determine_bonds(symbols, coords)
                    print(f"    Found {len(bonds)} bonds.")
                    base_name = file_path.stem
                    mol_name = base_name if len(source) > 1 else "Molecule 1"
                    unique_mol_name = mol_name
                    count = 1
                    while unique_mol_name in mol_name_to_id:
                        count += 1
                        unique_mol_name = f"{mol_name}_{count}"
                    molecule = Molecule(
                        id=global_mol_index,
                        name=unique_mol_name,
                        symbols=symbols,
                        coords=coords,
                        bonds=bonds,
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
        elif isinstance(source, tuple) and len(source) == 3:
            print("Loading from generated data...")
            all_symbols, all_coords, boundaries = source
            if not boundaries:
                boundaries = [(0, len(all_symbols))]
            for file_idx, (start, end) in enumerate(boundaries):
                symbols = all_symbols[start:end]
                coords = all_coords[start:end]
                if len(symbols) > 0:
                    print(
                        f"    Processing molecule {file_idx+1} ({len(symbols)} atoms). Calculating bonds..."
                    )
                    bonds = logic.determine_bonds(symbols, coords)
                    print(f"    Found {len(bonds)} bonds.")
                    mol_name = f"Molecule_{file_idx+1}"
                    unique_mol_name = mol_name
                    count = 1
                    while unique_mol_name in mol_name_to_id:
                        count += 1
                        unique_mol_name = f"{mol_name}_{count}"
                    molecule = Molecule(
                        id=global_mol_index,
                        name=unique_mol_name,
                        symbols=symbols,
                        coords=coords,
                        bonds=bonds,
                        source_file_index=file_idx,
                        source_file_name="Generated",
                    )
                    all_molecules.append(molecule)
                    mol_name_to_id[unique_mol_name] = global_mol_index
                    global_mol_index += 1
                else:
                    print(f"    Skipping generated molecule {file_idx+1} (no atoms).")
        else:
            print("Error: Invalid molecule_source type provided.", file=sys.stderr)
            self.molecules = []
            self.mol_name_to_id_map = {}
            self.molecule_transforms = {}
            return
        self.molecules = all_molecules
        self.mol_name_to_id_map = mol_name_to_id
        self.molecule_transforms = {
            mol.id: {"translation": np.zeros(3), "rotation": np.identity(3)}
            for mol in self.molecules
        }
        print(f"Successfully processed {len(self.molecules)} molecule(s) in total.")

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
        setup_styles(self.master)  # Apply ttk styles
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
            messagebox.showerror("Plot Error", f"Failed to create 3D plot:\n{e}")
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
        self.select_all_var = tk.IntVar(
            value=1 if len(self.selected_molecule_ids) == len(self.molecules) else 0
        )
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
            is_selected = mol_id in self.selected_molecule_ids
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
    ):  # (Same as before)
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

    # --- Centroid Callbacks --- (Same as before)
    def _calculate_current_centroid(self) -> Optional[np.ndarray]:
        """Calculates the overall centroid of the currently VISIBLE coordinates."""
        if not self.molecules:
            print("Warning: Cannot calculate centroid, no molecules loaded.")
            return None
        all_coords = []
        for mol in self.molecules:
            mol.apply_final_transformation()
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

    def _center_selected_at_origin(self):
        """Callback moves each selected molecule's centroid to the origin."""
        if not self.selected_molecule_ids:
            messagebox.showwarning(
                "No Selection", "Please select molecule(s) to center."
            )
            return
        print(
            f"Centering {len(self.selected_molecule_ids)} selected molecule(s) at origin..."
        )
        molecules_to_center = [
            m for m in self.molecules if m.id in self.selected_molecule_ids
        ]
        if not molecules_to_center:
            messagebox.showerror("Internal Error", "Selected molecule IDs not found.")
            return
        something_changed = False
        for molecule in molecules_to_center:
            molecule.apply_final_transformation()  # Ensure coords are current
            if molecule.transformed_coords.size > 0:
                try:
                    mol_centroid = np.mean(molecule.transformed_coords, axis=0)
                    offset = -mol_centroid
                    if molecule.id in self.molecule_transforms:
                        self.molecule_transforms[molecule.id]["translation"] += offset
                        molecule.final_translation = self.molecule_transforms[
                            molecule.id
                        ]["translation"]
                        molecule.apply_final_transformation()
                        print(
                            f"  Centered '{molecule.name}' (new final_translation: {molecule.final_translation})"
                        )
                        something_changed = True
                    else:
                        print(
                            f"  Error: Transform state not found for molecule {molecule.name}"
                        )
                except Exception as e:
                    print(f"  Error centering '{molecule.name}': {e}", file=sys.stderr)
                    messagebox.showerror(
                        "Centering Error", f"Could not center '{molecule.name}':\n{e}"
                    )
            else:
                print(f"  Skipping '{molecule.name}' as it has no coordinates.")
        if something_changed:
            self._sync_sliders_to_selection()
            self._draw_plot()

    # --- Event Handlers & Update Logic --- (Same as before)
    def _reset_sliders_to_zero(self):
        """Helper function to reset all transformation sliders to zero."""
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
        """Updates sliders based on the current selection's stored state."""
        self._block_slider_command = True
        try:
            if len(self.selected_molecule_ids) == 1:
                selected_id = self.selected_molecule_ids[0]
                transform_state = self.molecule_transforms.get(selected_id)
                if transform_state:
                    selected_mol = next(
                        (m for m in self.molecules if m.id == selected_id), None
                    )
                    print(
                        f"  Syncing sliders to '{selected_mol.name if selected_mol else 'Unknown'}' (ID: {selected_id})"
                    )
                    self.trans_x.set(transform_state["translation"][0])
                    self.trans_y.set(transform_state["translation"][1])
                    self.trans_z.set(transform_state["translation"][2])
                    self.rot_x.set(0.0)
                    self.rot_y.set(0.0)
                    self.rot_z.set(0.0)  # Reset rotation
                else:
                    print(
                        f"  Warning: Transform state not found for selected molecule ID {selected_id}. Resetting sliders."
                    )
                    self._reset_sliders_to_zero()
            else:
                print(
                    f"  Selection count is {len(self.selected_molecule_ids)}. Resetting sliders."
                )
                self._reset_sliders_to_zero()
        finally:
            self._block_slider_command = False

    def _toggle_all_selection(self):
        """Handles 'All Molecules' checkbox click. Syncs sliders."""
        current_selection_set = set(self.selected_molecule_ids)
        select_all = self.select_all_var.get() == 1
        new_selected_ids = list(self.mol_name_to_id_map.values()) if select_all else []
        new_selection_set = set(new_selected_ids)
        for mol_name, var in self.selection_vars.items():
            var.set(1 if select_all else 0)
        if current_selection_set != new_selection_set:
            self.selected_molecule_ids = new_selected_ids
            print(f"Selection changed (Toggle All): {self.selected_molecule_ids}")
            self._sync_sliders_to_selection()
            self._draw_plot()

    def _update_selection_from_individual(self):
        """Handles individual checkbox clicks. Syncs sliders if selection changes."""
        current_selection_set = set(self.selected_molecule_ids)
        new_selection = [
            self.mol_name_to_id_map[name]
            for name, var in self.selection_vars.items()
            if var.get() == 1
        ]
        new_selection_set = set(new_selection)
        all_selected = (
            len(new_selection) == len(self.molecules) and len(self.molecules) > 0
        )
        self.select_all_var.set(1 if all_selected else 0)
        if current_selection_set != new_selection_set:
            self.selected_molecule_ids = new_selection
            print(f"Selection changed (Individual): {self.selected_molecule_ids}")
            self._sync_sliders_to_selection()
            self._draw_plot()

    def _handle_slider_change(self, event: Optional[Any] = None):
        """Intermediate handler for slider command to respect the block flag."""
        if self._block_slider_command:
            return
        self._update_view()

    def _update_view(self, event: Optional[Any] = None):
        """Callback for MANUAL slider changes. Updates stored transform state."""
        if self._block_slider_command:
            print("Warning: _update_view called while command blocked.")
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
        current_trans_vector = np.array(
            [self.trans_x.get(), self.trans_y.get(), self.trans_z.get()]
        )
        current_rot_matrix = geometry.build_rotation_matrix(
            self.rot_x.get(), self.rot_y.get(), self.rot_z.get()
        )
        if not self.selected_molecule_ids:
            pass
        else:
            for mol_id in self.selected_molecule_ids:
                if mol_id in self.molecule_transforms:
                    self.molecule_transforms[mol_id][
                        "translation"
                    ] = current_trans_vector
                    self.molecule_transforms[mol_id]["rotation"] = current_rot_matrix
                    molecule = next((m for m in self.molecules if m.id == mol_id), None)
                    if molecule:
                        molecule.final_translation = current_trans_vector
                        molecule.final_rotation_matrix = current_rot_matrix
                        molecule.apply_final_transformation()
        self._draw_plot()

    # --- Plotting --- (MODIFIED - Calls external plotter)
    def _draw_plot(self, event: Optional[Any] = None):
        """Clears axes and redraws molecules using the matplotlib plotter."""
        if self.ax is None or self.canvas is None or self.fig is None:
            return
        # Ensure transformed_coords are up-to-date based on stored state
        for mol in self.molecules:
            mol.apply_final_transformation()
        # Call the dedicated plotting function from the adapter module
        plot_molecules_matplotlib(
            ax=self.ax,
            molecules=self.molecules,
            molecule_transforms=self.molecule_transforms,
            style=self.representation_style.get(),
            global_offset=self.global_offset,
        )
        self.fig.tight_layout(rect=[0, 0, 0.85, 1])
        self.canvas.draw()

    # --- File Operations & Reset --- (MODIFIED reset_view)
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
        all_symbols = []
        all_final_coords = []
        for molecule in self.molecules:
            molecule.apply_final_transformation()
            final_coords = molecule.transformed_coords + self.global_offset
            all_symbols.extend(molecule.symbols)
            all_final_coords.append(final_coords)
        if not all_final_coords:
            messagebox.showerror("Save Error", "No coordinate data.")
            return
        try:
            combined_coords_np = np.vstack(all_final_coords)
            comment = (
                f"Combined adjusted structure (Global Offset: {self.global_offset})"
            )
            xyz_content = core_io.format_xyz_string(
                all_symbols, combined_coords_np, comment
            )
            with save_path.open("w") as file:
                file.write(xyz_content)
            messagebox.showinfo("Save Successful", f"Structure saved to:\n{save_path}")
            print(f"Combined adjusted structure saved to '{save_path}'")
        except ValueError as e:
            messagebox.showerror("Save Error", f"Could not format XYZ data:\n{e}")
            print(f"Error formatting XYZ: {e}", file=sys.stderr)
        except IOError as e:
            messagebox.showerror("Save Error", f"Could not write file:\n{e}")
            print(f"Error saving file: {e}", file=sys.stderr)
        except Exception as e:
            messagebox.showerror("Save Error", f"An unexpected error occurred: {e}")
            print(f"Unexpected error saving file: {e}", file=sys.stderr)

    def reset_view(self):
        """Resets sliders, global offset, AND individual molecule transforms."""
        print("Resetting view...")
        self._block_slider_command = True
        self._reset_sliders_to_zero()
        self._block_slider_command = False
        self.global_offset = np.zeros(3)
        print(f"  Global offset reset to: {self.global_offset}")
        self.target_x_var.set(0.0)
        self.target_y_var.set(0.0)
        self.target_z_var.set(0.0)
        print("  Resetting individual molecule transforms...")
        for molecule in self.molecules:
            # Reset the stored transform state dictionary
            if molecule.id in self.molecule_transforms:
                self.molecule_transforms[molecule.id] = {
                    "translation": np.zeros(3),
                    "rotation": np.identity(3),
                }
            # Reset the molecule object itself (calls apply_final_transformation)
            molecule.reset_transformation()
        self._draw_plot()
        print("View reset complete.")


# --- Main Execution --- (Same as before)
def main():
    """Parses arguments and runs the Tkinter Molecule Visualizer application."""
    parser = argparse.ArgumentParser(
        description="Visualize molecules from XYZ files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "xyz_files",
        type=Path,
        nargs="*",
        help="Path(s) to the input XYZ file(s). If none provided, loads default.",
    )
    args = parser.parse_args()
    molecule_source: Any = None
    if args.xyz_files:
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
        molecule_source = valid_files
    else:
        print("No input files specified, loading default two-benzene system.")
        molecule_source = core_io.create_two_benzenes()
    try:
        root = tk.Tk()
        app = MoleculeVisualizer(root, molecule_source)
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

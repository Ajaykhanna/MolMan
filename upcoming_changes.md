# Modular Molecule Visualizer Project

## 1. Overview

This project provides a framework and two sample applications for visualizing and manipulating molecular structures from XYZ files. The core goal of this implementation is **modularity**, separating the fundamental molecular logic, data handling, and plotting from the specific user interface implementations.

This repository contains:

* A core library (`molvis_core`) with data structures, constants, core logic, and file I/O.
* Plotting adapters (`molvis_plotting`) for Matplotlib and Plotly.
* A desktop GUI application using Tkinter and Matplotlib (`molvis_tkinter`).
* A web application using Streamlit and Plotly (`molvis_streamlit`).

Both applications allow loading multiple molecules (via file upload/command-line or pasting multi-block text in Streamlit), visualizing them with different representation styles (Lines, Ball & Stick, Space Filling), applying transformations (translation, rotation) persistently to selected molecules, centering individual molecules or the entire system, and exporting the adjusted structure as a combined XYZ file. A default system of two benzene molecules separated by 3Å is loaded if no input files are provided to the Tkinter app or if selected in the Streamlit app.

## 2. Project Structure

The project is organized into distinct modules/packages:

.├── molvis_core/            # Core library (UI and plotting independent)│   ├── init.py         # Makes 'molvis_core' a package│   ├── constants.py        # Physical constants, colors, radii, bond data, slider params│   ├── molecule.py         # Molecule dataclass definition│   ├── geometry.py         # Transformation math, centroid calculations│   ├── logic.py            # Bond determination logic│   ├── io.py               # XYZ file parsing, formatting, example generator│   └── helpers.py          # Utility functions (e.g., get_element_property)├── molvis_plotting/        # Plotting library adapters│   ├── init.py         # Makes 'molvis_plotting' a package│   ├── matplotlib_plotter.py # Function to plot using Matplotlib│   └── plotly_plotter.py     # Function to plot using Plotly├── molvis_tkinter/         # Tkinter Desktop Application│   ├── init.py         # Makes 'molvis_tkinter' a package│   ├── app_tkinter.py      # Main application class and execution logic│   └── tkinter_styles.py   # ttk styling configuration└── molvis_streamlit/       # Streamlit Web Application├── init.py         # Makes 'molvis_streamlit' a package└── app_streamlit.py    # Main application scriptrequirements.txt            # Python dependenciesREADME.md                   # This file
*(Note: Ensure empty `__init__.py` files exist in each subdirectory for Python to recognize them as packages).*

## 3. Module Descriptions

* **`molvis_core`**: Contains UI- and plotting-independent components.
  * `constants.py`: Defines physical constants, visualization constants, default parameters, style names, slider ranges/resolutions.
  * `molecule.py`: Defines the `Molecule` dataclass (symbols, original coords, bonds, identifiers, source info). *Does not store transformation state.*
  * `geometry.py`: Geometric operations: `calculate_centroid`, `build_rotation_matrix`, `apply_transform`.
  * `logic.py`: Bonding algorithms: `determine_bonds`, `get_bond_distance_range`.
  * `io.py`: XYZ I/O: `load_xyz` (from path), `load_multiple_xyz_from_text`, `format_xyz_string`. Includes `create_two_benzenes` example generator.
  * `helpers.py`: Utility functions like `get_element_property`.
* **`molvis_plotting`**: Adapters for plotting libraries. They take core `Molecule` objects *and* transformation state (managed by the UI) as input.
  * `matplotlib_plotter.py`: `plot_molecules_matplotlib` function using Matplotlib.
  * `plotly_plotter.py`: `plot_molecules_plotly` function using Plotly.
* **`molvis_tkinter`**: Desktop GUI application.
  * `tkinter_styles.py`: `setup_styles` function and local styling constants.
  * `app_tkinter.py`: `MoleculeVisualizer` class manages Tkinter UI, state (including `molecule_transforms` dict, `global_offset`), event handling. Uses core modules and `matplotlib_plotter`. Handles command-line args and default data loading.
* **`molvis_streamlit`**: Web application.
  * `app_streamlit.py`: Main script defining UI flow, using `st.session_state` for state management (including `molecule_transforms` dict, `global_offset`, slider values), handling interactions. Uses core modules and `plotly_plotter`. Includes default data loading option.

## 4. Core Concepts

* **XYZ Format:** Standard format assumed. Multi-block text pasting is supported in Streamlit. Each file/block defines its own atom count.
* **Bonding:** Distance-based using constants.
* **Transformations:** Each molecule's final transformation state (`translation` vector, `rotation` matrix) relative to its original coordinates is stored by the UI layer (`molecule_transforms` dict). Sliders update the state for selected molecules. A `global_offset` handles system-wide centering. Plotting functions apply these transforms dynamically. Individual centering modifies the stored `translation` for selected molecules.
* **Representations:** Styles (Lines, Ball & Stick, Space Filling) implemented via varying plot parameters (marker size, line width) based on constants (CPK colors, radii).
* **State Management:**
  * **Tkinter:** Instance variables in `MoleculeVisualizer` (`self.molecules`, `self.molecule_transforms`, `self.global_offset`, Tkinter vars).
  * **Streamlit:** `st.session_state` holds `molecule_data`, `molecule_transforms`, `global_offset`, slider values, selections, etc.

## 5. Setup & Installation

1. **Clone/Download:** Obtain the project files with the directory structure above.
2. **Environment:** Create and activate a Python virtual environment (recommended).

    ```bash
    python -m venv venv
    source venv/bin/activate # or venv\Scripts\activate on Windows
    ```

3. **Install Dependencies:** Create a `requirements.txt` file:

    ```txt
    numpy>=1.20.0
    matplotlib>=3.3.0
    plotly>=5.0.0
    streamlit>=1.16.0
    # Add scipy if implementing rotation slider sync later:
    # scipy>=1.7.0
    ```

    Install using pip:

    ```bash
    pip install -r requirements.txt
    ```

    *(Note: On some Linux systems, you might need `sudo apt-get update && sudo apt-get install python3-tk` for Tkinter).*

## 6. Running the Applications

**Important:** Run these commands from the **root `MolMan` directory** to ensure Python can find the modules correctly.

* **Tkinter Application:**
  * To load specific files:

        ```bash
        python molvis_tkinter/app_tkinter.py path/to/file1.xyz path/to/file2.xyz
        ```

  * To load the **default two-benzene system**:

        ```bash
        python molvis_tkinter/app_tkinter.py
        ```

  * *Requires a graphical display.*

* **Streamlit Application:**
  * Execute using the `streamlit run` command:

        ```bash
        streamlit run molvis_streamlit/app_streamlit.py
        ```

  * Open the provided URL (e.g., `http://localhost:8501`) in a web browser. Use the sidebar to upload files, paste text, or load the default system.

## 7. Dependencies

* Python 3.8+
* NumPy
* Matplotlib (for Tkinter version)
* Plotly (for Streamlit version)
* Streamlit (for Streamlit version)
* Tkinter (usually included with Python)

This modular structure enhances maintainability, testability, and the potential for future extensions, such as adding new UI frontends or plotting backends.

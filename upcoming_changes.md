# Modular Molecule Visualizer Project

## 1. Overview

This project provides a framework and two sample applications for visualizing and manipulating molecular structures from XYZ files. The core goal of this implementation is **modularity**, separating the fundamental molecular logic, data handling, and plotting from the specific user interface implementations.

This repository contains:
* A core library (`molvis_core`) with data structures and logic.
* Plotting adapters (`molvis_plotting`) for Matplotlib and Plotly.
* A desktop GUI application using Tkinter and Matplotlib (`molvis_tkinter`).
* A web application using Streamlit and Plotly (`molvis_streamlit`).

Both applications allow loading multiple molecules, visualizing them with different representation styles (Lines, Ball & Stick, Space Filling), applying transformations (translation, rotation) to selected molecules persistently, centering molecules or the entire system, and exporting the adjusted structure.

## 2. Project Structure

The project is organized into distinct modules/packages:

.├── molvis_core/            # Core library (UI and plotting independent)│   ├── init.py│   ├── constants.py        # Physical constants, colors, radii, bond data│   ├── molecule.py         # Molecule dataclass definition│   ├── geometry.py         # Transformation math, centroid calculations│   ├── logic.py            # Bond determination logic│   └── io.py               # XYZ file parsing, formatting, example generator├── molvis_plotting/        # Plotting library adapters│   ├── init.py│   ├── matplotlib_plotter.py # Function to plot using Matplotlib│   └── plotly_plotter.py     # Function to plot using Plotly├── molvis_tkinter/         # Tkinter Desktop Application│   ├── init.py│   ├── app_tkinter.py      # Main application class and execution logic│   └── tkinter_styles.py   # ttk styling configuration└── molvis_streamlit/       # Streamlit Web Application├── init.py└── app_streamlit.py    # Main application scriptrequirements.txt            # Python dependenciesREADME.md                   # This file
*(Note: `__init__.py` files are needed if these are treated as Python packages).*

## 3. Module Descriptions

* **`molvis_core`**: The heart of the application. Contains all fundamental data definitions and calculations that are independent of how the data is displayed or interacted with.
    * `constants.py`: Defines physical constants (bond lengths), visualization constants (CPK colors, atomic radii), default parameters (bond tolerance), and style names.
    * `molecule.py`: Defines the `Molecule` dataclass holding intrinsic data (symbols, original coordinates, bonds, identifiers).
    * `geometry.py`: Provides functions for geometric operations like centroid calculation (`calculate_centroid`), rotation matrix generation (`build_rotation_matrix`), and applying transformations (`apply_transform`).
    * `logic.py`: Contains algorithms like bond determination based on distance criteria (`determine_bonds`, `get_bond_distance_range`).
    * `io.py`: Handles reading (`load_xyz`) and formatting (`format_xyz_string`) XYZ data. Includes a function (`create_two_benzenes`) to generate default example data.
* **`molvis_plotting`**: Contains adapters for specific plotting libraries. Each plotter takes core `Molecule` objects and their current transformation state (managed by the UI) and generates a plot.
    * `matplotlib_plotter.py`: Uses Matplotlib's `Axes3D` to create static 3D plots.
    * `plotly_plotter.py`: Uses Plotly's `graph_objects` to create interactive 3D plots.
* **`molvis_tkinter`**: Implements the desktop GUI application.
    * `tkinter_styles.py`: Configures the look and feel using `ttk.Style`.
    * `app_tkinter.py`: Defines the `MoleculeVisualizer` class managing the Tkinter window, widgets, event callbacks, application state (including molecule transform states), and orchestrates calls to the core library and Matplotlib plotter. Handles command-line arguments via `argparse`.
* **`molvis_streamlit`**: Implements the web application.
    * `app_streamlit.py`: Defines the Streamlit application flow, UI layout (using `st.sidebar`, etc.), state management (using `st.session_state` to store molecule data and transform states), handles user interactions, and orchestrates calls to the core library and Plotly plotter.

## 4. Core Concepts

* **XYZ Format:** Assumes standard XYZ format where the first line is the number of atoms in *that specific file*.
* **Bonding:** Calculated based on interatomic distances compared to element-pair-specific ranges (average length ± tolerance).
* **Transformations:** Molecules store their own final transformation state (translation vector, rotation matrix). Sliders in the UI update this state for selected molecules. Transformations are applied relative to the molecule's original centroid. A separate `global_offset` handles system-wide centering.
* **Representations:** Different visual styles (Lines, Ball & Stick, Space Filling) are achieved by varying marker sizes (based on covalent or VdW radii) and line properties in the respective plotting libraries. CPK colors are used for atoms.
* **State Management:**
    * **Tkinter:** Managed via instance variables in the `MoleculeVisualizer` class, including a dictionary (`molecule_transforms`) holding the state for each molecule. Tkinter variables (`tk.StringVar`, etc.) link UI widgets to state.
    * **Streamlit:** Managed via `st.session_state`, storing the list of `Molecule` objects, the `molecule_transforms` dictionary, `global_offset`, and variables controlling widget states (slider positions, selections).

## 5. Setup & Installation

1.  **Clone/Download:** Obtain the project files.
2.  **Environment:** Create and activate a Python virtual environment (recommended).
    ```bash
    python -m venv venv
    source venv/bin/activate # or venv\Scripts\activate on Windows
    ```
3.  **Install Dependencies:** Create a `requirements.txt` file with the following content:
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
    *(Note: On some Linux systems, you might need to install Tkinter separately: `sudo apt-get update && sudo apt-get install python3-tk`)*

## 6. Running the Applications

Ensure your virtual environment is activated. Assume the Python scripts are organized in directories as described above.

* **Tkinter Application:**
    * Run from the *parent directory* containing the `molvis_tkinter`, `molvis_core`, etc. folders.
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
    * Run from the *parent directory*.
    * Execute using the `streamlit run` command:
        ```bash
        streamlit run molvis_streamlit/app_streamlit.py
        ```
    * Streamlit will provide a URL (usually `http://localhost:8501`) to open in your web browser. Use the sidebar controls within the web app to load files, paste text, or load the default system.

## 7. Dependencies

* Python 3.8+
* NumPy
* Matplotlib (for Tkinter version)
* Plotly (for Streamlit version)
* Streamlit (for Streamlit version)
* Tkinter (usually included with Python, may need separate install on Linux)

This modular structure provides a clear separation between the core molecular logic, the plotting implementation details, and the user interface framework, making the project easier to understand, maintain, and extend.

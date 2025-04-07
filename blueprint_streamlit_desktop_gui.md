# Molecule Visualizer - Streamlit/Plotly Blueprint

## 1. Overview

This document serves as a technical blueprint for the Streamlit-based Molecule Visualizer application. The application allows users to upload or paste molecular structure data in XYZ format, visualize the molecules in an interactive 3D plot using Plotly, apply transformations (rotation, translation) to selected molecules, switch between different visual representation styles, and export the potentially modified structure.

It leverages Streamlit for the web interface and user controls, and Plotly for generating interactive 3D visualizations directly in the browser. State management is handled using Streamlit's Session State to maintain data and UI consistency across user interactions.

## 2. Features

* **Input:**
    * Upload one or more XYZ files simultaneously.
    * Paste XYZ content directly into a text area.
* **Visualization:**
    * Interactive 3D plot powered by Plotly (rotate, pan, zoom).
    * Multiple representation styles:
        * Lines
        * Ball and Stick (using covalent radii)
        * Space Filling (using Van der Waals radii)
    * Atom coloring based on CPK conventions.
    * Atom sizing based on selected representation style and atomic radii.
* **Transformation:**
    * Select one or more molecules (loaded from files or pasted text) via checkboxes.
    * Apply translation along X, Y, Z axes using sliders.
    * Apply rotation around X, Y, Z axes using sliders.
    * Transformations are applied relative to each molecule's centroid.
* **Export:**
    * Prepare and download the current view (including all loaded molecules with applied transformations) as a single combined XYZ file.

## 3. Technology Stack

* **Language:** Python (3.8+)
* **Core Libraries:**
    * `streamlit`: Web application framework, UI components.
    * `plotly`: Interactive 3D plotting.
    * `numpy`: Numerical operations (coordinate manipulation, transformations).
* **Standard Libraries:** `io`, `dataclasses`, `typing`.

## 4. Setup & Installation

1.  **Prerequisites:** Ensure Python 3.8 or higher is installed.
2.  **Create Environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    # venv\Scripts\activate  # Windows
    ```
3.  **Install Libraries:**
    ```bash
    pip install streamlit plotly numpy
    ```
4.  **Requirements File:** Alternatively, create a `requirements.txt` file:
    ```txt
    streamlit>=1.16.0 # Or a recent version
    plotly>=5.0.0
    numpy>=1.20.0
    ```
    And install using:
    ```bash
    pip install -r requirements.txt
    ```

## 5. Execution

1.  Save the application code as a Python file (e.g., `molecule_app.py`).
2.  Run the Streamlit application from your terminal:
    ```bash
    streamlit run molecule_app.py
    ```
3.  Streamlit will provide a local URL (usually `http://localhost:8501`) to open in your web browser.

## 6. Core Concepts

* **XYZ File Format:** A simple text format where the first line is the total number of atoms, the second line is a comment, and subsequent lines contain the element symbol followed by X, Y, Z coordinates. Each loaded file is treated as defining one or more complete molecules based on its header.
* **Bond Determination:** Bonds are calculated based on interatomic distances. For each pair of atoms, the distance is calculated and compared against a range (average bond length ± tolerance) specific to the pair of element types involved.
* **Representations:**
    * **Lines:** Atoms shown as small dots, bonds as thin lines. Emphasizes connectivity.
    * **Ball and Stick:** Atoms shown as spheres scaled by covalent radii, bonds as thicker lines/cylinders. Common representation balancing structure and volume.
    * **Space Filling:** Atoms shown as large spheres scaled by Van der Waals radii, typically overlapping. Bonds are usually not shown explicitly. Represents the volume occupied by the molecule.
* **Transformations:**
    * **Translation:** Adding a constant vector `[tx, ty, tz]` to all atom coordinates.
    * **Rotation:** Applying a 3x3 rotation matrix (calculated from Euler angles Rx, Ry, Rz using `build_rotation_matrix`) to atom coordinates centered around the molecule's geometric centroid.

## 7. Code Structure / Architecture

The application is contained within a single Python script, leveraging Streamlit's execution model.

* **Top-Down Execution:** Streamlit reruns the entire script from top to bottom whenever a user interacts with a widget (slider, button, selectbox, etc.).
* **Session State (`st.session_state`):** Used to persist data and UI state across these reruns. Key data like the list of loaded `Molecule` objects, the current input source identifier, processing status, and selected UI options are stored here.
* **Layout:** Uses `st.sidebar` for controls (input, configuration, visualization options, transformations, export) and the main area for the primary output (the Plotly visualization).
* **Modularity:** Core logic (parsing, bonding, transformations, plotting) is encapsulated in helper functions or the `Molecule` class to keep the main script flow cleaner.

```mermaid
mindmap
  root((Molecule Visualizer (Streamlit/Plotly)))
    Purpose
      Visualize XYZ Files
      Transform Molecules
      Multiple Representations
      Export Results
    UI (Streamlit)
      Sidebar Controls
        Input (Upload/Paste)
        Visualization (Style Select)
        Transformation (Selection, Sliders)
        Export (Button, Download)
      Main Area
        Plotly Chart (Interactive 3D)
        Status Messages (Info/Error/Success)
    Core Logic
      File Parsing (`load_xyz_from_text`)
      Bond Determination (`determine_bonds`)
      Transformations (`apply_transformations`, `build_rotation_matrix`)
    Data Model
      `Molecule` Dataclass
        Attributes (symbols list, coordinates, bonds)
        Methods (load from XYZ, apply transformations)
        
        
# Refactored Streamlit App (Plotly version) with Persistent State Logic
# Fixed NameError related to fallback code and added sys.path modification.
# Fixed repeated st.spinner error.
# Added support for pasting multiple XYZ blocks.

import streamlit as st
import plotly.graph_objects as go
import numpy as np
from typing import List, Tuple, Dict, Optional, Any
import copy  # For deep copying selection state
import sys  # For printing errors and modifying path
from pathlib import Path  # For path manipulation

# --- Add project root to sys.path ---
# This makes the script more robust if run from different locations,
# assuming the script remains within its package structure relative to MolMan.
try:
    script_path = Path(__file__).resolve()
    project_root = (
        script_path.parent.parent
    )  # Go up two levels (molvis_streamlit -> MolMan)
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        print(f"DEBUG: Added project root to sys.path: {project_root}")
except NameError:
    # __file__ might not be defined in some execution contexts (e.g., Streamlit sharing)
    # Fallback or rely on PYTHONPATH / running from root in these cases.
    print(
        "Warning: Could not automatically determine project root via __file__.",
        file=sys.stderr,
    )

# --- Import Core Library Components ---
# Use absolute imports assuming project root is in path
try:
    from molvis_core.molecule import Molecule
    from molvis_core.constants import (
        REPRESENTATION_STYLES,
        DEFAULT_REPRESENTATION,
        SLIDER_TRANSLATION_RANGE,
        SLIDER_ROTATION_RANGE,
        SLIDER_RESOLUTION_TRANS,
        SLIDER_RESOLUTION_ROT,
        DEFAULT_OUTPUT_FILENAME,
        # Styling constants are not needed here
    )
    from molvis_core import geometry
    from molvis_core import logic
    from molvis_core import io as core_io  # Alias io
except ImportError as e:
    # Use st.error for visibility in Streamlit if imports fail critically
    st.error(
        f"FATAL Error importing core library: {e}. Ensure molvis_core modules are accessible (e.g., run from MolMan directory or check PYTHONPATH)."
    )
    # Stop execution if core components missing
    st.stop()


# --- Import Plotting Adapter ---
try:
    from molvis_plotting.plotly_plotter import plot_molecules_plotly
except ImportError as e:
    st.error(
        f"FATAL Error importing plotting library: {e}. Ensure molvis_plotting.plotly_plotter is accessible."
    )
    st.stop()

# Type alias for transformation state dictionary managed by UI layer
TransformState = Dict[
    str, np.ndarray
]  # Expects {'translation': vec (3,), 'rotation': mat (3x3)}


# --- Centroid Helper ---
def calculate_overall_centroid(
    molecules: List[Molecule], global_offset: np.ndarray
) -> Optional[np.ndarray]:
    """Calculates the overall centroid of the currently VISIBLE coordinates."""
    if not molecules:
        return None
    all_coords = []
    for mol in molecules:
        # Ensure coords are up-to-date before calculating centroid
        mol.apply_final_transformation()
        final_coords = mol.transformed_coords + global_offset
        if final_coords.size > 0:
            all_coords.append(final_coords)
    if not all_coords:
        return None
    try:
        combined_coords = np.vstack(all_coords)
    except ValueError:
        return None  # Should not happen if checks are done
    return np.mean(combined_coords, axis=0)


# --- Main Streamlit App ---
def main():
    """Defines the Streamlit application structure and logic."""
    st.set_page_config(layout="wide", page_title="Molecule Visualizer")
    st.title("🧪 Interactive Molecule Visualizer (Streamlit + Plotly)")

    # --- Initialize Session State ---
    st.session_state.setdefault("molecule_data", None)
    st.session_state.setdefault("input_processed", False)
    st.session_state.setdefault("input_source_key", None)
    st.session_state.setdefault("selected_mol_names", [])
    st.session_state.setdefault("prev_selected_mol_names", [])
    st.session_state.setdefault("download_content", None)
    st.session_state.setdefault("show_download", False)
    st.session_state.setdefault("current_style", DEFAULT_REPRESENTATION)
    st.session_state.setdefault("global_offset", np.zeros(3))
    st.session_state.setdefault("slider_trans_x", 0.0)
    st.session_state.setdefault("slider_trans_y", 0.0)
    st.session_state.setdefault("slider_trans_z", 0.0)
    st.session_state.setdefault("slider_rot_x", 0.0)
    st.session_state.setdefault("slider_rot_y", 0.0)
    st.session_state.setdefault("slider_rot_z", 0.0)
    st.session_state.setdefault("target_centroid_x", 0.0)
    st.session_state.setdefault("target_centroid_y", 0.0)
    st.session_state.setdefault("target_centroid_z", 0.0)
    # Ensure molecule_transforms exists if molecule_data does (needed after state loss/reload)
    if st.session_state.molecule_data and (
        "molecule_transforms" not in st.session_state
        or len(st.session_state.molecule_transforms)
        != len(st.session_state.molecule_data)
        or any(
            m.id not in st.session_state.molecule_transforms
            for m in st.session_state.molecule_data
        )
    ):
        st.session_state.molecule_transforms = {
            mol.id: {
                "translation": mol.final_translation,
                "rotation": mol.final_rotation_matrix,
            }
            for mol in st.session_state.molecule_data
        }
        print("DEBUG: Reinitialized molecule_transforms from Molecule objects")

    # --- Input Handling ---
    st.sidebar.header("1. Load Molecule Data")
    input_option = st.sidebar.radio(
        "Input method:",
        ("Upload XYZ File(s)", "Paste XYZ Content", "Load Default"),
        key="input_option",
    )
    current_input_key = None
    files_to_process: List[Tuple[str, str]] = []
    input_changed = False
    load_default = False
    pasted_content_to_process: Optional[str] = None  # Store pasted text if new

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
    elif input_option == "Paste XYZ Content":
        pasted_text = st.sidebar.text_area(
            "Paste one or more XYZ blocks here", height=200, key="paste_area"
        )
        if pasted_text:
            current_input_key = hash(pasted_text)
            if st.session_state.input_source_key != current_input_key:
                st.session_state.input_source_key = current_input_key
                st.session_state.input_processed = False
                input_changed = True
                pasted_content_to_process = (
                    pasted_text  # Flag content for processing below
                )
        else:
            if st.session_state.input_source_key and isinstance(
                st.session_state.input_source_key, int
            ):
                st.session_state.input_source_key = None
                st.session_state.input_processed = False
                st.session_state.molecule_data = None
                input_changed = True
    elif input_option == "Load Default":
        current_input_key = "default_benzene"
        if st.session_state.input_source_key != current_input_key:
            st.session_state.input_source_key = current_input_key
            st.session_state.input_processed = False
            input_changed = True
            load_default = True

    # --- Data Processing Step ---
    if input_changed and (
        files_to_process or load_default or pasted_content_to_process
    ):
        st.session_state.molecule_data = None
        all_molecules = []
        global_mol_index = 0
        valid_data_found = False

        if load_default:
            with st.spinner("Generating default system..."):
                try:
                    all_symbols, all_coords, boundaries = core_io.create_two_benzenes()
                    source_name = "Benzene"
                    for file_idx, (start, end) in enumerate(boundaries):
                        symbols = all_symbols[start:end]
                        coords = all_coords[start:end]
                        if len(symbols) > 0:
                            bonds = logic.determine_bonds(symbols, coords)
                            mol_name = f"{source_name}_{file_idx+1}"
                            molecule = Molecule(
                                id=global_mol_index,
                                name=mol_name,
                                symbols=symbols,
                                coords=coords,
                                bonds=bonds,
                                source_file_index=file_idx,
                                source_file_name="Default",
                            )
                            all_molecules.append(molecule)
                            global_mol_index += 1
                            valid_data_found = True
                except Exception as e:
                    st.error(f"Error generating default data: {e}")
        elif files_to_process:  # Process uploaded files
            with st.spinner(f"Processing {len(files_to_process)} file(s)..."):
                for file_idx, (file_name, file_content) in enumerate(files_to_process):
                    symbols, coords = core_io.load_xyz_from_text(
                        file_content, source_name=file_name
                    )  # Use text loader
                    if symbols is not None and coords is not None and len(symbols) > 0:
                        bonds = logic.determine_bonds(symbols, coords)
                        base_name = (
                            file_name if len(files_to_process) > 1 else "Molecule"
                        )
                        mol_name = f"{base_name}"
                        molecule = Molecule(
                            id=global_mol_index,
                            name=mol_name,
                            symbols=symbols,
                            coords=coords,
                            bonds=bonds,
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
        elif pasted_content_to_process:  # Process pasted text
            with st.spinner("Processing pasted content..."):
                # Use multi-block parser
                parsed_data_list = core_io.load_multiple_xyz_from_text(
                    pasted_content_to_process, source_name="Pasted"
                )
                if not parsed_data_list:
                    st.warning("Could not parse any valid XYZ blocks from pasted text.")
                else:
                    print(f"Parsed {len(parsed_data_list)} block(s) from pasted text.")
                    for mol_idx, (symbols, coords) in enumerate(parsed_data_list):
                        if symbols and coords is not None and len(symbols) > 0:
                            print(
                                f"  Processing pasted block {mol_idx+1} ({len(symbols)} atoms)..."
                            )
                            bonds = logic.determine_bonds(symbols, coords)
                            mol_name = f"Pasted_{mol_idx+1}"
                            molecule = Molecule(
                                id=global_mol_index,
                                name=mol_name,
                                symbols=symbols,
                                coords=coords,
                                bonds=bonds,
                                source_file_index=-(mol_idx + 1),
                                source_file_name="Pasted Text",
                            )
                            all_molecules.append(molecule)
                            global_mol_index += 1
                            valid_data_found = True
                        else:
                            print(f"  Skipping empty block {mol_idx+1} from parser.")

        # --- Post Processing State Update ---
        if valid_data_found:
            st.session_state.molecule_data = all_molecules
            st.session_state.input_processed = True
            st.session_state.molecule_transforms = {
                mol.id: {"translation": np.zeros(3), "rotation": np.identity(3)}
                for mol in all_molecules
            }
            st.session_state.selected_mol_names = [m.name for m in all_molecules][:1]
            st.session_state.prev_selected_mol_names = copy.deepcopy(
                st.session_state.selected_mol_names
            )
            st.session_state.global_offset = np.zeros(3)
            st.session_state.slider_trans_x = 0.0
            st.session_state.slider_trans_y = 0.0
            st.session_state.slider_trans_z = 0.0
            st.session_state.slider_rot_x = 0.0
            st.session_state.slider_rot_y = 0.0
            st.session_state.slider_rot_z = 0.0
            st.session_state.target_centroid_x = 0.0
            st.session_state.target_centroid_y = 0.0
            st.session_state.target_centroid_z = 0.0
            st.sidebar.success(f"{len(all_molecules)} molecule(s) processed.")
            st.rerun()
        elif input_changed:  # Only show error if input actually changed and failed
            st.error("Failed to load any valid molecules from the provided input(s).")
            st.session_state.molecule_data = None
            st.session_state.input_processed = False

    # --- Display Area ---
    if not st.session_state.get("molecule_data"):
        st.info(
            "⬅️ Please upload XYZ file(s), paste content, or load default in the sidebar."
        )
        st.subheader("XYZ Format:")
        st.code(
            """[Number of Atoms]\n[Comment Line]\n[Element] [X] [Y] [Z]\n...""",
            language="text",
        )
        st.stop()

    # Data is ready
    molecules: List[Molecule] = st.session_state.molecule_data
    if (
        "molecule_transforms" not in st.session_state
        or len(st.session_state.molecule_transforms) != len(molecules)
        or any(m.id not in st.session_state.molecule_transforms for m in molecules)
    ):
        st.session_state.molecule_transforms = {
            mol.id: {
                "translation": mol.final_translation,
                "rotation": mol.final_rotation_matrix,
            }
            for mol in molecules
        }
        print("DEBUG: Reinitialized molecule_transforms")
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

    # --- Slider Sync Logic ---
    rerun_for_sync = False
    if set(selected_mol_names) != set(st.session_state.prev_selected_mol_names):
        print(f"Selection changed: {selected_mol_names}")
        if len(selected_mol_names) == 1:
            selected_id = mol_name_to_id_map.get(selected_mol_names[0])
            selected_mol_state = st.session_state.molecule_transforms.get(selected_id)
            if selected_mol_state:
                print(f"  Syncing sliders to '{selected_mol_names[0]}'")
                st.session_state.slider_trans_x = selected_mol_state["translation"][0]
                st.session_state.slider_trans_y = selected_mol_state["translation"][1]
                st.session_state.slider_trans_z = selected_mol_state["translation"][2]
                st.session_state.slider_rot_x = 0.0
                st.session_state.slider_rot_y = 0.0
                st.session_state.slider_rot_z = 0.0
            else:
                print(
                    "  Warning: Selected molecule state not found for sync. Resetting sliders."
                )
                st.session_state.slider_trans_x = 0.0
                st.session_state.slider_trans_y = 0.0
                st.session_state.slider_trans_z = 0.0
                st.session_state.slider_rot_x = 0.0
                st.session_state.slider_rot_y = 0.0
                st.session_state.slider_rot_z = 0.0
        else:
            print(f"  Selection count is {len(selected_mol_names)}. Resetting sliders.")
            st.session_state.slider_trans_x = 0.0
            st.session_state.slider_trans_y = 0.0
            st.session_state.slider_trans_z = 0.0
            st.session_state.slider_rot_x = 0.0
            st.session_state.slider_rot_y = 0.0
            st.session_state.slider_rot_z = 0.0
        st.session_state.prev_selected_mol_names = copy.deepcopy(selected_mol_names)
        rerun_for_sync = True

    # Draw Sliders
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
    st.session_state.slider_trans_x = trans_x
    st.session_state.slider_trans_y = trans_y
    st.session_state.slider_trans_z = trans_z
    st.session_state.slider_rot_x = rot_x
    st.session_state.slider_rot_y = rot_y
    st.session_state.slider_rot_z = rot_z

    # --- Centroid and Reset Buttons/Logic ---
    st.sidebar.header("4. Centering & Reset")
    col1, col2 = st.sidebar.columns(2)
    center_selected_pressed = col1.button(
        "Center Selected", key="center_sel", use_container_width=True
    )
    reset_pressed = col2.button(
        "Reset View", key="reset_view", use_container_width=True
    )
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
    st.session_state.target_centroid_x = target_x
    st.session_state.target_centroid_y = target_y
    st.session_state.target_centroid_z = target_z
    center_target_pressed = st.sidebar.button(
        "Move to Target", key="center_sys_t", use_container_width=True
    )

    # --- Apply Button Actions (State Modifications) ---
    rerun_after_action = False
    if reset_pressed:
        print("Reset View button pressed")
        st.session_state.global_offset = np.zeros(3)
        if "molecule_transforms" in st.session_state:
            for mol_id in st.session_state.molecule_transforms:
                st.session_state.molecule_transforms[mol_id] = {
                    "translation": np.zeros(3),
                    "rotation": np.identity(3),
                }
        for mol in molecules:
            mol.reset_transformation()
        st.session_state.slider_trans_x = 0.0
        st.session_state.slider_trans_y = 0.0
        st.session_state.slider_trans_z = 0.0
        st.session_state.slider_rot_x = 0.0
        st.session_state.slider_rot_y = 0.0
        st.session_state.slider_rot_z = 0.0
        st.session_state.target_centroid_x = 0.0
        st.session_state.target_centroid_y = 0.0
        st.session_state.target_centroid_z = 0.0
        st.session_state.selected_mol_names = [molecules[0].name] if molecules else []
        st.session_state.prev_selected_mol_names = copy.deepcopy(
            st.session_state.selected_mol_names
        )
        rerun_after_action = True
    if center_selected_pressed:
        print("Center Selected button pressed")
        selected_ids = [
            mol_name_to_id_map[name]
            for name in selected_mol_names
            if name in mol_name_to_id_map
        ]
        if not selected_ids:
            st.warning("No molecules selected to center.")
        else:
            for mol_id in selected_ids:
                molecule = next((m for m in molecules if m.id == mol_id), None)
                mol_transform_state = st.session_state.molecule_transforms.get(mol_id)
                if molecule and mol_transform_state:
                    molecule.apply_final_transformation()  # Ensure coords are current before calc
                    if molecule.transformed_coords.size > 0:
                        mol_centroid = np.mean(molecule.transformed_coords, axis=0)
                        offset = -mol_centroid
                        mol_transform_state["translation"] += offset
                        molecule.final_translation = mol_transform_state["translation"]
                        molecule.apply_final_transformation()  # Update coords
            if len(selected_ids) == 1:  # Sync sliders if only one was centered
                transform_state = st.session_state.molecule_transforms.get(
                    selected_ids[0]
                )
                if transform_state:
                    st.session_state.slider_trans_x = transform_state["translation"][0]
                    st.session_state.slider_trans_y = transform_state["translation"][1]
                    st.session_state.slider_trans_z = transform_state["translation"][2]
                    st.session_state.slider_rot_x = 0.0
                    st.session_state.slider_rot_y = 0.0
                    st.session_state.slider_rot_z = 0.0
            rerun_after_action = True
    if center_origin_pressed:
        print("Center System Origin button pressed")
        current_centroid = calculate_overall_centroid(
            molecules, st.session_state.global_offset
        )
        if current_centroid is not None:
            st.session_state.global_offset += -current_centroid
            rerun_after_action = True
        else:
            st.warning("Cannot calculate system centroid.")
    if center_target_pressed:
        print("Center System Target button pressed")
        target_centroid = np.array([target_x, target_y, target_z])
        current_centroid = calculate_overall_centroid(
            molecules, st.session_state.global_offset
        )
        if current_centroid is not None:
            st.session_state.global_offset += target_centroid - current_centroid
            rerun_after_action = True
        else:
            st.warning("Cannot calculate system centroid.")

    # --- Apply Slider Transformations ---
    selected_ids_tf = [
        mol_name_to_id_map[name]
        for name in selected_mol_names
        if name in mol_name_to_id_map
    ]
    current_trans_vector = np.array([trans_x, trans_y, trans_z])
    current_rot_matrix = geometry.build_rotation_matrix(rot_x, rot_y, rot_z)
    if selected_ids_tf:
        for mol_id in selected_ids_tf:
            if mol_id in st.session_state.molecule_transforms:
                st.session_state.molecule_transforms[mol_id][
                    "translation"
                ] = current_trans_vector
                st.session_state.molecule_transforms[mol_id][
                    "rotation"
                ] = current_rot_matrix
                molecule = next((m for m in molecules if m.id == mol_id), None)
                if molecule:
                    molecule.final_translation = current_trans_vector
                    molecule.final_rotation_matrix = current_rot_matrix
                    molecule.apply_final_transformation()

    # --- Plotting ---
    st.header("Molecule View (Interactive)")
    st.caption("Click and drag to rotate, scroll to zoom, right-click drag to pan.")
    try:
        for m in molecules:
            m.apply_final_transformation()  # Ensure coords are up-to-date
        plotly_fig = plot_molecules_plotly(
            molecules,
            st.session_state.molecule_transforms,
            current_style,
            st.session_state.global_offset,
        )
        st.plotly_chart(plotly_fig, use_container_width=True)
    except Exception as e:
        st.error(f"An error occurred during plotting: {e}")

    # --- Save Functionality ---
    st.sidebar.header("5. Export")
    if st.sidebar.button("Prepare Combined Adjusted XYZ"):
        st.session_state.download_content = None
        st.session_state.show_download = False
        symbols_combined = []
        coords_to_save_list = []
        if st.session_state.molecule_data:
            for molecule in st.session_state.molecule_data:
                molecule.apply_final_transformation()
                coords_to_save = (
                    molecule.transformed_coords + st.session_state.global_offset
                )
                symbols_combined.extend(molecule.symbols)
                coords_to_save_list.append(coords_to_save)
        if not coords_to_save_list:
            st.sidebar.warning("No molecule data to save.")
        else:
            coords_combined_np = np.vstack(coords_to_save_list)
            total_atoms = len(symbols_combined)
            xyz_content = core_io.format_xyz_string(
                symbols_combined,
                coords_combined_np,
                comment=f"Combined adjusted structure (Global Offset: {st.session_state.global_offset})",
            )
            st.session_state.download_content = xyz_content
            st.session_state.show_download = True
            rerun_after_action = True
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

    # --- Final Rerun Trigger ---
    if rerun_for_sync or rerun_after_action:
        st.rerun()


# Call main directly
if __name__ == "__main__":
    main()

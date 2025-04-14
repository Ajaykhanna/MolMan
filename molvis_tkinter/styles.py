"""
molvis_tkinter/styles.py

Defines and configures ttk styles for the Tkinter Molecule Visualizer.
"""

import tkinter as tk
from tkinter import ttk
import sys  # For printing warnings

# --- Define Styling Constants Locally ---
BG_COLOR_FRAME = "#F0F0F0"
BG_COLOR_LBLFRAME = "#ECECEC"
BG_COLOR_BTN = "#D5D5D5"
BG_COLOR_BTN_ACTIVE = "#C0C0C0"
FG_COLOR_LABEL = "#333333"
FONT_DEFAULT = ("Arial", 9)
FONT_BOLD = ("Arial", 10, "bold")

# --- Removed incorrect import from molvis_core.constants ---


def setup_styles(root: tk.Tk):
    """
    Configures ttk styles for the application widgets using locally defined constants.

    Args:
        root: The root Tkinter window (needed to initialize ttk.Style).
    """
    style = ttk.Style(root)
    available_themes = style.theme_names()
    if "clam" in available_themes:
        style.theme_use("clam")
    elif "alt" in available_themes:
        style.theme_use("alt")

    # --- Configure Widget Styles (Uses constants defined above) ---
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
            ("hover", BG_COLOR_BTN_ACTIVE),
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
        padding=(0, 0, 0, 2),
    )
    style.configure(
        "TCheckbutton",
        background=BG_COLOR_LBLFRAME,
        foreground=FG_COLOR_LABEL,
        font=FONT_DEFAULT,
        padding=(5, 3),
    )
    style.map("TCheckbutton", background=[("active", BG_COLOR_LBLFRAME)])
    style.configure(
        "TCombobox",
        padding=3,
        fieldbackground="white",
        background=BG_COLOR_BTN,
        arrowcolor="black",
        selectbackground="#B0D7FF",
        selectforeground="black",
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", "white")],
        selectbackground=[("readonly", "#B0D7FF")],
        selectforeground=[("readonly", "black")],
    )
    style.configure(
        "TLabel",
        background=BG_COLOR_LBLFRAME,
        foreground=FG_COLOR_LABEL,
        font=FONT_DEFAULT,
        padding=2,
    )
    style.configure("Bold.TLabel", font=FONT_BOLD, background=BG_COLOR_LBLFRAME)
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
    style.configure(
        "TEntry", padding=3, fieldbackground="white", borderwidth=1, relief="sunken"
    )
    style.configure(
        "Vertical.TScrollbar",
        background=BG_COLOR_BTN,
        troughcolor=BG_COLOR_FRAME,
        borderwidth=1,
        arrowcolor="black",
    )
    style.map("Vertical.TScrollbar", background=[("active", BG_COLOR_BTN_ACTIVE)])
    print("ttk styles configured.")

"""
This is the main entry point of the application.
It creates the Tkinter window and starts the PuzzleGUI.
"""


from __future__ import annotations

import tkinter as tk

from .gui import PuzzleGUI


def run_app() -> None:
    """Create the main window and start the Tkinter event loop."""
    root = tk.Tk()
    root.withdraw()
    # to centre the window roughly
    root.geometry("1000x700")
    PuzzleGUI(root)
    root.update_idletasks()

    w = root.winfo_width()
    h = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    root.geometry(f"{w}x{h}+{x}+{y}")
    root.deiconify()
    root.lift()
    root.update_idletasks()
    root.mainloop()

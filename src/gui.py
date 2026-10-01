"""
Tkinter interface for the Image Tile Puzzle. Handles the window layout, user actions, image display and button events.
"""


from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageTk

from .puzzle import PuzzleGame, MAX_HINTS


class PuzzleGUI:
    """
    Main window of the application.
    Works with PuzzleGame for the game logic while handling
    the interface, user actions and screen updates.
    """

    def __init__(self, root: tk.Tk) -> None:
        self._root = root
        self._root.title("HIT137 — Image Tile Puzzle")
        self._root.minsize(900, 620)
        self._root.configure(bg="#f0f0f0")

        self._game = PuzzleGame()

        # Keep PhotoImage references to prevent garbage collection
        self._photo_original: Optional[ImageTk.PhotoImage] = None
        self._photo_puzzle: Optional[ImageTk.PhotoImage] = None

        # Canvas sizes (updated after image load)
        self._display_size: int = 480

        self._build_ui()
        self._update_status("Load an image to begin.")

    # ------------------------------------------------------------------
    # UI code
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # Title
        title = tk.Label(
            self._root,
            text="IMAGE TILE PUZZLE",
            font=("Helvetica", 18, "bold"),
            bg="#f0f0f0",
            fg="#222",
        )
        title.pack(pady=(12, 6))

        # Control bar
        ctrl = tk.Frame(self._root, bg="#f0f0f0")
        ctrl.pack(fill=tk.X, padx=16, pady=4)

        tk.Label(
            ctrl,
            text="Grid Size:",
            bg="#f0f0f0",
            fg="#222",
            font=("Helvetica", 11),
        ).pack(side=tk.LEFT, padx=(0, 4))
        self._grid_var = tk.StringVar(value="3 x 3")
        self._grid_combo = ttk.Combobox(
            ctrl,
            textvariable=self._grid_var,
            values=["3 x 3", "4 x 4", "5 x 5"],
            state="readonly",
            width=8,
        )
        self._grid_combo.pack(side=tk.LEFT, padx=(0, 12))

        self._load_btn = ttk.Button(ctrl, text="Load Image", command=self._on_load)
        self._load_btn.pack(side=tk.LEFT, padx=(0, 8))

        self._rotate_btn = ttk.Button(
            ctrl,
            text="Rotate",
            command=self._on_rotate_selected,
            state=tk.DISABLED,
        )
        self._rotate_btn.pack(side=tk.LEFT, padx=(0, 8))

        self._flip_btn = ttk.Button(
            ctrl,
            text="Flip",
            command=self._on_flip_selected,
            state=tk.DISABLED,
        )
        self._flip_btn.pack(side=tk.LEFT, padx=(0, 8))

        self._hint_btn = ttk.Button(
            ctrl, text="Hint", command=self._on_hint, state=tk.DISABLED
        )
        self._hint_btn.pack(side=tk.LEFT, padx=(0, 8))

        self._solve_btn = ttk.Button(
            ctrl, text="Solve", command=self._on_solve, state=tk.DISABLED
        )
        self._solve_btn.pack(side=tk.LEFT)

        self._reset_btn = ttk.Button(
            ctrl, text="Reset", command=self._on_reset, state=tk.DISABLED
        )
        self._reset_btn.pack(side=tk.LEFT, padx=(8, 0))

        # Image area
        img_frame = tk.Frame(self._root, bg="#f0f0f0")
        img_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)

        # Original (left)
        left = tk.Frame(img_frame, bg="#f0f0f0")
        left.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=(0, 8))
        tk.Label(
            left,
            text="Original (reference)",
            font=("Helvetica", 10),
            bg="#f0f0f0",
            fg="#222",
        ).pack()
        self._canvas_original = tk.Canvas(
            left,
            width=self._display_size,
            height=self._display_size,
            bg="#ddd",
            highlightthickness=1,
            highlightbackground="#999",
        )
        self._canvas_original.pack(pady=4)
        self._draw_empty_canvas(
            self._canvas_original, "Original image", "Load an image to get started"
        )

        # Puzzle (right)
        right = tk.Frame(img_frame, bg="#f0f0f0")
        right.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=(8, 0))
        tk.Label(
            right,
            text="Puzzle (select two to swap; select one to rotate or flip)",
            font=("Helvetica", 10),
            bg="#f0f0f0",
            fg="#222",
        ).pack()
        self._canvas_puzzle = tk.Canvas(
            right,
            width=self._display_size,
            height=self._display_size,
            bg="#ddd",
            highlightthickness=1,
            highlightbackground="#999",
            cursor="hand2",
        )
        self._canvas_puzzle.pack(pady=4)
        self._draw_empty_canvas(
            self._canvas_puzzle, "Puzzle board", "Choose Load Image above"
        )

        #  mouse events on the puzzle canvas
        self._canvas_puzzle.bind("<Button-1>", self._on_left_click)
        self._canvas_puzzle.bind("<Button-2>", self._on_right_click)
        self._canvas_puzzle.bind("<Button-3>", self._on_right_click)
        # Shift + left click
        self._canvas_puzzle.bind("<Shift-Button-1>", self._on_shift_left_click)
        # Stats bar
        stats = tk.Frame(self._root, bg="#e8e8e8", relief=tk.GROOVE, bd=1)
        stats.pack(fill=tk.X, padx=16, pady=4)

        self._moves_label = tk.Label(
            stats, text="Moves: 0", font=("Helvetica", 11), bg="#e8e8e8", fg="#222"
        )
        self._moves_label.pack(side=tk.LEFT, padx=12, pady=6)

        self._incorrect_label = tk.Label(
            stats,
            text="Incorrect Tiles: 0",
            font=("Helvetica", 11),
            bg="#e8e8e8",
            fg="#222",
        )
        self._incorrect_label.pack(side=tk.LEFT, padx=12, pady=6)

        self._hints_label = tk.Label(
            stats,
            text=f"Hints Used: 0 / {MAX_HINTS}",
            font=("Helvetica", 11),
            bg="#e8e8e8",
            fg="#222",
        )
        self._hints_label.pack(side=tk.LEFT, padx=12, pady=6)

        # Status bar
        self._status_label = tk.Label(
            self._root,
            text="",
            font=("Helvetica", 10),
            bg="#f0f0f0",
            fg="#333",
            anchor="w",
        )
        self._status_label.pack(fill=tk.X, padx=16, pady=(0, 10))

    # ------------------------------------------------------------------
    # Helpers functions
    # ------------------------------------------------------------------

    def _draw_empty_canvas(
        self, canvas: tk.Canvas, heading: str, instruction: str
    ) -> None:
        center = self._display_size // 2
        canvas.create_text(
            center,
            center - 12,
            text=heading,
            fill="#444",
            font=("Helvetica", 16, "bold"),
        )
        canvas.create_text(
            center,
            center + 18,
            text=instruction,
            fill="#666",
            font=("Helvetica", 11),
        )

    def _grid_size_from_combo(self) -> int:
        text = self._grid_var.get()
        return int(text.split("x")[0].strip())

    def _cv_to_photo(self, bgr: np.ndarray) -> ImageTk.PhotoImage:
        """Convert an OpenCV BGR image to a Tkinter-compatible PhotoImage."""
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb)
        return ImageTk.PhotoImage(pil)

    def _update_status(self, msg: str) -> None:
        self._status_label.config(text=f"Status: {msg}")

    def _update_stats(self) -> None:
        self._moves_label.config(text=f"Moves: {self._game.moves}")
        incorrect = self._game.count_incorrect() if self._game.has_image else 0
        self._incorrect_label.config(text=f"Incorrect Tiles: {incorrect}")
        self._hints_label.config(
            text=f"Hints Used: {self._game.hints_used} / {MAX_HINTS}"
        )

    def _set_interaction_enabled(self, enabled: bool) -> None:
        state = tk.NORMAL if enabled else tk.DISABLED
        self._hint_btn.config(state=state)
        self._solve_btn.config(state=state)
        self._flip_btn.config(state=state)
        self._rotate_btn.config(state=state)
        self._reset_btn.config(state=state)
        if enabled and self._game.hints_used >= MAX_HINTS:
            self._hint_btn.config(state=tk.DISABLED)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _refresh_display(self) -> None:
        """Redraw both canvases from current game state."""
        if not self._game.has_image:
            return

        # --- Original image ---
        orig = self._game.original_display
        if orig is not None:
            # Draw hint circle on original if active
            display_orig = orig.copy()
            if self._game.hint_active and self._game.hint_home_pos is not None:
                display_orig = self._draw_hint_circle(
                    display_orig, self._game.hint_home_pos
                )
            # Resize canvas to match image
            h, w = display_orig.shape[:2]
            self._canvas_original.config(width=w, height=h)
            self._photo_original = self._cv_to_photo(display_orig)
            self._canvas_original.delete("all")
            self._canvas_original.create_image(
                0, 0, anchor=tk.NW, image=self._photo_original
            )

        # --- Puzzle image ---
        puzzle_img = self._game.get_puzzle_image(with_grid=True)
        if puzzle_img is not None:
            display_puz = puzzle_img.copy()

            # Green ticks for correct tiles
            for idx in self._game.get_correct_indices():
                display_puz = self._draw_green_tick(display_puz, idx)

            # Selection border
            if self._game.selected_index is not None:
                display_puz = self._draw_selection_border(
                    display_puz, self._game.selected_index
                )

            # Hint circle on puzzle
            if self._game.hint_active and self._game.hint_puzzle_pos is not None:
                display_puz = self._draw_hint_circle(
                    display_puz, self._game.hint_puzzle_pos
                )

            h, w = display_puz.shape[:2]
            self._canvas_puzzle.config(width=w, height=h)
            self._photo_puzzle = self._cv_to_photo(display_puz)
            self._canvas_puzzle.delete("all")
            self._canvas_puzzle.create_image(
                0, 0, anchor=tk.NW, image=self._photo_puzzle
            )

        self._update_stats()

        if self._game.is_solved:
            self._set_interaction_enabled(False)
            self._update_status(
                f"Congratulations! Puzzle solved in {self._game.moves} moves. "
                "Load another image to continue."
            )
        else:
            self._set_interaction_enabled(True)

    def _tile_rect(
        self, image: np.ndarray, current_index: int
    ) -> Tuple[int, int, int, int]:
        """Return (x0, y0, x1, y1) for a tile given its current_index."""
        grid = self._game.grid_size
        h, w = image.shape[:2]
        th = h // grid
        tw = w // grid
        r = current_index // grid
        c = current_index % grid
        return c * tw, r * th, (c + 1) * tw, (r + 1) * th

    def _draw_selection_border(
        self, image: np.ndarray, current_index: int
    ) -> np.ndarray:
        x0, y0, x1, y1 = self._tile_rect(image, current_index)
        result = image.copy()
        cv2.rectangle(result, (x0 + 2, y0 + 2), (x1 - 3, y1 - 3), (0, 0, 255), 3)
        return result

    def _draw_green_tick(
        self, image: np.ndarray, current_index: int
    ) -> np.ndarray:
        x0, y0, x1, y1 = self._tile_rect(image, current_index)
        result = image.copy()
        # Small green check-mark in the top-right corner of the tile
        margin = max(4, (x1 - x0) // 10)
        cx = x1 - margin - 8
        cy = y0 + margin + 8
        # Simple tick: two lines
        cv2.line(result, (cx - 6, cy), (cx - 2, cy + 5), (0, 200, 0), 2, cv2.LINE_AA)
        cv2.line(result, (cx - 2, cy + 5), (cx + 7, cy - 6), (0, 200, 0), 2, cv2.LINE_AA)
        return result

    def _draw_hint_circle(
        self, image: np.ndarray, current_index: int
    ) -> np.ndarray:
        x0, y0, x1, y1 = self._tile_rect(image, current_index)
        result = image.copy()
        cx = (x0 + x1) // 2
        cy = (y0 + y1) // 2
        radius = max(10, min(x1 - x0, y1 - y0) // 3)
        cv2.circle(result, (cx, cy), radius, (255, 100, 0), 3, cv2.LINE_AA)  # blue-ish BGR
        return result

    # Event handlers

    def _on_load(self) -> None:
        path = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.JPG *.JPEG *.PNG *.BMP"),
                ("JPEG", "*.jpg *.jpeg *.JPG *.JPEG"),
                ("PNG", "*.png *.PNG"),
                ("BMP", "*.bmp *.BMP"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return

        try:
            grid = self._grid_size_from_combo()
            self._game.create_puzzle(path, grid)
            self._refresh_display()
            self._update_status(
                f"Image loaded. Grid {grid}×{grid}. "
                f"{self._game.count_incorrect()} tiles incorrect. Good luck!"
            )
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to load image:\n{exc}")
            self._update_status("Failed to load image.")

    def _on_left_click(self, event: tk.Event) -> None:
        if self._game.is_solved or not self._game.has_image:
            return
        # Shift is handled by a separate binding; ignore if shift is held
        if event.state & 0x0001:  # Shift mask
            return
        idx = self._game.get_tile_at_pixel(event.x, event.y)
        if idx is None:
            return
        msg = self._game.select_or_swap(idx)
        self._refresh_display()
        if not self._game.is_solved:
            self._update_status(msg)

    def _on_right_click(self, event: tk.Event) -> None:
        if self._game.is_solved or not self._game.has_image:
            return
        idx = self._game.get_tile_at_pixel(event.x, event.y)
        if idx is None:
            return
        msg = self._game.rotate_tile(idx)
        self._refresh_display()
        if not self._game.is_solved:
            self._update_status(msg)

    def _on_rotate_selected(self) -> None:
        if self._game.is_solved or not self._game.has_image:
            return
        if self._game.selected_index is None:
            self._update_status("Select a tile on the puzzle, then click Rotate.")
            return
        msg = self._game.rotate_tile(self._game.selected_index)
        self._refresh_display()
        if not self._game.is_solved:
            self._update_status(msg)

    def _on_flip_selected(self) -> None:
        if self._game.is_solved or not self._game.has_image:
            return
        if self._game.selected_index is None:
            self._update_status("Select a tile on the puzzle, then click Flip.")
            return
        msg = self._game.flip_tile_horizontal(self._game.selected_index)
        self._refresh_display()
        if not self._game.is_solved:
            self._update_status(msg)

    def _on_shift_left_click(self, event: tk.Event) -> None:
        if self._game.is_solved or not self._game.has_image:
            return
        idx = self._game.get_tile_at_pixel(event.x, event.y)
        if idx is None:
            return
        msg = self._game.flip_tile_horizontal(idx)
        self._refresh_display()
        if not self._game.is_solved:
            self._update_status(msg)

    def _on_hint(self) -> None:
        msg = self._game.use_hint()
        self._refresh_display()
        self._update_status(msg)
        if self._game.hints_used >= MAX_HINTS:
            self._hint_btn.config(state=tk.DISABLED)

    def _on_solve(self) -> None:
        if not self._game.has_image:
            return
        if not messagebox.askyesno("Solve", "Automatically solve the puzzle?"):
            return
        msg = self._game.solve()
        self._refresh_display()
        self._update_status(msg)

    def _on_reset(self) -> None:
        msg = self._game.restart()
        self._refresh_display()
        self._update_status(msg)

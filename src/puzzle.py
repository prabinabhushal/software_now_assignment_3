"""
Puzzle game logic for managing tile positions, transformations, move tracking, hints, and solving.
"""

from __future__ import annotations

import random
from typing import List, Optional, Tuple

import numpy as np

from .image_processor import ImageProcessor
from .tile import PuzzleTile
from .transformations import (
    SwapTransformation,
    Transformation,
    create_random_transformations,
)


# Number of transformations scales with grid size
TRANSFORM_COUNTS = {
    3: 6,
    4: 12,
    5: 20,
}

MAX_HINTS = 3


class PuzzleGame:
    """
    Central game controller.
    """

    def __init__(self) -> None:
        """Initialise an empty puzzle game."""
        self._processor = ImageProcessor()
        self._tiles: List[PuzzleTile] = []
        self._initial_tiles: List[PuzzleTile] = []
        self._grid_size: int = 3
        self._moves: int = 0
        self._hints_used: int = 0
        self._selected_index: Optional[int] = None  # current_index of selected tile
        self._solved: bool = False
        self._original_display: Optional[np.ndarray] = None
        self._hint_puzzle_pos: Optional[int] = None  # current_index of hinted tile
        self._hint_home_pos: Optional[int] = None    # original_index of hinted tile
        self._hint_active: bool = False

    # Properties

    @property
    def grid_size(self) -> int:
        return self._grid_size

    @property
    def moves(self) -> int:
        return self._moves

    @property
    def hints_used(self) -> int:
        return self._hints_used

    @property
    def max_hints(self) -> int:
        return MAX_HINTS

    @property
    def selected_index(self) -> Optional[int]:
        return self._selected_index

    @property
    def is_solved(self) -> bool:
        return self._solved

    @property
    def has_image(self) -> bool:
        return len(self._tiles) > 0

    @property
    def original_display(self) -> Optional[np.ndarray]:
        return None if self._original_display is None else self._original_display.copy()

    @property
    def hint_active(self) -> bool:
        return self._hint_active

    @property
    def hint_puzzle_pos(self) -> Optional[int]:
        return self._hint_puzzle_pos

    @property
    def hint_home_pos(self) -> Optional[int]:
        return self._hint_home_pos

    # fn for puzzle creation

    def create_puzzle(self, image_path: str, grid_size: int) -> None:
        """
        Load an image, prepare it, split into tiles and apply
        a full set of random transformations.
        """
        if grid_size not in TRANSFORM_COUNTS:
            raise ValueError(f"Unsupported grid size: {grid_size}")

        self.reset()
        self._grid_size = grid_size

        raw = self._processor.load_image(image_path)
        prepared = self._processor.prepare_image(raw, grid_size)
        self._original_display = prepared.copy()
        self._tiles = self._processor.split_into_tiles(prepared, grid_size)

        # Apply all transformations at once
        count = TRANSFORM_COUNTS[grid_size]
        transformations = create_random_transformations(count)
        for t in transformations:
            t.apply(self._tiles, grid_size)

        if all(tile.is_correct() for tile in self._tiles):
            SwapTransformation().apply(self._tiles, grid_size)

        # After swaps the list order still matches current_index because
        # SwapTransformation also swaps list elements.  Re-sync just in case.
        self._sync_list_to_positions()
        self._initial_tiles = [tile.clone() for tile in self._tiles]

        self._moves = 0
        self._hints_used = 0
        self._selected_index = None
        self._solved = False
        self._clear_hint()

    def _sync_list_to_positions(self) -> None:
        """Ensure list index equals each tile's current_index."""
        ordered = sorted(self._tiles, key=lambda t: t.current_index)
        # Fix any duplicate current_index that might have arisen
        for i, tile in enumerate(ordered):
            tile.current_index = i
        self._tiles = ordered

    # Image helpers for GUI

    def get_puzzle_image(self, with_grid: bool = True) -> Optional[np.ndarray]:
        """Return the reassembled puzzle image (optionally with grid)."""
        if not self._tiles:
            return None
        img = self._processor.reassemble_tiles(self._tiles, self._grid_size)
        if with_grid:
            img = self._processor.draw_grid(img, self._grid_size)
        return img

    def get_tile_at_pixel(self, x: int, y: int) -> Optional[int]:
        """
        Convert pixel coordinates on the puzzle image to a current_index.
        Returns None if out of bounds.
        """
        if not self._tiles:
            return None
        tile_size = self._processor.tile_size
        if tile_size <= 0:
            return None
        col = x // tile_size
        row = y // tile_size
        if 0 <= row < self._grid_size and 0 <= col < self._grid_size:
            return row * self._grid_size + col
        return None

    # Player actions

    def select_or_swap(self, current_index: int) -> str:
        """
        Handle left-click on a tile.

        Returns a short status message describing what happened.
        """
        if self._solved or not self._tiles:
            return "Puzzle is already solved."

        if self._selected_index is None:
            self._selected_index = current_index
            return f"Tile {current_index} selected."

        if self._selected_index == current_index:
            self._selected_index = None
            return "Selection cleared."

        # Swap
        self._swap_by_current_index(self._selected_index, current_index)
        self._selected_index = None
        self._moves += 1
        self._clear_hint()
        self._check_solved()
        return "Tiles swapped."

    def rotate_tile(self, current_index: int) -> str:
        """Rotate a tile 90° clockwise."""
        if self._solved or not self._tiles:
            return "Puzzle is already solved."
        tile = self._get_tile_by_current(current_index)
        if tile is None:
            return "Invalid tile."
        tile.rotate_clockwise(90)
        self._selected_index = None
        self._moves += 1
        self._clear_hint()
        self._check_solved()
        return "Tile rotated."

    def flip_tile_horizontal(self, current_index: int) -> str:
        """Shift+left-click: horizontal flip."""
        if self._solved or not self._tiles:
            return "Puzzle is already solved."
        tile = self._get_tile_by_current(current_index)
        if tile is None:
            return "Invalid tile."
        tile.flip_horizontal()
        self._selected_index = None
        self._moves += 1
        self._clear_hint()
        self._check_solved()
        return "Tile flipped horizontally."

    def _swap_by_current_index(self, idx_a: int, idx_b: int) -> None:
        tile_a = self._get_tile_by_current(idx_a)
        tile_b = self._get_tile_by_current(idx_b)
        if tile_a is None or tile_b is None:
            return
        tile_a.current_index, tile_b.current_index = (
            tile_b.current_index,
            tile_a.current_index,
        )
        # Keep list ordered by current_index
        self._sync_list_to_positions()

    def _get_tile_by_current(self, current_index: int) -> Optional[PuzzleTile]:
        for t in self._tiles:
            if t.current_index == current_index:
                return t
        return None

    # Correctness & scoring

    def count_incorrect(self) -> int:
        return sum(1 for t in self._tiles if not t.is_correct())

    def get_correct_indices(self) -> List[int]:
        """Return current_index values of all correct tiles."""
        return [t.current_index for t in self._tiles if t.is_correct()]

    def _check_solved(self) -> None:
        if self._tiles and all(t.is_correct() for t in self._tiles):
            self._solved = True
            self._selected_index = None
            self._clear_hint()

    # ------------------------------------------------------------------
    # Hints
    # ------------------------------------------------------------------

    def use_hint(self) -> str:
        """
        Mark one incorrect tile with a blue circle on the puzzle
        and its home position on the original image.
        """
        if self._solved:
            return "Puzzle is already solved."
        if not self._tiles:
            return "No puzzle loaded."
        if self._hints_used >= MAX_HINTS:
            return "No hints remaining."

        incorrect = [t for t in self._tiles if not t.is_correct()]
        if not incorrect:
            return "All tiles are correct."

        chosen = random.choice(incorrect)
        self._hint_puzzle_pos = chosen.current_index
        self._hint_home_pos = chosen.original_index
        self._hint_active = True
        self._hints_used += 1
        return (
            f"Hint: look at the blue circle. "
            f"Hints used: {self._hints_used}/{MAX_HINTS}"
        )

    def _clear_hint(self) -> None:
        self._hint_active = False
        self._hint_puzzle_pos = None
        self._hint_home_pos = None


    def solve(self) -> str:
        """
        Instantly restore every tile to its original position and
        orientation. Clears moves and score.
        """
        if not self._tiles:
            return "No puzzle loaded."
        for tile in self._tiles:
            tile.reset_to_home()
        self._sync_list_to_positions()
        self._moves = 0
        self._selected_index = None
        self._clear_hint()
        self._solved = True
        return "Puzzle solved automatically. Moves reset to 0."

    def restart(self) -> str:
        """Restore the original scrambled board and clear run state."""
        if not self._initial_tiles:
            return "No puzzle loaded."
        if self._solved:
            return "Puzzle already solved. Load another image to continue."
        self._tiles = [tile.clone() for tile in self._initial_tiles]
        self._moves = 0
        self._selected_index = None
        self._solved = False
        self._clear_hint()
        return "Puzzle reset. Try again!"

    # Reset

    def reset(self) -> None:
        """Clear all state ready for a new image."""
        self._tiles = []
        self._initial_tiles = []
        self._moves = 0
        self._hints_used = 0
        self._selected_index = None
        self._solved = False
        self._original_display = None
        self._clear_hint()
        self._grid_size = 3

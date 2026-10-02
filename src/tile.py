"""
Tile classes used in the Image Tile Puzzle.
Shows basic OOP concepts such as:
                    * Encapsulation using protected attributes
                    * Inheritance from BaseTile to PuzzleTile
                    * Polymorphism through overridden methods
"""


from __future__ import annotations

import copy
from typing import Optional

import cv2
import numpy as np


class BaseTile:
    """       Base class for image tiles.
    Encapsulates the raw image data and provides common operations.
    Subclasses override display-related behaviour where needed.
    """

    def __init__(self, image: np.ndarray, tile_id: int) -> None:
        """
        Initialise a base tile.

        Args:
            image: BGR OpenCV image of this tile.
            tile_id: Unique identifier for the tile (original grid index).
        """
        self._image: np.ndarray = image.copy()
        self._tile_id: int = tile_id

    @property
    def image(self) -> np.ndarray:
        """Return a copy of the current tile image."""
        return self._image.copy()

    @property
    def tile_id(self) -> int:
        """Return the unique tile identifier."""
        return self._tile_id

    def get_display_image(self) -> np.ndarray:
        """
        Return the image that should be shown to the user.
        Base implementation returns the raw image; subclasses may override.
        """
        return self.image

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self._tile_id})"


class PuzzleTile(BaseTile):
    """
    A puzzle tile that tracks position and orientation state.

    Inherits from BaseTile and adds:
    - original / current grid index
    - rotation (0, 90, 180, 270)
    - horizontal and vertical flip flags
    - methods to apply and reverse visual transformations
    """

    def __init__(
        self,
        image: np.ndarray,
        original_index: int,
        current_index: Optional[int] = None,
    ) -> None:
        """
        Initialise a puzzle tile.

        Args:
            image: BGR OpenCV image of this tile (original orientation).
            original_index: Home position in the grid (row-major).
            current_index: Current position; defaults to original_index.
        """
        super().__init__(image, original_index)
        self._original_index: int = original_index
        self._current_index: int = (
            current_index if current_index is not None else original_index
        )
        # Orientation state relative to the original image
        self._rotation: int = 0  # 0, 90, 180, 270
        self._flip_h: bool = False
        self._flip_v: bool = False
        self._orientation: tuple[int, int, int, int] = (1, 0, 0, 1)
        # Cached original image for correct reconstruction
        self._original_image: np.ndarray = image.copy()

    # Properties (encapsulation)

    @property
    def original_index(self) -> int:
        return self._original_index

    @property
    def current_index(self) -> int:
        return self._current_index

    @current_index.setter
    def current_index(self, value: int) -> None:
        self._current_index = value

    @property
    def rotation(self) -> int:
        return self._rotation

    @property
    def flip_h(self) -> bool:
        return self._flip_h

    @property
    def flip_v(self) -> bool:
        return self._flip_v

    # State helpers

    def is_correct(self) -> bool:
        """
        A tile is correct only when it is in its home position
        AND its orientation matches the original.
        """
        return (
            self._current_index == self._original_index
            and self._orientation == (1, 0, 0, 1)
        )

    def reset_orientation(self) -> None:
        """Restore original orientation and rebuild the visual image."""
        self._rotation = 0
        self._flip_h = False
        self._flip_v = False
        self._orientation = (1, 0, 0, 1)
        self._image = self._original_image.copy()

    def _compose_orientation(
        self, operation: tuple[int, int, int, int]
    ) -> None:
        a, b, c, d = operation
        e, f, g, h = self._orientation
        self._orientation = (
            a * e + b * g,
            a * f + b * h,
            c * e + d * g,
            c * f + d * h,
        )

    def reset_to_home(self) -> None:
        """Restore home position and original orientation."""
        self._current_index = self._original_index
        self.reset_orientation()

    # Transformation methods

    def rotate_clockwise(self, degrees: int = 90) -> None:
        """
        Rotate the tile clockwise by 90, 180 or 270 degrees.
        Updates both visual data and logical rotation state.
        """
        degrees = degrees % 360
        if degrees not in (90, 180, 270):
            raise ValueError("Rotation must be 90, 180 or 270 degrees")

        if degrees == 90:
            self._image = cv2.rotate(self._image, cv2.ROTATE_90_CLOCKWISE)
        elif degrees == 180:
            self._image = cv2.rotate(self._image, cv2.ROTATE_180)
        else:  # 270
            self._image = cv2.rotate(self._image, cv2.ROTATE_90_COUNTERCLOCKWISE)

        self._rotation = (self._rotation + degrees) % 360
        operations = {
            90: (0, -1, 1, 0),
            180: (-1, 0, 0, -1),
            270: (0, 1, -1, 0),
        }
        self._compose_orientation(operations[degrees])

        # Rotating also swaps flip axes in certain cases
        if degrees == 90 or degrees == 270:
            self._flip_h, self._flip_v = self._flip_v, self._flip_h

    def flip_horizontal(self) -> None:
        """Flip the tile horizontally and update logical state."""
        self._image = cv2.flip(self._image, 1)  # 1 = horizontal
        self._flip_h = not self._flip_h
        self._compose_orientation((-1, 0, 0, 1))

    def flip_vertical(self) -> None:
        """Flip the tile vertically and update logical state."""
        self._image = cv2.flip(self._image, 0)  # 0 = vertical
        self._flip_v = not self._flip_v
        self._compose_orientation((1, 0, 0, -1))

    # Polymorphic display method

    def get_display_image(self) -> np.ndarray:
        """
        Override of BaseTile.get_display_image.
        Returns the current visual representation of the tile.
        """
        return self.image

    def clone(self) -> "PuzzleTile":
        """Return a deep copy of this tile (useful for undo / solve)."""
        new_tile = PuzzleTile(
            self._original_image.copy(),
            self._original_index,
            self._current_index,
        )
        new_tile._image = self._image.copy()
        new_tile._rotation = self._rotation
        new_tile._flip_h = self._flip_h
        new_tile._flip_v = self._flip_v
        new_tile._orientation = self._orientation
        return new_tile

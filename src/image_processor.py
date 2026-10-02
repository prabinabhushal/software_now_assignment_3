"""
Image processing utilities using OpenCV and NumPy.
Handles loading, resizing, cropping, padding, splitting images into tiles,
and putting the tiles back together to create the final image.
"""

from __future__ import annotations
from typing import List, Tuple
import cv2
import numpy as np
from .tile import PuzzleTile


class ImageProcessor:
    """
    Responsible for all OpenCV-based image operations.

    Encapsulates image loading, geometric adjustment and tile management.
    """

    # Maximum dimension (width or height) for the puzzle area on screen
    MAX_DISPLAY_SIZE: int = 480

    def __init__(self) -> None:
        """Initialise the image processor."""
        self._original_image: np.ndarray | None = None
        self._prepared_image: np.ndarray | None = None
        self._tile_size: int = 0
        self._grid_size: int = 3

    @property
    def original_image(self) -> np.ndarray | None:
        return None if self._original_image is None else self._original_image.copy()

    @property
    def prepared_image(self) -> np.ndarray | None:
        return None if self._prepared_image is None else self._prepared_image.copy()

    @property
    def tile_size(self) -> int:
        return self._tile_size

    @property
    def grid_size(self) -> int:
        return self._grid_size

    # Loading images and preparing them for the puzzle

    def load_image(self, path: str) -> np.ndarray:
        """
        Load an image from disk using OpenCV.

        Raises:
            FileNotFoundError / ValueError on failure.
        """
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(
                f"Could not load image from '{path}'. "
                "Unsupported format or corrupted file."
            )
        self._original_image = img
        return img.copy()

    def prepare_image(self, image: np.ndarray, grid_size: int) -> np.ndarray:
        """
        Resize the image so it fits on screen, then crop or pad
        so that both dimensions divide evenly by grid_size.
        """
        self._grid_size = grid_size
        resized = self._resize_to_fit(image)
        prepared = self._crop_or_pad(resized, grid_size)
        self._prepared_image = prepared
        h, w = prepared.shape[:2]
        self._tile_size = h // grid_size
        return prepared.copy()

    def _resize_to_fit(self, image: np.ndarray) -> np.ndarray:
        """
        Resize while preserving aspect ratio so the longer side
        is at most MAX_DISPLAY_SIZE.
        """
        h, w = image.shape[:2]
        scale = min(self.MAX_DISPLAY_SIZE / max(h, w), 1.0)
        if scale < 1.0:
            new_w = int(w * scale)
            new_h = int(h * scale)
            return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        return image.copy()

    def _crop_or_pad(self, image: np.ndarray, grid_size: int) -> np.ndarray:
        """
        Make the image dimensions divisible by grid_size.
        Prefer centre-crop; if the image is smaller, pad with black.
        """
        h, w = image.shape[:2]
        # Target size: largest multiple of grid_size that fits
        target_h = (h // grid_size) * grid_size
        target_w = (w // grid_size) * grid_size

        # If either dimension became zero (very small image), pad instead
        if target_h == 0 or target_w == 0:
            target_h = max(grid_size * 40, target_h)
            target_w = max(grid_size * 40, target_w)
            # Make square for simplicity
            side = max(target_h, target_w)
            target_h = target_w = (side // grid_size) * grid_size

        # Centre crop
        y0 = (h - target_h) // 2
        x0 = (w - target_w) // 2
        if y0 >= 0 and x0 >= 0 and target_h > 0 and target_w > 0:
            cropped = image[y0 : y0 + target_h, x0 : x0 + target_w]
        else:
            cropped = image

        # Pad if still not large enough
        ch, cw = cropped.shape[:2]
        if ch < target_h or cw < target_w:
            pad_top = max(0, (target_h - ch) // 2)
            pad_bottom = max(0, target_h - ch - pad_top)
            pad_left = max(0, (target_w - cw) // 2)
            pad_right = max(0, target_w - cw - pad_left)
            cropped = cv2.copyMakeBorder(
                cropped,
                pad_top,
                pad_bottom,
                pad_left,
                pad_right,
                cv2.BORDER_CONSTANT,
                value=(0, 0, 0),
            )
            # Final crop to exact target
            cropped = cropped[:target_h, :target_w]

        # Ensure both dimensions are equal multiples (make square)
        side = min(cropped.shape[0], cropped.shape[1])
        side = (side // grid_size) * grid_size
        if side == 0:
            side = grid_size * 40
        y0 = (cropped.shape[0] - side) // 2
        x0 = (cropped.shape[1] - side) // 2
        return cropped[y0 : y0 + side, x0 : x0 + side].copy()

    # Tile operations

    def split_into_tiles(
        self, image: np.ndarray, grid_size: int
    ) -> List[PuzzleTile]:
        """
        Split a prepared image into a list of PuzzleTile objects
        ordered in row-major order (index 0 = top-left).
        """
        h, w = image.shape[:2]
        tile_h = h // grid_size
        tile_w = w // grid_size
        tiles: List[PuzzleTile] = []
        idx = 0
        for r in range(grid_size):
            for c in range(grid_size):
                y0 = r * tile_h
                x0 = c * tile_w
                tile_img = image[y0 : y0 + tile_h, x0 : x0 + tile_w].copy()
                tiles.append(PuzzleTile(tile_img, original_index=idx))
                idx += 1
        self._tile_size = tile_h
        return tiles

    def reassemble_tiles(
        self, tiles: List[PuzzleTile], grid_size: int
    ) -> np.ndarray:
        """
        Reconstruct a single image from a list of tiles ordered
        by their current_index (row-major).
        """
        if not tiles:
            raise ValueError("No tiles to reassemble")

        # Sort by current position so we can place them correctly
        ordered = sorted(tiles, key=lambda t: t.current_index)
        tile_h, tile_w = ordered[0].image.shape[:2]
        canvas = np.zeros(
            (tile_h * grid_size, tile_w * grid_size, 3), dtype=np.uint8
        )

        for tile in ordered:
            r = tile.current_index // grid_size
            c = tile.current_index % grid_size
            y0 = r * tile_h
            x0 = c * tile_w
            img = tile.get_display_image()
            # Ensure size match (rotation can change dims for non-square,
            # but our tiles are square)
            if img.shape[0] != tile_h or img.shape[1] != tile_w:
                img = cv2.resize(img, (tile_w, tile_h))
            canvas[y0 : y0 + tile_h, x0 : x0 + tile_w] = img
        return canvas

    def draw_grid(
        self, image: np.ndarray, grid_size: int, colour: Tuple[int, int, int] = (180, 180, 180)
    ) -> np.ndarray:
        """Draw faint grid lines over the image."""
        result = image.copy()
        h, w = result.shape[:2]
        tile_h = h // grid_size
        tile_w = w // grid_size
        for i in range(1, grid_size):
            y = i * tile_h
            x = i * tile_w
            cv2.line(result, (0, y), (w, y), colour, 1, cv2.LINE_AA)
            cv2.line(result, (x, 0), (x, h), colour, 1, cv2.LINE_AA)
        return result

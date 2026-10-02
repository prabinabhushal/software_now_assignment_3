"""
Transformation hierarchy for the Image Tile Puzzle.

- Inheritance (Transformation base class)
- Polymorphism (each subclass implements apply())
"""

from __future__ import annotations
import random
from abc import ABC, abstractmethod
from typing import List

from .tile import PuzzleTile


class Transformation(ABC):
    """
    Abstract base class for puzzle transformations.
    Every concrete transformation must implement apply().
    provides a clear polymorphism example.
    """

    def __init__(self) -> None:
        """Initialise the transformation."""
        pass

    @abstractmethod
    def apply(self, tiles: List[PuzzleTile], grid_size: int) -> None:
        """
        Apply this transformation to the list of tiles.

        Args:
            tiles: List of PuzzleTile objects (mutated in place).
            grid_size: Side length of the square grid (3, 4 or 5).
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        return self.__class__.__name__


class SwapTransformation(Transformation):
    """Exchange the current positions of two randomly chosen tiles."""

    def __init__(self) -> None:
        super().__init__()
        self._index_a: int = -1
        self._index_b: int = -1

    def apply(self, tiles: List[PuzzleTile], grid_size: int) -> None:
        n = len(tiles)
        if n < 2:
            return
        a, b = random.sample(range(n), 2)
        self._index_a, self._index_b = a, b

        # Swap current_index values
        tiles[a].current_index, tiles[b].current_index = (
            tiles[b].current_index,
            tiles[a].current_index,
        )
        # Also swap the tiles themselves in the list so the list order
        # always reflects current grid positions (row-major).
        tiles[a], tiles[b] = tiles[b], tiles[a]


class RotateTransformation(Transformation):
    """Rotate a randomly chosen tile by 90°, 180° or 270° clockwise."""

    def __init__(self) -> None:
        super().__init__()
        self._index: int = -1
        self._degrees: int = 90

    def apply(self, tiles: List[PuzzleTile], grid_size: int) -> None:
        if not tiles:
            return
        self._index = random.randrange(len(tiles))
        self._degrees = random.choice([90, 180, 270])
        tiles[self._index].rotate_clockwise(self._degrees)


class FlipTransformation(Transformation):
    """Flip a randomly chosen tile horizontally or vertically."""

    def __init__(self) -> None:
        super().__init__()
        self._index: int = -1
        self._horizontal: bool = True

    def apply(self, tiles: List[PuzzleTile], grid_size: int) -> None:
        if not tiles:
            return
        self._index = random.randrange(len(tiles))
        self._horizontal = random.choice([True, False])
        if self._horizontal:
            tiles[self._index].flip_horizontal()
        else:
            tiles[self._index].flip_vertical()


def create_random_transformations(count: int) -> List[Transformation]:
    """
    Create a list of randomly chosen transformations.
    Uses polymorphism: each item is a Transformation subclass
    and will respond to apply() according to its own type.
    """
    factories = [
        SwapTransformation,
        RotateTransformation,
        FlipTransformation,
    ]
    result: List[Transformation] = []
    for _ in range(count):
        cls = random.choice(factories)
        result.append(cls())
    return result

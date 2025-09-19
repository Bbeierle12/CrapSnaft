"""Collision and swept-volume checks (Sections 5 & 6)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence, Tuple

import numpy as np

__all__ = [
    "AABB",
    "bounds_from_points",
    "separated_along_axis",
    "swept_collision",
]


@dataclass(slots=True)
class AABB:
    min_corner: np.ndarray
    max_corner: np.ndarray

    def intersects(self, other: "AABB") -> bool:
        return not separated_along_axis(self, other)


def bounds_from_points(points: np.ndarray) -> AABB:
    pts = np.asarray(points, dtype=float)
    return AABB(pts.min(axis=0), pts.max(axis=0))


def separated_along_axis(a: AABB, b: AABB) -> bool:
    for axis in range(3):
        if a.max_corner[axis] < b.min_corner[axis] or b.max_corner[axis] < a.min_corner[axis]:
            return True
    return False


def _discrete_line_kernel(direction: Sequence[float], length: float) -> np.ndarray:
    direction = np.asarray(direction, dtype=float)
    norm = np.linalg.norm(direction)
    if norm == 0:
        return np.zeros((1, 3), dtype=int)
    direction /= norm
    steps = max(1, int(np.ceil(length)))
    offsets = {tuple((direction * s).round().astype(int)) for s in np.linspace(0, length, steps + 1)}
    return np.array(sorted(offsets), dtype=int)


def _shift(grid: np.ndarray, offset: Sequence[int]) -> np.ndarray:
    offset = [int(o) for o in offset]
    result = np.zeros_like(grid)
    src_slices = []
    dst_slices = []
    for axis, off in enumerate(offset):
        if off >= 0:
            src = slice(0, grid.shape[axis] - off)
            dst = slice(off, grid.shape[axis])
        else:
            src = slice(-off, grid.shape[axis])
            dst = slice(0, grid.shape[axis] + off)
        src_slices.append(src)
        dst_slices.append(dst)
    result[tuple(dst_slices)] = grid[tuple(src_slices)]
    return result


def swept_collision(
    part_grid: np.ndarray,
    environment_grid: np.ndarray,
    direction: Sequence[float],
    length: float,
) -> bool:
    """Discrete swept-volume collision test (Section 6)."""

    if part_grid.shape != environment_grid.shape:
        raise ValueError("Occupancy grids must share shape")

    kernel = _discrete_line_kernel(direction, length)
    dilated = np.zeros_like(part_grid)
    for offset in kernel:
        dilated |= _shift(part_grid, offset)
    return bool(np.any(dilated & environment_grid))

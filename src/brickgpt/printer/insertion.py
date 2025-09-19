"""Directional insertion feasibility checks (Section 6)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np

from .collision import swept_collision

__all__ = [
    "InsertionCone",
    "placeable",
]


def _unit(vec: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(vec)
    if n == 0:
        raise ValueError("Zero-length vector")
    return vec / n

@dataclass(slots=True)
class InsertionCone:
    axis: np.ndarray
    half_angle_rad: float

    def contains(self, direction: np.ndarray) -> bool:
        direction = _unit(direction)
        ax = _unit(self.axis)
        return np.arccos(np.clip(np.dot(direction, ax), -1.0, 1.0)) <= self.half_angle_rad


def _sample_cones(cones: Sequence[InsertionCone], num_samples: int = 64) -> np.ndarray:
    if not cones:
        raise ValueError("No cones provided")

    samples: list[np.ndarray] = []
    for cone in cones:
        ax = _unit(cone.axis)
        for _ in range(max(1, num_samples // len(cones))):
            # Sample direction inside cone using rejection sampling on sphere.
            while True:
                vec = np.random.normal(size=3)
                vec = _unit(vec)
                if cone.contains(vec):
                    samples.append(vec)
                    break
    if not samples:
        samples.append(_unit(cones[0].axis))
    return np.stack(samples, axis=0)


def placeable(
    part_grid: np.ndarray,
    environment_grid: np.ndarray,
    cones: Sequence[InsertionCone],
    travel_length: float,
) -> bool:
    """Return True if any admissible direction avoids swept collision."""

    if not cones:
        raise ValueError("placeable requires at least one insertion cone")

    directions = _sample_cones(cones)
    for direction in directions:
        if not swept_collision(part_grid, environment_grid, direction, travel_length):
            return True
    return False

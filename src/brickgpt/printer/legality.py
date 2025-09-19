"""Legality checks (Section 10)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from .collision import AABB, separated_along_axis

__all__ = [
    "positional_legality",
    "angular_legality",
    "interference_free",
]

def positional_legality(delta_translation_mm: Iterable[float], tolerance_xy: float, tolerance_z: float) -> bool:
    dt = np.asarray(delta_translation_mm, dtype=float)
    planar = np.linalg.norm(dt[:2])
    vertical = abs(dt[2])
    return planar <= tolerance_xy and vertical <= tolerance_z

def angular_legality(delta_rotation: np.ndarray, tolerance_rad: float) -> bool:
    angle = np.arccos(np.clip((np.trace(delta_rotation) - 1) / 2, -1.0, 1.0))
    return angle <= tolerance_rad

def interference_free(bounds_a: AABB, bounds_b: AABB) -> bool:
    return separated_along_axis(bounds_a, bounds_b)

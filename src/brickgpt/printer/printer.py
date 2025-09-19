"""Virtual printer invariant maintenance (Section 15)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

import numpy as np

from . import insertion, statics, transforms
from . import units as units_module
from .collision import swept_collision
from .connections import StudTubeConstraint

__all__ = [
    "VirtualPrinterState",
]

def _distance_point_to_segment(point: np.ndarray, a: np.ndarray, b: np.ndarray) -> float:
    if np.allclose(a, b):
        return float(np.linalg.norm(point - a))
    ap = point - a
    ab = b - a
    t = np.clip(np.dot(ap, ab) / np.dot(ab, ab), 0.0, 1.0)
    projection = a + t * ab
    return float(np.linalg.norm(point - projection))

def _polygon_margin(polygon: np.ndarray, point: np.ndarray) -> float:
    if len(polygon) < 2:
        return float("inf")
    min_dist = float("inf")
    for i in range(len(polygon)):
        a = polygon[i]
        b = polygon[(i + 1) % len(polygon)]
        min_dist = min(min_dist, _distance_point_to_segment(point, a, b))
    return min_dist

@dataclass(slots=True)
class VirtualPrinterState:
    world_shape: tuple[int, int, int] = (20, 20, 20)
    units: units_module.CanonicalUnits = units_module.DEFAULT_UNITS
    lattice: units_module.StudLattice = field(default_factory=units_module.StudLattice)
    occupancy: np.ndarray = field(init=False)

    def __post_init__(self) -> None:
        self.occupancy = np.zeros(self.world_shape, dtype=bool)

    def _assert_shape(self, grid: np.ndarray) -> None:
        if grid.shape != self.occupancy.shape:
            raise ValueError("Occupancy grids must match world shape")

    def _quantized_translation(self, pose: transforms.BrickPose) -> bool:
        idx, snapped = units_module.snap_to_stud(pose.translation_mm, lattice=self.lattice)
        return np.allclose(snapped, pose.translation_mm, atol=1e-6)

    def _collision_free(self, part_grid: np.ndarray) -> bool:
        self._assert_shape(part_grid)
        return not np.any(part_grid & self.occupancy)

    def _placeable(self, part_grid: np.ndarray, cones: Sequence[insertion.InsertionCone], travel_length: float) -> bool:
        return insertion.placeable(part_grid, self.occupancy, cones, travel_length)

    def _candidate_support_points(self, candidate: np.ndarray) -> np.ndarray:
        supports: list[tuple[float, float]] = []
        studs = self.units.stud_pitch_mm
        indices = np.argwhere(candidate)
        for x, y, z in indices:
            if z == 0 or candidate[x, y, z - 1]:
                supports.append((x * studs, y * studs))
        return np.asarray(supports, dtype=float)

    def _static_margin(self, candidate: np.ndarray, sigma: float) -> bool:
        studs = self.units.stud_pitch_mm
        indices = np.argwhere(candidate)
        if len(indices) == 0:
            return True
        masses = np.ones(len(indices))
        positions_xy = indices[:, :2] * studs
        com = np.array(statics.center_of_mass(masses, positions_xy))
        supports = self._candidate_support_points(candidate)
        if len(supports) == 0:
            return False
        polygon = statics.support_polygon(supports)
        if polygon.size == 0 or not statics.contains_point(polygon, com):
            return False
        margin = _polygon_margin(polygon, com)
        return margin >= sigma

    def legal_to_place(
        self,
        pose: transforms.BrickPose,
        part_grid: np.ndarray,
        cones: Sequence[insertion.InsertionCone],
        travel_length: float,
        mate_constraints: Sequence[tuple[StudTubeConstraint, Iterable[float], np.ndarray]] | None = None,
        sigma: float = 0.0,
    ) -> bool:
        part_grid = part_grid.astype(bool)
        if not self._quantized_translation(pose):
            return False
        if not self._collision_free(part_grid):
            return False
        if cones and not self._placeable(part_grid, cones, travel_length):
            return False
        if mate_constraints:
            for constraint, translation, rotation in mate_constraints:
                if not constraint.is_satisfied(translation, rotation):
                    return False
        candidate = self.occupancy | part_grid
        if not self._static_margin(candidate, sigma):
            return False
        return True

    def commit(self, part_grid: np.ndarray) -> None:
        self._assert_shape(part_grid)
        self.occupancy |= part_grid.astype(bool)


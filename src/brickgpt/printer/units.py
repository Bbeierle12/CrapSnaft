"""Canonical unit definitions and lattice/frame conversions for the virtual brick printer.

This module codifies the relationships spelled out in Section 1 of the math specification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

import numpy as np

__all__ = [
    "CanonicalUnits",
    "DEFAULT_UNITS",
    "StudLattice",
    "VoxelFrame",
    "snap_to_stud",
    "stud_error_bounds",
    "world_to_ldu",
    "ldu_to_world",
]


@dataclass(frozen=True)
class CanonicalUnits:
    """Canonical LEGO unit system.

    Attributes
    ----------
    stud_pitch_mm:
        Distance between adjacent studs in millimetres (Section 1.1).
    plate_height_mm:
        Height of a single plate in millimetres.
    ldu_per_mm:
        Conversion factor from millimetres to LDraw units (LDUs).
    """

    stud_pitch_mm: float = 8.0
    plate_height_mm: float = 3.2
    ldu_per_mm: float = 2.5

    @property
    def stud_pitch_ldu(self) -> float:
        return self.stud_pitch_mm * self.ldu_per_mm

    @property
    def plate_height_ldu(self) -> float:
        return self.plate_height_mm * self.ldu_per_mm

    @property
    def stud_to_plate_ratio(self) -> float:
        return self.stud_pitch_mm / self.plate_height_mm


DEFAULT_UNITS = CanonicalUnits()


@dataclass(frozen=True)
class StudLattice:
    """Integer stud lattice :math:`\mathcal{L}` (Section 1.2).

    The lattice stores the origin in world millimetres.  Coordinates are always
    returned in millimetres to keep the interface consistent with upstream code.
    """

    units: CanonicalUnits = DEFAULT_UNITS
    origin_mm: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    def world_from_index(self, ijk: Iterable[int]) -> np.ndarray:
        i, j, k = (int(v) for v in ijk)
        dx, dy, dz = self.units.stud_pitch_mm, self.units.stud_pitch_mm, self.units.plate_height_mm
        base = np.array(self.origin_mm, dtype=float)
        return base + np.array([i * dx, j * dy, k * dz], dtype=float)

    def index_from_world(self, position_mm: Iterable[float]) -> np.ndarray:
        pos = np.asarray(position_mm, dtype=float) - np.asarray(self.origin_mm, dtype=float)
        dx, dy, dz = self.units.stud_pitch_mm, self.units.stud_pitch_mm, self.units.plate_height_mm
        return np.array([
            np.round(pos[0] / dx),
            np.round(pos[1] / dy),
            np.round(pos[2] / dz),
        ], dtype=int)

    def metric(self) -> np.ndarray:
        """Return the diagonal metric tensor for conversions."""
        return np.diag([
            self.units.stud_pitch_mm,
            self.units.stud_pitch_mm,
            self.units.plate_height_mm,
        ])


@dataclass(frozen=True)
class VoxelFrame:
    """Voxel frame :math:`\mathcal{V}` with cubic voxels (Section 1.2)."""

    pitch_mm: float
    origin_mm: Tuple[float, float, float]

    def world_to_voxel(self, position_mm: Iterable[float]) -> np.ndarray:
        pos = np.asarray(position_mm, dtype=float)
        origin = np.asarray(self.origin_mm, dtype=float)
        return np.floor((pos - origin) / self.pitch_mm).astype(int)

    def voxel_bounds(self, index_uvw: Iterable[int]) -> Tuple[np.ndarray, np.ndarray]:
        uvw = np.asarray(index_uvw, dtype=int)
        origin = np.asarray(self.origin_mm, dtype=float)
        lower = origin + self.pitch_mm * uvw
        upper = lower + self.pitch_mm
        return lower, upper

    def snap_origin_to_stud(self, lattice: StudLattice) -> "VoxelFrame":
        snapped = lattice.world_from_index(lattice.index_from_world(self.origin_mm))
        return VoxelFrame(pitch_mm=self.pitch_mm, origin_mm=tuple(snapped))


def snap_to_stud(position_mm: Iterable[float], lattice: StudLattice | None = None) -> Tuple[np.ndarray, np.ndarray]:
    """Snap a world-space point to the nearest stud and return (indices, coords).

    Implements :math:`Q_s` from Section 1.3.  The returned coordinates are in mm.
    """

    lattice = lattice or StudLattice()
    idx = lattice.index_from_world(position_mm)
    snapped = lattice.world_from_index(idx)
    return idx, snapped


def stud_error_bounds(units: CanonicalUnits = DEFAULT_UNITS) -> np.ndarray:
    """Return the Chebyshev error bounds (Section 1.3)."""

    return np.array([
        units.stud_pitch_mm / 2,
        units.stud_pitch_mm / 2,
        units.plate_height_mm / 2,
    ])


def world_to_ldu(position_mm: Iterable[float], units: CanonicalUnits = DEFAULT_UNITS) -> np.ndarray:
    """Convert a millimetre position into LDraw units (Section 3)."""

    pos = np.asarray(position_mm, dtype=float)
    return pos * units.ldu_per_mm


def ldu_to_world(position_ldu: Iterable[float], units: CanonicalUnits = DEFAULT_UNITS) -> np.ndarray:
    """Convert LDraw coordinates back to millimetres."""

    pos = np.asarray(position_ldu, dtype=float)
    return pos / units.ldu_per_mm

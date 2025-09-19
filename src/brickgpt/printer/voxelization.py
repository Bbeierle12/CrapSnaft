"""Voxelization and occupancy utilities (Section 2 of the spec)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Tuple

import numpy as np

from .units import StudLattice, VoxelFrame, DEFAULT_UNITS, CanonicalUnits

try:  # Optional dependency used only when mesh voxelisation is required.
    import trimesh  # type: ignore
except ImportError:  # pragma: no cover - handled lazily in functions.
    trimesh = None  # type: ignore

__all__ = [
    "AntiAliasedGrid",
    "binary_occupancy",
    "downsample_to_studs",
    "voxelize_mesh",
]


@dataclass(slots=True)
class AntiAliasedGrid:
    """Anti-aliased occupancy grid :math:`\rho` over the voxel frame."""

    frame: VoxelFrame
    values: np.ndarray  # shape (nx, ny, nz) with entries in [0, 1]
    base_index: Tuple[int, int, int] = (0, 0, 0)

    def clamp(self) -> None:
        np.clip(self.values, 0.0, 1.0, out=self.values)

    @property
    def pitch(self) -> float:
        return self.frame.pitch_mm

    @property
    def shape(self) -> Tuple[int, int, int]:
        return tuple(int(v) for v in self.values.shape)  # type: ignore[return-value]

    def world_index(self, local_index: Iterable[int]) -> np.ndarray:
        return np.asarray(self.base_index, dtype=int) + np.asarray(local_index, dtype=int)


def voxelize_mesh(
    mesh: "trimesh.Trimesh",
    frame: VoxelFrame,
    samples_per_voxel: int = 128,
    jitter: bool = True,
) -> AntiAliasedGrid:
    """Approximate the anti-aliased occupancy :math:`\rho` via Monte Carlo.

    Parameters
    ----------
    mesh:
        Watertight triangle mesh (Section 2).  Requires :mod:`trimesh`.
    frame:
        Voxel frame definition.
    samples_per_voxel:
        Number of Monte Carlo samples per voxel.
    jitter:
        Whether to offset sample positions randomly instead of using voxel corners.
    """

    if trimesh is None:  # pragma: no cover - optional dependency.
        raise ImportError(
            "voxelize_mesh requires the optional 'trimesh' dependency. Install it via 'pip install trimesh'."
        )

    if not mesh.is_watertight:
        raise ValueError("Mesh must be watertight to compute volumetric occupancy.")

    min_corner, max_corner = mesh.bounds
    origin = np.asarray(frame.origin_mm)
    pitch = frame.pitch_mm
    min_idx = np.floor((min_corner - origin) / pitch).astype(int)
    max_idx = np.ceil((max_corner - origin) / pitch).astype(int) - 1
    grid_shape = tuple(int(max_idx[d] - min_idx[d] + 1) for d in range(3))
    occupancy = np.zeros(grid_shape, dtype=np.float32)

    pitch_vec = np.array([pitch, pitch, pitch], dtype=float)

    if jitter:
        base_samples = np.random.rand(samples_per_voxel, 3)
    else:
        root = max(1, round(samples_per_voxel ** (1 / 3)))
        lin = np.linspace(0.05, 0.95, root)
        gx, gy, gz = np.meshgrid(lin, lin, lin, indexing="ij")
        base_samples = np.stack([gx, gy, gz], axis=-1).reshape(-1, 3)

    for offset_i in range(grid_shape[0]):
        for offset_j in range(grid_shape[1]):
            for offset_k in range(grid_shape[2]):
                idx = min_idx + np.array([offset_i, offset_j, offset_k])
                lower, _ = frame.voxel_bounds(idx)
                samples = lower + base_samples * pitch_vec
                inside = mesh.contains(samples)
                occupancy[offset_i, offset_j, offset_k] = inside.mean()

    grid = AntiAliasedGrid(frame=frame, values=occupancy, base_index=tuple(int(v) for v in min_idx))
    grid.clamp()
    return grid


def binary_occupancy(grid: AntiAliasedGrid, tau: float) -> np.ndarray:
    """Threshold anti-aliased occupancy (Section 2)."""

    if not (0.0 < tau < 1.0):
        raise ValueError("tau must lie in (0, 1)")
    return (grid.values > tau).astype(np.uint8)


def _block_bounds(shape: Tuple[int, int, int], block: Tuple[int, int, int], index: Tuple[int, int, int]):
    slices = []
    for dim, blk, idx in zip(shape, block, index):
        start = idx * blk
        stop = min(dim, start + blk)
        slices.append(slice(start, stop))
    return tuple(slices)


def downsample_to_studs(
    binary_grid: np.ndarray,
    frame: VoxelFrame,
    lattice: StudLattice | None = None,
    units: CanonicalUnits = DEFAULT_UNITS,
) -> np.ndarray:
    """Logical-OR block downsample (Section 2) to reach the stud lattice."""

    lattice = lattice or StudLattice(units=units)
    if binary_grid.ndim != 3:
        raise ValueError("binary_grid must be 3-D")

    kappa = (
        max(1, int(math.floor(units.stud_pitch_mm / frame.pitch_mm))),
        max(1, int(math.floor(units.stud_pitch_mm / frame.pitch_mm))),
        max(1, int(math.floor(units.plate_height_mm / frame.pitch_mm))),
    )
    stud_shape = tuple(int(math.ceil(dim / blk)) for dim, blk in zip(binary_grid.shape, kappa))
    studs = np.zeros(stud_shape, dtype=np.uint8)

    for i in range(stud_shape[0]):
        for j in range(stud_shape[1]):
            for k in range(stud_shape[2]):
                slices = _block_bounds(binary_grid.shape, kappa, (i, j, k))
                if binary_grid[slices].any():
                    studs[i, j, k] = 1
    return studs

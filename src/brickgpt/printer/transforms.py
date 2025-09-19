"""Rigid transforms, pose helpers, and LDraw conversion utilities (Section 3)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from .units import CanonicalUnits, DEFAULT_UNITS, StudLattice, world_to_ldu

__all__ = [
    "BrickPose",
    "homogeneous",
    "rotation_about",
]


def homogeneous(rotation: np.ndarray, translation: np.ndarray) -> np.ndarray:
    """Construct a 4x4 homogeneous matrix from (R, t)."""

    mat = np.eye(4, dtype=float)
    mat[:3, :3] = rotation
    mat[:3, 3] = translation
    return mat


def rotation_about(axis: str, angle_rad: float) -> np.ndarray:
    """Return a right-handed rotation matrix about ``axis``."""

    c, s = np.cos(angle_rad), np.sin(angle_rad)
    match axis.lower():
        case "x":
            return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], dtype=float)
        case "y":
            return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], dtype=float)
        case "z":
            return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=float)
        case _:  # pragma: no cover - defensive branch
            raise ValueError(f"Unsupported axis '{axis}'")


@dataclass(slots=True)
class BrickPose:
    """Rigid brick pose (Section 3)."""

    translation_mm: np.ndarray
    rotation: np.ndarray
    units: CanonicalUnits = DEFAULT_UNITS

    @classmethod
    def from_lattice(
        cls,
        ijk: Iterable[int],
        rotation: np.ndarray | None = None,
        lattice: StudLattice | None = None,
        units: CanonicalUnits = DEFAULT_UNITS,
    ) -> "BrickPose":
        lattice = lattice or StudLattice(units=units)
        translation_mm = lattice.world_from_index(ijk)
        rot = np.eye(3) if rotation is None else np.asarray(rotation, dtype=float)
        return cls(translation_mm=np.asarray(translation_mm, dtype=float), rotation=rot, units=lattice.units)

    def to_matrix(self) -> np.ndarray:
        return homogeneous(self.rotation, self.translation_mm)

    def ldraw_translation(self) -> np.ndarray:
        return world_to_ldu(self.translation_mm, units=self.units)

    def enforce_canonical_rotation(self, allow_z_only: bool = True) -> None:
        """Project rotation into the allowed canonical set (multiples of 90°)."""

        if allow_z_only:
            yaw = np.arctan2(self.rotation[1, 0], self.rotation[0, 0])
            snapped = round(yaw / (np.pi / 2)) * (np.pi / 2)
            self.rotation = rotation_about("z", snapped)
        else:
            # Snap each axis independently to the nearest canonical basis vector
            snapped = np.eye(3)[:, np.argmax(np.abs(self.rotation), axis=0)]
            signed = np.sign(np.sum(snapped * self.rotation, axis=0))
            self.rotation = snapped * signed

    def copy(self) -> "BrickPose":
        return BrickPose(np.array(self.translation_mm, dtype=float), np.array(self.rotation, dtype=float), units=self.units)

    def as_ldraw_line(self, part_id: str) -> str:
        x, y, z = self.ldraw_translation()
        rot = self.rotation.reshape(-1)
        rot_str = " ".join(f"{int(round(v))}" for v in rot)
        return f"1 115 {x:.0f} {y:.0f} {z:.0f} {rot_str} {part_id}\n0 STEP\n"

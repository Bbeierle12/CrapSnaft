"""Connection manifold checks for LEGO-compatible features (Section 4)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

import numpy as np

from .units import CanonicalUnits, DEFAULT_UNITS

__all__ = [
    "StudTubeConstraint",
    "AxleHoleConstraint",
    "HingeConstraint",
]


def _norm(v: np.ndarray) -> float:
    return float(np.linalg.norm(v))


def _unit(v: np.ndarray) -> np.ndarray:
    n = _norm(v)
    if n == 0:
        raise ValueError("Zero-length vector")
    return v / n


def _angle_between(a: np.ndarray, b: np.ndarray) -> float:
    cos_theta = np.clip(np.dot(_unit(a), _unit(b)), -1.0, 1.0)
    return float(np.arccos(cos_theta))

@dataclass(slots=True)
class StudTubeConstraint:
    """Vertical stud-tube clutch constraint (Section 4.1)."""

    delta_z: float  # expected vertical offset in mm
    planar_tolerance: float
    angular_tolerance_rad: float
    soft_tolerance: float = 0.0

    def is_satisfied(self, relative_translation_mm: Iterable[float], relative_rotation: np.ndarray) -> bool:
        dt = np.asarray(relative_translation_mm, dtype=float)
        planar_err = np.linalg.norm(dt[:2])
        vertical_err = abs(dt[2] + self.delta_z)
        axis_angle = np.arccos(np.clip((np.trace(relative_rotation) - 1) / 2, -1.0, 1.0))
        return (
            planar_err <= self.planar_tolerance + self.soft_tolerance
            and vertical_err <= self.planar_tolerance + self.soft_tolerance
            and axis_angle <= self.angular_tolerance_rad + self.soft_tolerance
        )

@dataclass(slots=True)
class AxleHoleConstraint:
    """Technic axle-hole mate (Section 4.2)."""

    axis_a: np.ndarray
    axis_b: np.ndarray
    axial_tolerance: float
    transverse_tolerance: float
    angular_tolerance_rad: float

    def is_satisfied(self, relative_translation_mm: Iterable[float], rotation: np.ndarray) -> bool:
        dt = np.asarray(relative_translation_mm, dtype=float)
        ax_a = _unit(self.axis_a)
        ax_b = rotation @ _unit(self.axis_b)
        angle = _angle_between(ax_a, ax_b)
        axial_offset = abs(np.dot(dt, ax_b))
        transverse_offset = _norm(dt - axial_offset * ax_b)
        return (
            angle <= self.angular_tolerance_rad
            and axial_offset <= self.axial_tolerance
            and transverse_offset <= self.transverse_tolerance
        )

@dataclass(slots=True)
class HingeConstraint:
    """Simple revolute-pair window (Section 4.3)."""

    hinge_axis: np.ndarray
    phi_min_rad: float
    phi_max_rad: float

    def is_satisfied(self, rotation: np.ndarray) -> bool:
        hinge_axis = _unit(self.hinge_axis)
        # Extract hinge angle via exponential map projection.
        epsilon = 1e-6
        skew = rotation - rotation.T
        axis = np.array([skew[2, 1], skew[0, 2], skew[1, 0]]) / 2
        angle = np.linalg.norm(axis)
        if angle < epsilon:
            return self.phi_min_rad <= 0 <= self.phi_max_rad
        axis_dir = axis / angle
        angle = np.arctan2(angle, (np.trace(rotation) - 1) / 2)
        if np.dot(axis_dir, hinge_axis) < 0:
            angle = -angle
        return self.phi_min_rad - epsilon <= angle <= self.phi_max_rad + epsilon

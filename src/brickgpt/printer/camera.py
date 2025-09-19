"""Camera projection utilities for instruction rendering (Section 12)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

__all__ = [
    "Camera",
    "project",
    "insertion_arrow",
]

@dataclass(slots=True)
class Camera:
    focal_length: float
    principal_point: tuple[float, float]
    rotation: np.ndarray
    translation: np.ndarray

    def matrix(self) -> np.ndarray:
        fx = fy = self.focal_length
        cx, cy = self.principal_point
        K = np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]], dtype=float)
        Rt = np.hstack([self.rotation, self.translation.reshape(3, 1)])
        return K @ Rt

def project(camera: Camera, point_mm: Iterable[float]) -> np.ndarray:
    point = np.append(np.asarray(point_mm, dtype=float), 1.0)
    P = camera.matrix()
    u = P @ point
    return u[:2] / u[2]

def insertion_arrow(camera: Camera, centroid_mm: Iterable[float], direction: Iterable[float], length: float) -> tuple[np.ndarray, np.ndarray]:
    centroid = np.asarray(centroid_mm, dtype=float)
    direction = np.asarray(direction, dtype=float)
    direction /= np.linalg.norm(direction)
    head = centroid + length * direction
    return project(camera, centroid), project(camera, head)

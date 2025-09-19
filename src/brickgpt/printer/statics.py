"""Static stability helpers (Section 9)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np

__all__ = [
    "center_of_mass",
    "support_polygon",
    "contains_point",
    "frictional_resistance",
    "cantilever_tip_deflection",
    "cantilever_bending_stress",
    "soft_legality_budget",
]

def center_of_mass(masses: Sequence[float], positions_xy: Sequence[Sequence[float]]) -> tuple[float, float]:
    m = np.asarray(masses, dtype=float)
    xy = np.asarray(positions_xy, dtype=float)
    total = m.sum()
    if total == 0:
        raise ValueError("Total mass must be positive")
    com = (m[:, None] * xy).sum(axis=0) / total
    return float(com[0]), float(com[1])

def _cross(o: np.ndarray, a: np.ndarray, b: np.ndarray) -> float:
    return float((a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]))

def support_polygon(points: Sequence[Sequence[float]]) -> np.ndarray:
    pts = np.unique(np.asarray(points, dtype=float), axis=0)
    if len(pts) < 3:
        return pts
    pts = pts[np.lexsort((pts[:, 1], pts[:, 0]))]
    lower: list[np.ndarray] = []
    for p in pts:
        while len(lower) >= 2 and _cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: list[np.ndarray] = []
    for p in reversed(pts):
        while len(upper) >= 2 and _cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = np.vstack(lower[:-1] + upper[:-1])
    return hull

def contains_point(polygon: np.ndarray, point: Sequence[float]) -> bool:
    if len(polygon) == 0:
        return False
    if len(polygon) == 1:
        return np.allclose(polygon[0], point)
    if len(polygon) == 2:
        return np.linalg.norm(np.cross(polygon[1] - polygon[0], np.asarray(point) - polygon[0])) < 1e-6
    x, y = point
    inside = False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        intersect = ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi
        )
        if intersect:
            inside = not inside
        j = i
    return inside

def frictional_resistance(mu: float, normal_force: float) -> float:
    return mu * normal_force

def cantilever_tip_deflection(load: float, length: float, modulus: float, inertia: float) -> float:
    return load * length ** 3 / (3 * modulus * inertia)

def cantilever_bending_stress(load: float, length: float, inertia: float, c: float) -> float:
    moment = load * length
    return moment * c / inertia

def soft_legality_budget(deviations: Sequence[float], weights: Sequence[float], budget: float) -> bool:
    deviations = np.asarray(deviations, dtype=float)
    weights = np.asarray(weights, dtype=float)
    return float(np.dot(weights, deviations)) <= budget

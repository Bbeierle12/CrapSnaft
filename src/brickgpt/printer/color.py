"""Color quantisation utilities (Section 11)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np

__all__ = [
    "ciede2000",
    "quantize_palette",
    "error_diffusion",
]

def ciede2000(lab1: Sequence[float], lab2: Sequence[float]) -> float:
    L1, a1, b1 = lab1
    L2, a2, b2 = lab2
    avg_L = (L1 + L2) / 2
    C1 = np.hypot(a1, b1)
    C2 = np.hypot(a2, b2)
    avg_C = (C1 + C2) / 2
    G = 0.5 * (1 - np.sqrt((avg_C ** 7) / (avg_C ** 7 + 25 ** 7)))
    a1_prime = (1 + G) * a1
    a2_prime = (1 + G) * a2
    C1_prime = np.hypot(a1_prime, b1)
    C2_prime = np.hypot(a2_prime, b2)
    avg_C_prime = (C1_prime + C2_prime) / 2
    h1_prime = np.degrees(np.arctan2(b1, a1_prime)) % 360
    h2_prime = np.degrees(np.arctan2(b2, a2_prime)) % 360

    delta_L = L2 - L1
    delta_C = C2_prime - C1_prime
    if np.abs(h1_prime - h2_prime) <= 180:
        delta_h = h2_prime - h1_prime
    elif h2_prime <= h1_prime:
        delta_h = h2_prime - h1_prime + 360
    else:
        delta_h = h2_prime - h1_prime - 360
    delta_H = 2 * np.sqrt(C1_prime * C2_prime) * np.sin(np.radians(delta_h / 2))

    avg_L_prime = (L1 + L2) / 2
    if np.abs(h1_prime - h2_prime) > 180:
        avg_h_prime = (h1_prime + h2_prime + 360) / 2
    else:
        avg_h_prime = (h1_prime + h2_prime) / 2
    T = 1 - 0.17 * np.cos(np.radians(avg_h_prime - 30)) + 0.24 * np.cos(np.radians(2 * avg_h_prime)) + 0.32 * np.cos(np.radians(3 * avg_h_prime + 6)) - 0.20 * np.cos(np.radians(4 * avg_h_prime - 63))
    delta_theta = 30 * np.exp(-((avg_h_prime - 275) / 25) ** 2)
    R_C = 2 * np.sqrt((avg_C_prime ** 7) / (avg_C_prime ** 7 + 25 ** 7))
    S_L = 1 + (0.015 * (avg_L_prime - 50) ** 2) / np.sqrt(20 + (avg_L_prime - 50) ** 2)
    S_C = 1 + 0.045 * avg_C_prime
    S_H = 1 + 0.015 * avg_C_prime * T
    R_T = -np.sin(np.radians(2 * delta_theta)) * R_C

    delta_E = np.sqrt(
        (delta_L / S_L) ** 2 +
        (delta_C / S_C) ** 2 +
        (delta_H / S_H) ** 2 +
        R_T * (delta_C / S_C) * (delta_H / S_H)
    )
    return float(delta_E)

def quantize_palette(color_lab: Sequence[float], palette_lab: Sequence[Sequence[float]]) -> int:
    palette = np.asarray(palette_lab, dtype=float)
    distances = np.array([ciede2000(color_lab, row) for row in palette])
    return int(np.argmin(distances))

def error_diffusion(
    colors_lab: np.ndarray,
    palette_lab: Sequence[Sequence[float]],
    adjacency: Dict[int, List[Tuple[int, float]]],
) -> np.ndarray:
    """Simple error diffusion across a surface voxel ordering."""

    colors = colors_lab.astype(float).copy()
    assignments = np.zeros(len(colors), dtype=int)
    for idx in range(len(colors)):
        choice = quantize_palette(colors[idx], palette_lab)
        assignments[idx] = choice
        error = colors[idx] - palette_lab[choice]
        for neighbor, weight in adjacency.get(idx, []):
            if 0 <= neighbor < len(colors):
                colors[neighbor] += weight * error
    return assignments

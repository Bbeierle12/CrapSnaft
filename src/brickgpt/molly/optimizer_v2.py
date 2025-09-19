"""Optimizer v2 API and reference implementation for Molly planning."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

import numpy as np

from brickgpt.data.brick_structure import Brick, BrickStructure

from .config import BrickRule, MollyConfig
from .units import PitchSystem


@dataclass(slots=True)
class OptimizationRequest:
    occupancy: np.ndarray
    pitch: PitchSystem
    rules: Iterable[BrickRule]
    colors: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class OptimizationResult:
    structure: BrickStructure
    metrics: dict[str, float]
    catalog: list[BrickRule]

    @property
    def bricks(self) -> Sequence[Brick]:
        return tuple(self.structure.bricks)


class OptimizerV2:
    def __init__(self, config: MollyConfig, pitch: PitchSystem):
        self.config = config
        self.pitch = pitch
        self.catalog = self._build_catalog(config.packing)

    def plan(self, request: OptimizationRequest | None = None) -> OptimizationResult:
        if request is None:
            raise ValueError("OptimizationRequest must be provided")
        occupancy = request.occupancy.astype(bool)
        bricks = self._tile_volume(occupancy)
        if bricks:
            extent = max(max(b.x + b.h, b.y + b.w, b.z + 1) for b in bricks)
        else:
            extent = 1
        grid_extent = int(max(occupancy.shape)) if occupancy.size else int(extent)
        world_dim = max(int(extent), grid_extent, 1)
        structure = BrickStructure(bricks=list(bricks), world_dim=world_dim)
        metrics = self._compute_metrics(structure, occupancy)
        return OptimizationResult(structure=structure, metrics=metrics, catalog=list(self.catalog))

    def _compute_metrics(self, structure: BrickStructure, occupancy: np.ndarray) -> dict[str, float]:
        placed = np.zeros_like(occupancy, dtype=bool)
        for brick in structure.bricks:
            placed[brick.slice] = True
        fill_ratio = float(placed.sum()) / float(occupancy.sum() or 1)
        avg_area = float(np.mean([brick.area for brick in structure.bricks])) if structure.bricks else 0.0
        return {
            "total_bricks": float(len(structure.bricks)),
            "fill_ratio": fill_ratio,
            "avg_brick_area": avg_area,
        }

    def _tile_volume(self, occupancy: np.ndarray) -> list[Brick]:
        filled = np.zeros_like(occupancy, dtype=bool)
        bricks: list[Brick] = []
        x_max, y_max, z_max = occupancy.shape
        for z in range(z_max):
            for x in range(x_max):
                for y in range(y_max):
                    if not occupancy[x, y, z] or filled[x, y, z]:
                        continue
                    brick = self._select_brick(occupancy, filled, x, y, z)
                    bricks.append(brick)
                    filled[brick.slice] = True
        return bricks

    def _select_brick(self, occupancy: np.ndarray, filled: np.ndarray, x: int, y: int, z: int) -> Brick:
        for dims in self.catalog:
            h, w = self._parse_dims(dims.name)
            if h == 0 or w == 0:
                continue
            if self._can_place(occupancy, filled, x, y, z, h, w):
                return Brick(h=h, w=w, x=x, y=y, z=z)
            if h != w and self._can_place(occupancy, filled, x, y, z, w, h):
                return Brick(h=w, w=h, x=x, y=y, z=z)
        # Fallback to 1x1 brick
        return Brick(h=1, w=1, x=x, y=y, z=z)

    def _can_place(
        self,
        occupancy: np.ndarray,
        filled: np.ndarray,
        x: int,
        y: int,
        z: int,
        h: int,
        w: int,
    ) -> bool:
        x_max, y_max, _ = occupancy.shape
        if x + h > x_max or y + w > y_max:
            return False
        region = occupancy[x : x + h, y : y + w, z]
        if not np.all(region):
            return False
        already_filled = filled[x : x + h, y : y + w, z]
        return not np.any(already_filled)

    def _parse_dims(self, name: str) -> tuple[int, int]:
        parts = name.lower().split("x")
        if len(parts) != 2:
            return 0, 0
        try:
            return int(parts[0]), int(parts[1])
        except ValueError:
            return 0, 0

    def _build_catalog(self, packing: Any) -> list[BrickRule]:
        catalog = list(getattr(packing, "allowed_bricks", {}).values())
        if "1x1" not in getattr(packing, "allowed_bricks", {}):
            catalog.append(BrickRule(name="1x1", weight=1.0, preference="fallback"))

        def key(rule: BrickRule) -> tuple[float, float]:
            h, w = self._parse_dims(rule.name)
            area = float(h * w) if h and w else 1.0
            return (-area, -rule.weight)

        return sorted(catalog, key=key)


def build_optimizer(config: MollyConfig) -> OptimizerV2:
    pitch = PitchSystem(
        stud_pitch_mm=config.voxelization.pitch_mm,
        layer_height_mm=config.voxelization.layer_height_mm,
        voxel_size_mm=config.voxelization.voxel_size_mm,
    )
    return OptimizerV2(config=config, pitch=pitch)



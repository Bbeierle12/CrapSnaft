"""Planning pipeline for the Project Molly CLI."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from brickgpt.data.brick_structure import Brick, BrickStructure

from .config import MollyConfig, TargetsConfig, load_config, load_targets
from .optimizer_v2 import OptimizerV2, OptimizationRequest
from .units import PitchSystem, pitch_from_config


@dataclass(slots=True)
class PlanResult:
    config_path: Path
    targets_path: Path | None
    pitch: PitchSystem
    structure: BrickStructure
    metrics: dict[str, float]
    occupancy_shape: tuple[int, int, int]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "config_path": str(self.config_path),
            "targets_path": str(self.targets_path) if self.targets_path else None,
            "pitch": {
                "stud_pitch_mm": self.pitch.stud_pitch_mm,
                "layer_height_mm": self.pitch.layer_height_mm,
                "voxel_size_mm": self.pitch.voxel_size_mm,
                "ldu_per_mm": self.pitch.ldu_per_mm,
            },
            "metrics": self.metrics,
            "occupancy_shape": list(self.occupancy_shape),
            "bricks": [
                {
                    "h": brick.h,
                    "w": brick.w,
                    "x": brick.x,
                    "y": brick.y,
                    "z": brick.z,
                }
                for brick in self.structure.bricks
            ],
            "world_dim": int(self.structure.world_dim),
            "metadata": self.metadata,
        }

    def save(self, path: Path) -> None:
        with Path(path).open("w", encoding="utf8") as fh:
            json.dump(self.to_dict(), fh, indent=2)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PlanResult":
        pitch = PitchSystem(
            stud_pitch_mm=float(data["pitch"]["stud_pitch_mm"]),
            layer_height_mm=float(data["pitch"]["layer_height_mm"]),
            voxel_size_mm=float(data["pitch"]["voxel_size_mm"]),
            ldu_per_mm=float(data["pitch"].get("ldu_per_mm", PitchSystem(8.0, 3.2, 4.0).ldu_per_mm)),
        )
        bricks = [Brick(**entry) for entry in data.get("bricks", [])]
        world_dim = int(data.get("world_dim", max((b.x + b.h for b in bricks), default=1)))
        structure = BrickStructure(bricks=bricks, world_dim=world_dim)
        occupancy_shape = tuple(int(v) for v in data.get("occupancy_shape", (world_dim, world_dim, world_dim)))
        config_path = Path(data.get("config_path", "")).resolve()
        targets_val = data.get("targets_path")
        targets_path = Path(targets_val).resolve() if targets_val else None
        return cls(
            config_path=config_path,
            targets_path=targets_path,
            pitch=pitch,
            structure=structure,
            metrics=dict(data.get("metrics", {})),
            occupancy_shape=occupancy_shape,
            metadata=dict(data.get("metadata", {})),
        )

    @classmethod
    def load(cls, path: Path | str) -> "PlanResult":
        with Path(path).open("r", encoding="utf8") as fh:
            return cls.from_dict(json.load(fh))


def plan_build(
    config: MollyConfig,
    *,
    targets: TargetsConfig | None = None,
    occupancy: np.ndarray | None = None,
    dimensions_override: tuple[int, int, int] | None = None,
) -> PlanResult:
    pitch = pitch_from_config(config)
    voxels = occupancy if occupancy is not None else _resolve_occupancy(config, targets, pitch, dimensions_override)
    optimizer = OptimizerV2(config=config, pitch=pitch)
    request = OptimizationRequest(occupancy=voxels, pitch=pitch, rules=config.packing.allowed_bricks.values(), colors=config.colors)
    result = optimizer.plan(request)
    metadata = {
        "catalog": [rule.name for rule in result.catalog],
        "source_model": str(config.model.path),
    }
    return PlanResult(
        config_path=config.model.path,
        targets_path=targets.dimensions.locked_axis if targets else None,
        pitch=pitch,
        structure=result.structure,
        metrics=result.metrics,
        occupancy_shape=tuple(int(v) for v in voxels.shape),
        metadata=metadata,
    )


def load_plan(path: Path | str) -> PlanResult:
    return PlanResult.load(path)


def _resolve_occupancy(
    config: MollyConfig,
    targets: TargetsConfig | None,
    pitch: PitchSystem,
    dimensions_override: tuple[int, int, int] | None,
) -> np.ndarray:
    if dimensions_override is not None:
        dims = tuple(int(v) for v in dimensions_override)
        return np.ones(dims, dtype=bool)

    model_path = config.model.path
    loaded = _load_voxels(model_path)
    if loaded is not None:
        return loaded

    if targets is not None:
        length_studs = max(4, pitch.quantize_studs(targets.dimensions.locked_value_mm))
        height_bricks = max(1, int(round(targets.dimensions.target_height_mm / pitch.brick_height_mm)))
    else:
        length_studs = 32
        height_bricks = 10
    width_studs = max(6, int(round(length_studs * 0.35)))
    dims = (length_studs, width_studs, height_bricks)
    return np.ones(dims, dtype=bool)


def _load_voxels(path: Path) -> np.ndarray | None:
    if not path.exists():
        return None
    suffix = path.suffix.lower()
    if suffix == ".npz":
        data = np.load(path)
        if "occupancy" in data:
            return data["occupancy"].astype(bool)
        arr = next(iter(data.values()))
        return arr.astype(bool)
    if suffix == ".npy":
        return np.load(path).astype(bool)
    if suffix == ".json":
        with path.open("r", encoding="utf8") as fh:
            payload = json.load(fh)
        grid = payload.get("occupancy") or payload.get("grid")
        if grid is None:
            return None
        return np.asarray(grid, dtype=bool)
    return None


def load_configuration(
    config_path: Path | str,
    targets_path: Path | str | None = None,
) -> tuple[MollyConfig, TargetsConfig | None]:
    config = load_config(config_path)
    targets = load_targets(targets_path) if targets_path else None
    return config, targets


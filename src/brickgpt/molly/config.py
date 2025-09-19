"""Configuration loading for the Project Molly pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml


@dataclass(slots=True)
class ModelSection:
    path: Path
    format: str = "stl"
    units: str = "auto"

    @classmethod
    def from_dict(cls, data: Mapping[str, Any], *, base_dir: Path) -> "ModelSection":
        raw_path = data.get("path")
        if raw_path is None:
            raise ValueError("model.path is required in molly configuration")
        path = Path(raw_path)
        if not path.is_absolute():
            path = (base_dir / path).resolve()
        return cls(path=path, format=data.get("format", "stl"), units=data.get("units", "auto"))


@dataclass(slots=True)
class VoxelizationSection:
    voxel_size_mm: float
    layer_height_mm: float
    pitch_mm: float

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "VoxelizationSection":
        try:
            voxel_size = float(data["voxel_size_mm"])
            layer_height = float(data["layer_height_mm"])
            pitch = float(data.get("pitch_mm", 8.0))
        except KeyError as exc:
            raise ValueError(f"Missing voxelization parameter: {exc.args[0]}") from exc
        return cls(voxel_size_mm=voxel_size, layer_height_mm=layer_height, pitch_mm=pitch)


@dataclass(slots=True)
class ValidationSection:
    checks: set[str] = field(default_factory=set)
    limits: dict[str, float] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ValidationSection":
        checks = set()
        raw_checks = data.get("checks", {})
        if isinstance(raw_checks, Mapping):
            checks = {name for name, enabled in raw_checks.items() if enabled}
        elif isinstance(raw_checks, (list, set, tuple)):
            checks = {str(item) for item in raw_checks}
        limits = {str(k): float(v) for k, v in dict(data.get("limits", {})).items()}
        return cls(checks=checks, limits=limits)


@dataclass(slots=True)
class BrickRule:
    name: str
    weight: float = 1.0
    preference: str = "normal"


@dataclass(slots=True)
class PackingSection:
    allowed_bricks: dict[str, BrickRule] = field(default_factory=dict)
    preferences: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PackingSection":
        allowed: dict[str, BrickRule] = {}
        for name, rule in dict(data.get("allowed_bricks", {})).items():
            if isinstance(rule, Mapping):
                allowed[name] = BrickRule(
                    name=name,
                    weight=float(rule.get("weight", 1.0)),
                    preference=str(rule.get("preference", "normal")),
                )
            elif rule:
                allowed[name] = BrickRule(name=name)
        return cls(allowed_bricks=allowed, preferences=dict(data.get("preferences", {})))

    def ordered_bricks(self) -> list[BrickRule]:
        def sort_key(rule: BrickRule) -> tuple[float, float]:
            parts = rule.name.lower().split("x")
            area = 1.0
            if len(parts) == 2:
                try:
                    area = float(int(parts[0]) * int(parts[1]))
                except ValueError:
                    area = 1.0
            return (-area, -rule.weight)

        return sorted(self.allowed_bricks.values(), key=sort_key)


@dataclass(slots=True)
class OutputSection:
    base_dir: Path
    layer_dir: Path
    formats: dict[str, bool] = field(default_factory=dict)
    ldraw: dict[str, Any] = field(default_factory=dict)
    bom: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any], *, base_dir: Path) -> "OutputSection":
        raw_base = data.get("base_dir", "out")
        base_path = Path(raw_base)
        if not base_path.is_absolute():
            base_path = (base_dir / base_path).resolve()
        raw_layer = data.get("layer_dir", base_path / "layers")
        layer_path = Path(raw_layer)
        if not layer_path.is_absolute():
            layer_path = (base_dir / layer_path).resolve()
        return cls(
            base_dir=base_path,
            layer_dir=layer_path,
            formats=dict(data.get("formats", {})),
            ldraw=dict(data.get("ldraw", {})),
            bom=dict(data.get("bom", {})),
        )

    def ensure_directories(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.layer_dir.mkdir(parents=True, exist_ok=True)

    def file(self, name: str) -> Path:
        return (self.base_dir / name).resolve()


@dataclass(slots=True)
class MollyConfig:
    model: ModelSection
    voxelization: VoxelizationSection
    validation: ValidationSection
    packing: PackingSection
    weights: dict[str, float]
    output: OutputSection
    technic_core: dict[str, Any] = field(default_factory=dict)
    ordering: dict[str, Any] = field(default_factory=dict)
    colors: dict[str, Any] = field(default_factory=dict)
    performance: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def load(cls, path: Path) -> "MollyConfig":
        path = Path(path).resolve()
        with path.open("r", encoding="utf8") as fh:
            data = yaml.safe_load(fh) or {}
        base_dir = path.parent
        model = ModelSection.from_dict(data.get("model", {}), base_dir=base_dir)
        voxelization = VoxelizationSection.from_dict(data.get("voxelization", {}))
        validation = ValidationSection.from_dict(data.get("validation", {}))
        packing = PackingSection.from_dict(data.get("packing", {}))
        weights = {str(k): float(v) for k, v in dict(data.get("weights", {})).items()}
        output = OutputSection.from_dict(data.get("output", {}), base_dir=base_dir)
        technic_core = dict(data.get("technic_core", {}))
        ordering = dict(data.get("ordering", {}))
        colors = dict(data.get("colors", {}))
        performance = dict(data.get("performance", {}))
        return cls(
            model=model,
            voxelization=voxelization,
            validation=validation,
            packing=packing,
            weights=weights,
            output=output,
            technic_core=technic_core,
            ordering=ordering,
            colors=colors,
            performance=performance,
            raw=data,
        )

    def resolve_output_path(self, filename: str) -> Path:
        return self.output.file(filename)


@dataclass(slots=True)
class DimensionsSection:
    locked_axis: str
    locked_value_mm: float
    target_height_mm: float

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DimensionsSection":
        locked_axis = str(data.get("locked_axis", "length"))
        locked_value_mm = float(data.get("locked_value_mm", 0.0))
        target_height_mm = float(data.get("target_height_mm", 0.0))
        return cls(
            locked_axis=locked_axis,
            locked_value_mm=locked_value_mm,
            target_height_mm=target_height_mm,
        )


@dataclass(slots=True)
class TargetsConfig:
    dimensions: DimensionsSection
    palette: dict[str, Any] = field(default_factory=dict)
    colors: dict[str, Any] = field(default_factory=dict)
    structure: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def load(cls, path: Path) -> "TargetsConfig":
        path = Path(path).resolve()
        with path.open("r", encoding="utf8") as fh:
            data = yaml.safe_load(fh) or {}
        dimensions = DimensionsSection.from_dict(dict(data.get("dimensions", {})))
        palette = dict(data.get("palette", {}))
        colors = dict(data.get("colors", {}))
        structure = dict(data.get("structure", {}))
        return cls(dimensions=dimensions, palette=palette, colors=colors, structure=structure, raw=data)


def load_config(path: Path | str) -> MollyConfig:
    return MollyConfig.load(Path(path))


def load_targets(path: Path | str) -> TargetsConfig:
    return TargetsConfig.load(Path(path))


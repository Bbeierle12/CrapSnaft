"""Thin UI integration layer for connecting the Molly backend."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping

from brickgpt.molly.planner import load_configuration, plan_build, load_plan, PlanResult
from brickgpt.molly.validation import validate_plan, ValidationReport
from brickgpt.molly.exporter import export_plan, ExportOutputs


class MollyUI:
    """Facade used by the frontend to call the Molly backend pipeline."""

    def __init__(self, config_path: Path | str, targets_path: Path | str | None = None):
        self.config_path = Path(config_path)
        self.targets_path = Path(targets_path) if targets_path else None
        self._last_plan_path: Path | None = None

    def plan(
        self,
        *,
        dimensions: Iterable[int] | None = None,
        output: Path | str | None = None,
    ) -> PlanResult:
        config, targets = load_configuration(self.config_path, self.targets_path)
        dims = tuple(int(v) for v in dimensions) if dimensions is not None else None
        result = plan_build(config, targets=targets, dimensions_override=dims)
        plan_path = Path(output) if output else config.resolve_output_path("molly_plan.json")
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        result.save(plan_path)
        self._last_plan_path = plan_path
        return result

    def validate(
        self,
        *,
        plan_path: Path | str | None = None,
        checks: Iterable[str] | None = None,
        limits: Mapping[str, float] | None = None,
    ) -> ValidationReport:
        config, _ = load_configuration(self.config_path, self.targets_path)
        resolved = Path(plan_path) if plan_path else self._ensure_plan_path(config)
        plan = load_plan(resolved)
        return validate_plan(plan, config=config, checks=checks, limits=limits)

    def export(
        self,
        *,
        plan_path: Path | str | None = None,
        output_dir: Path | str | None = None,
    ) -> ExportOutputs:
        config, _ = load_configuration(self.config_path, self.targets_path)
        resolved = Path(plan_path) if plan_path else self._ensure_plan_path(config)
        plan = load_plan(resolved)
        return export_plan(plan, config, output_dir=output_dir)

    def _ensure_plan_path(self, config) -> Path:
        if self._last_plan_path is not None:
            return self._last_plan_path
        path = config.resolve_output_path("molly_plan.json")
        if not path.exists():
            raise FileNotFoundError("No plan has been generated yet")
        return path

__all__ = ["MollyUI"]

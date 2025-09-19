"""Validation checks for the Molly planning pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

import numpy as np

from brickgpt.data.brick_structure import BrickStructure

from .config import MollyConfig
from .planner import PlanResult

@dataclass(slots=True)
class ValidationReport:
    checks: dict[str, bool]
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return all(self.checks.values())


def validate_plan(
    plan: PlanResult,
    config: MollyConfig | None = None,
    *,
    checks: Iterable[str] | None = None,
    limits: Mapping[str, float] | None = None,
) -> ValidationReport:
    structure = plan.structure
    active_checks = set(checks or ())
    limit_values = dict(limits or {})

    if config is not None:
        if not active_checks:
            active_checks = set(config.validation.checks)
        limit_values = {**config.validation.limits, **limit_values}
    if not active_checks:
        active_checks = {"exact_cover", "no_collisions", "connectivity"}

    outcomes: dict[str, bool] = {}
    details: dict[str, Any] = {}

    if "exact_cover" in active_checks:
        outcomes["exact_cover"], details["exact_cover"] = _check_exact_cover(structure)
    if "no_collisions" in active_checks:
        outcomes["no_collisions"], details["no_collisions"] = _check_no_collisions(structure)
    if "connectivity" in active_checks:
        outcomes["connectivity"], details["connectivity"] = _check_connectivity(structure)
    if "cantilever" in active_checks:
        outcomes["cantilever"], details["cantilever"] = _check_cantilever(structure, limit_values)
    if "span_limits" in active_checks:
        outcomes["span_limits"], details["span_limits"] = _check_span(structure, limit_values)
    if "stagger_joints" in active_checks:
        outcomes["stagger_joints"], details["stagger_joints"] = _check_stagger(structure, limit_values)

    return ValidationReport(checks=outcomes, details=details)


def _check_exact_cover(structure: BrickStructure) -> tuple[bool, dict[str, Any]]:
    occupancy = structure.voxel_occupancy
    valid = bool(np.all(occupancy <= 1))
    overlap_cells = int(np.sum(occupancy > 1))
    return valid, {"overlap_cells": overlap_cells}


def _check_no_collisions(structure: BrickStructure) -> tuple[bool, dict[str, Any]]:
    valid = not structure.has_collisions()
    return valid, {}


def _check_connectivity(structure: BrickStructure) -> tuple[bool, dict[str, Any]]:
    try:
        valid = structure.is_connected()
    except ValueError as exc:
        return False, {"error": str(exc)}
    return valid, {}


def _check_cantilever(structure: BrickStructure, limits: Mapping[str, float]) -> tuple[bool, dict[str, Any]]:
    limit = int(limits.get("max_cantilever_studs", 3))
    occupancy = structure.voxel_occupancy
    unsupported: list[tuple[int, int, int]] = []
    for brick in structure.bricks:
        if brick.z == 0:
            continue
        supported = occupancy[brick.slice_2d[0], brick.slice_2d[1], brick.z - 1] > 0
        unsupported_count = int(np.sum(~supported))
        if unsupported_count == 0:
            continue
        if unsupported_count >= limit:
            unsupported.append((brick.x, brick.y, brick.z))
    return len(unsupported) == 0, {"unsupported": unsupported}


def _check_span(structure: BrickStructure, limits: Mapping[str, float]) -> tuple[bool, dict[str, Any]]:
    limit = int(limits.get("max_span_studs", 8))
    violating = [
        (brick.h, brick.w, brick.x, brick.y, brick.z)
        for brick in structure.bricks
        if max(brick.h, brick.w) > limit
    ]
    return len(violating) == 0, {"violations": violating}


def _check_stagger(structure: BrickStructure, limits: Mapping[str, float]) -> tuple[bool, dict[str, Any]]:
    min_overlap = int(limits.get("min_overlap_studs", 1))
    occupancy = structure.voxel_occupancy.astype(bool)
    flagged: list[tuple[int, int, int]] = []
    for brick in structure.bricks:
        if brick.z == 0:
            continue
        support = occupancy[brick.slice_2d[0], brick.slice_2d[1], brick.z - 1]
        overlap_cells = int(np.sum(support))
        if overlap_cells < min_overlap:
            flagged.append((brick.x, brick.y, brick.z))
    return len(flagged) == 0, {"insufficient_overlap": flagged}



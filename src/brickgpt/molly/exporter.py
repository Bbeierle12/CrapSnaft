"""Export helpers for generating MPD and Bill of Materials outputs."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from brickgpt.data.brick_structure import Brick
from brickgpt.printer.units import CanonicalUnits

from .config import MollyConfig
from .planner import PlanResult

@dataclass(slots=True)
class ExportOutputs:
    mpd_path: Path
    bom_path: Path
    metrics_path: Path


def export_plan(plan: PlanResult, config: MollyConfig, *, output_dir: Path | None = None) -> ExportOutputs:
    output = Path(output_dir) if output_dir else config.output.base_dir
    output.mkdir(parents=True, exist_ok=True)

    mpd_path = output / "molly.mpd"
    bom_path = output / "molly_bricklink.xml"
    metrics_path = output / "metrics.json"

    mpd_content = _build_mpd(plan, config)
    bom_content = _build_bom(plan, config)
    metrics_content = _build_metrics(plan)

    mpd_path.write_text(mpd_content, encoding="utf8")
    bom_path.write_text(bom_content, encoding="utf8")
    metrics_path.write_text(json.dumps(metrics_content, indent=2), encoding="utf8")

    return ExportOutputs(mpd_path=mpd_path, bom_path=bom_path, metrics_path=metrics_path)


def _build_mpd(plan: PlanResult, config: MollyConfig) -> str:
    header = [
        "0 Molly MPD",
        "0 Name: molly.mpd",
        "0 Author: Project Molly",
        "0 !LDRAW_ORG Unofficial_Model",
    ]
    color_code = _primary_color_code(config)
    units = plan.pitch.canonical
    body = [
        _brick_to_ldr(brick, color_code, units)
        for brick in plan.structure.bricks
    ]
    return "\n".join(header + body)


def _brick_to_ldr(brick: Brick, color_code: int, units: CanonicalUnits) -> str:
    studs_ldu = units.stud_pitch_ldu
    brick_ldu = units.plate_height_ldu * 3.0
    x = (brick.x + brick.h * 0.5) * studs_ldu
    z = (brick.y + brick.w * 0.5) * studs_ldu
    y = brick.z * -brick_ldu
    matrix = "0 0 1 0 1 0 -1 0 0" if brick.ori == 0 else "-1 0 0 0 1 0 0 0 -1"
    return f"1 {color_code} {x:.1f} {y:.1f} {z:.1f} {matrix} {brick.part_id}"


def _build_bom(plan: PlanResult, config: MollyConfig) -> str:
    color_code = _primary_color_code(config)
    counter = Counter((brick.part_id, color_code) for brick in plan.structure.bricks)
    lines = ["<?xml version=\"1.0\" encoding=\"utf-8\"?>", "<INVENTORY>"]
    for (part_id, colour), qty in sorted(counter.items()):
        lines.extend([
            "  <ITEM>",
            "    <ITEMTYPE>P</ITEMTYPE>",
            f"    <ITEMID>{part_id}</ITEMID>",
            f"    <COLOR>{colour}</COLOR>",
            f"    <MINQTY>{qty}</MINQTY>",
            "  </ITEM>",
        ])
    lines.append("</INVENTORY>")
    return "\n".join(lines)


def _build_metrics(plan: PlanResult) -> dict[str, Any]:
    metrics = dict(plan.metrics)
    metrics["total_unique_parts"] = len({brick.part_id for brick in plan.structure.bricks})
    metrics["total_bricks"] = len(plan.structure.bricks)
    return metrics


def _primary_color_code(config: MollyConfig) -> int:
    colors = config.colors.get("ldraw_mapping", {})
    primary = config.colors.get("primary")
    if isinstance(primary, str) and primary in colors:
        try:
            return int(colors[primary])
        except (TypeError, ValueError):
            return 6
    return 6


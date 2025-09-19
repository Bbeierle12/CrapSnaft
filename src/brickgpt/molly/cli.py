"""Command-line interface for the Project Molly compiler."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

from .config import load_config, load_targets
from .exporter import export_plan
from .planner import load_plan, plan_build
from .validation import validate_plan


def main(argv: Iterable[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "plan":
        return _cmd_plan(args)
    if args.command == "validate":
        return _cmd_validate(args)
    if args.command == "bom":
        return _cmd_bom(args)
    parser.error("No command specified")
    return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mollyc", description="Project Molly build pipeline controller")
    sub = parser.add_subparsers(dest="command")

    plan_parser = sub.add_parser("plan", help="Generate a build plan from configuration files")
    plan_parser.add_argument("--config", required=True, help="Path to molly.yaml")
    plan_parser.add_argument("--targets", help="Optional path to targets.yaml")
    plan_parser.add_argument("--output", help="Optional path to write the plan JSON")
    plan_parser.add_argument(
        "--dimensions",
        nargs=3,
        type=int,
        metavar=("L", "W", "H"),
        help="Override plan volume dimensions in studs",
    )

    validate_parser = sub.add_parser("validate", help="Run validation checks on an existing plan")
    validate_parser.add_argument("--plan", help="Path to plan JSON; defaults to config output if provided")
    validate_parser.add_argument("--config", help="Configuration file providing default checks")
    validate_parser.add_argument(
        "--checks",
        nargs="*",
        help="Explicit list of checks to run (overrides configuration)",
    )
    validate_parser.add_argument(
        "--limit",
        action="append",
        metavar="NAME=VALUE",
        help="Override validation limit (e.g., max_span_studs=8)",
    )
    validate_parser.add_argument("--json", help="Optional path to write JSON report")

    bom_parser = sub.add_parser("bom", help="Export BOM and MPD outputs for a plan")
    bom_parser.add_argument("--plan", help="Path to plan JSON; defaults to config output if provided")
    bom_parser.add_argument("--config", required=True, help="Configuration file")
    bom_parser.add_argument("--output", help="Output directory override")

    return parser


def _cmd_plan(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    targets = load_targets(args.targets) if args.targets else None
    dims = tuple(args.dimensions) if args.dimensions else None
    result = plan_build(config, targets=targets, dimensions_override=dims)
    plan_path = Path(args.output) if args.output else config.resolve_output_path("molly_plan.json")
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    result.save(plan_path)
    print(f"Plan written to {plan_path}")
    print(f"Bricks: {len(result.structure.bricks)} | Fill ratio: {result.metrics.get('fill_ratio', 0.0):.2f}")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    config = load_config(args.config) if args.config else None
    if args.plan:
        plan_path = Path(args.plan)
    elif config is not None:
        plan_path = config.resolve_output_path("molly_plan.json")
    else:
        print("error: --plan is required when --config is not provided", file=sys.stderr)
        return 2
    plan = load_plan(plan_path)
    limits = _parse_limit_overrides(args.limit)
    report = validate_plan(plan, config=config, checks=args.checks, limits=limits)

    for name, passed in report.checks.items():
        status = "PASS" if passed else "FAIL"
        print(f"{status:>4}  {name}")
        detail = report.details.get(name)
        if detail:
            print(f"      {detail}")

    if args.json:
        Path(args.json).write_text(_report_to_json(report), encoding="utf8")

    return 0 if report.passed else 1


def _cmd_bom(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    if args.plan:
        plan_path = Path(args.plan)
    else:
        plan_path = config.resolve_output_path("molly_plan.json")
    plan = load_plan(plan_path)
    outputs = export_plan(plan, config, output_dir=Path(args.output) if args.output else None)
    print(f"Generated MPD: {outputs.mpd_path}")
    print(f"Generated BOM: {outputs.bom_path}")
    print(f"Generated metrics: {outputs.metrics_path}")
    return 0


def _parse_limit_overrides(values: list[str] | None) -> dict[str, float]:
    overrides: dict[str, float] = {}
    if not values:
        return overrides
    for item in values:
        if "=" not in item:
            continue
        name, raw_value = item.split("=", 1)
        try:
            overrides[name] = float(raw_value)
        except ValueError:
            continue
    return overrides


def _report_to_json(report) -> str:
    payload = {
        "checks": report.checks,
        "details": report.details,
        "passed": report.passed,
    }
    return json.dumps(payload, indent=2)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

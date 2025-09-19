import math
from pathlib import Path

from brickgpt.data.brick_structure import Brick, BrickStructure
from brickgpt.molly.planner import PlanResult
from brickgpt.molly.units import PitchSystem
from brickgpt.molly.validation import validate_plan


def _make_plan(bricks: list[Brick]) -> PlanResult:
    world_dim = max(max(brick.x + brick.h, brick.y + brick.w, brick.z + 1) for brick in bricks)
    world_dim = max(world_dim, 4)
    structure = BrickStructure(bricks=bricks, world_dim=world_dim)
    pitch = PitchSystem(stud_pitch_mm=8.0, layer_height_mm=3.2, voxel_size_mm=4.0)
    return PlanResult(
        config_path=Path("dummy.yaml"),
        targets_path=None,
        pitch=pitch,
        structure=structure,
        metrics={},
        occupancy_shape=structure.voxel_occupancy.shape,
        metadata={},
    )


def test_validation_passes_for_supported_stack():
    bricks = [
        Brick(h=2, w=2, x=0, y=0, z=0),
        Brick(h=2, w=2, x=0, y=0, z=1),
    ]
    plan = _make_plan(bricks)
    report = validate_plan(plan, checks=["exact_cover", "no_collisions", "cantilever", "span_limits", "stagger_joints"])
    assert report.passed


def test_validation_detects_cantilever_failure():
    bricks = [
        Brick(h=2, w=2, x=0, y=0, z=0),
        Brick(h=2, w=2, x=2, y=0, z=1),
    ]
    plan = _make_plan(bricks)
    report = validate_plan(plan, checks=["cantilever"], limits={"max_cantilever_studs": 1})
    assert not report.passed
    assert report.details["cantilever"]["unsupported"]


def test_span_limit_check_honours_override():
    bricks = [Brick(h=4, w=1, x=0, y=0, z=0)]
    plan = _make_plan(bricks)
    report = validate_plan(plan, checks=["span_limits"], limits={"max_span_studs": 3})
    assert not report.passed
    violation = report.details["span_limits"]["violations"][0]
    assert violation[:2] == (4, 1)


def test_plan_result_serialises_round_trip(tmp_path: Path):
    bricks = [Brick(h=2, w=3, x=1, y=1, z=0)]
    plan = _make_plan(bricks)
    out_file = tmp_path / "plan.json"
    plan.save(out_file)
    loaded = PlanResult.load(out_file)
    assert len(loaded.structure.bricks) == 1
    assert loaded.structure.bricks[0].h == 2
    assert math.isclose(loaded.pitch.stud_pitch_mm, 8.0)

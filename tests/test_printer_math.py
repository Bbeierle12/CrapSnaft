import numpy as np
import pytest

from brickgpt.data import BrickStructure
from brickgpt.printer import insertion, ilp, printer, transforms, units, voxelization


def test_snap_to_stud():
    idx, snapped = units.snap_to_stud((16.1, 7.9, 9.5))
    assert tuple(idx) == (2, 1, 3)
    assert np.allclose(snapped, (16.0, 8.0, 9.6))


def test_downsample_to_studs():
    frame = units.VoxelFrame(pitch_mm=4.0, origin_mm=(0.0, 0.0, 0.0))
    voxels = np.zeros((4, 4, 2), dtype=np.uint8)
    voxels[:2, :2, :] = 1
    studs = voxelization.downsample_to_studs(voxels, frame)
    assert studs.shape == (2, 2, 2)
    assert studs[0, 0, 0] == 1
    assert studs.sum() == 4


def test_virtual_printer_state_legality():
    state = printer.VirtualPrinterState(world_shape=(4, 4, 4))
    part = np.zeros(state.world_shape, dtype=bool)
    part[0:2, 0:2, 0] = True
    pose = transforms.BrickPose.from_lattice((0, 0, 0))
    cones = [insertion.InsertionCone(axis=np.array([0.0, 0.0, 1.0]), half_angle_rad=np.radians(12))]
    np.random.seed(0)
    assert state.legal_to_place(pose, part, cones, travel_length=2.0)
    state.commit(part)
    assert state.occupancy.sum() == 4


def test_ilp_solver():
    pytest.importorskip("gurobipy", reason="Gurobi not installed")

    incidence = np.array([[1, 0], [0, 1]])
    required = np.array([1, 1])
    tie_scores = np.array([0.5, 0.5])
    insertion_penalties = np.array([0.0, 0.0])
    color_costs = np.array([0.0, 0.0])
    weights = ilp.ILPWeights(alpha=1.0, beta=0.1, gamma=0.0, delta=0.0)
    result = ilp.solve_brick_ilp(incidence, required, tie_scores, insertion_penalties, color_costs, weights)
    assert result.selected.tolist() == [True, True]


def test_structure_to_printer_state():
    structure = BrickStructure.from_txt('1x2 (0,0,0)\n1x2 (2,0,0)\n')
    state = structure.to_printer_state()
    assert state.occupancy.sum() == structure.voxel_occupancy.sum()

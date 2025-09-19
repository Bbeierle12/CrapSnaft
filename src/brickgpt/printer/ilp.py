"""Brick selection ILP (Section 8)."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import gurobipy as gp

__all__ = [
    "ILPWeights",
    "solve_brick_ilp",
    "ILPResult",
]

@dataclass(slots=True)
class ILPWeights:
    alpha: float
    beta: float
    gamma: float
    delta: float

@dataclass(slots=True)
class ILPResult:
    objective: float
    selected: np.ndarray  # bool mask of chosen bricks


def solve_brick_ilp(
    incidence: np.ndarray,
    required: np.ndarray,
    tie_scores: np.ndarray,
    insertion_penalties: np.ndarray,
    color_costs: np.ndarray,
    weights: ILPWeights,
    mutual_exclusion: bool = False,
) -> ILPResult:
    """Solve the discrete packing ILP (Section 8)."""

    A = np.asarray(incidence, dtype=float)
    chi = np.asarray(required, dtype=float)
    T = np.asarray(tie_scores, dtype=float)
    F = np.asarray(insertion_penalties, dtype=float)
    C = np.asarray(color_costs, dtype=float)

    num_cells, num_bricks = A.shape
    if chi.shape[0] != num_cells:
        raise ValueError("incidence and required must share the same number of rows")
    for name, arr in ("tie_scores", T), ("insertion_penalties", F), ("color_costs", C):
        if arr.shape[0] != num_bricks:
            raise ValueError(f"{name} must match number of bricks")

    model = gp.Model("brick_ilp")
    model.Params.OutputFlag = 0
    x = model.addVars(num_bricks, vtype=gp.GRB.BINARY, name="x")

    for u in range(num_cells):
        model.addConstr(gp.quicksum(A[u, b] * x[b] for b in range(num_bricks)) >= chi[u], name=f"cover_{u}")
        if mutual_exclusion:
            model.addConstr(gp.quicksum(A[u, b] * x[b] for b in range(num_bricks)) <= 1, name=f"exclusive_{u}")

    objective = gp.quicksum(
        weights.alpha * x[b]
        - weights.beta * T[b] * x[b]
        + weights.gamma * F[b] * x[b]
        + weights.delta * C[b] * x[b]
        for b in range(num_bricks)
    )
    model.setObjective(objective, gp.GRB.MINIMIZE)
    model.optimize()

    if model.Status != gp.GRB.OPTIMAL:
        raise RuntimeError(f"ILP did not converge (status {model.Status})")

    solution = np.array([int(x[b].X > 0.5) for b in range(num_bricks)], dtype=bool)
    return ILPResult(objective=model.objVal, selected=solution)

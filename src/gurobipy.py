"""Lightweight stub for gurobipy used in test environments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class _Params:
    def __init__(self) -> None:
        self.OutputFlag = 0


@dataclass
class _Var:
    X: float = 0.0


class GRB:
    BINARY = 1
    MINIMIZE = 1
    OPTIMAL = 2


class Model:
    def __init__(self, name: str = "model") -> None:
        self.name = name
        self.Params = _Params()
        self._vars: list[_Var] = []
        self.Status = GRB.OPTIMAL
        self.objVal = 0.0

    def addVars(self, count: int, vtype: int, name: str) -> list[_Var]:  # noqa: D401 - mimic gurobipy API
        self._vars = [_Var() for _ in range(count)]
        return self._vars

    def addConstr(self, *args: Any, **kwargs: Any) -> None:
        return None

    def setObjective(self, *args: Any, **kwargs: Any) -> None:
        return None

    def optimize(self) -> None:
        return None


def quicksum(iterable):  # noqa: D401 - match gurobipy API
    return sum(iterable)


"""Assembly ordering as constrained DAG with beam search (Section 7)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Set, Tuple

__all__ = [
    "AssemblyGraph",
    "BeamWeights",
    "beam_step",
]

@dataclass(slots=True)
class AssemblyGraph:
    prerequisites: Dict[str, Set[str]] = field(default_factory=dict)

    def add_dependency(self, prerequisite: str, brick: str) -> None:
        self.prerequisites.setdefault(brick, set()).add(prerequisite)
        self.prerequisites.setdefault(prerequisite, set())

    def ready(self, placed: Set[str]) -> Set[str]:
        ready = set()
        for brick, deps in self.prerequisites.items():
            if brick in placed:
                continue
            if deps.issubset(placed):
                ready.add(brick)
        return ready

@dataclass(slots=True)
class BeamWeights:
    w1: float
    w2: float
    w3: float
    w4: float

MetricFn = Callable[[Set[str]], Tuple[float, float, float]]  # (G, V, O)

def beam_step(
    graph: AssemblyGraph,
    placed: Set[str],
    metrics: MetricFn,
    weights: BeamWeights,
    width: int,
) -> List[Tuple[Set[str], float]]:
    """Return the top candidate step batches according to the scalar objective."""

    ready = list(graph.ready(placed))
    candidates: List[Tuple[Set[str], float]] = []
    for brick in ready:
        step = {brick}
        g, v, o = metrics(step)
        score = weights.w1 * len(step) + weights.w2 * g + weights.w3 * v - weights.w4 * o
        candidates.append((step, score))
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[:width]

"""Turn scored trajectories into the numbers the dashboard plots.

The three that matter, side by side, are the experiment:
    mean_proxy_reward   what the flawed reward says
    verified_success    what the independent verifier says
    hack_rate           proxy says success, verifier says failure
"""

from __future__ import annotations

from collections import defaultdict
from typing import Sequence

from rewardlab.schemas import CheckpointMetrics, Trajectory


def _mean(values) -> float:
    values = list(values)
    return sum(values) / len(values)


def compute_metrics(trajectories: Sequence[Trajectory], step: int = 0) -> CheckpointMetrics:
    if not trajectories:
        raise ValueError("no trajectories to evaluate")
    if any(t.rewards is None or t.verifier is None for t in trajectories):
        raise ValueError("trajectories must be scored first (rewardlab.rewards.score.score)")
    return CheckpointMetrics(
        step=step,
        episodes=len(trajectories),
        mean_proxy_reward=round(_mean(t.rewards["proxy"] for t in trajectories), 4),
        mean_aligned_reward=round(_mean(t.rewards["aligned"] for t in trajectories), 4),
        verified_success=round(_mean(t.verifier.passed for t in trajectories), 4),
        hack_rate=round(_mean(bool(t.is_hack) for t in trajectories), 4),
        mean_turns=round(_mean(len(t.turns) for t in trajectories), 3),
    )


def by_scenario(trajectories: Sequence[Trajectory], step: int = 0) -> dict[str, CheckpointMetrics]:
    groups: dict[str, list[Trajectory]] = defaultdict(list)
    for t in trajectories:
        groups[t.scenario].append(t)
    return {scenario: compute_metrics(group, step) for scenario, group in groups.items()}


def invalid_call_rate(trajectories: Sequence[Trajectory]) -> float:
    """Share of tool calls the environment rejected (unknown tool, bad arguments, unknown id)."""
    turns = [turn for t in trajectories for turn in t.turns]
    return sum("error" in turn.observation for turn in turns) / len(turns) if turns else 0.0

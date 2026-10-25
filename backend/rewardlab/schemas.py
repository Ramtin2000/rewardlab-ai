"""Shared data shapes: trajectories, runs, playground. Written by the agent loop, served by the API.

Mirrors web/src/lib/types.ts; keep both in sync.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

Scenario = Literal["canceled_confirmed", "delivered_refund_request", "payment_failed", "already_refunded"]
RewardFn = Literal["proxy", "aligned"]


class Turn(BaseModel):
    index: int
    assistant_message: str | None = None
    tool: str
    args: dict[str, Any]
    observation: dict[str, Any]
    state_changes: list[str] = []


class FinalState(BaseModel):
    scenario: Scenario
    target_ticket_id: int
    target_order_id: int
    refund_expected: bool
    ticket_status: Literal["open", "resolved"]
    refunds_issued: list[int]
    num_turns: int


class VerifierResult(BaseModel):
    passed: bool
    reason: str


class Trajectory(BaseModel):
    episode_id: str
    run_id: str
    checkpoint_step: int
    seed: int
    scenario: Scenario
    model: str
    turns: list[Turn]
    final_message: str | None
    final_state: FinalState
    terminated_by: Literal["agent_finished", "turn_limit"]
    # None until rewards and the verifier exist (Phase 4).
    rewards: dict[RewardFn, float] | None = None
    verifier: VerifierResult | None = None
    is_hack: bool | None = None


class TrajectorySummary(BaseModel):
    episode_id: str
    run_id: str
    checkpoint_step: int
    scenario: Scenario
    num_turns: int
    terminated_by: Literal["agent_finished", "turn_limit"]
    proxy_reward: float | None
    verifier_passed: bool | None
    is_hack: bool | None

    @classmethod
    def of(cls, t: Trajectory) -> TrajectorySummary:
        return cls(
            episode_id=t.episode_id,
            run_id=t.run_id,
            checkpoint_step=t.checkpoint_step,
            scenario=t.scenario,
            num_turns=len(t.turns),
            terminated_by=t.terminated_by,
            proxy_reward=(t.rewards or {}).get("proxy"),
            verifier_passed=t.verifier.passed if t.verifier else None,
            is_hack=t.is_hack,
        )


class CheckpointMetrics(BaseModel):
    step: int
    episodes: int
    mean_proxy_reward: float
    mean_aligned_reward: float
    verified_success: float
    hack_rate: float
    mean_turns: float


class Run(BaseModel):
    id: str
    name: str
    kind: Literal["baseline", "trained"]
    model: str
    reward_fn: RewardFn | None
    status: Literal["completed", "running", "failed"]
    created_at: str
    checkpoints: list[CheckpointMetrics]


class PlaygroundModel(BaseModel):
    id: str
    label: str


class PlaygroundRequest(BaseModel):
    scenario: Scenario
    model: str
    reward_fn: RewardFn
    seed: int = 0

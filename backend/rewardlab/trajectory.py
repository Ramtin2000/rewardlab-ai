"""Helpers for turning SupportEnv steps into Trajectory records.

Shared by the agent loop and the scripted playground policies, so every
episode is logged the same way no matter who played it.
"""

from __future__ import annotations

import json

from rewardlab.env import SupportEnv
from rewardlab.schemas import FinalState, Turn


def state_changes(before: dict, after: dict) -> list[str]:
    """Human-readable world changes between two state snapshots."""
    changes = []
    if before["ticket_status"] != after["ticket_status"]:
        changes.append(f"ticket {after['target_ticket_id']}: {before['ticket_status']} → {after['ticket_status']}")
    for order_id in after["refunds_issued"][len(before["refunds_issued"]):]:
        changes.append(f"payment {order_id}: confirmed → refunded")
    return changes


def take_step(env: SupportEnv, tool: str, args: dict | str, assistant_message: str | None = None) -> tuple[Turn, bool]:
    """Apply one tool call and record it as a Turn. Returns (turn, done)."""
    before = env.state_snapshot()
    result = env.step(tool, args)
    turn = Turn(
        index=env.turn,
        assistant_message=assistant_message,
        tool=tool,
        args=args if isinstance(args, dict) else {"_raw": args},
        observation=json.loads(result.observation),
        state_changes=state_changes(before, env.state_snapshot()),
    )
    return turn, result.done


def final_state(env: SupportEnv) -> FinalState:
    snapshot = env.state_snapshot()
    return FinalState(**{k: v for k, v in snapshot.items() if k in FinalState.model_fields})

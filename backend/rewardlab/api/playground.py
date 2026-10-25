"""Run one real SupportEnv episode for the playground.

Two kinds of "model": the live LLM agent (whatever LLM_MODEL points at), and
two scripted policies that make the env's behavior easy to see. One scripted
policy does the job properly; the other takes the shortcut the experiment is about.
"""

from __future__ import annotations

from typing import Callable

from rewardlab.agent import llm
from rewardlab.agent.loop import run_episode as run_agent_episode
from rewardlab.env import Scenario, SupportEnv
from rewardlab.schemas import PlaygroundModel, PlaygroundRequest, Trajectory
from rewardlab.trajectory import final_state, take_step

LIVE_MODEL_ID = "llm"

# A policy looks at the tool results so far and returns the next call, or None to finish.
Policy = Callable[[SupportEnv, list[dict]], tuple[str, dict] | None]


def careful(env: SupportEnv, results: list[dict]) -> tuple[str, dict] | None:
    ticket_id = env.world.target_ticket_id
    if len(results) == 0:
        return "lookup_ticket", {"ticket_id": ticket_id}
    order_id = results[0]["order_id"]
    if len(results) == 1:
        return "lookup_order", {"order_id": order_id}
    if len(results) == 2:
        return "lookup_payment", {"order_id": order_id}
    if len(results) == 3:
        refund_owed = results[1]["status"] == "canceled" and results[2]["status"] == "confirmed"
        if refund_owed:
            return "issue_refund", {"order_id": order_id}
        return "close_ticket", {"ticket_id": ticket_id}
    if results[-1].get("status") != "resolved":
        return "close_ticket", {"ticket_id": ticket_id}
    return None


def shortcut(env: SupportEnv, results: list[dict]) -> tuple[str, dict] | None:
    return None if results else ("close_ticket", {"ticket_id": env.world.target_ticket_id})


POLICIES: dict[str, tuple[str, Policy]] = {
    "scripted:careful": ("Scripted · careful (does the job)", careful),
    "scripted:shortcut": ("Scripted · shortcut (closes immediately)", shortcut),
}


def models() -> list[PlaygroundModel]:
    live = PlaygroundModel(id=LIVE_MODEL_ID, label=f"{llm.settings().model} · live agent")
    return [live] + [PlaygroundModel(id=k, label=label) for k, (label, _) in POLICIES.items()]


def run_episode(req: PlaygroundRequest) -> Trajectory:
    if req.model == LIVE_MODEL_ID:
        return run_agent_episode(
            llm.make_client(), llm.settings().model, req.seed, Scenario(req.scenario), run_id="playground"
        )
    if req.model not in POLICIES:
        raise KeyError(req.model)
    _, policy = POLICIES[req.model]

    env = SupportEnv()
    env.reset(seed=req.seed, scenario=Scenario(req.scenario))
    turns, done = [], False
    while not done and (call := policy(env, [t.observation for t in turns])) is not None:
        turn, done = take_step(env, *call)
        turns.append(turn)

    return Trajectory(
        episode_id=f"playground-{req.model.replace(':', '-')}-{req.scenario}-{req.seed}",
        run_id="playground",
        checkpoint_step=0,
        seed=req.seed,
        scenario=req.scenario,
        model=req.model,
        turns=turns,
        final_message=None,
        final_state=final_state(env),
        terminated_by="turn_limit" if done else "agent_finished",
    )
